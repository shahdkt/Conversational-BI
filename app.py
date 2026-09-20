import streamlit as st
import pandas as pd
from src.agent import app

# Page Configuration
st.set_page_config(
    page_title="Conversational BI Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    /* Global Page Styling */
    .stApp {
        background-color: #FAFAFA;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Top Fixed Header - Centered */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #FAFAFA;
        z-index: 99999;
        padding: 1.2rem 2rem 0.8rem 2rem;
        border-bottom: 1px solid #E2E8F0;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.03);
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* Adjust main content padding so fixed header doesn't overlap content */
    .main .block-container {
        padding-top: 7rem !important;
    }
    
    /* Headers */
    .main-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #64748B;
        margin: 0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
        z-index: 100000; /* Sidebar above header */
    }
    .sidebar-title {
        font-size: 1rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Custom Sample Questions Card */
    .sample-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .sample-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 0.3rem;
    }
    .sample-subtitle {
        font-size: 0.85rem;
        color: #64748B;
    }
    
    /* Chat Message Styling */
    .stChatMessage {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
    }
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
    }
    
    /* Forcefully Hide All Avatar Containers & Icons */
    div[data-testid="stChatMessageAvatar"],
    div[data-testid="stChatMessageAvatarUser"],
    div[data-testid="stChatMessageAvatarAssistant"],
    .stChatMessageAvatar,
    div[data-testid="stChatMessage"] img,
    div[data-testid="stChatMessage"] svg {
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
        height: 0px !important;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    </style>
""", unsafe_allow_html=True)

# Sample Question Repository
SQL_QUESTIONS = [
    "Quel est le prix moyen au m² des appartements à Lyon 5e ?",
    "Combien de transactions ont été enregistrées à Villeurbanne ?",
    "Quel est le prix moyen d'une maison vs un appartement dans le 69 ?",
    "Quelle est la répartition des ventes par nombre de pièces à Lyon ?",
    "Quelles sont les 5 communes les plus chères du département ?"
]

GRAPH_QUESTIONS = [
    "Trouve les appartements à Lyon 5e avec une surface > 80m².",
    "Affiche les maisons individuelles vendues à Lyon.",
    "Quelles sont les transactions effectuées par Jean Dupont ?",
    "Trouve les entités ayant vendu plus de 3 biens à Lyon 5e."
]

DEFAULT_DROPDOWN_OPTION = "-- Sélectionnez une question suggérée --"
ALL_SAMPLE_QUESTIONS = [DEFAULT_DROPDOWN_OPTION] + SQL_QUESTIONS + GRAPH_QUESTIONS

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = None

# Callback function to handle dropdown selection cleanly
def handle_dropdown_selection():
    selected = st.session_state.get("sample_dropdown")
    if selected and selected != DEFAULT_DROPDOWN_OPTION:
        st.session_state.selected_prompt = selected
        st.session_state.sample_dropdown = DEFAULT_DROPDOWN_OPTION

# Sidebar Architecture Info
with st.sidebar:
    st.markdown('<div class="sidebar-title">System Architecture</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **Core Engine**
    - LLM: Groq (Llama-3.3-70b)
    - Orchestrator: LangGraph StateMachine
    
    ---
    **Relational Store**
    - Neon PostgreSQL
    - Table: `dvf_transactions`
    
    ---
    **Graph Store**
    - Neo4j AuraDB
    - Nodes: `Entity`, `Property`, `Municipality`
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.selected_prompt = None
        st.rerun()

# Centered Top Fixed Header Component
st.markdown("""
    <div class="fixed-header">
        <div class="main-header">Conversational BI Assistant</div>
        <div class="sub-header">French Real Estate Analytics (DVF Lyon / Department 69)</div>
    </div>
""", unsafe_allow_html=True)

# Render Initial Grid Cards when conversation is completely empty
if len(st.session_state.messages) == 0:
    st.markdown("""
        <div class="sample-container">
            <div class="sample-title">Exemples de questions suggérées</div>
            <div class="sample-subtitle">Sélectionnez une question ci-dessous ou utilisez le menu déroulant :</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption("**Statistiques & Agrégations (SQL Engine)**")
        for idx, q in enumerate(SQL_QUESTIONS):
            if st.button(q, key=f"sql_q_{idx}", use_container_width=True):
                st.session_state.selected_prompt = q
                st.rerun()

    with col2:
        st.caption("**Recherche & Entités (Graph Engine)**")
        for idx, q in enumerate(GRAPH_QUESTIONS):
            if st.button(q, key=f"graph_q_{idx}", use_container_width=True):
                st.session_state.selected_prompt = q
                st.rerun()

# Render Active Chat History
for msg in st.session_state.messages:
    avatar_label = "User" if msg["role"] == "user" else "Assistant"
    with st.chat_message(msg["role"]):
        st.markdown(f"**{avatar_label}**")
        
        if "route" in msg and msg["route"]:
            st.caption(f"Route Selected: `{msg['route']}`")
            
        if "query" in msg and msg["query"]:
            with st.expander("View Executed Query"):
                st.code(msg["query"], language="sql" if msg.get("route") == "SQL" else "cypher")
                
        st.markdown(msg["content"])

# Bottom Sample Question Dropdown using on_change callback
st.selectbox(
    "Exemples de questions :",
    options=ALL_SAMPLE_QUESTIONS,
    key="sample_dropdown",
    on_change=handle_dropdown_selection,
    label_visibility="collapsed"
)

# Capture User Input from TextInput
user_input = st.chat_input("Posez une question sur le marché immobilier (ex: Prix moyen au m² à Lyon 5e...)...")

# Resolve input prompt source
prompt = None
if st.session_state.selected_prompt:
    prompt = st.session_state.selected_prompt
    st.session_state.selected_prompt = None
elif user_input:
    prompt = user_input

# Process Execution Pipeline
if prompt:
    # Append User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Execute Pipeline
    try:
        response = app.invoke({"question": prompt})
        
        route = response.get("route", "")
        gen_query = response.get("generated_query", "")
        answer = response.get("final_answer", "")
        
        # Save Assistant Response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": answer,
            "route": route,
            "query": gen_query
        })
    except Exception as e:
        error_msg = f"Une erreur est survenue lors de l'exécution : {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
    st.rerun()