import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

class RouteDecision(BaseModel):
    destination: Literal["SQL", "GRAPH"] = Field(
        ..., 
        description="SQL for numerical aggregations/averages/prices. GRAPH for named people, buyers, sellers, or property networks."
    )
    reasoning: str = Field(..., description="Explanation for routing decision.")

class QueryRouter:
    def __init__(self, llm: ChatGroq):
        self.structured_llm = llm.with_structured_output(RouteDecision)

    def route(self, question: str) -> RouteDecision:
        prompt = f"""
        Classify the query into SQL or GRAPH based on these strict rules:
        
        - **GRAPH**: Use if the query mentions specific people, buyers, sellers, entity names (e.g., 'Jean Dupont'), or asks about ownership, transfers, or relationships.
        - **SQL**: Use if the query asks for numerical aggregations, average prices, price per sqm, room counts, or general statistics in a municipality/department.
        
        Question: {question}
        """
        return self.structured_llm.invoke(prompt)