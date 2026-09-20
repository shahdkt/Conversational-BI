import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq


class RouteDecision(BaseModel):
    destination: Literal["SQL", "GRAPH"] = Field(
        ..., 
        description="SQL for numerical aggregations/averages/prices/counts. GRAPH for named people, entities, buyers, property ownership, or location-based node listings."
    )
    reasoning: str = Field(..., description="Explanation for routing decision.")


class QueryRouter:
    def __init__(self, llm: ChatGroq):
        self.structured_llm = llm.with_structured_output(RouteDecision)

    def route(self, question: str) -> RouteDecision:
        prompt = f"""
        You are an expert routing classifier for a French Real Estate Conversational BI system.
        Classify the query into 'SQL' or 'GRAPH' based on these strict rules:

        - **GRAPH**: Use if the query asks about:
          1. Specific people, buyers, sellers, or corporate entities (e.g., 'Jean Dupont', 'Rhône Investissement').
          2. Property networks, ownership, acquisitions, or transfer relationships.
          3. Node listings or location mappings (e.g., 'Quelles sont les propriétés situées dans...', 'Show properties in...', 'Entities in...').

        - **SQL**: Use if the query asks for:
          1. Numerical aggregations, calculations, or financial metrics (e.g., average price, median value, price per sqm).
          2. Transaction volume counts or statistical distributions (e.g., 'Prix moyen au m²', 'Combien de transactions...').
          3. Max/min property valuations or room count filtering.

        Question: {question}
        """
        return self.structured_llm.invoke(prompt)