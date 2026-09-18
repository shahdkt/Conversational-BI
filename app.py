import streamlit as st
from src.agent import app

st.set_page_config(
    page_title="Conversational BI Assistant",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Conversational BI — Hybrid SQL/Graph Assistant")
st.markdown("Ask questions about real estate transactions using hybrid database retrieval (PostgreSQL + Neo4j).")

# Sidebar - Architecture Info
st.sidebar.header("System Architecture")
st.sidebar.markdown("""
- **LLM Engine:** Groq (gpt-oss-120b)
- **Relational DB:** Neon PostgreSQL (`dvf_transactions`)
- **Graph DB:** Neo4j AuraDB (`Entity`, `Property`, `Municipality`)
- **Orchestration:** LangGraph Multi-Agent StateMachine
""")

# Chat History Setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ex: Quel est le prix moyen au m² à Paris 11e? or Quelles transactions par Jean Dupont?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing & Executing Query..."):
            try:
                response = app.invoke({"question": prompt})
                
                # Display Route Metadata
                st.caption(f"**Route Selected:** `{response['route']}` | **Generated Query:** `{response['generated_query']}`")
                
                # Display Final Answer
                answer = response["final_answer"]
                st.markdown(answer)
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"An error occurred during execution: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})