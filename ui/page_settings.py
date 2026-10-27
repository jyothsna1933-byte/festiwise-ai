"""Settings, API Key Configuration, and System Health page for FestiWise AI."""

import os
import streamlit as st

from config import (
    get_gemini_api_key,
    SUPPORTED_GEMINI_MODELS,
    DEFAULT_GEMINI_MODEL,
    CURRENCY_SYMBOLS,
    DATABASE_PATH
)
from services.gemini_service import is_gemini_available


def render_settings():
    """Render system settings, Gemini API credentials configuration, and diagnostics."""
    st.markdown("### ⚙️ System Settings & GenAI Configuration")
    st.markdown("Manage your Google Gemini API credentials, select AI models, and view application diagnostics.")

    is_ai_live, ai_status = is_gemini_available()

    # GenAI Status Card
    if is_ai_live:
        st.markdown(f"""
        <div class="alert-box alert-success">
            <strong>✅ Google Gemini API Connected:</strong> {ai_status}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-box alert-warning">
            <strong>ℹ️ High-Fidelity Demonstration Mode Active:</strong> {ai_status}<br>
            To activate live GenAI generation, enter a free Gemini API key below or set <code>GEMINI_API_KEY</code> in your <code>.env</code> file.
        </div>
        """, unsafe_allow_html=True)

    tab_api, tab_pref, tab_diag = st.tabs([
        "🔑 Gemini API Credentials",
        "🌐 Preferences & Regional Settings",
        "🛠️ System Diagnostics"
    ])

    with tab_api:
        st.markdown("#### Google Gemini API Configuration")
        st.markdown("""
        FestiWise AI uses the official Google GenAI Python SDK (`google-genai`).
        You can obtain a free API key at **[Google AI Studio](https://aistudio.google.com/)**.
        """)

        current_key = get_gemini_api_key()
        masked_key = f"{current_key[:6]}...{current_key[-4:]}" if len(current_key) > 10 else ("Configured" if current_key else "Not Configured")
        st.text_input("Active API Key Status", value=masked_key, disabled=True)

        with st.form("api_key_form"):
            new_key = st.text_input("Enter or Update Gemini API Key", type="password", placeholder="AIzaSy...")
            model_selection = st.selectbox(
                "Gemini Model Identifier",
                options=SUPPORTED_GEMINI_MODELS,
                index=SUPPORTED_GEMINI_MODELS.index(st.session_state.get("configured_model", DEFAULT_GEMINI_MODEL)) if st.session_state.get("configured_model", DEFAULT_GEMINI_MODEL) in SUPPORTED_GEMINI_MODELS else 0
            )

            save_key_btn = st.form_submit_button("Test & Save Key for Session", type="primary")

            if save_key_btn:
                if new_key.strip():
                    os.environ["GEMINI_API_KEY"] = new_key.strip()
                    st.session_state["configured_model"] = model_selection
                    # Test key
                    try:
                        from google import genai
                        client = genai.Client(api_key=new_key.strip())
                        test_resp = client.models.generate_content(
                            model=model_selection,
                            contents="Say 'OK' if you can read this."
                        )
                        st.success(f"🎉 Verification Succeeded! Gemini model '{model_selection}' responded: {test_resp.text.strip()}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Verification Failed with provided key: {str(e)}")
                else:
                    st.session_state["configured_model"] = model_selection
                    st.success(f"Model preference updated to '{model_selection}'.")
                    st.rerun()

    with tab_pref:
        st.markdown("#### Celebration Defaults & Regional Formats")
        currs = list(CURRENCY_SYMBOLS.keys())
        active_curr = st.session_state.get("user_default_currency", "INR")
        c_idx = currs.index(active_curr) if active_curr in currs else 0
        new_curr = st.selectbox("Preferred Default Currency", options=currs, index=c_idx)
        if st.button("Save Regional Currency Preference", type="primary"):
            st.session_state["user_default_currency"] = new_curr
            st.success(f"Default currency set to {new_curr} ({CURRENCY_SYMBOLS[new_curr]}).")

    with tab_diag:
        st.markdown("#### Application Diagnostics & Stack Info")
        import sys
        import streamlit
        import pydantic
        import sqlite3

        diag_data = {
            "Application Name": "FestiWise AI",
            "Version": "1.0.0 (Hack2Skill PromptWars Edition)",
            "Python Version": sys.version.split()[0],
            "Streamlit Version": streamlit.__version__,
            "Pydantic Version": pydantic.__version__,
            "SQLite Version": sqlite3.sqlite_version,
            "Database File Path": DATABASE_PATH,
            "Active Gemini Model": st.session_state.get("configured_model", DEFAULT_GEMINI_MODEL),
            "Cloud Prerequisites": "None (100% Free-tier, zero GCP credit prerequisites)",
        }

        for k, v in diag_data.items():
            st.markdown(f"- **{k}:** `{v}`")
