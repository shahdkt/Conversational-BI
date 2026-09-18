import psycopg2
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

class SQLQueryOutput(BaseModel):
    query: str = Field(description="Executable PostgreSQL query.")
    explanation: str = Field(description="Technical explanation of the calculation.")

class SQLAgent:
    def __init__(self, db_url: str, llm: ChatGroq):
        self.db_url = db_url
        self.llm = llm

    def execute_query(self, query: str):
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(colnames, row)) for row in results]