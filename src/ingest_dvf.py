import os
import pandas as pd
import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load credentials from local .env file
load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = "73946c42"  # Custom tenant username verified in Step 2


def get_secure_ssc_uri(uri: str) -> str:
    """Converts standard Neo4j URIs (neo4j+s:// or neo4j://) to self-signed trust scheme (+ssc)."""
    if uri.startswith("neo4j+s://"):
        return uri.replace("neo4j+s://", "neo4j+ssc://")
    elif uri.startswith("neo4j://"):
        return uri.replace("neo4j://", "neo4j+ssc://")
    elif uri.startswith("bolt+s://"):
        return uri.replace("bolt+s://", "bolt+ssc://")
    elif uri.startswith("bolt://"):
        return uri.replace("bolt://", "bolt+ssc://")
    return uri


def ingest_to_postgres(df: pd.DataFrame):
    """Creates relational schema and inserts transactional records into Neon PostgreSQL."""
    print("--- Ingesting DVF Data into Neon PostgreSQL ---")
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    # 1. Create relational table schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dvf_transactions (
        id SERIAL PRIMARY KEY,
        mutation_id VARCHAR(50),
        mutation_date DATE,
        property_type VARCHAR(50),
        valeur_fonciere NUMERIC(12, 2),
        surface_reelle_bati NUMERIC(10, 2),
        price_per_sqm NUMERIC(10, 2),
        code_departement VARCHAR(10),
        nom_commune VARCHAR(100),
        nombre_pieces_principales INT
    );
    """)
    conn.commit()
    
    # 2. Prepare parameterized bulk insertion query
    insert_query = """
    INSERT INTO dvf_transactions 
    (mutation_id, mutation_date, property_type, valeur_fonciere, surface_reelle_bati, price_per_sqm, code_departement, nom_commune, nombre_pieces_principales)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    records = []
    for idx, row in df.iterrows():
        surface = max(float(row.get("surface_reelle_bati", 1.0)), 1.0)
        valeur = float(row.get("valeur_fonciere", 0.0))
        records.append((
            str(row.get("mutation_id", f"MUT_{idx}")),
            row.get("mutation_date", "2024-01-15"),
            str(row.get("property_type", "Appartement")),
            valeur,
            surface,
            round(valeur / surface, 2),
            str(row.get("code_departement", "75")),
            str(row.get("nom_commune", "Paris")),
            int(row.get("nombre_pieces_principales", 2))
        ))
        
    cursor.executemany(insert_query, records)
    conn.commit()
    print(f"SUCCESS: Inserted {len(records)} records into Neon PostgreSQL.")
    cursor.close()
    conn.close()


def ingest_to_neo4j(df: pd.DataFrame):
    """Creates entity nodes and directed edges inside Neo4j AuraDB."""
    print("--- Ingesting DVF Graph Networks into Neo4j AuraDB ---")
    
    # Format URI to use +ssc protocol scheme for local SSL certificate bypass
    ssc_uri = get_secure_ssc_uri(NEO4J_URI)
    driver = GraphDatabase.driver(ssc_uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    cypher_query = """
    UNWIND $rows AS row
    MERGE (m:Municipality {name: row.nom_commune, department: row.code_departement})
    MERGE (p:Property {id: row.mutation_id})
    ON CREATE SET p.type = row.property_type, p.surface = row.surface_reelle_bati, p.rooms = row.nombre_pieces_principales
    MERGE (p)-[:LOCATED_IN]->(m)
    
    MERGE (b:Entity {name: row.buyer_name, role: 'Buyer'})
    MERGE (s:Entity {name: row.seller_name, role: 'Seller'})
    
    MERGE (s)-[:TRANSFERRED {date: row.mutation_date, price: row.valeur_fonciere}]->(p)
    MERGE (b)-[:ACQUIRED {date: row.mutation_date, price: row.valeur_fonciere}]->(p)
    """
    
    rows = df.to_dict('records')
    with driver.session() as session:
        session.run(cypher_query, rows=rows)
    print("SUCCESS: Ingested graph entities and relationships into Neo4j AuraDB.")
    driver.close()


if __name__ == "__main__":
    # Sample DVF dataset records for ingestion testing
    sample_data = pd.DataFrame([
        {
            "mutation_id": "MUT_2024_001", "mutation_date": "2024-03-10", "property_type": "Appartement",
            "valeur_fonciere": 450000.0, "surface_reelle_bati": 52.0, "code_departement": "75",
            "nom_commune": "Paris 11e", "nombre_pieces_principales": 3, "buyer_name": "Jean Dupont", "seller_name": "SCI Immobilier Centre"
        },
        {
            "mutation_id": "MUT_2024_002", "mutation_date": "2024-04-22", "property_type": "Maison",
            "valeur_fonciere": 820000.0, "surface_reelle_bati": 110.0, "code_departement": "92",
            "nom_commune": "Boulogne-Billancourt", "nombre_pieces_principales": 5, "buyer_name": "Marie Curie", "seller_name": "Jean Dupont"
        },
        {
            "mutation_id": "MUT_2024_003", "mutation_date": "2024-05-05", "property_type": "Appartement",
            "valeur_fonciere": 310000.0, "surface_reelle_bati": 38.0, "code_departement": "75",
            "nom_commune": "Paris 18e", "nombre_pieces_principales": 2, "buyer_name": "Pierre Martin", "seller_name": "Agence Parisienne"
        }
    ])
    
    ingest_to_postgres(sample_data)
    ingest_to_neo4j(sample_data)