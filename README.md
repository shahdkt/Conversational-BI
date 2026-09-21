# Conversational BI Assistant

[Live Interactive Demo](https://conversational-bi-ui.streamlit.app) 

Ask questions about French real estate transactions in plain English or French, and get answers from the right database.
Instead of writing SQL or Cypher by hand, the system reads your question, decides whether it needs a relational database (PostgreSQL) or a graph database (Neo4j), writes the query, runs it and shows the result.

## What this project does:
- **Smart Question Routing:** Automatically sends relational questions (like averages or sums) to PostgreSQL, and relationship questions (like property ownership connections) to Neo4j.
- **Data Ingestion:** Automatically loads and structures official French real estate data (DVF dataset) into both databases.
- **User Interface:** Simple web app built with Streamlit so anyone can type questions and see visual results.
- **Automated Testing:** Script that runs 50 real test questions to test accuracy and execution speed.

## How it works: 
1. **User Input:** You ask a question in the Streamlit app.
2. **Intent Router:** An LLM agent analyzes the question to decide if PostgreSQL or Neo4j is best suited to answer it.
3. **Query Generation & Execution:** The selected agent writes the database query (SQL or Cypher), runs it against the live database, and formats the response.

## Performance results:
Tested on a suite of 50 sample questions:
- **Routing Accuracy:** 70.0% (picks the right database agent)
- **Query Execution Success:** 72.0% (returns correct results without error)
- **Average Latency:** 12.96 seconds per query

## What I would do next:
- **Better Routing Prompts:** Add example questions to the router prompt to get accuracy above 80%.
- **Faster Responses:** Trim database schemas sent to the LLM to lower response time below 5 seconds.
- **Error Recovery:** Add a retry mechanism so if a generated query fails, the system fixes its own syntax and tries again.
  

## How to run the project
### 1. Set up the project
```bash
git clone https://github.com/shahdkt/Conversational-BI.git
cd Conversational-BI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials:
Create a .env file in the root directory with the following variables:

```env
GROQ_API_KEY=groq_api_key
POSTGRES_URL=postgres_connection_string
NEO4J_URI=neo4j_uri
NEO4J_PASSWORD=neo4j_password
```

### 3. Verify database connections:

```bash
python check_schema.py
```

### 4. Launch the app:

```bash
streamlit run app.py
```

### Author
Shahd AlKattan.


