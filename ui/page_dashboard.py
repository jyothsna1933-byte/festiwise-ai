"""Dashboard & Landing page for FestiWise AI."""

import streamlit as st
from config import format_currency
from database.db import list_events, get_full_event
from ui.components import render_hero, render_metric_tile, render_empty_state
from services.budget_service import calculate_budget_summary
from services.timeline_service import calculate_timeline_metrics


def render_dashboard():
    """Render main dashboard with brand hero, quick action cards, and active event metrics."""
    render_hero(
        title="FestiWise AI",
        subtitle="Every celebration, perfectly planned. Transform concepts into executable blueprints, deterministic budgets, and intelligent Plan Rescue recovery.",
        badge="FESTIWISE AI • SMART EVENT SUITE"
    )

    events = list_events()

    # Top CTA Bar
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📊 Celebration Command Center")
    with col2:
        if st.button("➕ Plan New Celebration", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "Create Event"
            st.rerun()

    if not events:
        render_empty_state(
            title="No Celebrations Created Yet",
            message="Start planning your dream wedding, birthday party, festival, or college gathering with GenAI precision and deterministic budget control.",
            action_page="Create Event",
            action_label="Create Your First Event"
        )
        return

    # Check active event in session state
    active_id = st.session_state.get("active_event_id")
    if not active_id or not any(e["id"] == active_id for e in events):
        active_id = events[0]["id"]
        st.session_state["active_event_id"] = active_id

    # Event Switcher Dropdown
    event_options = {e["id"]: f"{e['name']} ({e['category']} - {e['event_date']})" for e in events}
    selected_id = st.selectbox(
        "Select Active Celebration to Inspect:",
        options=list(event_options.keys()),
        format_func=lambda x: event_options[x],
        index=list(event_options.keys()).index(active_id)
    )
    if selected_id != active_id:
        st.session_state["active_event_id"] = selected_id
        st.rerun()

    active_event = get_full_event(active_id)
    if not active_event:
        st.warning("Could not load event details.")
        return

    # Metric summaries
    inp = active_event.input_details
    curr = inp.currency
    budget_sum = calculate_budget_summary(
        inp.total_budget,
        active_event.budget_allocations,
        active_event.expenses,
        inp.guest_count
    )
    timeline_sum = calculate_timeline_metrics(active_event.tasks)

    m1, m2, m3, m4 = st.columns(4)
    render_metric_tile(m1, "Total Budget", format_currency(inp.total_budget, curr), f"{curr} {budget_sum['per_guest_planned']:,.0f} / guest")
    render_metric_tile(m2, "Committed Expenses", format_currency(budget_sum["total_committed"], curr), f"{budget_sum['burn_percentage']:.1f}% committed", is_negative=budget_sum["is_overbudget"])
    render_metric_tile(m3, "Guest Count", f"{inp.guest_count} Guests", f"Location: {inp.city_location}")
    render_metric_tile(m4, "Milestone Progress", f"{timeline_sum['completion_percentage']:.0f}%", f"{timeline_sum['completed_tasks']}/{timeline_sum['total_tasks']} tasks done")

    # Quick Navigation Cards
    st.markdown("---")
    st.markdown("#### ⚡ Quick Modules")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.markdown("""
        <div class="saas-card" style="padding: 16px;">
            <h4 style="margin: 0 0 6px 0; color: #1E293B;">💰 Budget & Spend</h4>
            <p style="color: #64748B; font-size: 0.85rem; margin-bottom: 12px;">Track expenses, view allocation breakdown, and detect overspending.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Budget Planner", key="dash_btn_budget", use_container_width=True):
            st.session_state["nav_selection"] = "Budget Planner"
            st.rerun()

    with q2:
        st.markdown("""
        <div class="saas-card" style="padding: 16px;">
            <h4 style="margin: 0 0 6px 0; color: #1E293B;">⏱️ Timeline & Tasks</h4>
            <p style="color: #64748B; font-size: 0.85rem; margin-bottom: 12px;">Milestone checklist and minute-by-minute day-of schedule.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Timeline", key="dash_btn_timeline", use_container_width=True):
            st.session_state["nav_selection"] = "Timeline & Tasks"
            st.rerun()

    with q3:
        st.markdown("""
        <div class="saas-card" style="padding: 16px;">
            <h4 style="margin: 0 0 6px 0; color: #E11D48;">🚨 Plan Rescue Mode</h4>
            <p style="color: #64748B; font-size: 0.85rem; margin-bottom: 12px;">Resolve venue cancellations, guest surges, bad weather, and budget shocks.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Plan Rescue", key="dash_btn_rescue", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "Plan Rescue"
            st.rerun()

    with q4:
        st.markdown("""
        <div class="saas-card" style="padding: 16px;">
            <h4 style="margin: 0 0 6px 0; color: #1E293B;">🎨 Creative Studio</h4>
            <p style="color: #64748B; font-size: 0.85rem; margin-bottom: 12px;">Themes, color palettes, invitations, menus, and low-waste tips.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Creative Studio", key="dash_btn_creative", use_container_width=True):
            st.session_state["nav_selection"] = "Creative Studio"
            st.rerun()

    # Active Event Overview
    st.markdown("---")
    st.markdown(f"#### 📋 Blueprint Overview: {inp.event_name}")
    st.write(active_event.overview)

    colA, colB = st.columns([1, 1])
    with colA:
        st.markdown("##### 🎭 Recommended Theme")
        st.info(f"**{active_event.creative.recommended_theme}**\n\n{active_event.creative.theme_rationale}")
        st.markdown("**Palette:** " + " • ".join([f"`{c}`" for c in active_event.creative.color_palette]))
    with colB:
        st.markdown("##### 🛡️ Key Contingencies & Assumptions")
        for r in active_event.risks_and_contingencies[:2]:
            st.markdown(f"- ⚠️ {r}")
        for a in active_event.assumptions[:2]:
            st.markdown(f"- 📌 {a}")
