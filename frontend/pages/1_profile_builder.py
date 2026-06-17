import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Profile Builder", page_icon="👤", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

st.title("Master Profile Builder")
st.caption("This is your complete experience database. Fill it once — the AI selects what to show per JD.")


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ── BASIC INFO ──────────────────────────────────────────
st.subheader("Basic Information")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
with col2:
    linkedin = st.text_input("LinkedIn URL")
    github = st.text_input("GitHub URL")

summary = st.text_area("Professional Summary (write maximum detail — AI will trim per JD)", height=100)

st.divider()

# ── PROJECTS ───────────────────────────────────────────
st.subheader("Projects")
st.caption("Add ALL your projects. AI picks the most relevant ones per JD.")

if "projects" not in st.session_state:
    st.session_state.projects = [{}]

for i, proj in enumerate(st.session_state.projects):
    with st.expander(f"Project {i+1}: {proj.get('title', 'Untitled')}", expanded=(i == 0)):
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.session_state.projects[i]["title"] = st.text_input("Title", value=proj.get("title", ""), key=f"p_title_{i}")
            st.session_state.projects[i]["duration"] = st.text_input("Duration (e.g. Jan 2024 – Mar 2024)", value=proj.get("duration", ""), key=f"p_dur_{i}")
            st.session_state.projects[i]["github_url"] = st.text_input("GitHub URL", value=proj.get("github_url", ""), key=f"p_gh_{i}")
        with p_col2:
            tech_raw = st.text_input("Tech Stack (comma-separated)", value=", ".join(proj.get("tech_stack", [])), key=f"p_tech_{i}")
            st.session_state.projects[i]["tech_stack"] = [t.strip() for t in tech_raw.split(",") if t.strip()]
            role_raw = st.text_input("Role Types (e.g. Agentic AI, GenAI)", value=", ".join(proj.get("role_types", [])), key=f"p_role_{i}")
            st.session_state.projects[i]["role_types"] = [r.strip() for r in role_raw.split(",") if r.strip()]
        st.session_state.projects[i]["description"] = st.text_area("Description (full detail)", value=proj.get("description", ""), key=f"p_desc_{i}", height=80)
        outcomes_raw = st.text_area("Outcomes (one per line, quantify if possible)", value="\n".join(proj.get("outcomes", [])), key=f"p_out_{i}", height=60)
        st.session_state.projects[i]["outcomes"] = [o.strip() for o in outcomes_raw.split("\n") if o.strip()]

col_add, col_rem = st.columns([1, 5])
with col_add:
    if st.button("+ Add Project"):
        st.session_state.projects.append({})
        st.rerun()
with col_rem:
    if len(st.session_state.projects) > 1 and st.button("Remove Last"):
        st.session_state.projects.pop()
        st.rerun()

st.divider()

# ── SKILLS ─────────────────────────────────────────────
st.subheader("Skills")
st.caption("Add ALL skills — AI will show only relevant ones per JD.")

if "skills" not in st.session_state:
    st.session_state.skills = [{}]

for i, skill in enumerate(st.session_state.skills):
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        st.session_state.skills[i]["name"] = st.text_input("Skill", value=skill.get("name", ""), key=f"s_name_{i}")
    with s_col2:
        st.session_state.skills[i]["category"] = st.selectbox(
            "Category", ["Agentic AI", "GenAI", "Conversational AI", "Machine Learning", "Programming", "Backend", "Frontend", "Cloud", "DevOps", "Databases", "Tools", "Soft Skills"],
            key=f"s_cat_{i}",
        )
    with s_col3:
        st.session_state.skills[i]["proficiency"] = st.selectbox("Level", ["expert", "proficient", "familiar"], key=f"s_prof_{i}")

if st.button("+ Add Skill"):
    st.session_state.skills.append({})
    st.rerun()

st.divider()

# ── EXPERIENCE ─────────────────────────────────────────
st.subheader("Work Experience")

if "experiences" not in st.session_state:
    st.session_state.experiences = [{}]

for i, exp in enumerate(st.session_state.experiences):
    with st.expander(f"Experience {i+1}: {exp.get('company', 'Company')}", expanded=(i == 0)):
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            st.session_state.experiences[i]["company"] = st.text_input("Company", value=exp.get("company", ""), key=f"e_co_{i}")
            st.session_state.experiences[i]["role"] = st.text_input("Role", value=exp.get("role", ""), key=f"e_role_{i}")
        with e_col2:
            st.session_state.experiences[i]["start_date"] = st.text_input("Start Date", value=exp.get("start_date", ""), key=f"e_start_{i}")
            st.session_state.experiences[i]["end_date"] = st.text_input("End Date", value=exp.get("end_date", "Present"), key=f"e_end_{i}")
        bullets_raw = st.text_area("Bullets (one per line — write ALL achievements)", value="\n".join(exp.get("bullets", [])), key=f"e_bullets_{i}", height=100)
        st.session_state.experiences[i]["bullets"] = [b.strip() for b in bullets_raw.split("\n") if b.strip()]

if st.button("+ Add Experience"):
    st.session_state.experiences.append({})
    st.rerun()

st.divider()

# ── EDUCATION ──────────────────────────────────────────
st.subheader("Education")
edu_degree = st.text_input("Degree")
edu_institution = st.text_input("Institution")
edu_year = st.text_input("Graduation Year")
edu_coursework_raw = st.text_input("Relevant Coursework (comma-separated)")

st.divider()

# ── SAVE ───────────────────────────────────────────────
if st.button("Save & Index Profile", type="primary", use_container_width=True):
    payload = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "summary": summary,
        "projects": [p for p in st.session_state.projects if p.get("title")],
        "skills": [s for s in st.session_state.skills if s.get("name")],
        "experiences": [e for e in st.session_state.experiences if e.get("company")],
        "education": [{"degree": edu_degree, "institution": edu_institution, "year": edu_year,
                       "relevant_coursework": [c.strip() for c in edu_coursework_raw.split(",") if c.strip()]}],
    }
    with st.spinner("Saving and indexing your profile into ChromaDB..."):
        try:
            resp = requests.post(f"{BACKEND_URL}/profile/", json=payload, headers=auth_headers(), timeout=60)
            if resp.status_code == 201:
                st.success("Profile saved and indexed! You're ready to generate resumes.")
            else:
                st.error(f"Error: {resp.json()}")
        except Exception as e:
            st.error(f"Backend error: {e}")
