"""Demo sign-in and guest mode for Streamlit apps."""

import streamlit as st

USERS = {"demo": "demo123", "raju": "portfolio"}

RESPONSIVE = """
<style>
  @media (max-width: 900px) {
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
    [data-testid="stHorizontalBlock"] > div { width: 100% !important; }
    .stTabs [data-baseweb="tab-list"] { flex-wrap: wrap; gap: 0.25rem; }
    [data-testid="stMetric"] { min-width: 100%; }
    .stChatFloatingInputContainer { left: 0.5rem !important; right: 0.5rem !important; }
  }
  @media (max-width: 600px) {
    h1 { font-size: 1.6rem !important; }
    .block-container { padding: 1rem 0.7rem 5rem !important; }
  }
</style>
"""


def inject_responsive() -> None:
    st.markdown(RESPONSIVE, unsafe_allow_html=True)


def current_user() -> str | None:
    return st.session_state.get("user")


def is_signed_in() -> bool:
    return bool(current_user())


def render_auth(app_name: str) -> str | None:
    if "user" not in st.session_state:
        st.session_state.user = None
    inject_responsive()
    with st.sidebar:
        st.markdown(f"### {app_name}")
        if is_signed_in():
            st.success(f"Signed in as **{current_user()}**")
            st.caption("Saved history and downloads are unlocked.")
            if st.button("Sign out"):
                st.session_state.user = None
                st.rerun()
        else:
            st.info("**Guest mode** — explore freely. Sign in to save.")
            with st.form("signin"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                col_a, col_b = st.columns(2)
                sign = col_a.form_submit_button("Sign in")
                guest = col_b.form_submit_button("Stay guest")
                if sign:
                    if USERS.get(username) == password:
                        st.session_state.user = username
                        st.rerun()
                    else:
                        st.error("Try `demo` / `demo123`")
                if guest:
                    st.session_state.user = None
                    st.caption("Continuing as guest.")
            st.caption("Demo account: **demo** / **demo123**")
    return current_user()
