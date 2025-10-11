import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# ------------------------------------------------------
# Load environment variables from .env next to this file
# (works even when run from another working directory)
# ------------------------------------------------------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "env", ".env"))

# ------------------------------------------------------
# Streamlit configuration
# ------------------------------------------------------
st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# ------------------------------------------------------
# Check environment variables
# ------------------------------------------------------
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables.")
    st.stop()

# ------------------------------------------------------
# Create Supabase client
# ------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

supabase = get_client()

# ------------------------------------------------------
# Auth helper functions
# ------------------------------------------------------
def set_user_session(user):
    st.session_state["user"] = {
        "id": user.id,
        "email": user.email,
    }

def is_logged_in() -> bool:
    return "user" in st.session_state and st.session_state["user"] is not None

def logout():
    try:
        supabase.auth.sign_out()
    finally:
        st.session_state["user"] = None
        st.rerun()

# ------------------------------------------------------
# UI
# ------------------------------------------------------
def show_login_ui():
    st.title("🔐 Login")

    if is_logged_in():
        st.success(f"✅ Logged in as {st.session_state['user']['email']}")
        col1, _ = st.columns(2)
        with col1:
            if st.button("Log out", type="primary"):
                logout()
        st.stop()

    tab_login, tab_signup = st.tabs(["Login", "Sign up"])

    # ------------------------------------------------------
    # Login Tab
    # ------------------------------------------------------
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

            if submitted:
                if not email or not password:
                    st.error("⚠️ Please enter email and password.")
                else:
                    try:
                        resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if resp.user:
                            set_user_session(resp.user)
                            st.success("🎉 Logged in successfully. Redirecting…")
                            st.rerun()
                        else:
                            st.error("❌ Login failed.")
                    except Exception as e:
                        st.error(f"Login error: {e}")

    # ------------------------------------------------------
    # Signup Tab
    # ------------------------------------------------------
    with tab_signup:
        with st.form("signup_form"):
            email_su = st.text_input("Email", key="email_signup")
            password_su = st.text_input("Password", type="password", key="password_signup")
            submitted_su = st.form_submit_button("Create account")

            if submitted_su:
                if not email_su or not password_su:
                    st.error("⚠️ Please enter email and password.")
                else:
                    try:
                        resp = supabase.auth.sign_up({"email": email_su, "password": password_su})
                        if resp.user:
                            st.success("✅ Account created! Check your email for verification.")
                        else:
                            st.error("❌ Sign-up failed.")
                    except Exception as e:
                        st.error(f"Sign up error: {e}")

