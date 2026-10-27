"""Plan Rescue Mode page for FestiWise AI.

Signature differentiator:
Interactive recovery workflow that responds to real-world disruptions
(venue cancellation, bad weather, budget shocks, guest surges, vendor drops),
calculates mathematical impacts in Python, queries Gemini for strategic alternatives,
and presents an interactive before-and-after diff review before applying changes.
"""

import streamlit as st
import pandas as pd

from config import format_currency
from database.db import get_full_event
from models.schemas import PlanRescueRequest
from services.rescue_service import evaluate_plan_rescue, apply_plan_rescue_changes
from ui.components import render_active_event_pill, render_metric_tile, render_empty_state, render_disclaimer_notice


def render_plan_rescue():
    """Render interactive Plan Rescue workflow operating on the active saved event."""
    st.markdown("""
    <div class="rescue-banner">
        <div style="font-size: 0.8rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #F472B6; margin-bottom: 6px;">
            🚨 SIGNATURE DIFFERENTIATOR • INTELLIGENT PLAN RESCUE
        </div>
        <h2 style="margin: 0 0 8px 0; color: #FFFFFF;">Plan Rescue Mode</h2>
        <p style="margin: 0; color: #E0E7FF; font-size: 0.95rem; max-width: 750px;">
            Unexpected crisis? FestiWise AI analyzes the impact against your current blueprint, computes 
            the exact financial delta using code, generates strategic recovery alternatives with Gemini, 
            and allows you to review the proposed diff before safely updating your saved plan.
        </p>
    </div>
    """, unsafe_allow_html=True)

    active_id = st.session_state.get("active_event_id")
    if not active_id:
        render_empty_state(
            title="No Active Celebration Selected",
            message="Please select or create an event to launch Plan Rescue Mode.",
            action_page="Create Event",
            action_label="Plan Celebration"
        )
        return

    event = get_full_event(active_id)
    if not event:
        st.warning("Could not load active event.")
        return

    render_active_event_pill(event)

    inp = event.input_details
    curr = inp.currency

    # Step 1: Disruption Input
    st.markdown("#### 1. Report Disruption or Last-Minute Change")
    st.caption(f"Currently analyzing for: **{inp.event_name}** ({curr} {inp.total_budget:,.2f} budget, {inp.guest_count} guests, {inp.venue_type} venue)")

    with st.form("plan_rescue_form"):
        disruption_types = [
            "Venue cancellation or sudden fee increase",
            "Unexpected additional guests surge",
            "Bad weather / heavy rain affecting outdoor venue",
            "Budget constraint / sudden budget cut",
            "Caterer or core vendor cancellation",
            "Delayed equipment delivery or transport failure",
            "Day-of schedule conflict or timing delay",
            "Custom emergency or last-minute change"
        ]
        sel_dtype = st.selectbox("Disruption Category *", options=disruption_types)
        details = st.text_area(
            "Describe What Happened & The Specific Numbers *",
            placeholder="e.g. The venue informed us lawn fees increased from ₹25,000 to ₹35,000, and 25 extra family guests just confirmed attendance!"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            extra_guests = st.number_input("Additional Guests (If Any)", min_value=0, max_value=2000, value=0, step=5)
        with col2:
            override_budget = st.number_input(f"Target Budget Cap ({curr}, optional)", min_value=0.0, value=float(inp.total_budget), step=1000.0)
        with col3:
            venue_override = st.selectbox("Venue Preference Change", options=["Keep Current", "Switch to Indoor Hall", "Switch to Covered Canopy"])

        # Category cost delta expander
        st.markdown("**Direct Cost Increases (Optional Specifics):**")
        cat_c1, cat_c2 = st.columns(2)
        with cat_c1:
            delta_cat = st.selectbox("Category Experiencing Price Increase", options=[a.category for a in event.budget_allocations])
        with cat_c2:
            delta_amount = st.number_input(f"Direct Price Increase Amount ({curr})", min_value=0.0, value=0.0, step=500.0)

        eval_btn = st.form_submit_button("🚨 Run Plan Rescue Assessment", type="primary", use_container_width=True)

    if eval_btn:
        if not details or len(details.strip()) < 5:
            st.error("Please provide a brief description of the unexpected change.")
            return

        with st.spinner("Analyzing crisis impact, recalculating finances in Python, and generating recovery strategies..."):
            cat_deltas = {delta_cat: float(delta_amount)} if delta_amount > 0 else {}
            venue_target = None if venue_override == "Keep Current" else ("Indoor" if "Indoor" in venue_override else "Outdoor")

            req = PlanRescueRequest(
                event_id=event.id,
                disruption_type=sel_dtype,
                disruption_details=details.strip(),
                new_budget=float(override_budget) if override_budget > 0 else None,
                additional_guests=int(extra_guests) if extra_guests > 0 else None,
                new_venue_type=venue_target
            )

            rec, diff, used_ai, model_used = evaluate_plan_rescue(
                current_plan=event,
                request=req,
                category_cost_deltas=cat_deltas
            )

            # Store in session state for interactive review & apply
            st.session_state["pending_rescue_rec"] = rec
            st.session_state["pending_rescue_diff"] = diff
            st.session_state["rescue_ai_flag"] = "Live Google Gemini AI" if used_ai else "Demonstration Crisis Engine"
            st.session_state["rescue_model_used"] = model_used

    # Step 2: Render Evaluation & Diff Review if available
    if "pending_rescue_rec" in st.session_state and "pending_rescue_diff" in st.session_state:
        rec = st.session_state["pending_rescue_rec"]
        diff = st.session_state["pending_rescue_diff"]
        ai_engine = st.session_state.get("rescue_ai_flag", "AI Engine")

        st.markdown("---")
        st.markdown(f"### 🛡️ Plan Rescue Assessment Results ({ai_engine})")
        st.markdown(f"**Disruption Summary:** {rec.disruption_summary}")

        # Quantitative Impact Tiles
        st.markdown("#### Programmatic Financial Impact (Calculated by Python Engine)")
        imp = rec.quantitative_impact
        q1, q2, q3, q4 = st.columns(4)
        render_metric_tile(q1, "Original Budget", format_currency(imp.get("original_budget", 0), curr), f"{inp.guest_count} guests")
        render_metric_tile(q2, "Total Cost Impact", format_currency(imp.get("total_cost_increase", 0), curr), f"Direct: {format_currency(imp.get('total_direct_delta', 0), curr)} + Guest var: {format_currency(imp.get('guest_variable_delta', 0), curr)}", is_negative=imp.get("total_cost_increase", 0) > 0)
        render_metric_tile(q3, "Projected Required", format_currency(imp.get("projected_required_budget", 0), curr), f"{imp.get('new_guest_count')} guests ({format_currency(imp.get('projected_per_guest', 0), curr)}/guest)")
        
        def_label = "Budget Deficit (Cuts Required)" if imp.get("requires_cuts") else "Budget Headroom"
        render_metric_tile(q4, def_label, format_currency(abs(imp.get("deficit_or_surplus", 0)), curr), "Safe balance" if not imp.get("requires_cuts") else "Must trim other items", is_negative=imp.get("requires_cuts"))

        if rec.rebalancing_strategy:
            st.info(f"💡 **Rebalancing Strategy:** {rec.rebalancing_strategy}")

        # Strategic Recovery Alternatives
        st.markdown("#### Strategic Alternatives & Trade-Offs")
        for idx, alt in enumerate(rec.recommended_alternatives):
            with st.expander(f"Option {idx+1}: {alt.title}", expanded=(idx == 0)):
                st.write(alt.description)
                colA, colB = st.columns(2)
                with colA:
                    st.markdown("**Advantages:**")
                    for adv in alt.advantages:
                        st.markdown(f"- ✅ {adv}")
                with colB:
                    st.markdown("**Disadvantages & Trade-Offs:**")
                    for dis in alt.disadvantages:
                        st.markdown(f"- ⚠️ {dis}")
                st.markdown(f"**Key Compromise / Trade-Off:** *{alt.trade_offs}*")
                if alt.estimated_cost_delta != 0:
                    st.markdown(f"**Estimated Financial Delta:** {format_currency(alt.estimated_cost_delta, curr)}")

        # Contingency Checklist
        st.markdown("#### Immediate Contingency Action Steps")
        for step in rec.contingency_steps:
            st.markdown(f"- ⚡ **Immediate Action:** {step}")

        # Plan Diff Comparison Table
        st.markdown("---")
        st.markdown("### 🔍 Proposed Plan Diff (Before vs Proposed Revisions)")
        st.caption("Review exactly what will change in your saved celebration blueprint:")

        diff_summary = [
            {"Parameter": "Total Budget Cap", "Current Saved Plan": format_currency(diff["old_budget"], curr), "Proposed Revised Plan": format_currency(diff["proposed_budget"], curr), "Net Change": format_currency(diff["budget_variance"], curr)},
            {"Parameter": "Guest Headcount", "Current Saved Plan": f"{diff['old_guest_count']} Guests", "Proposed Revised Plan": f"{diff['proposed_guest_count']} Guests", "Net Change": f"+{diff['proposed_guest_count'] - diff['old_guest_count']}"},
            {"Parameter": "Venue Type", "Current Saved Plan": diff["old_venue_type"], "Proposed Revised Plan": diff["proposed_venue_type"], "Net Change": "Updated" if diff["old_venue_type"] != diff["proposed_venue_type"] else "Unchanged"},
            {"Parameter": "Contingency Tasks Added", "Current Saved Plan": "0", "Proposed Revised Plan": f"{len(diff['contingency_tasks_to_add'])} High-Priority Tasks", "Net Change": "Added to Timeline"},
        ]
        st.dataframe(pd.DataFrame(diff_summary), use_container_width=True)

        # Apply Revisions Button
        st.markdown("#### 3. Confirm and Apply Plan Rescue Revisions")
        col_app1, col_app2 = st.columns([2, 1])
        with col_app1:
            st.caption("Applying this plan will update your saved event budget, adjust category allocations, and inject crisis tasks into your timeline.")
        with col_app2:
            if st.button("✅ Approve & Apply Revised Plan", type="primary", use_container_width=True):
                updated_event = apply_plan_rescue_changes(event, diff)
                del st.session_state["pending_rescue_rec"]
                del st.session_state["pending_rescue_diff"]
                st.success("🎉 Plan Rescue revisions applied successfully! Your event, budget allocations, and tasks have been updated.")
                st.rerun()

    # Rescue History Log
    if event.rescue_history:
        st.markdown("---")
        st.markdown("#### 📜 Plan Rescue Audit History")
        st.caption("History of previous disruptions and recovery adjustments applied to this event:")
        for h in reversed(event.rescue_history):
            st.markdown(f"""
            <div class="saas-card" style="padding: 12px 18px; margin-bottom: 8px;">
                <div style="font-size: 0.82rem; color: #64748B;">{h.get('timestamp', '')[:19].replace('T', ' ')}</div>
                <strong style="color: #0F172A;">{h.get('disruption_type', '')}</strong>
                <p style="margin: 4px 0 0 0; font-size: 0.88rem; color: #475569;">
                    {h.get('disruption_details', '')} • Revised Budget: {curr} {h.get('applied_budget', 0):,.2f} • Guests: {h.get('applied_guests', 0)}
                </p>
            </div>
            """, unsafe_allow_html=True)

    render_disclaimer_notice()
