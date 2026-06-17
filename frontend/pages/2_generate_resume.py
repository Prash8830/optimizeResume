import json
import os

import requests
import sseclient
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Generate Resume", page_icon="✨", layout="wide")

st.title("Generate Optimized Resume")
st.caption("Paste any job description. The AI pipeline selects and rewrites your most relevant experience.")

col1, col2 = st.columns([1, 1])
with col1:
    company = st.text_input("Company Name", placeholder="e.g. Google")
with col2:
    role_title = st.text_input("Role Title", placeholder="e.g. AI Engineer")

job_description = st.text_area(
    "Job Description (paste full JD)",
    height=300,
    placeholder="Paste the complete job description here...",
)

st.divider()

NODE_LABELS = {
    "jd_analyzer":      "Analyzing job description...",
    "profile_scorer":   "Scoring your profile against the JD...",
    "content_selector": "Selecting most relevant content...",
    "resume_writer":    "Writing your optimized resume...",
    "ats_checker":      "Running ATS validation...",
    "report_generator": "Generating optimization report...",
}

if st.button("Generate Resume", type="primary", use_container_width=True):
    if not job_description.strip():
        st.error("Please paste a job description.")
        st.stop()

    st.subheader("Pipeline Progress")
    progress_bar = st.progress(0)
    status_text = st.empty()
    ats_placeholder = st.empty()

    node_order = list(NODE_LABELS.keys())
    completed_nodes = 0
    result_data = None

    try:
        with requests.post(
            f"{BACKEND_URL}/resume/generate",
            json={"job_description": job_description, "company": company, "role_title": role_title},
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=180,
        ) as resp:
            client = sseclient.SSEClient(resp)
            for event in client.events():
                if not event.data:
                    continue
                try:
                    data = json.loads(event.data)
                except json.JSONDecodeError:
                    continue

                if data["type"] == "progress":
                    node = data.get("node", "")
                    if data.get("status") == "done":
                        completed_nodes += 1
                        progress_bar.progress(completed_nodes / len(node_order))
                        status_text.success(f"✓ {NODE_LABELS.get(node, node)}")
                        if node == "ats_checker":
                            score = data.get("ats_score", 0)
                            iteration = data.get("iteration", 1)
                            color = "green" if score >= 0.75 else "orange"
                            ats_placeholder.markdown(
                                f"ATS Score after iteration {iteration}: **:{color}[{round(score * 100, 1)}%]**"
                            )
                    else:
                        status_text.info(f"→ {NODE_LABELS.get(node, node)}")

                elif data["type"] == "complete":
                    result_data = data
                    progress_bar.progress(1.0)
                    status_text.success("Pipeline complete!")

    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.stop()

    if result_data:
        version_id = result_data.get("resume_version_id", "")
        ats_score = result_data.get("ats_score", 0)
        st.session_state["last_version_id"] = version_id
        st.success(f"Resume generated! ATS Score: **{round(ats_score * 100, 1)}%**")
        st.info("Go to the **Results** page to preview and download your resume.")
