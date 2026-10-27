"""FestiWise AI - Every celebration, perfectly planned.

Main Streamlit Application Entrypoint.
Hack2Skill PromptWars | Challenge 5: Celebration & Event Planner
"""

import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
from database.db import init_db, list_events, save_full_event
from ui.styles import apply_custom_styles
from ui.page_dashboard import render_dashboard
from ui.page_create_event import render_create_event
from ui.page_my_events import render_my_events
from ui.page_budget import render_budget_planner
from ui.page_timeline import render_timeline
from ui.page_vendors import render_vendors
from ui.page_rescue import render_plan_rescue
from ui.page_creative import render_creative_studio
from ui.page_guests import render_guest_management
from ui.page_settings import render_settings
from services.gemini_service import _generate_demo_event_blueprint
from services.budget_service import generate_initial_allocations
from services.timeline_service import generate_baseline_tasks
from models.schemas import EventInput, FullEventPlan, ExpenseItem, VendorItem, GuestItem


# Set Streamlit Page Configuration
st.set_page_config(
    page_title="FestiWise AI — Every celebration, perfectly planned",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom SaaS Design System CSS
apply_custom_styles()

# Ensure Database is Initialized
init_db()


def seed_initial_demo_event_if_empty():
    """Seed a realistic, rich celebration plan on first launch so the user/judge

    can immediately interact with the Budget Planner, Timeline, and Plan Rescue Mode.
    """
    events = list_events()
    if not events:
        sample_input = EventInput(
            event_name="Rohan & Maya's Grand Wedding & Sangeet",
            event_category="Wedding",
            event_date="2026-11-20",
            city_location="Bangalore",
            venue_type="Hybrid (Indoor + Lawn)",
            guest_count=150,
            total_budget=500000.0,
            currency="INR",
            preferred_theme="Regal Heritage & Marigold Glow",
            food_preference="Mixed (Vegetarian & Non-Vegetarian)",
            special_requirements="Wheelchair accessible mandap pathway, elderly quiet lounge",
            additional_notes="Live Punjabi Dhol for entry, strict 10 PM sound curfew"
        )
        blueprint = _generate_demo_event_blueprint(sample_input)
        allocations = generate_initial_allocations(500000.0, "Wedding")
        tasks = generate_baseline_tasks(sample_input)

        # Seed sample verified expenses
        sample_expenses = [
            ExpenseItem(
                id="exp-01",
                category="Venue & Rentals",
                item_name="Grand Heritage Palace Lawn & Banquet Deposit",
                estimated_cost=140000.0,
                actual_cost=140000.0,
                vendor_name="Palace Banquet & Lawns",
                payment_status="Paid",
                is_verified=True,
                notes="Advance payment completed via bank transfer"
            ),
            ExpenseItem(
                id="exp-02",
                category="Catering & Drinks",
                item_name="Live Chaat Counter & Gourmet Dinner Buffet Advance",
                estimated_cost=160000.0,
                actual_cost=155000.0,
                vendor_name="Spice Art Culinary Caterers",
                payment_status="Partially Paid",
                is_verified=True,
                notes="Tasting approved, 50% paid"
            ),
            ExpenseItem(
                id="exp-03",
                category="Photography & Video",
                item_name="Cinematic Wedding Teaser & Candid Album Package",
                estimated_cost=50000.0,
                actual_cost=48000.0,
                vendor_name="Studio Lumina Weddings",
                payment_status="Partially Paid",
                is_verified=True,
                notes="2 candid + 1 traditional photographer"
            ),
            ExpenseItem(
                id="exp-04",
                category="Decor & Flowers",
                item_name="Marigold Mandap & Fairy Light Canopy",
                estimated_cost=70000.0,
                actual_cost=None,
                vendor_name="Blossom Decorators",
                payment_status="Pending",
                is_verified=False,
                notes="Quotation under negotiation"
            )
        ]

        sample_vendors = [
            VendorItem(
                id="ven-01",
                category="Venue & Rentals",
                name="Palace Banquet & Lawns",
                contact_info="+91 98450 11223 / events@palace.com",
                quoted_price=140000.0,
                booking_status="Booked",
                follow_up_date="2026-11-10",
                notes="Contract signed, generator backup included"
            ),
            VendorItem(
                id="ven-02",
                category="Catering & Drinks",
                name="Spice Art Culinary Caterers",
                contact_info="+91 97410 44556 / info@spiceart.in",
                quoted_price=155000.0,
                booking_status="Booked",
                follow_up_date="2026-11-15",
                notes="Dietary tags confirmed for Jain food"
            ),
            VendorItem(
                id="ven-03",
                category="Decor & Flowers",
                name="Blossom Decorators",
                contact_info="+91 99000 88776",
                quoted_price=70000.0,
                booking_status="Quoted",
                follow_up_date="2026-10-30",
                notes="Waiting on sample mock setup photos"
            )
        ]

        sample_guests = [
            GuestItem(id="gst-01", name="Rohan (Groom)", contact="+91 99999 11111", rsvp_status="Attending", plus_ones=0, table_group="VIP Stage"),
            GuestItem(id="gst-02", name="Maya (Bride)", contact="+91 99999 22222", rsvp_status="Attending", plus_ones=0, table_group="VIP Stage"),
            GuestItem(id="gst-03", name="Uncle Vikram & Family", contact="+91 98888 33333", rsvp_status="Attending", plus_ones=3, table_group="Family Row A", dietary_notes="Pure Vegetarian"),
            GuestItem(id="gst-04", name="Sunita Aunty", contact="+91 97777 44444", rsvp_status="Attending", plus_ones=1, table_group="Family Row A", dietary_notes="Jain Food"),
            GuestItem(id="gst-05", name="Kunal Verma", contact="kunal@verma.com", rsvp_status="Pending", plus_ones=1, table_group="College Friends"),
        ]

        demo_plan = FullEventPlan(
            id="demo-wedding-01",
            input_details=sample_input,
            overview=blueprint["overview"],
            creative=blueprint["creative"],
            budget_allocations=allocations,
            expenses=sample_expenses,
            tasks=tasks,
            day_schedule=blueprint["day_schedule"],
            vendor_guidance=blueprint["vendor_guidance"],
            vendors=sample_vendors,
            guests=sample_guests,
            risks_and_contingencies=blueprint["risks_and_contingencies"],
            assumptions=blueprint["assumptions"],
            rescue_history=[]
        )
        save_full_event(demo_plan)
        st.session_state["active_event_id"] = "demo-wedding-01"


# Run initial seed if database is clean
seed_initial_demo_event_if_empty()


# ----------------------------------------------------
# Sidebar Navigation
# ----------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
        <span style="font-size: 2rem;">🎉</span>
        <div>
            <div style="font-size: 1.3rem; font-weight: 800; font-family: 'Outfit', sans-serif; color: #0F172A; line-height: 1.1;">FestiWise AI</div>
            <div style="font-size: 0.72rem; color: #FF5A5F; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Celebration Planner</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "Dashboard",
        "Create Event",
        "My Events",
        "Budget Planner",
        "Timeline & Tasks",
        "Vendors",
        "Plan Rescue",
        "Creative Studio",
        "Guest Management",
        "Settings"
    ]

    current_selection = st.session_state.get("nav_selection", "Dashboard")
    if current_selection not in nav_options:
        current_selection = "Dashboard"

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(current_selection),
        format_func=lambda x: f"🚨 {x} (Signature)" if x == "Plan Rescue" else (
            "📊 " + x if x == "Dashboard" else (
            "➕ " + x if x == "Create Event" else (
            "📁 " + x if x == "My Events" else (
            "💰 " + x if x == "Budget Planner" else (
            "⏱️ " + x if x == "Timeline & Tasks" else (
            "🤝 " + x if x == "Vendors" else (
            "🎨 " + x if x == "Creative Studio" else (
            "👥 " + x if x == "Guest Management" else "⚙️ " + x
        )))))))),
        label_visibility="collapsed"
    )

    if selected_nav != current_selection:
        st.session_state["nav_selection"] = selected_nav
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.78rem; color: #64748B; line-height: 1.5;">
        <strong>Hack2Skill PromptWars</strong><br>
        Challenge 5: Celebration Planner<br>
        <em>"Every celebration, perfectly planned."</em>
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------
# Main Content Router
# ----------------------------------------------------
if selected_nav == "Dashboard":
    render_dashboard()
elif selected_nav == "Create Event":
    render_create_event()
elif selected_nav == "My Events":
    render_my_events()
elif selected_nav == "Budget Planner":
    render_budget_planner()
elif selected_nav == "Timeline & Tasks":
    render_timeline()
elif selected_nav == "Vendors":
    render_vendors()
elif selected_nav == "Plan Rescue":
    render_plan_rescue()
elif selected_nav == "Creative Studio":
    render_creative_studio()
elif selected_nav == "Guest Management":
    render_guest_management()
elif selected_nav == "Settings":
    render_settings()


# App Footer
st.markdown("""
<div class="app-footer">
    <strong>FestiWise AI</strong> • Hack2Skill PromptWars Challenge 5 Submission • Built with Google GenAI SDK, Streamlit, and SQLite.<br>
    Zero Google Cloud Credits prerequisite. Free-tier compatible.
</div>
""", unsafe_allow_html=True)
