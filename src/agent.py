import os
import sys
from pathlib import Path
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

sys.path.append(str(Path(__file__).parent.parent))

from src.router import QueryRouter
from src.sql_agent import SQLAgent
from src.graph_agent import GraphAgent

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = "73946c42"

if NEO4J_URI and NEO4J_URI.startswith("neo4j+s://"):
    NEO4J_URI = NEO4J_URI.replace("neo4j+s://", "neo4j+ssc://")

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, groq_api_key=GROQ_API_KEY)
router = QueryRouter(llm=llm)
sql_agent = SQLAgent(db_url=POSTGRES_URL, llm=llm)
graph_agent = GraphAgent(uri=NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), llm=llm)


class AgentState(TypedDict):
    question: str
    route: str
    generated_query: str
    query_results: str
    final_answer: str


def router_node(state: AgentState) -> AgentState:
    print(f"\n--- [Node: Router] Question: '{state['question']}' ---")
    decision = router.route(state["question"])
    print(f"-> Destination: {decision.destination} | Rationale: {decision.reasoning}")
    return {**state, "route": decision.destination}


def sql_node(state: AgentState) -> AgentState:
    print("--- [Node: SQL Agent] Processing Relational Path ---")
    
    # Exact table context provided to avoid bad SQL generation
    schema_info = """
    Table: dvf_transactions
    Columns:
    - mutation_id (VARCHAR)
    - mutation_date (DATE)
    - property_type (VARCHAR) -- e.g. 'Appartement', 'Maison'
    - valeur_fonciere (NUMERIC)
    - surface_reelle_bati (NUMERIC)
    - price_per_sqm (NUMERIC)
    - code_departement (VARCHAR) -- e.g. '75'
    - nom_commune (VARCHAR) -- e.g. 'Paris 11e', 'Paris 18e', 'Boulogne-Billancourt'
    - nombre_pieces_principales (INT)
    """
    
    prompt = f"""
    Write ONLY a valid PostgreSQL SQL query (no markdown, no ```sql formatting) to answer the user request.
    {schema_info}
    
    User Question: {state['question']}
    """
    generated_sql = llm.invoke(prompt).content.strip().replace("```sql", "").replace("```", "").strip()
    
    try:
        results = sql_agent.execute_query(generated_sql)
    except Exception as e:
        results = f"SQL Execution Error: {str(e)}"
        
    return {**state, "generated_query": generated_sql, "query_results": str(results)}


def graph_node(state: AgentState) -> AgentState:
    print("--- [Node: Graph Agent] Processing Network Path ---")
    
    graph_info = """
    Neo4j Graph Schema:
    - Nodes:
      (:Property {id, type, surface, rooms})
      (:Municipality {name, department})
      (:Entity {name, role})
    - Relationships:
      (:Property)-[:LOCATED_IN]->(:Municipality)
      (seller:Entity)-[:TRANSFERRED {date, price}]->(p:Property)
      (buyer:Entity)-[:ACQUIRED {date, price}]->(p:Property)
    """
    
    prompt = f"""
    Write ONLY a valid Cypher query (no markdown, no ```cypher formatting) to answer the user request.
    {graph_info}
    
    User Question: {state['question']}
    """
    generated_cypher = llm.invoke(prompt).content.strip().replace("```cypher", "").replace("```", "").strip()
    
    try:
        results = graph_agent.execute_cypher(generated_cypher)
    except Exception as e:
        results = f"Graph Execution Error: {str(e)}"
        
    return {**state, "generated_query": generated_cypher, "query_results": str(results)}


def synthesizer_node(state: AgentState) -> AgentState:
    print("--- [Node: Synthesizer] Drafting Final Answer ---")
    prompt = f"""
    You are an expert Real Estate BI Assistant. Answer the user's question clearly using ONLY the provided database results.
    
    User Question: {state['question']}
    Execution Engine: {state['route']}
    Executed Query: {state['generated_query']}
    Retrieved Data: {state['query_results']}
    
    Respond in the language of the question.
    """
    response = llm.invoke(prompt)
    return {**state, "final_answer": response.content}


def route_decision(state: AgentState) -> str:
    return "sql_agent" if state["route"] == "SQL" else "graph_agent"


workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("sql_agent", sql_node)
workflow.add_node("graph_agent", graph_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("router")
workflow.add_conditional_edges("router", route_decision, {"sql_agent": "sql_agent", "graph_agent": "graph_agent"})

workflow.add_edge("sql_agent", "synthesizer")
workflow.add_edge("graph_agent", "synthesizer")
workflow.add_edge("synthesizer", END)

app = workflow.compile()


if __name__ == "__main__":
    # Test 1: Relational SQL Query
    res_sql = app.invoke({"question": "Quel est le prix moyen au mètre carré des appartements à Paris 11e?"})
    print(f"\n[FINAL RESPONSE - SQL PATH]:\n{res_sql['final_answer']}\n")
    print("=" * 70)

    # Test 2: Graph Network Query
    res_graph = app.invoke({"question": "Quelles transactions ont été effectuées par Jean Dupont?"})
    print(f"\n[FINAL RESPONSE - GRAPH PATH]:\n{res_graph['final_answer']}\n")