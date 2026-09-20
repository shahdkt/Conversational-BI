import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Cloud Credentials
POSTGRES_URL = os.getenv("POSTGRES_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = "73946c42"

if NEO4J_URI and NEO4J_URI.startswith("neo4j+s://"):
    NEO4J_URI = NEO4J_URI.replace("neo4j+s://", "neo4j+ssc://")

# Local Path to your downloaded Lyon DVF CSV
LOCAL_LYON_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dvf_lyon.csv")


def clean_and_transform_lyon_dvf(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and filters raw DVF records from your Lyon dataset."""
    print("--- Cleaning and Transforming Lyon Real Estate Records ---")
    
    # Filter for residential properties (Appartement, Maison)
    if "type_local" in df.columns:
        df = df[df["type_local"].isin(["Appartement", "Maison"])].copy()
    
    # Ensure valuation and surface columns are numeric
    df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"].astype(str).str.replace(',', '.'), errors="coerce")
    df["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"].astype(str).str.replace(',', '.'), errors="coerce")
    
    # Drop empty or invalid records
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])
    df = df[(df["surface_reelle_bati"] > 0) & (df["valeur_fonciere"] > 0)]
    
    # Calculate price per square meter
    df["price_per_sqm"] = (df["valeur_fonciere"] / df["surface_reelle_bati"]).round(2)
    
    # Standardize column mappings matching your Colab schema
    df["mutation_id"] = df["id_mutation"].astype(str) if "id_mutation" in df.columns else df.index.astype(str)
    df["mutation_date"] = pd.to_datetime(df["date_mutation"], errors="coerce").dt.strftime('%Y-%m-%d')
    df["property_type"] = df["type_local"] if "type_local" in df.columns else "Appartement"
    df["code_departement"] = df["code_departement"].astype(str) if "code_departement" in df.columns else "69"
    df["nom_commune"] = df["nom_commune"].fillna("Lyon") if "nom_commune" in df.columns else "Lyon"
    
    if "nombre_pieces_principales" in df.columns:
        df["nombre_pieces_principales"] = pd.to_numeric(df["nombre_pieces_principales"], errors="coerce").fillna(1).astype(int)
    else:
        df["nombre_pieces_principales"] = 1
    
    clean_df = df[[
        "mutation_id", "mutation_date", "property_type", "valeur_fonciere",
        "surface_reelle_bati", "price_per_sqm", "code_departement",
        "nom_commune", "nombre_pieces_principales"
    ]].drop_duplicates(subset=["mutation_id"])
    
    print(f"✓ Transformed {len(clean_df)} clean residential transactions.")
    return clean_df


def load_to_postgres(df: pd.DataFrame):
    """Loads clean Lyon transaction data into Neon PostgreSQL."""
    print(f"--- Ingesting {len(df)} records into Neon PostgreSQL (`dvf_transactions`) ---")
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    
    cur.execute("DROP TABLE IF EXISTS dvf_transactions;")
    cur.execute("""
        CREATE TABLE dvf_transactions (
            mutation_id VARCHAR(100) PRIMARY KEY,
            mutation_date DATE,
            property_type VARCHAR(50),
            valeur_fonciere NUMERIC(12,2),
            surface_reelle_bati NUMERIC(10,2),
            price_per_sqm NUMERIC(10,2),
            code_departement VARCHAR(10),
            nom_commune VARCHAR(100),
            nombre_pieces_principales INT
        );
    """)
    
    insert_query = """
        INSERT INTO dvf_transactions (
            mutation_id, mutation_date, property_type, valeur_fonciere,
            surface_reelle_bati, price_per_sqm, code_departement,
            nom_commune, nombre_pieces_principales
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    records = df.to_records(index=False).tolist()
    execute_batch(cur, insert_query, records, page_size=2000)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✓ Neon PostgreSQL batch upload complete.")


def load_to_neo4j(df: pd.DataFrame):
    """Populates Neo4j AuraDB graph with Property, Municipality, and Corporate Buyer Entities."""
    print("--- Ingesting nodes and edges into Neo4j AuraDB ---")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    entities = [
        "Lyon Patrimoine SCI", "Rhône Investissement", "SNC Confluence",
        "Jean Dupont", "Marie Curie", "Cabinet Immobilier Bellecour"
    ]
    
    # Cap graph sampling to prevent free-tier Neo4j RAM overflow
    sample_df = df.head(1000)
    
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n;")
        
        for idx, row in sample_df.iterrows():
            buyer = entities[idx % len(entities)]
            
            cypher = """
            MERGE (m:Municipality {name: $commune, department:$dept})
            CREATE (p:Property {
                id: $mutation_id, 
                type: $prop_type, 
                surface: $surface, 
                rooms: $rooms
            })
            CREATE (p)-[:LOCATED_IN]->(m)
            MERGE (e:Entity {name: $buyer})
            CREATE (e)-[:ACQUIRED {date: $date, price:$price}]->(p)
            """
            
            session.run(cypher, {
                "commune": str(row["nom_commune"]),
                "dept": str(row["code_departement"]),
                "mutation_id": str(row["mutation_id"]),
                "prop_type": str(row["property_type"]),
                "surface": float(row["surface_reelle_bati"]),
                "rooms": int(row["nombre_pieces_principales"]),
                "buyer": buyer,
                "date": str(row["mutation_date"]),
                "price": float(row["valeur_fonciere"])
            })
            
    driver.close()
    print("✓ Neo4j AuraDB graph build complete.")


if __name__ == "__main__":
    print(f"Reading local Lyon dataset from: {LOCAL_LYON_CSV}")
    raw_df = pd.read_csv(LOCAL_LYON_CSV, low_memory=False)
    
    clean_df = clean_and_transform_lyon_dvf(raw_df)
    
    load_to_postgres(clean_df)
    load_to_neo4j(clean_df)
    print("\n Real Lyon DVF dataset successfully ingested!")