import streamlit as st

st.set_page_config(
    page_title="OptimizeResume",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state defaults
if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from components.auth_panel import render_auth

if not st.session_state.token:
    render_auth()
else:
    st.sidebar.success(f"Logged in")
    st.sidebar.page_link("pages/1_profile_builder.py", label="Profile Builder", icon="👤")
    st.sidebar.page_link("pages/2_generate_resume.py", label="Generate Resume", icon="✨")
    st.sidebar.page_link("pages/3_results.py", label="Results", icon="📊")
    st.sidebar.page_link("pages/4_history.py", label="History", icon="🕓")

    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.user_id = None
        st.rerun()

    st.title("OptimizeResume")
    st.markdown("""
    **AI-powered resume optimizer** — tailors your resume to any job description using a
    6-node LangGraph agentic pipeline backed by Google Gemini.

    **Get started:**
    1. Build your **Master Profile** (one-time setup)
    2. Paste any **Job Description** to generate a tailored resume
    3. Download your optimized resume as **PDF or DOCX**
    """)
