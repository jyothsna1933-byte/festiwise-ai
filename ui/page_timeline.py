"""Timeline and Task Management page for FestiWise AI."""

import uuid
from datetime import datetime, date
import streamlit as st
import pandas as pd

from database.db import get_full_event, save_full_event, update_task_status
from models.schemas import TaskItem, EventScheduleItem
from services.timeline_service import calculate_timeline_metrics, validate_day_schedule
from ui.components import render_active_event_pill, render_metric_tile, render_empty_state


def render_timeline():
    """Render interactive milestone preparation checklist and chronological event-day schedule."""
    st.markdown("### ⏱️ Timeline & Task Management")
    st.markdown("Chronological milestone checklist, task delegation, and minute-by-minute day-of itinerary.")

    active_id = st.session_state.get("active_event_id")
    if not active_id:
        render_empty_state(
            title="No Active Celebration Selected",
            message="Please select or create an event to access the Timeline & Task Manager.",
            action_page="Create Event",
            action_label="Plan Celebration"
        )
        return

    event = get_full_event(active_id)
    if not event:
        st.warning("Could not load active event.")
        return

    render_active_event_pill(event)

    metrics = calculate_timeline_metrics(event.tasks)

    m1, m2, m3, m4 = st.columns(4)
    render_metric_tile(m1, "Completion Progress", f"{metrics['completion_percentage']:.0f}%", f"{metrics['completed_tasks']} of {metrics['total_tasks']} tasks done")
    render_metric_tile(m2, "In Progress", f"{metrics['in_progress_tasks']} Tasks", "Actively being worked on")
    render_metric_tile(m3, "High Priority Open", f"{metrics['high_priority_remaining']} Tasks", "Requires immediate attention", is_negative=metrics['high_priority_remaining'] > 0)
    render_metric_tile(m4, "Overdue Tasks", f"{metrics['overdue_tasks']} Tasks", "Deadline has passed", is_negative=metrics['overdue_tasks'] > 0)

    # Progress bar
    st.progress(metrics["completion_percentage"] / 100.0)

    tab_tasks, tab_schedule, tab_add = st.tabs([
        "📋 Preparation Milestones",
        "🕒 Day-Of Schedule",
        "➕ Add Milestone Task"
    ])

    with tab_tasks:
        st.markdown("#### Interactive Milestone Checklist")
        st.caption("Tasks are sorted chronologically by deadline. Check items off as you complete them.")

        if not event.tasks:
            st.info("No milestone tasks currently in the plan. Use the 'Add Milestone Task' tab to create tasks.")
        else:
            today_str = datetime.now().strftime("%Y-%m-%d")
            for t in event.tasks:
                is_done = (t.status == "Completed")
                is_overdue = (t.suggested_deadline < today_str and not is_done)

                prio_color = {"High": "tag-amber", "Medium": "tag-blue", "Low": "tag-purple"}.get(t.priority, "tag-blue")
                overdue_badge = '<span class="tag-pill" style="background:#FEE2E2; color:#B91C1C;">OVERDUE</span>' if is_overdue else ""

                col_chk, col_info, col_status = st.columns([1, 6, 2])
                with col_chk:
                    chk = st.checkbox("Done", value=is_done, key=f"chk_task_{t.id}", label_visibility="collapsed")
                    if chk != is_done:
                        new_stat = "Completed" if chk else "In Progress"
                        update_task_status(t.id, new_stat)
                        st.rerun()

                with col_info:
                    st_style = "text-decoration: line-through; color: #94A3B8;" if is_done else "color: #1E293B; font-weight: 600;"
                    st.markdown(f"""
                    <div style="{st_style} font-size: 1rem;">{t.title}</div>
                    <div style="font-size: 0.82rem; color: #64748B;">
                        📅 Due: <strong>{t.suggested_deadline}</strong> • Category: {t.category} • Assignee: {t.responsible_person or 'Unassigned'}
                        <span class="tag-pill {prio_color}" style="margin-left: 6px;">{t.priority}</span>
                        {overdue_badge}
                    </div>
                    """, unsafe_allow_html=True)

                with col_status:
                    stat_options = ["Not Started", "In Progress", "Completed"]
                    cur_idx = stat_options.index(t.status) if t.status in stat_options else 0
                    sel_stat = st.selectbox(
                        "Status",
                        options=stat_options,
                        index=cur_idx,
                        key=f"sel_stat_{t.id}",
                        label_visibility="collapsed"
                    )
                    if sel_stat != t.status:
                        update_task_status(t.id, sel_stat)
                        st.rerun()

                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)

    with tab_schedule:
        st.markdown("#### Chronological Day-Of Itinerary")
        st.caption(f"Detailed timeline for event day ({event.input_details.event_date}).")

        warnings = validate_day_schedule(event.day_schedule)
        if warnings:
            for w in warnings:
                st.warning(f"⚠️ {w}")

        if not event.day_schedule:
            st.info("No schedule items recorded for this event yet.")
        else:
            sch_rows = []
            for s in event.day_schedule:
                sch_rows.append({
                    "Start Time": s.start_time,
                    "Activity": s.activity_name,
                    "Duration": f"{s.duration_minutes} mins",
                    "Notes": s.notes or "—"
                })
            st.dataframe(pd.DataFrame(sch_rows), use_container_width=True)

        with st.expander("➕ Add Item to Day-Of Schedule"):
            with st.form("add_sched_form"):
                sc_time = st.text_input("Start Time", placeholder="e.g. 05:30 PM")
                sc_name = st.text_input("Activity Name", placeholder="e.g. Ring Exchange & Vows")
                sc_dur = st.number_input("Duration (minutes)", min_value=5, max_value=480, value=45, step=5)
                sc_notes = st.text_input("Notes", placeholder="e.g. Photographer position in center aisle")

                submit_sch = st.form_submit_button("Add Activity", type="primary")
                if submit_sch:
                    if not sc_time or not sc_name:
                        st.error("Start time and activity name are required.")
                    else:
                        event.day_schedule.append(EventScheduleItem(
                            start_time=sc_time.strip(),
                            activity_name=sc_name.strip(),
                            duration_minutes=int(sc_dur),
                            notes=sc_notes.strip() if sc_notes else ""
                        ))
                        save_full_event(event)
                        st.success("Activity added to day schedule!")
                        st.rerun()

    with tab_add:
        st.markdown("#### ➕ Add New Preparation Milestone Task")
        with st.form("create_task_form"):
            t_title = st.text_input("Task Title *", placeholder="e.g. Book luxury transport van for bridal party")
            t_desc = st.text_area("Description / Checklist", placeholder="Check AC condition, luggage capacity, and driver fuel policy")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                t_deadline = st.date_input("Suggested Deadline *", min_value=date.today())
                t_prio = st.selectbox("Priority", options=["High", "Medium", "Low"])
            with col_t2:
                t_cat = st.selectbox("Category", options=[a.category for a in event.budget_allocations] + ["General"])
                t_assignee = st.text_input("Responsible Person (Optional)", placeholder="e.g. Cousin Rahul")

            submit_task = st.form_submit_button("Create Milestone Task", type="primary")
            if submit_task:
                if not t_title:
                    st.error("Task title is required.")
                else:
                    new_task = TaskItem(
                        id=str(uuid.uuid4())[:8],
                        title=t_title.strip(),
                        description=t_desc.strip() if t_desc else "",
                        suggested_deadline=t_deadline.strftime("%Y-%m-%d"),
                        days_before_event=None,
                        priority=t_prio,
                        status="Not Started",
                        responsible_person=t_assignee.strip() if t_assignee else "",
                        category=t_cat
                    )
                    event.tasks.append(new_task)
                    event.tasks.sort(key=lambda x: x.suggested_deadline)
                    save_full_event(event)
                    st.success(f"Task '{t_title}' created successfully!")
                    st.rerun()
