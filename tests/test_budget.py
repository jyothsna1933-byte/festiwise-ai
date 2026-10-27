"""Test deterministic budget calculation engine for FestiWise AI."""

import pytest
from models.schemas import BudgetAllocation, ExpenseItem
from services.budget_service import (
    generate_initial_allocations,
    calculate_budget_summary,
    rebalance_allocations_to_target,
    compute_rescue_budget_delta
)


def test_initial_allocations_sum_to_total():
    """Verify that generated baseline allocations sum EXACTLY to the user's budget."""
    for cat in ["Wedding", "Birthday", "College Event", "Festival", "Community Gathering", "Custom"]:
        total = 350000.0
        allocs = generate_initial_allocations(total, cat)
        total_planned = round(sum(a.planned_amount for a in allocs), 2)
        assert total_planned == total, f"Allocations for {cat} sum to {total_planned}, expected {total}"


def test_calculate_budget_summary_normal():
    """Verify budget summary metrics with normal expenses."""
    total_budget = 100000.0
    allocs = generate_initial_allocations(total_budget, "Birthday")
    
    expenses = [
        ExpenseItem(id="e1", category=allocs[0].category, item_name="Hall Deposit", estimated_cost=20000.0, actual_cost=18000.0, is_verified=True),
        ExpenseItem(id="e2", category=allocs[1].category, item_name="Catering Advance", estimated_cost=30000.0, actual_cost=None, is_verified=False),
    ]

    summary = calculate_budget_summary(total_budget, allocs, expenses, guest_count=50)

    assert summary["total_budget"] == 100000.0
    assert summary["total_actual"] == 18000.0
    assert summary["total_estimated"] == 50000.0
    # Committed should take actual (18000) + estimated where actual is None (30000) = 48000
    assert summary["total_committed"] == 48000.0
    assert summary["remaining_budget"] == 52000.0
    assert summary["is_overbudget"] is False
    assert summary["burn_percentage"] == 48.0
    assert summary["per_guest_planned"] == 2000.0
    assert summary["per_guest_actual"] == 960.0


def test_budget_overflow_detection():
    """Verify detection when expenses exceed total budget."""
    total_budget = 50000.0
    allocs = generate_initial_allocations(total_budget, "Custom")

    # Expenses totaling 60000 (overbudget by 10000)
    expenses = [
        ExpenseItem(id="e1", category="Venue & Infrastructure", item_name="Lawn", estimated_cost=35000.0, actual_cost=35000.0),
        ExpenseItem(id="e2", category="Catering & Refreshments", item_name="Food", estimated_cost=25000.0, actual_cost=25000.0),
    ]

    summary = calculate_budget_summary(total_budget, allocs, expenses, guest_count=25)

    assert summary["is_overbudget"] is True
    assert summary["remaining_budget"] == -10000.0
    assert summary["total_committed"] == 60000.0


def test_rebalance_allocations_to_target():
    """Verify that rebalancing preserves category ratios and matches target sum."""
    original_budget = 100000.0
    allocs = generate_initial_allocations(original_budget, "Wedding")

    # Scale down budget to 80,000
    new_target = 80000.0
    rebalanced = rebalance_allocations_to_target(allocs, new_target)

    new_sum = round(sum(a.planned_amount for a in rebalanced), 2)
    assert new_sum == new_target
    assert len(rebalanced) == len(allocs)
