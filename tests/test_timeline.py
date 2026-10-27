"""Test timeline, day schedule, and task management for FestiWise AI."""

import pytest
from datetime import datetime, date, timedelta
from models.schemas import EventInput, TaskItem, EventScheduleItem
from services.timeline_service import (
    generate_baseline_tasks,
    calculate_timeline_metrics,
    validate_day_schedule
)


def test_generate_baseline_tasks_ordering():
    """Verify tasks are generated and ordered chronologically by deadline."""
    inp = EventInput(
        event_name="Graduation Gala",
        event_category="College Event",
        event_date=(date.today() + timedelta(days=60)).strftime("%Y-%m-%d"),
        city_location="Hyderabad",
        guest_count=200,
        total_budget=150000.0
    )

    tasks = generate_baseline_tasks(inp)
    assert len(tasks) > 0

    # Ensure chronological order
    deadlines = [t.suggested_deadline for t in tasks]
    assert deadlines == sorted(deadlines)


def test_calculate_timeline_metrics():
    """Verify task completion and overdue calculations."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    tasks = [
        TaskItem(id="t1", title="Task 1", suggested_deadline=today_str, status="Completed", priority="High"),
        TaskItem(id="t2", title="Task 2", suggested_deadline=yesterday_str, status="In Progress", priority="High"),
        TaskItem(id="t3", title="Task 3", suggested_deadline=tomorrow_str, status="Not Started", priority="Low"),
    ]

    metrics = calculate_timeline_metrics(tasks)
    assert metrics["total_tasks"] == 3
    assert metrics["completed_tasks"] == 1
    assert metrics["in_progress_tasks"] == 1
    assert metrics["not_started_tasks"] == 1
    assert metrics["completion_percentage"] == 33.3
    assert metrics["overdue_tasks"] == 1  # Task 2 is yesterday and in progress
    assert metrics["high_priority_remaining"] == 1  # Task 2 is High and open


def test_validate_day_schedule():
    """Verify schedule warnings for invalid durations or empty times."""
    valid_schedule = [
        EventScheduleItem(start_time="10:00 AM", activity_name="Welcome", duration_minutes=30),
        EventScheduleItem(start_time="10:30 AM", activity_name="Keynote", duration_minutes=45),
    ]
    assert validate_day_schedule(valid_schedule) == []

    invalid_schedule = [
        EventScheduleItem(start_time="", activity_name="Bad Time", duration_minutes=30),
        EventScheduleItem(start_time="11:00 AM", activity_name="Bad Duration", duration_minutes=0),
    ]
    warnings = validate_day_schedule(invalid_schedule)
    assert len(warnings) == 2
