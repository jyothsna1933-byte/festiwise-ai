"""My Events management page for FestiWise AI."""

import json
import streamlit as st
from config import format_currency
from database.db import list_events, get_full_event, delete_event
from ui.components import render_empty_state


def render_my_events():
    """Render full list of saved events with search, inspection, export, and delete."""
    st.markdown("### 📁 My Celebrations")
    st.markdown("Search, inspect, export, or manage your saved celebration blueprints.")

    events = list_events()
    if not events:
        render_empty_state(
            title="No Saved Celebrations Found",
            message="You haven't created any celebrations yet. Click below to start planning.",
            action_page="Create Event",
            action_label="Plan New Event"
        )
        return

    # Search & Filter controls
    col_search, col_filter = st.columns([3, 2])
    with col_search:
        search_query = st.text_input("🔍 Search by event name or city", placeholder="e.g. Bangalore, Wedding, Birthday")
    with col_filter:
        categories = ["All Categories"] + sorted(list({e["category"] for e in events}))
        cat_filter = st.selectbox("Filter Category", options=categories)

    filtered_events = events
    if search_query:
        q = search_query.lower()
        filtered_events = [e for e in filtered_events if q in e["name"].lower() or q in e["city"].lower()]
    if cat_filter != "All Categories":
        filtered_events = [e for e in filtered_events if e["category"] == cat_filter]

    st.markdown(f"Showing **{len(filtered_events)}** of **{len(events)}** celebrations:")

    active_id = st.session_state.get("active_event_id")

    for e in filtered_events:
        is_active = (e["id"] == active_id)
        active_border = "border: 2px solid #FF5A5F;" if is_active else "border: 1px solid #E2E8F0;"
        active_badge = '<span class="tag-pill tag-purple">CURRENTLY ACTIVE</span>' if is_active else ""

        budget_fmt = format_currency(e["total_budget"], e["currency"])

        st.markdown(f"""
        <div class="saas-card" style="{active_border} margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div>
                    <h4 style="margin: 0 0 4px 0; color: #0F172A;">{e['name']}</h4>
                    <p style="margin: 0; color: #64748B; font-size: 0.88rem;">
                        📍 {e['city']} • 📅 {e['event_date']} • 👥 {e['guest_count']} Guests • 🏷️ {e['category']}
                    </p>
                </div>
                <div style="text-align: right; margin-top: 4px;">
                    {active_badge}
                    <div style="font-weight: 700; font-size: 1.15rem; color: #1E293B;">{budget_fmt}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        with c1:
            if not is_active:
                if st.button("👉 Set as Active", key=f"set_active_{e['id']}", use_container_width=True):
                    st.session_state["active_event_id"] = e["id"]
                    st.success(f"Switched active celebration to '{e['name']}'!")
                    st.rerun()
            else:
                st.button("✓ Active Selection", key=f"active_lbl_{e['id']}", disabled=True, use_container_width=True)

        with c2:
            if st.button("📊 View Dashboard", key=f"view_dash_{e['id']}", use_container_width=True):
                st.session_state["active_event_id"] = e["id"]
                st.session_state["nav_selection"] = "Dashboard"
                st.rerun()

        with c3:
            full_e = get_full_event(e["id"])
            if full_e:
                json_str = full_e.model_dump_json(indent=2)
                st.download_button(
                    label="📥 Export JSON",
                    data=json_str,
                    file_name=f"festiwise_{e['id']}.json",
                    mime="application/json",
                    key=f"export_{e['id']}",
                    use_container_width=True
                )

        with c4:
            # Delete button with confirmation toggle
            delete_key = f"confirm_del_{e['id']}"
            if st.session_state.get(delete_key):
                st.error("Delete this event?")
                col_y, col_n = st.columns(2)
                with col_y:
                    if st.button("Yes", key=f"yes_del_{e['id']}", type="primary", use_container_width=True):
                        delete_event(e["id"])
                        if st.session_state.get("active_event_id") == e["id"]:
                            st.session_state["active_event_id"] = None
                        st.session_state[delete_key] = False
                        st.success("Deleted celebration.")
                        st.rerun()
                with col_n:
                    if st.button("No", key=f"no_del_{e['id']}", use_container_width=True):
                        st.session_state[delete_key] = False
                        st.rerun()
            else:
                if st.button("🗑️ Delete", key=f"del_{e['id']}", use_container_width=True):
                    st.session_state[delete_key] = True
                    st.rerun()
