"""Guest List and RSVP Management page for FestiWise AI."""

import uuid
import streamlit as st
import pandas as pd

from database.db import get_full_event, save_full_event
from models.schemas import GuestItem
from ui.components import render_active_event_pill, render_metric_tile, render_empty_state


def render_guest_management():
    """Render guest list, RSVP tracker, headcount summary, and dietary requirements."""
    st.markdown("### 👥 Guest & RSVP Management")
    st.markdown("Track guest responses, plus-ones, dietary notes, and overall attendance headcount.")

    active_id = st.session_state.get("active_event_id")
    if not active_id:
        render_empty_state(
            title="No Active Celebration Selected",
            message="Please select or create an event to access Guest Management.",
            action_page="Create Event",
            action_label="Plan Celebration"
        )
        return

    event = get_full_event(active_id)
    if not event:
        st.warning("Could not load active event.")
        return

    render_active_event_pill(event)

    guests = event.guests or []
    target_capacity = event.input_details.guest_count

    # Calculate headcount statistics
    attending_count = sum(1 + g.plus_ones for g in guests if g.rsvp_status == "Attending")
    declined_count = sum(1 for g in guests if g.rsvp_status == "Declined")
    pending_count = sum(1 + g.plus_ones for g in guests if g.rsvp_status in ["Pending", "Tentative"])
    total_tracked_heads = attending_count + pending_count

    m1, m2, m3, m4 = st.columns(4)
    render_metric_tile(m1, "Planned Capacity", f"{target_capacity} Guests", "Target headcount")
    render_metric_tile(m2, "Confirmed Attending", f"{attending_count} Heads", f"Includes plus-ones")
    render_metric_tile(m3, "Awaiting RSVP", f"{pending_count} Heads", "Pending / Tentative", is_negative=pending_count > 0)
    render_metric_tile(m4, "Declined", f"{declined_count}", "Not attending")

    # Headcount alert
    if attending_count > target_capacity:
        st.warning(f"⚠️ **Headcount Surge:** Confirmed attendees ({attending_count}) exceed your venue's planned capacity ({target_capacity})! Use Plan Rescue Mode to adjust seating and food.")

    tab_list, tab_add = st.tabs([
        "📋 Guest Register",
        "➕ Add Guest"
    ])

    with tab_list:
        st.markdown("#### Guest Register & Dietary Requirements")
        if not guests:
            st.info("No guests added yet. Use the 'Add Guest' tab to add attendees.")
        else:
            g_table = []
            for g in guests:
                total_for_g = 1 + g.plus_ones
                g_table.append({
                    "Name": g.name,
                    "Contact": g.contact or "—",
                    "Status": g.rsvp_status,
                    "Party Size": f"{total_for_g} (self + {g.plus_ones})",
                    "Dietary Notes": g.dietary_notes or "Regular",
                    "Table / Group": g.table_group or "—"
                })
            st.dataframe(pd.DataFrame(g_table), use_container_width=True)

            with st.expander("✏️ Update Guest RSVP or Remove"):
                g_id_sel = st.selectbox(
                    "Select Guest to Update",
                    options=[g.id for g in guests],
                    format_func=lambda x: next((g.name for g in guests if g.id == x), "")
                )
                sel_g = next((g for g in guests if g.id == g_id_sel), None)
                if sel_g:
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        new_rsvp = st.selectbox(
                            "Update RSVP Status",
                            options=["Attending", "Declined", "Pending", "Tentative"],
                            index=["Attending", "Declined", "Pending", "Tentative"].index(sel_g.rsvp_status) if sel_g.rsvp_status in ["Attending", "Declined", "Pending", "Tentative"] else 0
                        )
                        new_p1 = st.number_input("Plus-Ones", min_value=0, max_value=10, value=sel_g.plus_ones)
                    with col_u2:
                        new_diet = st.text_input("Dietary Notes", value=sel_g.dietary_notes or "")
                        new_grp = st.text_input("Table / Group", value=sel_g.table_group or "")

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("Save Guest Update", type="primary"):
                            sel_g.rsvp_status = new_rsvp
                            sel_g.plus_ones = int(new_p1)
                            sel_g.dietary_notes = new_diet
                            sel_g.table_group = new_grp
                            save_full_event(event)
                            st.success("Guest record updated!")
                            st.rerun()
                    with col_b2:
                        if st.button("Remove Guest"):
                            event.guests = [g for g in guests if g.id != g_id_sel]
                            save_full_event(event)
                            st.success("Guest removed.")
                            st.rerun()

    with tab_add:
        st.markdown("#### ➕ Add Guest Entry")
        with st.form("add_guest_form"):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                g_name = st.text_input("Guest Name *", placeholder="e.g. Priya Sharma")
                g_contact = st.text_input("Contact Info (Optional)", placeholder="e.g. priya@email.com / +91 98765 00000")
                g_status = st.selectbox("RSVP Status", options=["Attending", "Pending", "Tentative", "Declined"])
            with col_g2:
                g_plus = st.number_input("Plus-Ones (Family / Guests)", min_value=0, max_value=10, value=0)
                g_diet = st.text_input("Dietary Preferences / Allergies", placeholder="e.g. Strictly Vegan, Nut allergy, Jain food")
                g_group = st.text_input("Seating Group / Table", placeholder="e.g. College Friends Table, Family Row A")

            submit_g = st.form_submit_button("Add Guest", type="primary")
            if submit_g:
                if not g_name:
                    st.error("Guest name is required.")
                else:
                    new_guest = GuestItem(
                        id=str(uuid.uuid4())[:8],
                        name=g_name.strip(),
                        contact=g_contact.strip() if g_contact else "",
                        rsvp_status=g_status,
                        plus_ones=int(g_plus),
                        dietary_notes=g_diet.strip() if g_diet else "",
                        table_group=g_group.strip() if g_group else ""
                    )
                    event.guests.append(new_guest)
                    save_full_event(event)
                    st.success(f"Added guest '{g_name}'!")
                    st.rerun()
