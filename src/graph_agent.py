from neo4j import GraphDatabase
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


class GraphQueryOutput(BaseModel):
    query: str = Field(description="Executable Cypher query for Neo4j.")
    explanation: str = Field(description="Technical explanation of the graph traversal.")


class GraphAgent:
    def __init__(self, uri: str, auth: tuple, llm: ChatGroq):
        if uri:
            if uri.startswith("neo4j+s://"):
                uri = uri.replace("neo4j+s://", "neo4j+ssc://")
            elif uri.startswith("bolt+s://"):
                uri = uri.replace("bolt+s://", "bolt+ssc://")
            
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.llm = llm

    def generate_query(self, question: str) -> GraphQueryOutput:
        system_prompt = """You are an expert Cypher query engineer converting natural language questions into executable Neo4j queries for French DVF real estate data.

EXACT GRAPH SCHEMA (STRICTLY ADHERE TO THIS):
Node Labels:
- (:Municipality {name: STRING})
- (:Property {id: STRING, type: STRING, surface: FLOAT, rooms: INT})
- (:Entity {name: STRING})

Allowed Relationship Types (ONLY USE THESE TWO):
- (:Property)-[:LOCATED_IN]->(:Municipality)
- (:Entity)-[:ACQUIRED {date: STRING, price: FLOAT}]->(:Property)

CRITICAL RULES FOR CYPHER GENERATION:

1. PROPERTY TYPE VALUES (MUST USE FRENCH TERMS):
   - "apartment" / "appartement" -> `p.type =~ '(?i).*appartement.*'`
   - "house" / "maison" -> `p.type =~ '(?i).*maison.*'`
   - DO NOT filter by `p.type` unless the user explicitly specifies apartment or house.

2. MUNICIPALITY REGEX PATTERNS (KEEP PATTERNS FLEXIBLE):
   - NEVER use exact string equality (`=`). ALWAYS use case-insensitive regex:
     `WHERE m.name =~ '(?i).*<term>.*'`
   - Examples:
     - "Lyon 2e" / "Lyon 2" -> `WHERE m.name =~ '(?i).*lyon.*2.*'`
     - "Lyon 5e" -> `WHERE m.name =~ '(?i).*lyon.*5.*'`
     - "Lyon 6e" -> `WHERE m.name =~ '(?i).*lyon.*6.*'`
     - "Villeurbanne" -> `WHERE m.name =~ '(?i).*villeurbanne.*'`
   - DO NOT force suffixes like "Arrondissement" or trailing 'e' letters into the regex pattern. Match the core city name and district number.

3. NUMERIC ATTRIBUTE FILTERS:
   - Rooms: `p.rooms > X` or `p.rooms = X`
   - Surface: `p.surface > X` or `p.surface = X`

4. ENTITY & BUYER QUERIES:
   - If asked for buyers or entity acquisitions, match `(:Entity)-[:ACQUIRED]->(:Property)` or `(:Entity)-[:ACQUIRED]-(:Property)`.

5. ALWAYS RETURN EXPLICIT ALIASES:
   `RETURN p.id AS propertyId, p.type AS type, p.surface AS surface, p.rooms AS rooms, m.name AS municipality`
"""

        structured_llm = self.llm.with_structured_output(GraphQueryOutput)
        messages = [
            ("system", system_prompt),
            ("user", question)
        ]
        return structured_llm.invoke(messages)

    def execute_cypher(self, cypher_query: str):
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [record.data() for record in result]

    def close(self):
        self.driver.close()