import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "")
# Use your database user ID as fallback if not present in .env
NEO4J_USER = os.getenv("NEO4J_USER", "73946c42")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# Automatically handle self-signed certificate protocol for Neo4j Cloud/Aurora
if NEO4J_URI:
    if NEO4J_URI.startswith("neo4j+s://"):
        NEO4J_URI = NEO4J_URI.replace("neo4j+s://", "neo4j+ssc://")
    elif NEO4J_URI.startswith("bolt+s://"):
        NEO4J_URI = NEO4J_URI.replace("bolt+s://", "bolt+ssc://")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

with driver.session() as session:
    print("\n--- DATABASE SCHEMA CHECK ---")
    labels = session.run("CALL db.labels()").value()
    print("📌 Node Labels in Database:", labels)

    rel_types = session.run("CALL db.relationshipTypes()").value()
    print("📌 Relationship Types in Database:", rel_types)

    print("\n--- PROPERTY DATA INSPECTION ---")
    sample_props = session.run("""
        MATCH (p:Property)-[:LOCATED_IN]->(m:Municipality)
        RETURN p.type AS type, p.rooms AS rooms, p.surface AS surface, m.name AS municipality
        LIMIT 5
    """).data()
    
    print("🔍 Sample Property Records:")
    for record in sample_props:
        print("  ", record)

driver.close()