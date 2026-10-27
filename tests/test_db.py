"""Test SQLite database persistence layer for FestiWise AI."""

import os
import tempfile
import pytest
from models.schemas import (
    FullEventPlan,
    EventInput,
    BudgetAllocation,
    ExpenseItem,
    TaskItem,
    CreativeConcepts
)
from database.db import (
    init_db,
    save_full_event,
    get_full_event,
    list_events,
    delete_event,
    update_task_status,
    add_or_update_expense
)


@pytest.fixture
def temp_db():
    """Create a temporary test database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_save_and_retrieve_event(temp_db):
    """Verify complete event roundtrip through SQLite."""
    inp = EventInput(
        event_name="Pooja & Rohan Reception",
        event_category="Wedding",
        event_date="2026-12-25",
        city_location="Chennai",
        venue_type="Indoor",
        guest_count=150,
        total_budget=400000.0,
        currency="INR"
    )

    plan = FullEventPlan(
        id="test-event-01",
        input_details=inp,
        overview="A grand reception celebration in Chennai.",
        creative=CreativeConcepts(
            recommended_theme="Carnatic Heritage",
            theme_rationale="Traditional elegance",
            color_palette=["Gold", "Emerald"],
            decor_concepts=["Mogra floral chandeliers"]
        ),
        budget_allocations=[
            BudgetAllocation(category="Venue", planned_amount=120000.0, percentage=30.0),
            BudgetAllocation(category="Catering", planned_amount=160000.0, percentage=40.0),
        ],
        tasks=[
            TaskItem(id="t1", title="Book Hall", suggested_deadline="2026-11-01", status="Not Started")
        ],
        expenses=[
            ExpenseItem(id="e1", category="Venue", item_name="Hall Advance", estimated_cost=50000.0, actual_cost=50000.0)
        ]
    )

    save_full_event(plan, db_path=temp_db)

    # Retrieve
    retrieved = get_full_event("test-event-01", db_path=temp_db)
    assert retrieved is not None
    assert retrieved.input_details.event_name == "Pooja & Rohan Reception"
    assert retrieved.input_details.total_budget == 400000.0
    assert len(retrieved.budget_allocations) == 2
    assert len(retrieved.tasks) == 1
    assert len(retrieved.expenses) == 1
    assert retrieved.creative.recommended_theme == "Carnatic Heritage"


def test_task_status_quick_update(temp_db):
    """Verify task status quick update in database."""
    test_save_and_retrieve_event(temp_db)

    success = update_task_status("t1", "Completed", db_path=temp_db)
    assert success is True

    updated_event = get_full_event("test-event-01", db_path=temp_db)
    task = next((t for t in updated_event.tasks if t.id == "t1"), None)
    assert task is not None
    assert task.status == "Completed"


def test_delete_event_cascade(temp_db):
    """Verify event deletion and foreign key cascading."""
    test_save_and_retrieve_event(temp_db)

    events_before = list_events(db_path=temp_db)
    assert len(events_before) == 1

    deleted = delete_event("test-event-01", db_path=temp_db)
    assert deleted is True

    events_after = list_events(db_path=temp_db)
    assert len(events_after) == 0

    assert get_full_event("test-event-01", db_path=temp_db) is None
