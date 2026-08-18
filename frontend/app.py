import streamlit as st
import sys
import os

# Add parent directory so we can import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import Orchestrator

st.set_page_config(
    page_title="Aether – Enterprise Data Steward",
    page_icon="📊",
    layout="wide"
)

st.title("Aether – Enterprise Data Steward & BI Copilot")
st.caption("Powered by Exasol + Multi-Agent System")

# Initialize orchestrator only once
@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orch = get_orchestrator()

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Aether** is a multi-agent BI copilot.
    
    Specialized agents collaborate to:
    - Understand your question
    - Explore the database schema
    - Generate safe SQL
    - Run it on **Exasol**
    - Produce clear insights
    """)
    st.markdown("---")
    st.markdown("**Example Questions:**")
    st.code("Compare total revenue by region")
    st.code("Who are the top 10 customers by total spend?")
    st.code("Which suppliers have the highest order volume?")
    st.code("Show average order value by nation")

# Main chat input
question = st.text_input(
    "Ask a business question:",
    placeholder="e.g. Compare total revenue by region",
    key="question_input"
)

if st.button("Ask Aether", type="primary") or (question and st.session_state.get("last_question") != question):
    if question.strip():
        st.session_state["last_question"] = question
        
        with st.spinner("Agents are working..."):
            response = orch.answer(question)
        
        if response["success"]:
            st.success("Answer ready")
            
            # Summary
            st.subheader("Executive Summary")
            st.markdown(response["summary"])
            
            # Data table
            if response.get("data"):
                st.subheader("Results")
                st.dataframe(response["data"], use_container_width=True)
            
            # Technical details (collapsible)
            with st.expander("Technical Details (SQL + Agent Flow)"):
                st.code(response["sql"], language="sql")
                st.write(f"Rows returned: {response['row_count']}")
        else:
            st.error(f"Failed: {response.get('error', 'Unknown error')}")
            if response.get("sql"):
                with st.expander("Generated SQL"):
                    st.code(response["sql"], language="sql")
    else:
        st.warning("Please enter a question.")