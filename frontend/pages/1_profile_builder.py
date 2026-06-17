import io
import json
import os

import google.generativeai as genai
import pdfplumber
import requests
import streamlit as st
from docx import Document

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="Profile Builder", page_icon="👤", layout="wide")

# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────────
CONSULTANT_SYSTEM_PROMPT = """You are an expert career consultant and resume strategist. Your job is to build a comprehensive master profile for the user by having a natural, friendly conversation.

YOUR PERSONALITY:
- Warm, encouraging, and professional — like a trusted career coach
- Proactive — you drive the conversation, not the user
- Thorough — you probe for specifics, numbers, and impact
- Smart — you notice gaps and ask about them

YOUR GOAL:
Extract maximum detail across these sections:
1. Basic Info: name, email, phone, LinkedIn, GitHub
2. Professional Summary: career goal, expertise areas
3. Projects: title, description, tech stack, outcomes (with NUMBERS), duration, GitHub URL, what type of AI/ML work it was
4. Skills: all technical skills with proficiency level
5. Work Experience: company, role, dates, key achievements (with NUMBERS)
6. Education: degree, institution, year, relevant coursework

CONVERSATION RULES:
- Ask ONE focused question at a time — never overwhelm
- Always probe for numbers: "How many users?", "What was the latency improvement?", "What accuracy did you achieve?"
- For every project ask: What problem did it solve? What tech stack? Any metrics? Was it deployed?
- After each answer, acknowledge it warmly then ask the next logical question
- If the user is vague ("I built a chatbot"), probe: "What was it built with? Who used it? What did it achieve?"
- Track what you've collected and what's still missing
- When you sense a section is complete, naturally transition: "Great, that gives me a clear picture of your projects. Let's talk about your skills next."
- After covering all sections, say exactly: "PROFILE_COMPLETE: I have everything I need. Let me save your profile now." — this triggers the save

IF A RESUME WAS UPLOADED:
- Summarize what you extracted: "I've pulled the following from your resume: [summary]. Let me ask a few follow-up questions to fill in the gaps and add more detail."
- Ask specifically about missing quantified outcomes, missing tech stacks, and any projects not in the resume

START the conversation with: "Hi! I'm your profile consultant. I'll help you build a comprehensive master profile that the AI can use to generate tailored resumes. You can upload your existing resume to get started quickly, or we can build it from scratch. Which would you prefer?"
"""

EXTRACT_PROFILE_PROMPT = """Based on this conversation, extract a structured profile as JSON.
Be thorough — include everything mentioned. If something wasn't discussed, use null.

Return ONLY valid JSON matching this exact schema:
{
  "name": "string",
  "email": "string",
  "phone": "string or null",
  "linkedin": "string or null",
  "github": "string or null",
  "summary": "string — 2-3 sentence professional summary",
  "projects": [
    {
      "title": "string",
      "description": "string — detailed description",
      "tech_stack": ["string"],
      "outcomes": ["string — each outcome on its own, keep numbers if mentioned"],
      "role_types": ["string — from: Agentic AI, GenAI, Conversational AI, Machine Learning, Full-stack, Backend, Data Science"],
      "duration": "string or null",
      "github_url": "string or null"
    }
  ],
  "skills": [
    {
      "name": "string",
      "category": "string — from: Agentic AI, GenAI, Conversational AI, Machine Learning, Programming, Backend, Frontend, Cloud, DevOps, Databases, Tools",
      "proficiency": "string — expert/proficient/familiar"
    }
  ],
  "experiences": [
    {
      "company": "string",
      "role": "string",
      "start_date": "string",
      "end_date": "string",
      "bullets": ["string — each achievement as a bullet, include numbers"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "year": "string or null",
      "relevant_coursework": ["string"]
    }
  ]
}

Conversation:
{conversation}"""


