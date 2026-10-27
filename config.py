"""Configuration management for FestiWise AI.

Loads settings from environment variables, .env file, or Streamlit secrets.
Supports runtime override via in-app settings.
"""

import os
from pathlib import Path
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    # Load .env if present
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass

def get_config_val(key: str, default: str = "") -> str:
    """Retrieve configuration from environment variable, Streamlit secrets, or fallback default."""
    val = os.getenv(key, "").strip()
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = get_config_val("DATABASE_PATH", str(BASE_DIR / "festiwise.db"))

# Gemini API Configuration
DEFAULT_GEMINI_MODEL = get_config_val("GEMINI_MODEL", "gemini-3.8-flash")
SUPPORTED_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash"
]
FALLBACK_GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash"
]

# Supported Currencies & Symbols
CURRENCY_SYMBOLS: Dict[str, str] = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "AUD": "A$",
    "CAD": "C$",
    "SGD": "S$",
    "AED": "AED ",
}

DEFAULT_CURRENCY = get_config_val("DEFAULT_CURRENCY", "INR")

# Event Categories supported by FestiWise AI
EVENT_CATEGORIES = [
    "Wedding",
    "Birthday",
    "College Event",
    "Festival",
    "Community Gathering",
    "Corporate Celebration",
    "Custom"
]

# Default baseline budget allocation percentages by category
DEFAULT_BUDGET_RATIOS: Dict[str, Dict[str, float]] = {
    "Wedding": {
        "Venue & Rentals": 0.28,
        "Catering & Drinks": 0.32,
        "Decor & Flowers": 0.14,
        "Photography & Video": 0.10,
        "Entertainment & Music": 0.06,
        "Outfits & Makeup": 0.05,
        "Emergency Reserve": 0.05,
    },
    "Birthday": {
        "Venue & Play Area": 0.22,
        "Catering & Cake": 0.38,
        "Decor & Balloons": 0.15,
        "Entertainment & Games": 0.12,
        "Photography": 0.05,
        "Favors & Gifts": 0.04,
        "Emergency Reserve": 0.04,
    },
    "College Event": {
        "Stage, Sound & Lights": 0.32,
        "Food & Refreshments": 0.28,
        "Guest Speakers/Artists": 0.18,
        "Promotion & Merchandise": 0.08,
        "Security & Logistics": 0.08,
        "Emergency Reserve": 0.06,
    },
    "Festival": {
        "Venue & Community Setup": 0.25,
        "Prasadam / Food Stalls": 0.35,
        "Traditional Decor & Lights": 0.18,
        "Cultural Performances": 0.10,
        "Permits & Logistics": 0.06,
        "Emergency Reserve": 0.06,
    },
    "Community Gathering": {
        "Venue & Seating": 0.30,
        "Potluck / Catering": 0.35,
        "Activities & Supplies": 0.15,
        "Audio / Visual Setup": 0.10,
        "Emergency Reserve": 0.10,
    },
    "Corporate Celebration": {
        "Venue & AV Equipment": 0.35,
        "Gourmet Dining & Bar": 0.32,
        "Branding & Decor": 0.12,
        "Entertainment & Host": 0.11,
        "Gifts & Mementos": 0.05,
        "Emergency Reserve": 0.05,
    },
    "Custom": {
        "Venue & Infrastructure": 0.30,
        "Catering & Refreshments": 0.32,
        "Decor & Atmosphere": 0.15,
        "Entertainment & Production": 0.10,
        "Photography & Misc": 0.08,
        "Emergency Reserve": 0.05,
    }
}


def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from environment, st.secrets, or empty string.
    
    Never prints or logs the key.
    """
    key = get_config_val("GEMINI_API_KEY", "")
    if key:
        return key
    return get_config_val("GOOGLE_API_KEY", "")


def format_currency(amount: float, currency_code: str = "INR") -> str:
    """Format numeric amount with clean currency symbol and comma separators."""
    symbol = CURRENCY_SYMBOLS.get(currency_code.upper(), f"{currency_code} ")
    if amount is None:
        amount = 0.0
    return f"{symbol}{amount:,.2f}"
