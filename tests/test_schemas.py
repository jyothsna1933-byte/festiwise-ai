"""Test Pydantic schemas and input validation for FestiWise AI."""

import pytest
from pydantic import ValidationError
from models.schemas import EventInput, BudgetAllocation, ExpenseItem, TaskItem


def test_valid_event_input():
    """Verify that a correctly formatted EventInput succeeds."""
    inp = EventInput(
        event_name="Sharma Golden Anniversary",
        event_category="Community Gathering",
        event_date="2026-12-15",
        city_location="Mumbai",
        venue_type="Indoor",
        guest_count=120,
        total_budget=250000.0,
        currency="INR"
    )
    assert inp.event_name == "Sharma Golden Anniversary"
    assert inp.guest_count == 120
    assert inp.total_budget == 250000.0


def test_invalid_event_date_format():
    """Verify that invalid date formats trigger validation errors."""
    with pytest.raises(ValidationError):
        EventInput(
            event_name="Birthday Bash",
            event_category="Birthday",
            event_date="15-12-2026",  # Invalid, must be YYYY-MM-DD
            city_location="Delhi",
            guest_count=50,
            total_budget=50000.0
        )


def test_zero_or_negative_budget():
    """Verify that zero or negative budgets are rejected."""
    with pytest.raises(ValidationError):
        EventInput(
            event_name="College Fest",
            event_category="College Event",
            event_date="2026-11-10",
            city_location="Pune",
            guest_count=500,
            total_budget=0.0  # Must be > 0
        )

    with pytest.raises(ValidationError):
        EventInput(
            event_name="College Fest",
            event_category="College Event",
            event_date="2026-11-10",
            city_location="Pune",
            guest_count=500,
            total_budget=-5000.0  # Must be > 0
        )


def test_zero_guest_count():
    """Verify that guest count must be > 0."""
    with pytest.raises(ValidationError):
        EventInput(
            event_name="Intimate Dinner",
            event_category="Custom",
            event_date="2026-11-10",
            city_location="Goa",
            guest_count=0,  # Invalid
            total_budget=10000.0
        )
