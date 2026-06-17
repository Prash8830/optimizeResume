import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="History", page_icon="🕓", layout="wide")
st.title("Resume History")
st.caption("All your JD-specific resume versions, newest first.")

resp = requests.get(f"{BACKEND_URL}/resume/versions", timeout=10)
if resp.status_code != 200:
    st.error("Could not load history.")
    st.stop()

versions = resp.json()
if not versions:
    st.info("No resumes generated yet. Go to Generate Resume to create your first one.")
    st.stop()

for version in versions:
    score = version.get("ats_score", 0)
    color = "green" if score >= 0.75 else ("orange" if score >= 0.5 else "red")
    score_badge = f":{color}[{round(score * 100, 1)}%]"

    with st.expander(
        f"{version.get('role_title', 'Unknown Role')} @ {version.get('company', 'Unknown')} — {score_badge} — {version.get('created_at', '')[:10]}",
        expanded=False,
    ):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_area("Resume", value=version.get("resume_text", ""), height=300, key=f"hist_{version['id']}")
        with col2:
            st.metric("ATS Score", f"{round(score * 100, 1)}%")
            if st.button("Load to Results", key=f"load_{version['id']}"):
                st.session_state["last_version_id"] = version["id"]
                st.success("Loaded! Go to Results page.")

            pdf_resp = requests.get(f"{BACKEND_URL}/export/pdf/{version['id']}", timeout=30)
            if pdf_resp.status_code == 200:
                st.download_button(
                    "Download PDF", data=pdf_resp.content,
                    file_name=f"resume_{version.get('company', 'job')}.pdf",
                    mime="application/pdf", key=f"pdf_{version['id']}",
                )
            docx_resp = requests.get(f"{BACKEND_URL}/export/docx/{version['id']}", timeout=30)
            if docx_resp.status_code == 200:
                st.download_button(
                    "Download DOCX", data=docx_resp.content,
                    file_name=f"resume_{version.get('company', 'job')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"docx_{version['id']}",
                )
