import streamlit as st
import sys
import os
import importlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv

load_dotenv()

# Add parent directory so we can import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import agents.schema_agent
import agents.sql_agent
import agents.governance_agent
import agents.storyteller_agent
import agents.orchestrator

importlib.reload(agents.schema_agent)
importlib.reload(agents.sql_agent)
importlib.reload(agents.governance_agent)
importlib.reload(agents.storyteller_agent)
importlib.reload(agents.orchestrator)

from agents.orchestrator import Orchestrator

st.set_page_config(
    page_title="Aether Copilot | Exasol",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State for Conversational Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

if "auto_submit_query" not in st.session_state:
    st.session_state.auto_submit_query = None

def get_orchestrator():
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = Orchestrator()
    return st.session_state.orchestrator

orch = get_orchestrator()

def transcribe_audio(audio_bytes):
    """Uses Groq Whisper API for STT"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "GROQ_API_KEY is not set."
        
    try:
        files = {'file': ('audio.wav', audio_bytes, 'audio/wav')}
        data = {'model': 'whisper-large-v3-turbo'}
        headers = {'Authorization': f'Bearer {api_key}'}
        
        response = requests.post('https://api.groq.com/openai/v1/audio/transcriptions', headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json().get('text', '')
    except Exception as e:
        st.error(f"Error in transcription: {e}")
        try:
            st.error(response.text)
        except:
            pass
        return None

# ==========================================
# CSS (Enterprise Dark/Light Mode)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp, h1, h2, h3, h4, h5, h6, p, li, label, input, button, span, div {
        font-family: 'Inter', sans-serif;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 1400px !important;
    }
    
    /* Top Header */
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 24px;
        backdrop-filter: blur(12px);
        margin-top: -1rem;
        margin-bottom: 2rem;
        border-radius: 12px;
    }

    /* Cards */
    .card, .insight-card {
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(15, 23, 42, 0.08);
    }
    
    /* KPI */
    .kpi-container { height: 100%; display: flex; flex-direction: column; }
    .kpi-value { font-size: 2.25rem; font-weight: 700; letter-spacing: -0.03em; margin-bottom: 8px; }
    .kpi-label { font-size: 0.875rem; font-weight: 500; display: flex; align-items: center; gap: 6px; }
    
    /* Trends */
    .trend-indicator { font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 4px; padding: 4px 8px; border-radius: 6px; }
    .trend-up { background: rgba(16, 185, 129, 0.1); color: #10B981; }

    /* Light Theme */
    @media (prefers-color-scheme: light) {
        .stApp { background-color: #F8FAFC !important; color: #0F172A !important; }
        .card, .insight-card { background-color: #FFFFFF; }
        .muted-text { color: #64748B; }
        .top-header { background-color: rgba(255, 255, 255, 0.8); border-bottom: 1px solid rgba(15, 23, 42, 0.08); }
        .agent-card { background-color: #FFFFFF; border: 1px solid #E2E8F0; }
        .agent-card:hover { border-color: #4F46E5; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1); }
    }

    /* Dark Theme */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #080B14 !important; color: #F8FAFC !important; }
        .card, .insight-card { background-color: #111827; border-color: rgba(148, 163, 184, 0.15); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); }
        .muted-text { color: #94A3B8; }
        .top-header { background-color: rgba(8, 11, 20, 0.8); border-bottom: 1px solid rgba(148, 163, 184, 0.1); }
        .agent-card { background-color: #111827; border: 1px solid #1E293B; }
        .agent-card:hover { border-color: #818CF8; box-shadow: 0 4px 20px rgba(79, 70, 229, 0.15); }
    }
    
    .agent-card {
        padding: 12px 16px; border-radius: 12px; margin-bottom: 12px; transition: all 0.2s; position: relative; overflow: hidden;
    }
    .agent-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: #4F46E5; opacity: 0.3; }
    .agent-card:hover::before { opacity: 1; width: 4px; }
    
    .insight-card { display: flex; gap: 20px; position: relative; }
    .insight-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: #06B6D4; }
    
    /* Chat message overrides */
    .stChatMessage {
        background-color: transparent !important;
        padding: 1rem 0 !important;
    }
    
    /* Audio input wrapper */
    .audio-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
        <span style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.04em;">EXASOL</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 32px; padding: 8px 12px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2); font-size: 0.8rem; font-weight: 600; color: #10B981;">
        <div style="width: 8px; height: 8px; background-color: #10B981; border-radius: 50%;"></div>
        Workspace Connected
    </div>
    
    <div class="muted-text" style="font-size: 0.85rem; margin-bottom: 24px; text-transform: uppercase; font-weight: 600;">AI Copilots</div>
    
    <div class="agent-card"><div class="agent-header" style="font-weight: 600;">Schema Agent</div><div class="agent-desc muted-text" style="font-size: 0.8rem;">Database structure discovery</div></div>
    <div class="agent-card"><div class="agent-header" style="font-weight: 600;">SQL Agent</div><div class="agent-desc muted-text" style="font-size: 0.8rem;">Natural language to Exasol SQL</div></div>
    <div class="agent-card"><div class="agent-header" style="font-weight: 600;">Governance Agent</div><div class="agent-desc muted-text" style="font-size: 0.8rem;">Security & read-only enforcement</div></div>
    <div class="agent-card"><div class="agent-header" style="font-weight: 600;">Storyteller Agent</div><div class="agent-desc muted-text" style="font-size: 0.8rem;">Executive-ready insights + Dynamic Charts</div></div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**🎙️ Voice Query**")
    audio_val = st.audio_input("Record a query")
    if audio_val:
        with st.spinner("Transcribing via Groq Whisper..."):
            text = transcribe_audio(audio_val.getvalue())
            if text:
                st.session_state.auto_submit_query = text
                st.rerun()

# ==========================================
# MAIN APP HEADER
# ==========================================
st.markdown("""
<div class="top-header">
    <div class="breadcrumbs muted-text" style="font-size: 0.85rem; font-weight: 500;">Workspace / Aether / Analytics</div>
    <div style="display: flex; gap: 16px; align-items: center;">
        <div style="padding: 6px 12px; border-radius: 9999px; font-size: 0.8rem; color: #94A3B8; border: 1px solid #E2E8F0;">Search (⌘K)</div>
        <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #4F46E5, #06B6D4); color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px;">JD</div>
    </div>
</div>
""", unsafe_allow_html=True)

# HERO & INPUT
st.markdown("""
<div style="text-align: center; max-width: 800px; margin: 0 auto 2rem auto;">
    <div style="font-size: 2.75rem; font-weight: 800; letter-spacing: -0.04em; margin-bottom: 0.75rem;">Aether <span style="background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Copilot</span></div>
    <div class="muted-text">Ask complex business questions in plain English, securely powered by Exasol Data Intelligence.</div>
</div>
""", unsafe_allow_html=True)

def handle_text_submit():
    if st.session_state.top_query_input:
        st.session_state.auto_submit_query = st.session_state.top_query_input
        st.session_state.top_query_input = ""

st.text_input(
    "Ask a business question... (e.g., 'Compare total revenue by region')", 
    key="top_query_input", 
    on_change=handle_text_submit,
    placeholder="Ask a business question... (e.g., 'Compare total revenue by region')"
)

def set_q(q):
    st.session_state.auto_submit_query = q

if not st.session_state.messages:
    st.markdown('<div style="display: flex; justify-content: center; gap: 10px; margin-top: 1rem;">', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]: st.button("📊 Revenue by region", on_click=set_q, args=("Compare total revenue by region",), use_container_width=True)
    with cols[1]: st.button("👥 Top 10 customers", on_click=set_q, args=("Who are the top 10 customers by total spend?",), use_container_width=True)
    with cols[2]: st.button("🚚 Top suppliers", on_click=set_q, args=("Which suppliers have the highest order volume?",), use_container_width=True)
    with cols[3]: st.button("📅 Parts ordered per year", on_click=set_q, args=("What is the total quantity of parts ordered per year?",), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# EXECUTION LOGIC
# ==========================================
if st.session_state.auto_submit_query:
    prompt = st.session_state.auto_submit_query
    st.session_state.auto_submit_query = None
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("AI Agents processing query..."):
        chat_context = [{"role": m["role"], "content": m["content"] if m["role"] == "user" else m["content"].get("sql", "")} for m in st.session_state.messages[:-1]]
        response = orch.answer(prompt, chat_history=chat_context)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================
# CHAT RENDER LOOP
# ==========================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🌌" if msg["role"] == "assistant" else "👤"):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            resp = msg["content"]
            if not resp.get("success"):
                st.error(resp.get("error"))
                if resp.get("sql"):
                    st.code(resp["sql"], language="sql")
                continue
                
            st.markdown(f"""
            <div class="insight-card card">
                <div style="font-size: 2rem;">✨</div>
                <div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 8px;">Executive Summary</div>
                    <div class="muted-text">{resp.get("summary")}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if resp.get("data") and resp.get("columns"):
                df = pd.DataFrame(resp["data"], columns=resp["columns"])
                
                tab_viz, tab_data, tab_sql = st.tabs(["📊 Visualization", "📋 Data Table", "🛠️ Execution & SQL"])
                
                with tab_viz:
                    st.markdown('<div class="card" style="padding: 16px;">', unsafe_allow_html=True)
                    chart_config = resp.get("chart_config")
                    
                    if chart_config and chart_config.get("x") and chart_config.get("y"):
                        c_type = chart_config.get("type", "bar")
                        x_col = chart_config["x"]
                        y_col = chart_config["y"]
                        
                        try:
                            is_dark = st.get_option("theme.base") == "dark"
                            bg_color = "rgba(0,0,0,0)"
                            font_color = "#F8FAFC" if is_dark else "#0F172A"
                            template = "plotly_dark" if is_dark else "plotly_white"
                            
                            if c_type == "line": fig = px.line(df, x=x_col, y=y_col, template=template, markers=True)
                            elif c_type == "pie": fig = px.pie(df, names=x_col, values=y_col, template=template)
                            elif c_type == "scatter": fig = px.scatter(df, x=x_col, y=y_col, template=template, size=y_col)
                            else: fig = px.bar(df, x=x_col, y=y_col, template=template, color=y_col, color_continuous_scale="Purp")
                                
                            fig.update_layout(
                                plot_bgcolor=bg_color, paper_bgcolor=bg_color, font_color=font_color,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Could not render AI requested chart ({c_type}). Showing table instead.")
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.info("AI determined this data is better viewed as a table.")
                        st.dataframe(df, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with tab_data:
                    st.markdown('<div class="card" style="padding: 16px;">', unsafe_allow_html=True)
                    st.dataframe(df, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with tab_sql:
                    st.markdown("""
                    <div style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; background: rgba(16, 185, 129, 0.1); color: #10B981; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; margin-bottom: 12px;">
                        Read-only query approved
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(resp["sql"], language="sql")