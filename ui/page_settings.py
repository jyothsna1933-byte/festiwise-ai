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
from services.gemini_service import (
    is_gemini_available,
    verify_gemini_connection,
    sanitize_api_message
)


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

        current_configured_model = st.session_state.get("configured_model", DEFAULT_GEMINI_MODEL)
        if current_configured_model not in SUPPORTED_GEMINI_MODELS:
            current_configured_model = DEFAULT_GEMINI_MODEL

        with st.form("api_key_form"):
            new_key = st.text_input(
                "Enter or Update Gemini API Key",
                type="password",
                placeholder="Leave blank to use active key or enter new key..."
            )
            model_selection = st.selectbox(
                "Gemini Model Identifier",
                options=SUPPORTED_GEMINI_MODELS,
                index=SUPPORTED_GEMINI_MODELS.index(current_configured_model),
                help="Select your primary Gemini model. If this model experiences high demand (HTTP 503), FestiWise AI can route to an active fallback."
            )
            enable_fallback = st.checkbox(
                "Enable automatic fallback to alternate models (e.g. gemini-3.6-flash, gemini-3.5-flash-lite) if selected model is busy",
                value=st.session_state.get("enable_model_fallback", True),
                help="Recommended: Prevents 503 errors during temporary peak demand spikes."
            )

            save_key_btn = st.form_submit_button("Test Connection & Save Preference", type="primary")

            if save_key_btn:
                key_to_test = new_key.strip() if new_key.strip() else current_key
                st.session_state["enable_model_fallback"] = enable_fallback

                if not key_to_test:
                    st.session_state["configured_model"] = model_selection
                    st.info("ℹ️ No API key entered or configured. FestiWise AI will operate in Demonstration Mode.")
                else:
                    with st.spinner(f"Testing Gemini API connectivity for model '{model_selection}'..."):
                        res = verify_gemini_connection(
                            api_key=key_to_test,
                            model_name=model_selection,
                            allow_fallback=enable_fallback,
                            max_retries=1
                        )

                    if res["success"]:
                        if new_key.strip():
                            os.environ["GEMINI_API_KEY"] = new_key.strip()

                        if res["fallback_used"]:
                            st.warning(
                                f"⚠️ **Primary Model Busy (HTTP 503):** `{res['primary_model']}` is currently experiencing high demand. "
                                f"FestiWise AI successfully connected using fallback model **`{res['model_used']}`**!\n\n"
                                f"**Live Response:** `{res['response_text']}`"
                            )
                            st.session_state["configured_model"] = res["model_used"]
                        else:
                            st.success(
                                f"🎉 **Verification Succeeded!** Gemini model **`{res['model_used']}`** connected successfully.\n\n"
                                f"**Live Response:** `{res['response_text']}`"
                            )
                            st.session_state["configured_model"] = model_selection
                    else:
                        cat = res.get("error_category", "UNKNOWN")
                        msg = res.get("error_message", "Unknown verification error")

                        if cat == "INVALID_KEY":
                            st.error(
                                "❌ **Invalid API Key (HTTP 400/403):** The key was rejected by Google AI Studio. "
                                "Please verify that your key is copied correctly and has Gemini API enabled."
                            )
                        elif cat == "TEMPORARY_UNAVAILABLE":
                            st.warning(
                                f"⏳ **Model Temporarily Overloaded (HTTP 503):** `{model_selection}` is currently experiencing high demand spikes. "
                                "Bounded retries were attempted. Please check 'Enable automatic fallback' above or switch to `gemini-3.6-flash`."
                            )
                        elif cat == "RATE_LIMITED":
                            st.warning(
                                "⚠️ **Quota / Rate Limit Exceeded (HTTP 429):** Free-tier request rate limit reached. "
                                "Please wait a moment before trying again."
                            )
                        elif cat == "TIMEOUT":
                            st.warning(
                                "⏱️ **Request Timeout:** The request timed out while communicating with the Gemini API. "
                                "Please check your network and retry."
                            )
                        else:
                            st.error(f"❌ **Verification Failed:** {msg}")

                    if res.get("diagnostic_trail"):
                        with st.expander("🔍 Show Diagnostics & Attempt Trail"):
                            for step in res["diagnostic_trail"]:
                                st.write(f"- {step}")

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
