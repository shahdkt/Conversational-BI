from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

class RouteDecision(BaseModel):
    destination: str = Field(
        description="Must be 'SQL' for quantitative/tabular data or 'GRAPH' for network/ownership data."
    )
    reasoning: str = Field(description="Rationale for routing decision.")

class QueryRouter:
    def __init__(self, llm: ChatGroq):
        self.structured_llm = llm.with_structured_output(RouteDecision)

    def route(self, user_query: str) -> RouteDecision:
        prompt = f"""
        Analyze the following real estate query and decide the execution path:
        - Route to 'SQL' if asking for averages, aggregations, prices, or market trends.
        - Route to 'GRAPH' if asking about ownership chains, buyer-seller networks, or agency connections.

        User Query: "{user_query}"
        """
        return self.structured_llm.invoke(prompt)