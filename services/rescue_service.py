"""Plan Rescue Engine for FestiWise AI.

Signature differentiator:
Analyzes disruptions against the current saved event, computes quantitative
impacts deterministically in Python, queries Gemini for contextual strategic
alternatives, builds a clear before-and-after diff, and applies approved revisions.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from models.schemas import (
    FullEventPlan,
    PlanRescueRequest,
    PlanRescueRecommendation,
    BudgetAllocation,
    TaskItem,
    ExpenseItem
)
from services.budget_service import (
    calculate_budget_summary,
    compute_rescue_budget_delta,
    rebalance_allocations_to_target
)
from services.gemini_service import generate_plan_rescue_advice
from database.db import save_full_event


def evaluate_plan_rescue(
    current_plan: FullEventPlan,
    request: PlanRescueRequest,
    cost_per_guest_override: Optional[float] = None,
    category_cost_deltas: Optional[Dict[str, float]] = None,
    model_name: Optional[str] = None
) -> Tuple[PlanRescueRecommendation, Dict[str, Any], bool, str]:
    """Execute Plan Rescue assessment against the existing event.
    
    Returns:
    - PlanRescueRecommendation
    - PlanDiff dictionary (detailed before-and-after comparison)
    - used_live_ai (bool)
    - model_used (str)
    """
    category_cost_deltas = category_cost_deltas or {}
    
    # 1. Determine baseline cost per guest from catering allocation or current budget
    catering_alloc = next(
        (a.planned_amount for a in current_plan.budget_allocations if "cater" in a.category.lower() or "food" in a.category.lower()),
        current_plan.input_details.total_budget * 0.35
    )
    default_cpg = round(catering_alloc / max(1, current_plan.input_details.guest_count), 2)
    effective_cpg = cost_per_guest_override if cost_per_guest_override is not None else default_cpg

    # 2. Programmatically calculate financial impact
    additional_guests = request.additional_guests or 0
    budget_impact = compute_rescue_budget_delta(
        original_budget=current_plan.input_details.total_budget,
        current_guest_count=current_plan.input_details.guest_count,
        additional_guests=additional_guests,
        cost_per_guest_estimate=effective_cpg,
        category_cost_deltas=category_cost_deltas,
        new_total_budget_cap=request.new_budget
    )

    # 3. Call Gemini (or demo engine) for qualitative mitigation strategies
    event_data = {
        "name": current_plan.input_details.event_name,
        "category": current_plan.input_details.event_category,
        "event_date": current_plan.input_details.event_date,
        "city": current_plan.input_details.city_location,
        "venue_type": current_plan.input_details.venue_type,
        "guest_count": current_plan.input_details.guest_count,
        "total_budget": current_plan.input_details.total_budget,
        "currency": current_plan.input_details.currency,
    }

    recommendation, used_live_ai, model_used = generate_plan_rescue_advice(
        request=request,
        event_data=event_data,
        budget_impact=budget_impact,
        model_name=model_name
    )

    # 4. Construct Proposed Revised Allocations deterministically
    target_budget = request.new_budget if request.new_budget is not None else budget_impact["projected_required_budget"]
    
    # Calculate proposed allocations adjusted for direct deltas
    proposed_allocations: List[BudgetAllocation] = []
    current_alloc_map = {a.category: a for a in current_plan.budget_allocations}
    
    # If the user wishes to maintain their existing budget cap despite cost shocks,
    # we must rebalance flexible categories to absorb the deficit
    if request.new_budget is not None and request.new_budget < budget_impact["projected_required_budget"]:
        # Scale flexible categories down
        proposed_allocations = rebalance_allocations_to_target(
            current_plan.budget_allocations,
            request.new_budget
        )
    else:
        # Expand budget or accommodate direct deltas
        for cat, a in current_alloc_map.items():
            delta = category_cost_deltas.get(cat, 0.0)
            if "cater" in cat.lower() or "food" in cat.lower():
                delta += budget_impact["guest_variable_delta"]
            new_amt = round(max(0.0, a.planned_amount + delta), 2)
            proposed_allocations.append(
                BudgetAllocation(
                    category=cat,
                    planned_amount=new_amt,
                    percentage=round((new_amt / target_budget * 100), 2) if target_budget > 0 else 0.0,
                    notes=f"Adjusted via Plan Rescue for {request.disruption_type}",
                    is_flexible=a.is_flexible
                )
            )

    # 5. Build before-and-after diff
    plan_diff = {
        "event_id": current_plan.id,
        "disruption_type": request.disruption_type,
        "disruption_details": request.disruption_details,
        "old_budget": current_plan.input_details.total_budget,
        "proposed_budget": target_budget,
        "budget_variance": round(target_budget - current_plan.input_details.total_budget, 2),
        "old_guest_count": current_plan.input_details.guest_count,
        "proposed_guest_count": current_plan.input_details.guest_count + additional_guests,
        "old_venue_type": current_plan.input_details.venue_type,
        "proposed_venue_type": request.new_venue_type or current_plan.input_details.venue_type,
        "category_deltas": category_cost_deltas,
        "cost_per_guest_estimate": effective_cpg,
        "proposed_allocations": [a.model_dump() for a in proposed_allocations],
        "contingency_tasks_to_add": recommendation.contingency_steps,
        "calculated_at": datetime.now().isoformat()
    }

    return recommendation, plan_diff, used_live_ai, model_used


def apply_plan_rescue_changes(
    current_plan: FullEventPlan,
    plan_diff: Dict[str, Any],
    db_path: Optional[str] = None
) -> FullEventPlan:
    """Apply the reviewed and approved Plan Rescue diff to the saved event."""
    # 1. Update event input details
    current_plan.input_details.total_budget = round(float(plan_diff["proposed_budget"]), 2)
    current_plan.input_details.guest_count = int(plan_diff["proposed_guest_count"])
    if plan_diff.get("proposed_venue_type"):
        current_plan.input_details.venue_type = plan_diff["proposed_venue_type"]

    # 2. Update allocations
    new_allocations = [
        BudgetAllocation(**a) for a in plan_diff["proposed_allocations"]
    ]
    current_plan.budget_allocations = new_allocations

    # 3. Add contingency tasks to timeline with High priority
    today_str = datetime.now().strftime("%Y-%m-%d")
    for step in plan_diff.get("contingency_tasks_to_add", []):
        current_plan.tasks.insert(0, TaskItem(
            id=str(uuid.uuid4())[:8],
            title=f"[RESCUE] {step[:80]}",
            description=step,
            suggested_deadline=today_str,
            days_before_event=0,
            priority="High",
            status="Not Started",
            responsible_person="Crisis Coordinator",
            category="Emergency Mitigation"
        ))

    # 4. Record entry in rescue history
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "disruption_type": plan_diff["disruption_type"],
        "disruption_details": plan_diff["disruption_details"],
        "budget_variance": plan_diff["budget_variance"],
        "applied_budget": plan_diff["proposed_budget"],
        "applied_guests": plan_diff["proposed_guest_count"],
    }
    current_plan.rescue_history.append(history_entry)
    current_plan.updated_at = datetime.now().isoformat()

    # 5. Persist to database
    save_full_event(current_plan, db_path)
    return current_plan
