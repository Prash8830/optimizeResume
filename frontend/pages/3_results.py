import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
st.title("Resume Results")

version_id = st.session_state.get("last_version_id")
if not version_id:
    st.info("No resume generated yet. Go to Generate Resume first.")
    st.stop()

resp = requests.get(f"{BACKEND_URL}/resume/versions/{version_id}", timeout=10)
if resp.status_code != 200:
    st.error("Could not load resume version.")
    st.stop()

version = resp.json()
report = version.get("optimization_report", {})
ats_score = version.get("ats_score", 0)

# ── SCORE HEADER ───────────────────────────────────────
col_score, col_info = st.columns([1, 3])
with col_score:
    st.metric("ATS Match Score", f"{round(ats_score * 100, 1)}%")
with col_info:
    st.markdown(f"**Role:** {version.get('role_title', '')} at {version.get('company', '')}")
    st.markdown(f"**Iterations:** {report.get('iteration_count', 1)} | **Word count:** {report.get('word_count', 0)}")

st.divider()

tab_resume, tab_report, tab_download = st.tabs(["Resume Preview", "Optimization Report", "Download"])

with tab_resume:
    st.text_area("Your Optimized Resume", value=version.get("resume_text", ""), height=600)

with tab_report:
    kw_coverage = report.get("required_keyword_coverage", {})
    matched = kw_coverage.get("matched", [])
    missing = kw_coverage.get("missing", [])

    col_matched, col_missing = st.columns(2)
    with col_matched:
        st.success(f"Matched Keywords ({len(matched)})")
        for kw in matched:
            st.markdown(f"- ✓ {kw}")
    with col_missing:
        st.warning(f"Missing Keywords ({len(missing)})")
        for kw in missing:
            st.markdown(f"- ✗ {kw}")

    st.divider()
    gap_skills = report.get("gap_skills", [])
    if gap_skills:
        st.error("Skill Gaps (not in your profile)")
        for skill in gap_skills:
            st.markdown(f"- {skill}")

    swappable = report.get("swappable_items", [])
    if swappable:
        st.info("Swappable Items (scored well but didn't fit — you can add manually)")
        for item in swappable:
            st.markdown(f"- `{item['content']}` *(score: {item['score']})*")

with tab_download:
    st.subheader("Download Your Resume")
    col_pdf, col_docx = st.columns(2)
    with col_pdf:
        pdf_resp = requests.get(f"{BACKEND_URL}/export/pdf/{version_id}", timeout=30)
        if pdf_resp.status_code == 200:
            st.download_button(
                label="Download PDF",
                data=pdf_resp.content,
                file_name=f"resume_{version.get('company', 'job')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    with col_docx:
        docx_resp = requests.get(f"{BACKEND_URL}/export/docx/{version_id}", timeout=30)
        if docx_resp.status_code == 200:
            st.download_button(
                label="Download DOCX",
                data=docx_resp.content,
                file_name=f"resume_{version.get('company', 'job')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
