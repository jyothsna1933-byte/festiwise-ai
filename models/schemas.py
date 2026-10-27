"""Pydantic data schemas for FestiWise AI.

Defines schemas for:
- User event inputs & validation
- Programmatic budget allocations & expenses
- Preparation timeline & day-of schedule
- Vendors & category guidelines
- Creative themes & invitations
- Guests & RSVP tracking
- Plan Rescue requests, impact analyses, and plan diffs
"""

from datetime import date, datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class EventInput(BaseModel):
    """User input for creating or updating an event plan."""
    event_name: str = Field(..., min_length=2, max_length=120, description="Name of the celebration")
    event_category: str = Field(..., description="Category (Wedding, Birthday, College Event, Festival, etc.)")
    event_date: str = Field(..., description="Date of the event in YYYY-MM-DD format")
    city_location: str = Field(..., min_length=2, max_length=100, description="City or venue locality")
    venue_type: str = Field(default="Indoor", description="Indoor, Outdoor, or Hybrid preference")
    guest_count: int = Field(..., gt=0, le=100000, description="Estimated number of guests")
    total_budget: float = Field(..., gt=0, description="Total budget in selected currency")
    currency: str = Field(default="INR", description="Currency code (e.g. INR, USD, EUR)")
    preferred_theme: Optional[str] = Field(default="", max_length=150, description="User's style/theme wish")
    food_preference: Optional[str] = Field(default="Mixed (Veg & Non-Veg)", description="Dietary preferences")
    special_requirements: Optional[str] = Field(default="", max_length=500, description="Crucial needs (e.g., wheelchair accessible, Jain food)")
    additional_notes: Optional[str] = Field(default="", max_length=1000, description="Any additional context")

    @field_validator("event_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Event date must be in YYYY-MM-DD format.")
        return v

    @field_validator("total_budget")
    @classmethod
    def validate_budget_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Total budget must be strictly greater than 0.")
        return round(float(v), 2)


class BudgetAllocation(BaseModel):
    """Allocation for a specific category calculated programmatically."""
    category: str
    planned_amount: float
    percentage: float
    notes: Optional[str] = ""
    is_flexible: bool = True

    @field_validator("planned_amount", "percentage")
    @classmethod
    def round_amounts(cls, v: float) -> float:
        return round(float(v), 2)


class ExpenseItem(BaseModel):
    """Specific line item expense entered by user or generated as estimate."""
    id: str
    category: str
    item_name: str
    estimated_cost: float = 0.0
    actual_cost: Optional[float] = None
    vendor_name: Optional[str] = ""
    payment_status: str = "Pending"  # Pending, Partially Paid, Paid
    is_verified: bool = False        # Whether verified with vendor receipt/quote
    notes: Optional[str] = ""


class TaskItem(BaseModel):
    """Preparation task on the timeline."""
    id: str
    title: str
    description: str = ""
    suggested_deadline: str  # YYYY-MM-DD
    days_before_event: Optional[int] = None
    priority: str = "Medium"  # High, Medium, Low
    status: str = "Not Started"  # Not Started, In Progress, Completed
    responsible_person: Optional[str] = ""
    category: str = "General"


class EventScheduleItem(BaseModel):
    """Day-of chronological schedule item."""
    start_time: str  # e.g., "10:00 AM" or "10:00"
    activity_name: str
    duration_minutes: int
    notes: Optional[str] = ""


class VendorItem(BaseModel):
    """Vendor record managed by the organizer."""
    id: str
    category: str
    name: str
    contact_info: Optional[str] = ""
    quoted_price: float = 0.0
    booking_status: str = "Researching"  # Researching, Contacted, Quoted, Booked, Declined
    follow_up_date: Optional[str] = ""
    notes: Optional[str] = ""


class VendorCategoryGuidance(BaseModel):
    """AI guidance for evaluating and interrogating vendors in a category."""
    category: str
    key_questions: List[str]
    evaluation_checklist: List[str]
    caution_red_flags: List[str] = []


class GuestItem(BaseModel):
    """Guest entry in RSVP tracking list."""
    id: str
    name: str
    contact: Optional[str] = ""
    rsvp_status: str = "Pending"  # Attending, Declined, Pending, Tentative
    plus_ones: int = 0
    dietary_notes: Optional[str] = ""
    table_group: Optional[str] = ""


class CreativeConcepts(BaseModel):
    """Personalized creative and thematic ideas."""
    recommended_theme: str
    theme_rationale: str
    color_palette: List[str] = []
    decor_concepts: List[str] = []
    invitation_wording: str = ""
    menu_suggestions: List[str] = []
    activities_and_games: List[str] = []
    music_entertainment: List[str] = []
    eco_friendly_tips: List[str] = []


class PlanRescueRequest(BaseModel):
    """User request describing an unexpected disruption to an existing event."""
    event_id: str
    disruption_type: str
    disruption_details: str
    new_budget: Optional[float] = None
    additional_guests: Optional[int] = None
    new_venue_type: Optional[str] = None


class PlanRescueAlternative(BaseModel):
    """A strategic option proposed by AI for recovering from disruption."""
    title: str
    description: str
    advantages: List[str]
    disadvantages: List[str]
    trade_offs: str
    estimated_cost_delta: float = 0.0


class PlanRescueRecommendation(BaseModel):
    """Structured AI recovery plan that will be programmatically validated."""
    disruption_summary: str
    quantitative_impact: Dict[str, Any] = {}
    affected_tasks: List[str] = []
    affected_vendors: List[str] = []
    recommended_alternatives: List[PlanRescueAlternative] = []
    contingency_steps: List[str] = []
    rebalancing_strategy: str = ""
    proposed_budget_allocations: Dict[str, float] = {}  # Category -> New planned amount
    proposed_schedule_changes: List[Dict[str, str]] = []


class FullEventPlan(BaseModel):
    """Complete aggregated model representing an entire celebration plan."""
    id: str
    input_details: EventInput
    overview: str
    creative: CreativeConcepts
    budget_allocations: List[BudgetAllocation]
    expenses: List[ExpenseItem] = []
    tasks: List[TaskItem] = []
    day_schedule: List[EventScheduleItem] = []
    vendor_guidance: List[VendorCategoryGuidance] = []
    vendors: List[VendorItem] = []
    guests: List[GuestItem] = []
    risks_and_contingencies: List[str] = []
    assumptions: List[str] = []
    rescue_history: List[Dict[str, Any]] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
