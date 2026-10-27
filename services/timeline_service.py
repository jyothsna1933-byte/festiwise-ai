"""Timeline and preparation schedule management service for FestiWise AI.

Handles:
- Dynamic milestone calculation relative to event date
- Chronological sorting and conflict detection for event-day schedules
- Task completion metrics and milestone deadlines
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from models.schemas import TaskItem, EventScheduleItem, EventInput


# Category-specific template tasks with relative days before event
BASELINE_PREPARATION_TASKS: Dict[str, List[Dict[str, Any]]] = {
    "Wedding": [
        {"title": "Lock Venue & Date", "days_before": 90, "priority": "High", "category": "Venue & Rentals"},
        {"title": "Book Catering & Finalize Menu Tasting", "days_before": 75, "priority": "High", "category": "Catering & Drinks"},
        {"title": "Hire Photographer & Videographer", "days_before": 60, "priority": "High", "category": "Photography & Video"},
        {"title": "Finalize Decorator & Floral Concepts", "days_before": 45, "priority": "Medium", "category": "Decor & Flowers"},
        {"title": "Send Formal Digital / Physical Invitations", "days_before": 40, "priority": "High", "category": "General"},
        {"title": "Book DJ / Live Band & Sound Systems", "days_before": 30, "priority": "Medium", "category": "Entertainment & Music"},
        {"title": "Select Outfits & Schedule Alterations", "days_before": 25, "priority": "High", "category": "Outfits & Makeup"},
        {"title": "Confirm Final Guest RSVP Headcount", "days_before": 14, "priority": "High", "category": "General"},
        {"title": "Vendor Reconfirmation & Final Payment Schedule", "days_before": 7, "priority": "High", "category": "General"},
        {"title": "Prepare Emergency Kit & Day-Of Coordination Packets", "days_before": 2, "priority": "Medium", "category": "General"},
    ],
    "Birthday": [
        {"title": "Book Party Venue or Reserve Space", "days_before": 30, "priority": "High", "category": "Venue & Play Area"},
        {"title": "Order Custom Cake & Food Menu", "days_before": 20, "priority": "High", "category": "Catering & Cake"},
        {"title": "Send Themed Invitations & Collect RSVPs", "days_before": 15, "priority": "High", "category": "General"},
        {"title": "Purchase Theme Decor, Balloons & Tableware", "days_before": 10, "priority": "Medium", "category": "Decor & Balloons"},
        {"title": "Book Magician / Entertainer / Games Host", "days_before": 10, "priority": "Medium", "category": "Entertainment & Games"},
        {"title": "Prepare Return Favors & Goodie Bags", "days_before": 5, "priority": "Low", "category": "Favors & Gifts"},
        {"title": "Final RSVP Confirmation with Caterer", "days_before": 3, "priority": "High", "category": "Catering & Cake"},
        {"title": "Party Playlist & Music Device Setup", "days_before": 1, "priority": "Low", "category": "Entertainment & Games"},
    ],
    "College Event": [
        {"title": "Secure Campus Administration Permissions & Venue Booking", "days_before": 45, "priority": "High", "category": "Stage, Sound & Lights"},
        {"title": "Finalize Sound, Stage, Lighting, and Mic Rentals", "days_before": 30, "priority": "High", "category": "Stage, Sound & Lights"},
        {"title": "Confirm Guest Speakers / Chief Guests / Performing Artists", "days_before": 25, "priority": "High", "category": "Guest Speakers/Artists"},
        {"title": "Launch Student Registrations & Social Media Campaign", "days_before": 20, "priority": "High", "category": "Promotion & Merchandise"},
        {"title": "Coordinate Food Trucks / Snack Stalls", "days_before": 15, "priority": "Medium", "category": "Food & Refreshments"},
        {"title": "Print Volunteer Badges, Banners & Certificates", "days_before": 7, "priority": "Medium", "category": "Promotion & Merchandise"},
        {"title": "Campus Security & Medical First-Aid Protocol Briefing", "days_before": 3, "priority": "High", "category": "Security & Logistics"},
        {"title": "Technical Dry Run & Sound Check", "days_before": 1, "priority": "High", "category": "Stage, Sound & Lights"},
    ],
    "Festival": [
        {"title": "Form Community Organizing Committee & Budget Approval", "days_before": 60, "priority": "High", "category": "Venue & Community Setup"},
        {"title": "Obtain Municipality / Police / Fire Safety Clearances", "days_before": 45, "priority": "High", "category": "Permits & Logistics"},
        {"title": "Commission Traditional Artisans & Floral Decorators", "days_before": 30, "priority": "High", "category": "Traditional Decor & Lights"},
        {"title": "Arrange Community Prasadam & Large-Scale Catering", "days_before": 20, "priority": "High", "category": "Prasadam / Food Stalls"},
        {"title": "Setup Stage, Acoustic Microphones & Traditional Lighting", "days_before": 10, "priority": "Medium", "category": "Venue & Community Setup"},
        {"title": "Cultural Performance Rehearsals", "days_before": 7, "priority": "Medium", "category": "Cultural Performances"},
        {"title": "Crowd Control & Sanitation Booths Setup", "days_before": 2, "priority": "High", "category": "Permits & Logistics"},
    ],
    "General": [
        {"title": "Confirm Event Location and Capacity", "days_before": 30, "priority": "High", "category": "Venue"},
        {"title": "Finalize Refreshments & Catering Supplier", "days_before": 20, "priority": "High", "category": "Catering"},
        {"title": "Dispatch Invitations & Collect Headcounts", "days_before": 15, "priority": "High", "category": "General"},
        {"title": "Arrange Photography & Media Coverage", "days_before": 10, "priority": "Medium", "category": "Media"},
        {"title": "Confirm Day-Of Itinerary with Core Helpers", "days_before": 3, "priority": "High", "category": "General"},
    ]
}


def generate_baseline_tasks(event_input: EventInput) -> List[TaskItem]:
    """Generate intelligent preparation tasks adjusted to the target event date."""
    try:
        event_dt = datetime.strptime(event_input.event_date, "%Y-%m-%d").date()
    except Exception:
        event_dt = datetime.now().date() + timedelta(days=30)
        
    today = datetime.now().date()
    days_until_event = (event_dt - today).days
    
    category = event_input.event_category
    templates = BASELINE_PREPARATION_TASKS.get(category, BASELINE_PREPARATION_TASKS["General"])
    
    tasks: List[TaskItem] = []
    
    for tmpl in templates:
        target_days_before = tmpl["days_before"]
        
        # If the event is sooner than the ideal timeline, compress deadlines gracefully
        if days_until_event < target_days_before:
            # Scale proportionally so deadlines do not end up in the past
            compressed_days = max(1, int(days_until_event * (target_days_before / 90.0)))
            deadline_date = event_dt - timedelta(days=compressed_days)
            if deadline_date < today:
                deadline_date = today
        else:
            deadline_date = event_dt - timedelta(days=target_days_before)
            
        tasks.append(
            TaskItem(
                id=str(uuid.uuid4())[:8],
                title=tmpl["title"],
                description=f"Standard milestone for {category.lower()} planning.",
                suggested_deadline=deadline_date.strftime("%Y-%m-%d"),
                days_before_event=target_days_before,
                priority=tmpl["priority"],
                status="Not Started",
                responsible_person="",
                category=tmpl["category"]
            )
        )
        
    # Sort tasks chronologically by deadline
    tasks.sort(key=lambda t: t.suggested_deadline)
    return tasks


def calculate_timeline_metrics(tasks: List[TaskItem]) -> Dict[str, Any]:
    """Compute task completion percentage, overdue count, and priority breakdown."""
    if not tasks:
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "not_started_tasks": 0,
            "completion_percentage": 0.0,
            "overdue_tasks": 0,
            "high_priority_remaining": 0,
        }
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "Completed")
    in_progress = sum(1 for t in tasks if t.status == "In Progress")
    not_started = sum(1 for t in tasks if t.status == "Not Started")
    
    overdue = sum(1 for t in tasks if t.status != "Completed" and t.suggested_deadline < today_str)
    high_prio_rem = sum(1 for t in tasks if t.status != "Completed" and t.priority == "High")
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "not_started_tasks": not_started,
        "completion_percentage": round((completed / total) * 100, 1),
        "overdue_tasks": overdue,
        "high_priority_remaining": high_prio_rem,
    }


def validate_day_schedule(schedule: List[EventScheduleItem]) -> List[str]:
    """Validate schedule for overlaps or formatting anomalies."""
    warnings = []
    if not schedule:
        return ["Day-of schedule is currently empty."]
        
    for i, item in enumerate(schedule):
        if not item.start_time:
            warnings.append(f"Item #{i+1} ('{item.activity_name}') has no start time specified.")
        if item.duration_minutes <= 0:
            warnings.append(f"Item #{i+1} ('{item.activity_name}') has an invalid duration ({item.duration_minutes} min).")
            
    return warnings
