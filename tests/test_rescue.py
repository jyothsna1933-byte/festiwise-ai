"""Test Plan Rescue Mode and crisis budget recalculations for FestiWise AI."""

import os
import tempfile
import pytest
from models.schemas import (
    FullEventPlan,
    EventInput,
    BudgetAllocation,
    CreativeConcepts,
    PlanRescueRequest
)
from services.rescue_service import evaluate_plan_rescue, apply_plan_rescue_changes
from services.budget_service import compute_rescue_budget_delta
from database.db import init_db, save_full_event, get_full_event


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_compute_rescue_budget_delta_direct_and_guests():
    """Verify programmatic math for the prompt's example:

    Original plan:
    - Budget: 15,000
    - Venue allocation: 3,000
    - Guest count: 30
    Unexpected change:
    - Venue cost increases to 5,000 (direct delta +2,000)
    - Guest count increases to 40 (additional guests +10, cost per guest 100)
    """
    delta = compute_rescue_budget_delta(
        original_budget=15000.0,
        current_guest_count=30,
        additional_guests=10,
        cost_per_guest_estimate=100.0,
        category_cost_deltas={"Venue": 2000.0},
        new_total_budget_cap=15000.0  # Cap kept fixed
    )

    # Direct delta = +2000
    assert delta["total_direct_delta"] == 2000.0
    # Guest variable delta = 10 * 100 = 1000
    assert delta["guest_variable_delta"] == 1000.0
    # Total cost increase = 3000
    assert delta["total_cost_increase"] == 3000.0
    # Projected required = 18000
    assert delta["projected_required_budget"] == 18000.0
    # Requires cuts = True, cut needed = 3000
    assert delta["requires_cuts"] is True
    assert delta["cut_amount_needed"] == 3000.0
    assert delta["new_guest_count"] == 40


def test_evaluate_and_apply_plan_rescue(temp_db):
    """Verify end-to-end evaluation and application of Plan Rescue revisions."""
    inp = EventInput(
        event_name="College Hackathon Night",
        event_category="College Event",
        event_date="2026-11-15",
        city_location="Delhi",
        venue_type="Outdoor",
        guest_count=100,
        total_budget=100000.0,
        currency="INR"
    )

    plan = FullEventPlan(
        id="rescue-test-01",
        input_details=inp,
        overview="Hackathon night.",
        creative=CreativeConcepts(recommended_theme="Tech Glow", theme_rationale="Engaging"),
        budget_allocations=[
            BudgetAllocation(category="Venue & Infrastructure", planned_amount=30000.0, percentage=30.0),
            BudgetAllocation(category="Food & Refreshments", planned_amount=40000.0, percentage=40.0),
            BudgetAllocation(category="Emergency Reserve", planned_amount=10000.0, percentage=10.0),
        ],
        tasks=[],
        expenses=[]
    )
    save_full_event(plan, db_path=temp_db)

    # Disruption: Bad weather threat -> Switch to Indoor & expand budget to 110,000
    req = PlanRescueRequest(
        event_id="rescue-test-01",
        disruption_type="Bad weather affecting outdoor event",
        disruption_details="Heavy torrential rain forecast on hackathon night.",
        new_budget=110000.0,
        additional_guests=10,
        new_venue_type="Indoor"
    )

    rec, diff, used_ai, model = evaluate_plan_rescue(
        current_plan=plan,
        request=req,
        category_cost_deltas={"Venue & Infrastructure": 5000.0}
    )

    assert rec is not None
    assert diff["proposed_venue_type"] == "Indoor"
    assert diff["proposed_guest_count"] == 110
    assert diff["proposed_budget"] == 110000.0
    assert len(rec.recommended_alternatives) > 0

    # Apply revisions
    updated_plan = apply_plan_rescue_changes(plan, diff, db_path=temp_db)

    # Verify persisted changes
    saved_plan = get_full_event("rescue-test-01", db_path=temp_db)
    assert saved_plan.input_details.total_budget == 110000.0
    assert saved_plan.input_details.guest_count == 110
    assert saved_plan.input_details.venue_type == "Indoor"
    assert len(saved_plan.rescue_history) == 1
    assert any("[RESCUE]" in t.title for t in saved_plan.tasks)
