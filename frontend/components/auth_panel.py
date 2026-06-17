import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def render_auth():
    st.title("OptimizeResume")
    st.subheader("Sign in to continue")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary"):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json={"email": email, "password": password},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user_id = data["user_id"]
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Login failed"))
            except Exception as e:
                st.error(f"Cannot reach backend: {e}")

    with tab_register:
        email_r = st.text_input("Email", key="reg_email")
        password_r = st.text_input("Password", type="password", key="reg_password")
        if st.button("Create Account", type="primary"):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/auth/register",
                    json={"email": email_r, "password": password_r},
                    timeout=10,
                )
                if resp.status_code == 201:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user_id = data["user_id"]
                    st.success("Account created!")
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Registration failed"))
            except Exception as e:
                st.error(f"Cannot reach backend: {e}")
