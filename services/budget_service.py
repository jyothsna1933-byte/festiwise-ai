"""Deterministic programmatic budget calculation engine for FestiWise AI.

CRITICAL FINANCIAL CALCULATION RULE:
Never rely on the language model for arithmetic.
All totals, percentages, remaining balances, per-guest averages, variances,
and rescue differences are calculated strictly in Python code.
"""

from typing import List, Dict, Any, Optional
from config import DEFAULT_BUDGET_RATIOS
from models.schemas import BudgetAllocation, ExpenseItem


def generate_initial_allocations(total_budget: float, category: str) -> List[BudgetAllocation]:
    """Generate baseline budget allocations based on event category ratios.
    
    Ensures that sum of planned_amount exactly equals total_budget,
    handling any minor rounding pennies on the largest flexible category.
    """
    if total_budget <= 0:
        raise ValueError("Total budget must be greater than zero.")
        
    ratios = DEFAULT_BUDGET_RATIOS.get(category, DEFAULT_BUDGET_RATIOS["Custom"])
    allocations: List[BudgetAllocation] = []
    
    cumulative_amount = 0.0
    items = list(ratios.items())
    
    for i, (cat_name, ratio) in enumerate(items):
        if i == len(items) - 1:
            # Last item absorbs any rounding difference to guarantee exact match
            amount = round(total_budget - cumulative_amount, 2)
            pct = round((amount / total_budget) * 100, 2)
        else:
            amount = round(total_budget * ratio, 2)
            pct = round(ratio * 100, 2)
            cumulative_amount += amount
            
        allocations.append(
            BudgetAllocation(
                category=cat_name,
                planned_amount=amount,
                percentage=pct,
                notes=f"Baseline allocation ({pct:.1f}%) for {category.lower()} event",
                is_flexible=(cat_name != "Emergency Reserve")
            )
        )
        
    return allocations


def calculate_budget_summary(
    total_budget: float,
    allocations: List[BudgetAllocation],
    expenses: List[ExpenseItem],
    guest_count: int = 1
) -> Dict[str, Any]:
    """Calculate comprehensive budget metrics, variances, and category breakdowns programmatically.
    
    Returns:
    - total_budget: float
    - total_planned: float
    - total_spent_actual: float
    - total_estimated_expenses: float
    - total_committed: float (actual if recorded, else estimated)
    - remaining_budget: float
    - variance_amount: float
    - is_overbudget: bool
    - allocation_variance: float (total_budget - total_planned)
    - per_guest_planned: float
    - per_guest_actual: float
    - category_breakdown: Dict of category -> details
    """
    if guest_count <= 0:
        guest_count = 1
        
    total_budget = round(float(total_budget), 2)
    total_planned = round(sum(a.planned_amount for a in allocations), 2)
    
    total_actual = 0.0
    total_estimated = 0.0
    total_committed = 0.0
    
    # Category trackers
    cat_expenses: Dict[str, Dict[str, float]] = {}
    for a in allocations:
        cat_expenses[a.category] = {
            "planned": a.planned_amount,
            "estimated": 0.0,
            "actual": 0.0,
            "committed": 0.0,
            "verified_count": 0,
            "item_count": 0
        }
        
    for exp in expenses:
        est = round(float(exp.estimated_cost or 0.0), 2)
        act = round(float(exp.actual_cost), 2) if exp.actual_cost is not None else None
        committed = act if act is not None else est
        
        total_estimated += est
        if act is not None:
            total_actual += act
        total_committed += committed
        
        cat = exp.category
        if cat not in cat_expenses:
            cat_expenses[cat] = {
                "planned": 0.0,
                "estimated": 0.0,
                "actual": 0.0,
                "committed": 0.0,
                "verified_count": 0,
                "item_count": 0
            }
            
        cat_expenses[cat]["estimated"] += est
        if act is not None:
            cat_expenses[cat]["actual"] += act
        cat_expenses[cat]["committed"] += committed
        cat_expenses[cat]["item_count"] += 1
        if exp.is_verified:
            cat_expenses[cat]["verified_count"] += 1

    total_actual = round(total_actual, 2)
    total_estimated = round(total_estimated, 2)
    total_committed = round(total_committed, 2)
    remaining_budget = round(total_budget - total_committed, 2)
    allocation_variance = round(total_budget - total_planned, 2)
    
    is_overbudget = total_committed > total_budget
    is_allocations_over = total_planned > total_budget
    
    per_guest_planned = round(total_budget / guest_count, 2)
    per_guest_actual = round(total_committed / guest_count, 2)
    
    # Calculate percentages for category breakdown
    for cat, data in cat_expenses.items():
        data["planned_pct"] = round((data["planned"] / total_budget * 100), 2) if total_budget > 0 else 0.0
        data["committed_pct"] = round((data["committed"] / total_budget * 100), 2) if total_budget > 0 else 0.0
        data["variance"] = round(data["planned"] - data["committed"], 2)
        data["is_category_over"] = data["committed"] > data["planned"]

    return {
        "total_budget": total_budget,
        "total_planned": total_planned,
        "total_actual": total_actual,
        "total_estimated": total_estimated,
        "total_committed": total_committed,
        "remaining_budget": remaining_budget,
        "allocation_variance": allocation_variance,
        "is_overbudget": is_overbudget,
        "is_allocations_over": is_allocations_over,
        "burn_percentage": round((total_committed / total_budget * 100), 2) if total_budget > 0 else 0.0,
        "per_guest_planned": per_guest_planned,
        "per_guest_actual": per_guest_actual,
        "category_breakdown": cat_expenses,
        "expense_count": len(expenses),
    }


