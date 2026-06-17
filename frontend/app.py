import streamlit as st

st.set_page_config(
    page_title="OptimizeResume",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("OptimizeResume")
st.sidebar.page_link("pages/1_profile_builder.py", label="Profile Builder", icon="👤")
st.sidebar.page_link("pages/2_generate_resume.py", label="Generate Resume", icon="✨")
st.sidebar.page_link("pages/3_results.py", label="Results", icon="📊")
st.sidebar.page_link("pages/4_history.py", label="History", icon="🕓")

st.title("OptimizeResume")
st.markdown("""
**AI-powered resume optimizer** — tailors your resume to any job description using a
6-node LangGraph agentic pipeline backed by Google Gemini.

**Get started:**
1. Build your **Master Profile** — add all your projects, skills, experience (one-time setup)
2. Paste any **Job Description** to generate a tailored resume
3. Download your optimized resume as **PDF or DOCX**
""")
