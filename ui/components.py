"""Reusable UI components and visual widgets for FestiWise AI."""

import streamlit as st
from typing import Optional, List, Dict, Any
from config import format_currency
from models.schemas import FullEventPlan


def render_hero(
    title: str = "FestiWise AI",
    subtitle: str = "Every celebration, perfectly planned.",
    badge: Optional[str] = "HACK2SKILL PROMPTWARS | CHALLENGE 5"
):
    """Render hero header banner with celebratory gradients."""
    badge_html = f'<div class="badge-signature">{badge}</div>' if badge else ""
    st.markdown(f"""
    <div class="hero-banner">
        {badge_html}
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_tile(
    container,
    label: str,
    value: str,
    sub_text: Optional[str] = None,
    is_negative: bool = False
):
    """Render a clean metric tile within a Streamlit column."""
    sub_class = "negative" if is_negative else ""
    sub_html = f'<div class="metric-sub {sub_class}">{sub_text}</div>' if sub_text else ""
    container.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(
    title: str,
    message: str,
    icon: str = "sparkles",
    action_page: Optional[str] = None,
    action_label: Optional[str] = None
):
    """Render helpful empty state card with guidance."""
    st.markdown(f"""
    <div class="saas-card" style="text-align: center; padding: 48px 24px;">
        <div style="font-size: 2.4rem; margin-bottom: 12px;">✨</div>
        <h3 style="margin-bottom: 8px; color: #1E293B;">{title}</h3>
        <p style="color: #64748B; max-width: 480px; margin: 0 auto 20px auto; font-size: 0.95rem;">{message}</p>
    </div>
    """, unsafe_allow_html=True)
    if action_page and action_label:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, key=f"empty_cta_{action_page}", type="primary", use_container_width=True):
                st.session_state["nav_selection"] = action_page
                st.rerun()


def render_active_event_pill(event: FullEventPlan):
    """Display persistent status bar showing currently selected event."""
    curr = event.input_details.currency
    budget_fmt = format_currency(event.input_details.total_budget, curr)
    st.markdown(f"""
    <div style="background: #F1F5F9; border-left: 4px solid #FF5A5F; padding: 10px 16px; border-radius: 6px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <strong style="color: #0F172A;">Active Event:</strong> 
            <span style="font-weight: 600; color: #FF5A5F;">{event.input_details.event_name}</span>
            <span style="color: #64748B; font-size: 0.88rem;"> • {event.input_details.event_category} • {event.input_details.event_date} • {event.input_details.city_location}</span>
        </div>
        <div>
            <span class="tag-pill tag-blue">Guests: {event.input_details.guest_count}</span>
            <span class="tag-pill tag-purple">Budget: {budget_fmt}</span>
            <span class="tag-pill tag-green">Rescue: Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_disclaimer_notice():
    """Render honest pricing & vendor disclaimer as required by rules."""
    st.markdown("""
    <div class="alert-box alert-info" style="font-size: 0.8rem; margin-top: 24px;">
        ℹ️ <strong>Financial & Vendor Notice:</strong> All budget allocations and expense numbers are computed programmatically in Python code. 
        Estimates represent planning benchmarks, not guaranteed live market quotations or booked contracts. 
        Always verify final pricing directly with your chosen vendors before signing.
    </div>
    """, unsafe_allow_html=True)
