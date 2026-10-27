"""End-to-end integration workflow tests for FestiWise AI.

Tests complete user journeys:
1. Seeded event loading & dashboard metrics
2. Event creation & blueprint persistence
3. Budget expense addition, variance tracking, and rebalancing
4. Timeline milestone tracking & status updates
5. Vendor management & AI guidance
6. Plan Rescue Mode disruption evaluation, diff generation, and revision application
7. JSON export and schema rehydration
"""

import json
import pytest
from database.db import (
    init_db,
    list_events,
    get_full_event,
    save_full_event,
    add_or_update_expense,
    update_task_status,
    delete_event
)
from models.schemas import (
    EventInput,
    FullEventPlan,
    ExpenseItem,
    VendorItem,
    GuestItem,
    PlanRescueRequest
)
from services.gemini_service import _generate_demo_event_blueprint
from services.budget_service import (
    generate_initial_allocations,
    calculate_budget_summary,
    rebalance_allocations_to_target
)
from services.timeline_service import generate_baseline_tasks, calculate_timeline_metrics
from services.rescue_service import evaluate_plan_rescue, apply_plan_rescue_changes


def test_full_user_lifecycle_workflow():
    """Verify entire celebration lifecycle from creation through Plan Rescue and export."""
    init_db()

    # 1. Create a new event
    event_input = EventInput(
        event_name="Meera's 18th Neon Birthday",
        event_category="Birthday",
        event_date="2026-12-10",
        city_location="Mumbai",
        venue_type="Indoor",
        guest_count=60,
        total_budget=80000.0,
        currency="INR",
        preferred_theme="Neon Arcade Glow",
        food_preference="Mixed (Veg & Non-Veg)"
    )

    blueprint = _generate_demo_event_blueprint(event_input)
    allocations = generate_initial_allocations(event_input.total_budget, event_input.event_category)
    tasks = generate_baseline_tasks(event_input)

    plan = FullEventPlan(
        id="test-lifecycle-01",
        input_details=event_input,
        overview=blueprint["overview"],
        creative=blueprint["creative"],
        budget_allocations=allocations,
        expenses=[],
        tasks=tasks,
        day_schedule=blueprint["day_schedule"],
        vendor_guidance=blueprint["vendor_guidance"],
        vendors=[
            VendorItem(
                id="v-01",
                category="Venue & Play Area",
                name="Neon Arena Arcade",
                quoted_price=24000.0,
                booking_status="Researching"
            )
        ],
        guests=[
            GuestItem(id="g-01", name="Meera", rsvp_status="Attending", plus_ones=0),
            GuestItem(id="g-02", name="Ria Sharma", rsvp_status="Pending", plus_ones=1),
        ],
        risks_and_contingencies=blueprint["risks_and_contingencies"],
        assumptions=blueprint["assumptions"]
    )

    save_full_event(plan)

    # 2. Verify retrieval
    retrieved = get_full_event("test-lifecycle-01")
    assert retrieved is not None
    assert retrieved.input_details.event_name == "Meera's 18th Neon Birthday"
    assert len(retrieved.budget_allocations) > 0
    assert len(retrieved.tasks) > 0
    assert len(retrieved.guests) == 2

    # 3. Add an expense item & verify deterministic calculation
    exp = ExpenseItem(
        id="exp-life-1",
        category="Venue & Play Area",
        item_name="Arcade Booking Advance",
        estimated_cost=25000.0,
        actual_cost=24000.0,
        vendor_name="Neon Arena Arcade",
        payment_status="Paid",
        is_verified=True
    )
    add_or_update_expense("test-lifecycle-01", exp)

    updated_event = get_full_event("test-lifecycle-01")
    summary = calculate_budget_summary(
        updated_event.input_details.total_budget,
        updated_event.budget_allocations,
        updated_event.expenses,
        updated_event.input_details.guest_count
    )
    assert summary["total_committed"] == 24000.0
    assert summary["remaining_budget"] == 56000.0
    assert summary["is_overbudget"] is False

    # 4. Update task completion status
    first_task = updated_event.tasks[0]
    update_task_status(first_task.id, "Completed")
    event_after_task = get_full_event("test-lifecycle-01")
    t_metrics = calculate_timeline_metrics(event_after_task.tasks)
    assert t_metrics["completed_tasks"] == 1
    assert t_metrics["completion_percentage"] > 0

    # 5. Execute Plan Rescue Mode workflow
    rescue_req = PlanRescueRequest(
        event_id="test-lifecycle-01",
        disruption_type="Venue cancellation or sudden fee increase",
        disruption_details="Arcade venue increased fees by Rs. 15,000 and 20 extra friends RSVPed!",
        new_budget=105000.0,
        additional_guests=20
    )

    rec, diff, used_ai, model_used = evaluate_plan_rescue(
        current_plan=event_after_task,
        request=rescue_req,
        category_cost_deltas={"Venue & Play Area": 15000.0}
    )

    # Check that diff is computed before application
    assert diff["old_guest_count"] == 60
    assert diff["proposed_guest_count"] == 80
    assert diff["old_budget"] == 80000.0
    assert diff["proposed_budget"] == 105000.0
    assert len(rec.recommended_alternatives) > 0
    assert len(rec.contingency_steps) > 0

    # Apply Plan Rescue revisions
    apply_plan_rescue_changes(event_after_task, diff)

    # 6. Verify changes persisted in SQLite
    rescued_event = get_full_event("test-lifecycle-01")
    assert rescued_event.input_details.total_budget == 105000.0
    assert rescued_event.input_details.guest_count == 80
    assert len(rescued_event.rescue_history) == 1
    assert any("[RESCUE]" in t.title for t in rescued_event.tasks)

    # 7. JSON Export validation
    json_str = rescued_event.model_dump_json(indent=2)
    rehydrated = FullEventPlan.model_validate_json(json_str)
    assert rehydrated.id == rescued_event.id
    assert rehydrated.input_details.total_budget == 105000.0

    # Clean up
    delete_event("test-lifecycle-01")
    assert get_full_event("test-lifecycle-01") is None