# ── HELPERS ────────────────────────────────────────────────────────────────────
def parse_resume_file(uploaded_file) -> str:
    """Extract plain text from uploaded PDF or DOCX."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()

    if name.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    if name.endswith(".docx"):
        doc = Document(io.BytesIO(raw))
        return "\n".join(para.text for para in doc.paragraphs)

    return raw.decode("utf-8", errors="ignore")


def extract_profile_json(messages: list[dict]) -> dict:
    """Ask Gemini to convert the conversation into a structured profile JSON."""
    conversation_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Consultant'}: {m['content']}"
        for m in messages
    )
    prompt = EXTRACT_PROFILE_PROMPT.format(conversation=conversation_text)
    response = _model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


def chat_with_consultant(messages: list[dict], resume_context: str = "") -> str:
    """Send message history to Gemini and get consultant reply."""
    system = CONSULTANT_SYSTEM_PROMPT
    if resume_context:
        system += f"\n\nRESUME ALREADY UPLOADED — extracted text:\n{resume_context[:3000]}"

    history = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    chat = _model.start_chat(history=history[:-1] if history else [])
    response = chat.send_message(
        history[-1]["parts"][0] if history else "Hello",
        generation_config=genai.GenerationConfig(temperature=0.7),
        # Pass system instruction via prepended context
    )
    return response.text


def save_profile(profile: dict) -> bool:
    """POST extracted profile to the FastAPI backend."""
    try:
        resp = requests.post(f"{BACKEND_URL}/profile/", json=profile, timeout=60)
        return resp.status_code == 201
    except Exception:
        return False


# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "resume_context" not in st.session_state:
    st.session_state.resume_context = ""
if "profile_saved" not in st.session_state:
    st.session_state.profile_saved = False
if "extracted_profile" not in st.session_state:
    st.session_state.extracted_profile = None
if "chat_initialized" not in st.session_state:
    st.session_state.chat_initialized = False


# ── PAGE LAYOUT ────────────────────────────────────────────────────────────────
st.title("Profile Builder")
st.caption("Chat with your AI career consultant to build your master profile.")

col_chat, col_side = st.columns([3, 1])

with col_side:
    st.subheader("Resume Upload")
    st.caption("Upload your existing resume to get started faster.")
    uploaded = st.file_uploader("PDF or DOCX", type=["pdf", "docx"], label_visibility="collapsed")

    if uploaded and not st.session_state.resume_context:
        with st.spinner("Parsing your resume..."):
            text = parse_resume_file(uploaded)
            st.session_state.resume_context = text
            st.session_state.chat_messages = []   # reset chat with new context
            st.session_state.chat_initialized = False
        st.success(f"Parsed {len(text.split())} words from your resume.")

    if st.session_state.resume_context:
        with st.expander("View parsed text"):
            st.text(st.session_state.resume_context[:1500] + "...")

    st.divider()

    if st.button("Start Fresh", use_container_width=True):
        st.session_state.chat_messages = []
        st.session_state.resume_context = ""
        st.session_state.profile_saved = False
        st.session_state.extracted_profile = None
        st.session_state.chat_initialized = False
        st.rerun()

    if st.session_state.extracted_profile:
        st.divider()
        st.subheader("Extracted Profile")
        st.json(st.session_state.extracted_profile, expanded=False)


with col_chat:
    # ── INITIALIZE CHAT ────────────────────────────────────────────────────────
    if not st.session_state.chat_initialized:
        with st.spinner("Starting your consultation..."):
            # Build first message from Gemini
            system_with_context = CONSULTANT_SYSTEM_PROMPT
            if st.session_state.resume_context:
                system_with_context += f"\n\nRESUME ALREADY UPLOADED:\n{st.session_state.resume_context[:3000]}"

            opening_prompt = (
                "Start the conversation. Greet the user and ask how they want to proceed. "
                "If a resume was uploaded, acknowledge it and summarize what you see, then ask follow-up questions."
                if st.session_state.resume_context
                else "Start the conversation with your opening greeting."
            )

            # Use Gemini with system prompt baked into first turn
            response = _model.generate_content(
                system_with_context + "\n\nNow begin: " + opening_prompt,
                generation_config=genai.GenerationConfig(temperature=0.7),
            )
            opening = response.text
            st.session_state.chat_messages = [{"role": "assistant", "content": opening}]
            st.session_state.chat_initialized = True
            st.rerun()

    # ── RENDER CHAT HISTORY ────────────────────────────────────────────────────
    if st.session_state.profile_saved:
        st.success("Profile saved and indexed successfully! Head to **Generate Resume** to create your first resume.")
        if st.button("Go to Generate Resume"):
            st.switch_page("pages/2_generate_resume.py")

    for msg in st.session_state.chat_messages:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            content = msg["content"]
            # Hide the PROFILE_COMPLETE trigger from display
            display = content.replace("PROFILE_COMPLETE:", "").strip() if "PROFILE_COMPLETE:" in content else content
            st.markdown(display)

    # ── CHAT INPUT ─────────────────────────────────────────────────────────────
    if not st.session_state.profile_saved:
        user_input = st.chat_input("Type your response here...")

        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Build full prompt with system context + history
                    system_with_context = CONSULTANT_SYSTEM_PROMPT
                    if st.session_state.resume_context:
                        system_with_context += f"\n\nRESUME CONTEXT:\n{st.session_state.resume_context[:3000]}"

                    # Reconstruct history for Gemini
                    history_for_gemini = []
                    for m in st.session_state.chat_messages[:-1]:  # all except the last user message
                        role = "user" if m["role"] == "user" else "model"
                        history_for_gemini.append({"role": role, "parts": [m["content"]]})

                    # Add system context to history as a leading model turn if fresh
                    if len(history_for_gemini) == 1:
                        history_for_gemini = [
                            {"role": "user", "parts": ["Begin the consultation."]},
                            {"role": "model", "parts": [history_for_gemini[0]["parts"][0]]},
                        ]

                    chat = _model.start_chat(history=history_for_gemini)
                    reply = chat.send_message(
                        system_with_context[:500] + "\n\n" + user_input,
                        generation_config=genai.GenerationConfig(temperature=0.7),
                    ).text

                st.session_state.chat_messages.append({"role": "assistant", "content": reply})

                display_reply = reply.replace("PROFILE_COMPLETE:", "").strip() if "PROFILE_COMPLETE:" in reply else reply
                st.markdown(display_reply)

                # ── PROFILE COMPLETE TRIGGER ───────────────────────────────────
                if "PROFILE_COMPLETE:" in reply:
                    st.divider()
                    with st.spinner("Extracting your structured profile..."):
                        try:
                            profile = extract_profile_json(st.session_state.chat_messages)
                            st.session_state.extracted_profile = profile
                        except Exception as e:
                            st.error(f"Could not extract profile: {e}")
                            st.stop()

                    st.subheader("Here's what I captured:")
                    st.json(profile, expanded=True)

                    col_save, col_edit = st.columns(2)
                    with col_save:
                        if st.button("Save Profile", type="primary", use_container_width=True):
                            with st.spinner("Saving and indexing..."):
                                ok = save_profile(profile)
                            if ok:
                                st.session_state.profile_saved = True
                                st.rerun()
                            else:
                                st.error("Save failed — check the backend.")
                    with col_edit:
                        if st.button("Keep Chatting to Add More", use_container_width=True):
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": "Sure! What else would you like to add or clarify?",
                            })
                            st.rerun()