def rebalance_allocations_to_target(
    allocations: List[BudgetAllocation],
    target_budget: float
) -> List[BudgetAllocation]:
    """Proportionally rebalance allocations so their sum matches target_budget exactly.
    
    Maintains relative weighting between categories while preserving internal mathematical consistency.
    """
    if target_budget <= 0:
        raise ValueError("Target budget must be strictly positive.")
    if not allocations:
        return []
        
    current_sum = sum(a.planned_amount for a in allocations)
    if current_sum <= 0:
        # Equal split
        share = round(target_budget / len(allocations), 2)
        rebalanced = []
        c_sum = 0.0
        for i, a in enumerate(allocations):
            if i == len(allocations) - 1:
                amt = round(target_budget - c_sum, 2)
            else:
                amt = share
                c_sum += amt
            pct = round((amt / target_budget) * 100, 2)
            rebalanced.append(
                BudgetAllocation(
                    category=a.category,
                    planned_amount=amt,
                    percentage=pct,
                    notes=a.notes,
                    is_flexible=a.is_flexible
                )
            )
        return rebalanced

    rebalanced = []
    c_sum = 0.0
    for i, a in enumerate(allocations):
        ratio = a.planned_amount / current_sum
        if i == len(allocations) - 1:
            amt = round(target_budget - c_sum, 2)
        else:
            amt = round(target_budget * ratio, 2)
            c_sum += amt
        pct = round((amt / target_budget) * 100, 2)
        rebalanced.append(
            BudgetAllocation(
                category=a.category,
                planned_amount=amt,
                percentage=pct,
                notes=a.notes,
                is_flexible=a.is_flexible
            )
        )
    return rebalanced


def compute_rescue_budget_delta(
    original_budget: float,
    current_guest_count: int,
    additional_guests: int = 0,
    cost_per_guest_estimate: float = 0.0,
    category_cost_deltas: Optional[Dict[str, float]] = None,
    new_total_budget_cap: Optional[float] = None
) -> Dict[str, Any]:
    """Calculate the precise financial impact of disruptions for Plan Rescue Mode.
    
    All calculations are strictly deterministic in Python code.
    """
    category_cost_deltas = category_cost_deltas or {}
    
    # 1. Direct category changes (e.g., venue cost increased by 2000)
    total_direct_delta = round(sum(category_cost_deltas.values()), 2)
    
    # 2. Guest surge calculations
    guest_variable_delta = round(max(0, additional_guests) * max(0.0, cost_per_guest_estimate), 2)
    
    # 3. Total additional cost impact
    total_cost_increase = round(total_direct_delta + guest_variable_delta, 2)
    
    # 4. Projected required total budget
    projected_required_budget = round(original_budget + total_cost_increase, 2)
    
    # 5. Cap comparison
    target_cap = new_total_budget_cap if new_total_budget_cap is not None else original_budget
    deficit_or_surplus = round(target_cap - projected_required_budget, 2)
    
    # 6. Rebalancing deficit (amount that must be cut from other categories if cap is fixed)
    requires_cuts = deficit_or_surplus < 0
    cut_amount_needed = abs(deficit_or_surplus) if requires_cuts else 0.0
    
    new_guest_count = current_guest_count + max(0, additional_guests)
    projected_per_guest = round(projected_required_budget / new_guest_count, 2) if new_guest_count > 0 else 0.0

    return {
        "original_budget": round(original_budget, 2),
        "target_cap": round(target_cap, 2),
        "category_cost_deltas": category_cost_deltas,
        "total_direct_delta": total_direct_delta,
        "additional_guests": additional_guests,
        "new_guest_count": new_guest_count,
        "cost_per_guest_estimate": cost_per_guest_estimate,
        "guest_variable_delta": guest_variable_delta,
        "total_cost_increase": total_cost_increase,
        "projected_required_budget": projected_required_budget,
        "deficit_or_surplus": deficit_or_surplus,
        "requires_cuts": requires_cuts,
        "cut_amount_needed": round(cut_amount_needed, 2),
        "projected_per_guest": projected_per_guest,
    }
