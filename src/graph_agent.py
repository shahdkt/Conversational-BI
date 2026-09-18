from neo4j import GraphDatabase
from langchain_groq import ChatGroq

class GraphAgent:
    def __init__(self, uri: str, auth: tuple, llm: ChatGroq):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.llm = llm

    def execute_cypher(self, cypher_query: str):
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [record.data() for record in result]

    def close(self):
        self.driver.close()