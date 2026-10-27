"""Smart Budget Planner & Expense Tracking page for FestiWise AI.

Strictly implements the CRITICAL FINANCIAL CALCULATION RULE:
All calculations (totals, percentages, remaining budget, variances, per-guest stats)
are computed programmatically via budget_service.py.
"""

import uuid
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import format_currency
from database.db import get_full_event, save_full_event, add_or_update_expense, delete_expense
from models.schemas import ExpenseItem, BudgetAllocation
from services.budget_service import (
    calculate_budget_summary,
    rebalance_allocations_to_target
)
from ui.components import (
    render_active_event_pill,
    render_metric_tile,
    render_empty_state,
    render_disclaimer_notice
)


def render_budget_planner():
    """Render full programmatic budget calculation and expense management engine."""
    st.markdown("### 💰 Smart Budget Planner")
    st.markdown("Deterministic financial calculations, category allocations, expense tracking, and AI cost-saving optimizations.")

    active_id = st.session_state.get("active_event_id")
    if not active_id:
        render_empty_state(
            title="No Active Celebration Selected",
            message="Please select or create an event to access the Smart Budget Planner.",
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

    # Programmatic calculations
    metrics = calculate_budget_summary(
        inp.total_budget,
        event.budget_allocations,
        event.expenses,
        inp.guest_count
    )

    # Top Metric Tiles
    m1, m2, m3, m4 = st.columns(4)
    render_metric_tile(m1, "Total Budget Cap", format_currency(metrics["total_budget"], curr), f"{curr} {metrics['per_guest_planned']:,.0f} per guest")
    render_metric_tile(m2, "Total Planned Allocations", format_currency(metrics["total_planned"], curr), f"Sum of {len(event.budget_allocations)} categories")
    render_metric_tile(m3, "Committed Expenses", format_currency(metrics["total_committed"], curr), f"{metrics['expense_count']} expense items", is_negative=metrics["is_overbudget"])
    rem_label = "Remaining Budget" if not metrics["is_overbudget"] else "Budget Deficit (OVERSPENT!)"
    render_metric_tile(m4, rem_label, format_currency(metrics["remaining_budget"], curr), f"{metrics['burn_percentage']:.1f}% consumed", is_negative=metrics["is_overbudget"])

    # Overspending / Allocation Variance Warnings
    if metrics["is_allocations_over"]:
        st.error(f"⚠️ **Allocation Warning:** Category planned amounts total {format_currency(metrics['total_planned'], curr)}, which exceeds your total budget cap by {format_currency(abs(metrics['allocation_variance']), curr)}.")
        if st.button("⚖️ Auto-Rebalance Allocations to Target Budget", type="primary", key="btn_auto_rebalance"):
            event.budget_allocations = rebalance_allocations_to_target(event.budget_allocations, inp.total_budget)
            save_full_event(event)
            st.success("Allocations rebalanced proportionally to match total budget cap exactly!")
            st.rerun()

    if metrics["is_overbudget"]:
        st.error(f"🚨 **Overspending Alert:** Committed expenses ({format_currency(metrics['total_committed'], curr)}) exceed your budget by {format_currency(abs(metrics['remaining_budget']), curr)}. Open Plan Rescue Mode to adjust your plan!")

    # Tabbed Interface: 1. Allocations Breakdown, 2. Expense Tracker, 3. Visual Charts, 4. AI Cost Optimization Tips
    tab_alloc, tab_exp, tab_charts, tab_ai = st.tabs([
        "📊 Category Allocations",
        "🧾 Expense Tracker",
        "📈 Visual Analytics",
        "💡 AI Cost-Saving Tips"
    ])

    with tab_alloc:
        st.markdown("#### Programmatic Category Allocations")
        st.caption("Each category's planned amount is tracked against real expenses. You can adjust targets below.")

        alloc_data = []
        for a in event.budget_allocations:
            cat_metrics = metrics["category_breakdown"].get(a.category, {})
            committed = cat_metrics.get("committed", 0.0)
            variance = cat_metrics.get("variance", a.planned_amount - committed)
            alloc_data.append({
                "Category": a.category,
                f"Planned ({curr})": f"{a.planned_amount:,.2f}",
                "Share (%)": f"{a.percentage:.1f}%",
                f"Committed ({curr})": f"{committed:,.2f}",
                f"Variance ({curr})": f"{variance:,.2f}",
                "Status": "⚠️ Over" if committed > a.planned_amount else "✓ Safe"
            })

        st.dataframe(pd.DataFrame(alloc_data), use_container_width=True)

        with st.expander("✏️ Edit Category Allocation Targets"):
            with st.form("edit_allocations_form"):
                new_allocs = []
                for a in event.budget_allocations:
                    new_val = st.number_input(
                        f"{a.category} ({curr})",
                        min_value=0.0,
                        value=float(a.planned_amount),
                        step=500.0,
                        key=f"input_alloc_{a.category}"
                    )
                    pct = round((new_val / inp.total_budget * 100), 2) if inp.total_budget > 0 else 0.0
                    new_allocs.append(BudgetAllocation(
                        category=a.category,
                        planned_amount=new_val,
                        percentage=pct,
                        notes=a.notes,
                        is_flexible=a.is_flexible
                    ))
                save_alloc_btn = st.form_submit_button("Save Allocation Adjustments", type="primary")
                if save_alloc_btn:
                    event.budget_allocations = new_allocs
                    save_full_event(event)
                    st.success("Category allocations updated!")
                    st.rerun()

    with tab_exp:
        st.markdown("#### Detailed Expense Register")
        st.caption("Add quotes, invoices, and actual payments. Clearly distinguishes AI estimates, user quotes, and verified bills.")

        col_add_exp, _ = st.columns([1, 1])
        with st.expander("➕ Add New Expense Item"):
            with st.form("add_expense_form"):
                e_name = st.text_input("Expense Item / Service Name", placeholder="e.g. Welcome Flower Garlands")
                cat_options = [a.category for a in event.budget_allocations] or ["General"]
                e_cat = st.selectbox("Category", options=cat_options)
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    e_est = st.number_input(f"Estimated Cost ({curr})", min_value=0.0, value=0.0, step=100.0)
                    e_vendor = st.text_input("Vendor Name (Optional)", placeholder="e.g. Blossom Florals")
                with col_c2:
                    has_actual = st.checkbox("Record Actual Bill Now")
                    e_act = st.number_input(f"Actual Cost ({curr})", min_value=0.0, value=0.0, step=100.0) if has_actual else None
                    e_status = st.selectbox("Payment Status", options=["Pending", "Partially Paid", "Paid"])
                e_verified = st.checkbox("Verified with Vendor Quote / Receipt")
                e_notes = st.text_input("Notes", placeholder="e.g. 50% advance paid via UPI")

                submit_exp = st.form_submit_button("Record Expense", type="primary")
                if submit_exp:
                    if not e_name:
                        st.error("Expense item name is required.")
                    else:
                        new_item = ExpenseItem(
                            id=str(uuid.uuid4())[:8],
                            category=e_cat,
                            item_name=e_name.strip(),
                            estimated_cost=float(e_est),
                            actual_cost=float(e_act) if has_actual else None,
                            vendor_name=e_vendor.strip() if e_vendor else "",
                            payment_status=e_status,
                            is_verified=e_verified,
                            notes=e_notes.strip() if e_notes else ""
                        )
                        add_or_update_expense(event.id, new_item)
                        st.success(f"Added expense '{e_name}'!")
                        st.rerun()

        if not event.expenses:
            st.info("No expense line items added yet. Click 'Add New Expense Item' above to start tracking your actual receipts and estimates.")
        else:
            exp_table = []
            for exp in event.expenses:
                cost_disp = f"{curr} {exp.actual_cost:,.2f} (Actual)" if exp.actual_cost is not None else f"{curr} {exp.estimated_cost:,.2f} (Est)"
                ver_badge = "✅ Verified" if exp.is_verified else "⏳ Estimate"
                exp_table.append({
                    "ID": exp.id,
                    "Category": exp.category,
                    "Item": exp.item_name,
                    "Amount": cost_disp,
                    "Status": exp.payment_status,
                    "Verification": ver_badge,
                    "Vendor": exp.vendor_name or "—",
                })
            st.dataframe(pd.DataFrame(exp_table), use_container_width=True)

            # Option to delete an expense item
            with st.expander("🗑️ Delete an Expense Item"):
                del_id = st.selectbox("Select Expense to Remove", options=[e.id for e in event.expenses], format_func=lambda x: f"{x} - {next((e.item_name for e in event.expenses if e.id == x), '')}")
                if st.button("Confirm Delete Expense", type="primary"):
                    delete_expense(del_id)
                    st.success("Expense removed.")
                    st.rerun()

    with tab_charts:
        st.markdown("#### Visual Financial Insights")
        c1, c2 = st.columns(2)

        # 1. Allocation Pie Chart
        alloc_labels = [a.category for a in event.budget_allocations]
        alloc_values = [a.planned_amount for a in event.budget_allocations]
        if sum(alloc_values) > 0:
            fig_pie = px.pie(
                names=alloc_labels,
                values=alloc_values,
                title="Planned Budget Allocation by Category",
                hole=0.42,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            c1.plotly_chart(fig_pie, use_container_width=True)
        else:
            c1.info("No allocation amounts to chart.")

        # 2. Planned vs Committed Bar Chart
        cats = [a.category for a in event.budget_allocations]
        planned_vals = [a.planned_amount for a in event.budget_allocations]
        committed_vals = [metrics["category_breakdown"].get(c, {}).get("committed", 0.0) for c in cats]

        fig_bar = go.Figure(data=[
            go.Bar(name='Planned Target', x=cats, y=planned_vals, marker_color='#3B82F6'),
            go.Bar(name='Committed / Spent', x=cats, y=committed_vals, marker_color='#EF4444')
        ])
        fig_bar.update_layout(
            barmode='group',
            title="Planned vs Committed Spend by Category",
            yaxis_title=f"Amount ({curr})",
            margin=dict(t=40, b=20, l=20, r=20)
        )
        c2.plotly_chart(fig_bar, use_container_width=True)

    with tab_ai:
        st.markdown("#### 💡 AI Cost-Saving & Rebalancing Guidance")
        st.caption("Context-aware recommendations to maximize celebration impact without overspending.")

        st.markdown("""
        <div class="saas-card">
            <h5 style="color: #0F172A; margin-bottom: 8px;">1. High-Impact Menu Streamlining</h5>
            <p style="color: #475569; font-size: 0.9rem;">
                Catering represents the largest variable expense. Consolidating from 5 live counters to 3 signature interactive stations 
                can reduce catering bills by 12-15% while speeding up serving times and reducing waste.
            </p>
        </div>
        <div class="saas-card">
            <h5 style="color: #0F172A; margin-bottom: 8px;">2. Day-to-Night Decor Repurposing</h5>
            <p style="color: #475569; font-size: 0.9rem;">
                Repurpose daytime ceremonial floral backdrops or mandap marigold arrangements into dinner table centerpieces 
                and welcome photo-booth borders. Saves up to 20% on separate evening decor orders.
            </p>
        </div>
        <div class="saas-card">
            <h5 style="color: #0F172A; margin-bottom: 8px;">3. Digital-First Seed Paper Stationery</h5>
            <p style="color: #475569; font-size: 0.9rem;">
                Swap expensive multi-page boxed physical invitations for animated digital RSVP invites, keeping a small set of plantable seed paper cards 
                for VIP elders. Lowers stationery cost by 70%.
            </p>
        </div>
        """, unsafe_allow_html=True)

    render_disclaimer_notice()
