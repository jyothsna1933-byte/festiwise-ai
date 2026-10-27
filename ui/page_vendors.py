"""Vendor Organizer and AI Evaluation Guidance page for FestiWise AI."""

import uuid
import streamlit as st
import pandas as pd

from config import format_currency
from database.db import get_full_event, save_full_event
from models.schemas import VendorItem
from ui.components import render_active_event_pill, render_empty_state, render_disclaimer_notice


def render_vendors():
    """Render vendor management organizer and AI interrogation guidance."""
    st.markdown("### 🤝 Vendor Management & AI Guidance")
    st.markdown("Track candidate vendors, compare quotations, and review AI-curated interrogation checklists before booking.")

    active_id = st.session_state.get("active_event_id")
    if not active_id:
        render_empty_state(
            title="No Active Celebration Selected",
            message="Please select or create an event to access Vendor Management.",
            action_page="Create Event",
            action_label="Plan Celebration"
        )
        return

    event = get_full_event(active_id)
    if not event:
        st.warning("Could not load active event.")
        return

    render_active_event_pill(event)

    curr = event.input_details.currency

    tab_org, tab_guidance, tab_add = st.tabs([
        "📒 Vendor Organizer",
        "💡 AI Question Checklist & Red Flags",
        "➕ Add New Vendor"
    ])

    with tab_org:
        st.markdown("#### Tracked Vendors")
        st.caption("Organize vendor contacts, quoted prices, and booking progress.")

        if not event.vendors:
            st.info("No vendors tracked yet. Use the 'Add New Vendor' tab to record candidate vendors.")
        else:
            v_rows = []
            for v in event.vendors:
                v_rows.append({
                    "Category": v.category,
                    "Vendor Name": v.name,
                    "Contact": v.contact_info or "—",
                    "Quoted Price": format_currency(v.quoted_price, curr),
                    "Status": v.booking_status,
                    "Follow-up Date": v.follow_up_date or "—",
                    "Notes": v.notes or "—"
                })
            st.dataframe(pd.DataFrame(v_rows), use_container_width=True)

            with st.expander("✏️ Update Booking Status or Remove Vendor"):
                ven_to_mod = st.selectbox(
                    "Select Vendor",
                    options=[v.id for v in event.vendors],
                    format_func=lambda x: f"{next((v.name for v in event.vendors if v.id == x), '')} ({next((v.category for v in event.vendors if v.id == x), '')})"
                )
                selected_v = next((v for v in event.vendors if v.id == ven_to_mod), None)
                if selected_v:
                    stat_opts = ["Researching", "Contacted", "Quoted", "Booked", "Declined"]
                    c_idx = stat_opts.index(selected_v.booking_status) if selected_v.booking_status in stat_opts else 0
                    new_st = st.selectbox("Update Status", options=stat_opts, index=c_idx)
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        if st.button("Save Status Update", type="primary"):
                            selected_v.booking_status = new_st
                            save_full_event(event)
                            st.success("Vendor status updated!")
                            st.rerun()
                    with col_u2:
                        if st.button("Remove Vendor"):
                            event.vendors = [v for v in event.vendors if v.id != ven_to_mod]
                            save_full_event(event)
                            st.success("Vendor removed from organizer.")
                            st.rerun()

    with tab_guidance:
        st.markdown("#### AI Vendor Interrogation Checklists")
        st.caption("Vital questions to ask before transferring deposits, plus critical red flags to look out for.")

        if not event.vendor_guidance:
            st.info("No specific category guidance generated for this event yet.")
        else:
            for vg in event.vendor_guidance:
                with st.expander(f"📌 {vg.category} — What to Ask & Verify", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Key Questions to Ask:**")
                        for q in vg.key_questions:
                            st.markdown(f"- ❓ {q}")
                    with col2:
                        st.markdown("**Verification Checklist:**")
                        for item in vg.evaluation_checklist:
                            st.markdown(f"- ✅ {item}")
                        if vg.caution_red_flags:
                            st.markdown("**⚠️ Caution Red Flags:**")
                            for rf in vg.caution_red_flags:
                                st.markdown(f"- 🚩 <span style='color: #DC2626;'>{rf}</span>", unsafe_allow_html=True)

    with tab_add:
        st.markdown("#### ➕ Add Vendor to Organizer")
        with st.form("add_vendor_form"):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                v_name = st.text_input("Vendor / Company Name *", placeholder="e.g. Royal Banquet & Catering Co.")
                cat_opts = [
                    "Venue & Rentals",
                    "Catering & Drinks",
                    "Photography & Video",
                    "Decor & Flowers",
                    "Entertainment & Music",
                    "Transportation",
                    "Outfits & Makeup",
                    "General"
                ]
                v_cat = st.selectbox("Category *", options=cat_opts)
                v_contact = st.text_input("Phone / Email / Address", placeholder="e.g. +91 98765 43210 / manager@venue.com")
            with col_v2:
                v_quote = st.number_input(f"Quoted Price ({curr})", min_value=0.0, value=0.0, step=1000.0)
                v_status = st.selectbox("Booking Status", options=["Researching", "Contacted", "Quoted", "Booked", "Declined"])
                v_fupdate = st.text_input("Follow-up Date", placeholder="e.g. YYYY-MM-DD or Next Monday")

            v_notes = st.text_area("Notes & Terms", placeholder="e.g. Includes stage lighting, tables, and security guards; requires 30% advance deposit")

            submit_v = st.form_submit_button("Add Vendor", type="primary")
            if submit_v:
                if not v_name:
                    st.error("Vendor name is required.")
                else:
                    new_v = VendorItem(
                        id=str(uuid.uuid4())[:8],
                        category=v_cat,
                        name=v_name.strip(),
                        contact_info=v_contact.strip() if v_contact else "",
                        quoted_price=float(v_quote),
                        booking_status=v_status,
                        follow_up_date=v_fupdate.strip() if v_fupdate else "",
                        notes=v_notes.strip() if v_notes else ""
                    )
                    event.vendors.append(new_v)
                    save_full_event(event)
                    st.success(f"Vendor '{v_name}' added to organizer!")
                    st.rerun()

    render_disclaimer_notice()
