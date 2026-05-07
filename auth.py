"""Authentication module for ProcureIQ — demo-grade login gate."""
import os
import bcrypt
import streamlit as st
from typing import Dict, Optional
import yaml
from pathlib import Path


_SESSION_KEY = "_piq_authenticated"
_SESSION_USER = "_piq_username"
_SESSION_NAME = "_piq_name"


def _load_config(config_file: str = "auth_config.yaml") -> Optional[Dict]:
    """Load credentials from auth_config.yaml or env vars."""
    if Path(config_file).exists():
        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    demo_user = os.getenv("PROCUREIQ_DEMO_USER", "").strip()
    demo_pass = os.getenv("PROCUREIQ_DEMO_PASS", "").strip()
    if demo_user and demo_pass:
        return {
            "credentials": {
                "usernames": {
                    demo_user: {
                        "name": demo_user.capitalize(),
                        "password": demo_pass,
                    }
                }
            }
        }
    return None


def _check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def require_authentication() -> str:
    """Gate the entire app behind a login form. Returns username on success."""
    config = _load_config()

    if config is None:
        st.error("**Authentication not configured.**")
        st.markdown(
            "Copy `auth_config.yaml.example` to `auth_config.yaml` and fill in "
            "bcrypt-hashed passwords, then restart the app."
        )
        st.stop()

    # Already logged in this session
    if st.session_state.get(_SESSION_KEY):
        username = st.session_state[_SESSION_USER]
        name = st.session_state[_SESSION_NAME]
        if st.sidebar.button("Logout", key="_piq_logout_btn"):
            st.session_state[_SESSION_KEY] = False
            st.session_state[_SESSION_USER] = None
            st.session_state[_SESSION_NAME] = None
            st.rerun()
        st.sidebar.success(f"Welcome {name}!")
        return username

    # Disclaimer banner
    st.markdown(
        '<div style="background:rgba(59,130,246,0.07);border:1px solid '
        'rgba(96,165,250,0.25);border-radius:10px;padding:1rem 1.2rem;'
        'margin-bottom:1.2rem;text-align:center">'
        '<div style="font-size:0.95rem;font-weight:700;color:#93C5FD;'
        'margin-bottom:0.3rem">Demo Login Required</div>'
        '<div style="font-size:0.82rem;color:#94A3B8">'
        'ProcureIQ is a portfolio-grade sourcing decision support tool, '
        'not an enterprise production system.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Live demo entry (no credentials required) ───────────
    st.markdown(
        '<div style="background:rgba(74,222,128,0.07);border:1px solid rgba(74,222,128,0.25);'
        'border-radius:10px;padding:0.9rem 1.2rem;margin-bottom:1rem;text-align:center">'
        '<div style="font-size:0.85rem;font-weight:700;color:#4ADE80;margin-bottom:0.25rem">'
        '▶ Live Demo Available</div>'
        '<div style="font-size:0.78rem;color:#94A3B8">'
        'HRIS vendor evaluation — Workday vs. Rippling vs. UKG Pro — fully preloaded.<br/>'
        'No API key required. Decision Brief renders in one click.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("▶ Open Live Demo", key="_piq_demo_btn", use_container_width=True, type="primary"):
        st.session_state[_SESSION_KEY] = True
        st.session_state[_SESSION_USER] = "demo"
        st.session_state[_SESSION_NAME] = "Demo"
        st.session_state["_piq_demo_active"] = True
        st.rerun()

    st.markdown(
        '<div style="text-align:center;color:#475569;font-size:0.75rem;'
        'margin:0.6rem 0 0.8rem 0">— or log in with credentials —</div>',
        unsafe_allow_html=True,
    )

    # Login form
    with st.form("_piq_login_form"):
        entered_user = st.text_input("Username")
        entered_pass = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        users = config["credentials"]["usernames"]
        user_record = users.get(entered_user)
        if user_record and _check_password(entered_pass, user_record["password"]):
            st.session_state[_SESSION_KEY] = True
            st.session_state[_SESSION_USER] = entered_user
            st.session_state[_SESSION_NAME] = user_record.get("name", entered_user)
            st.rerun()
        else:
            st.error("Username or password is incorrect.")

    st.stop()
