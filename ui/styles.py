"""Custom CSS design system and theme styles for FestiWise AI.

Implements a refined, contemporary celebration SaaS design:
- Deep indigo / obsidian background with warm champagne gold and festive coral accents
- Modern typography, generous card padding, and subtle glassmorphic borders
- Distinct badge pills, stat tiles, and alert callouts
"""

import streamlit as st


def apply_custom_styles():
    """Inject polished SaaS styling into the active Streamlit app."""
    st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

    :root {
        --primary: #FF5A5F;
        --primary-gradient: linear-gradient(135deg, #FF5A5F 0%, #D83B01 100%);
        --accent-gold: #F5A623;
        --gold-gradient: linear-gradient(135deg, #FFD166 0%, #F5A623 100%);
        --festive-teal: #06D6A0;
        --card-bg: #FFFFFF;
        --text-dark: #1E293B;
        --text-muted: #64748B;
        --border-color: #E2E8F0;
        --border-radius-lg: 14px;
        --border-radius-sm: 8px;
        --shadow-soft: 0 4px 20px -2px rgba(0, 0, 0, 0.05), 0 2px 6px -1px rgba(0, 0, 0, 0.03);
    }

    /* Main Container typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Hero Banner Card */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #31103F 100%);
        border-radius: 16px;
        padding: 36px 32px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 8px;
        background: linear-gradient(90deg, #FFFFFF 0%, #FDE047 50%, #FF85A1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #CBD5E1;
        max-width: 720px;
        line-height: 1.6;
        margin-bottom: 18px;
    }

    .badge-signature {
        display: inline-block;
        background: rgba(245, 166, 35, 0.18);
        border: 1px solid #F5A623;
        color: #FDE047;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 12px;
    }

    /* Glass / Clean Cards */
    .saas-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .saas-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }

    /* Stat Box */
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: left;
    }
    .metric-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #64748B;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0F172A;
        font-family: 'Outfit', sans-serif;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #10B981;
        font-weight: 500;
        margin-top: 2px;
    }
    .metric-sub.negative {
        color: #EF4444;
    }

    /* Plan Rescue Signature Banner */
    .rescue-banner {
        background: linear-gradient(135deg, #1E1B4B 0%, #4C1D95 50%, #831843 100%);
        border: 1px solid rgba(244, 114, 182, 0.4);
        border-radius: 14px;
        padding: 24px;
        color: white;
        margin-bottom: 24px;
    }

    /* Callout alert badges */
    .alert-box {
        border-radius: 10px;
        padding: 14px 18px;
        margin: 12px 0;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .alert-info {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        color: #1E40AF;
    }
    .alert-warning {
        background-color: #FFFBEB;
        border-left: 4px solid #F59E0B;
        color: #92400E;
    }
    .alert-danger {
        background-color: #FEF2F2;
        border-left: 4px solid #EF4444;
        color: #991B1B;
    }
    .alert-success {
        background-color: #ECFDF5;
        border-left: 4px solid #10B981;
        color: #065F46;
    }

    /* Pill Tags */
    .tag-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .tag-blue { background: #E0F2FE; color: #0369A1; }
    .tag-purple { background: #F3E8FF; color: #7E22CE; }
    .tag-green { background: #DCFCE7; color: #15803D; }
    .tag-amber { background: #FEF3C7; color: #B45309; }

    /* Streamlit Button Tweaks */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        padding: 8px 18px;
        transition: all 0.2s;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF5A5F 0%, #D83B01 100%);
        border: none;
        color: white;
        box-shadow: 0 4px 12px rgba(255, 90, 95, 0.3);
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(255, 90, 95, 0.4);
    }

    /* Footer styling */
    .app-footer {
        margin-top: 48px;
        padding: 24px 0 12px 0;
        border-top: 1px solid #E2E8F0;
        text-align: center;
        color: #94A3B8;
        font-size: 0.82rem;
    }
    </style>
    """, unsafe_allow_html=True)
