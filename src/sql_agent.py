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

    def generate_query(self, question: str) -> SQLQueryOutput:
        """Generates a structured PostgreSQL query with flexible fuzzy matching for location names."""
        system_prompt = """You are a SQL expert converting natural language questions into PostgreSQL queries for the `dvf_transactions` table.

Table Schema:
- mutation_id (VARCHAR)
- mutation_date (DATE)
- property_type (VARCHAR) -- 'Appartement' or 'Maison'
- valeur_fonciere (NUMERIC)
- surface_reelle_bati (NUMERIC)
- price_per_sqm (NUMERIC)
- code_departement (VARCHAR)
- nom_commune (VARCHAR) -- e.g. 'Lyon 5e Arrondissement', 'Caluire-et-Cuire'
- nombre_pieces_principales (INT)

STRICT RULES FOR LOCATION MATCHING:
1. Always use case-insensitive partial matching (ILIKE) for `nom_commune`.
2. Extract the core number or name from user queries:
   - For "Lyon 6e", "Lyon 6ème", or "Lyon 6", use: nom_commune ILIKE '%Lyon 6%'
   - For "Lyon 3e", use: nom_commune ILIKE '%Lyon 3%'
   - For "Villeurbanne", use: nom_commune ILIKE '%Villeurbanne%'
3. Never use exact equality (`=`) when filtering `nom_commune`.
"""

        structured_llm = self.llm.with_structured_output(SQLQueryOutput)
        messages = [
            ("system", system_prompt),
            ("user", question)
        ]
        return structured_llm.invoke(messages)

    def execute_query(self, query: str):
        """Executes the generated SQL query on Neon PostgreSQL and returns list of dicts."""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(colnames, row)) for row in results]