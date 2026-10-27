"""Event Creation and AI Blueprint Generation page for FestiWise AI."""

import uuid
from datetime import datetime, date, timedelta
import streamlit as st

from config import EVENT_CATEGORIES, CURRENCY_SYMBOLS, DEFAULT_CURRENCY
from models.schemas import EventInput, FullEventPlan, GuestItem
from services.gemini_service import generate_ai_event_blueprint, is_gemini_available
from services.budget_service import generate_initial_allocations
from services.timeline_service import generate_baseline_tasks
from database.db import save_full_event


def render_create_event():
    """Render comprehensive multi-attribute event creation workflow."""
    st.markdown("### ➕ Plan a New Celebration")
    st.markdown("Provide your celebration parameters. FestiWise AI will generate a personalized blueprint, deterministic budget, and milestone timeline.")

    is_ai_live, ai_status_msg = is_gemini_available()
    if is_ai_live:
        st.success(f"🤖 GenAI Status: Connected to Google Gemini API ({st.session_state.get('configured_model', 'gemini-3.8-flash')})")
    else:
        st.info(f"ℹ️ GenAI Status: {ai_status_msg} (Operating in High-Fidelity Demonstration Mode)")

    with st.form("event_creation_form"):
        st.markdown("#### 1. Core Event Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Celebration Name *", placeholder="e.g. Ananya & Rohit's Sangeet & Wedding")
            category = st.selectbox("Event Category *", options=EVENT_CATEGORIES)
            event_date = st.date_input("Event Date *", min_value=date.today(), value=date.today() + timedelta(days=60))
        with col2:
            city = st.text_input("City / Locality *", placeholder="e.g. Bangalore, South India")
            venue_type = st.selectbox("Venue Preference", options=["Indoor", "Outdoor", "Hybrid (Indoor + Lawn)"])
            guest_count = st.number_input("Estimated Guests *", min_value=5, max_value=25000, value=100, step=10)

        st.markdown("#### 2. Financial & Thematic Scope")
        col3, col4 = st.columns(2)
        with col3:
            currency = st.selectbox("Currency", options=list(CURRENCY_SYMBOLS.keys()), index=list(CURRENCY_SYMBOLS.keys()).index(DEFAULT_CURRENCY))
            default_budget = 350000.0 if currency == "INR" else 5000.0
            total_budget = st.number_input(f"Total Budget ({currency}) *", min_value=500.0, max_value=100000000.0, value=default_budget, step=5000.0)
        with col4:
            preferred_theme = st.text_input("Desired Theme / Vibe", placeholder="e.g. Regal Heritage, Sunset Boho, Cyberpunk Neon")
            food_preference = st.selectbox("Food Preference", options=[
                "Mixed (Vegetarian & Non-Vegetarian)",
                "Pure Vegetarian",
                "Jain Vegetarian (No Onion/Garlic)",
                "Vegan & Plant-Based",
                "Continental & Finger Foods",
                "Traditional Regional Cuisine"
            ])

        st.markdown("#### 3. Special Requirements & Context")
        special_reqs = st.text_area("Important Requirements", placeholder="e.g., Wheelchair accessibility, elderly resting lounge, live acoustic audio restrictions, zero-waste focus")
        additional_notes = st.text_input("Additional Notes", placeholder="e.g., Groom's family loves Punjabi Dhol; strict 10 PM sound curfew")

        submit_btn = st.form_submit_button("🚀 Generate FestiWise Blueprint", type="primary", use_container_width=True)

    if submit_btn:
        # Validate inputs
        if not name or len(name.strip()) < 2:
            st.error("Please enter a valid Celebration Name (at least 2 characters).")
            return
        if not city or len(city.strip()) < 2:
            st.error("Please enter a valid City or locality.")
            return
        if total_budget <= 0:
            st.error("Total budget must be strictly greater than 0.")
            return

        with st.spinner("✨ FestiWise AI is generating your personalized blueprint, calculating budget allocations, and structuring your timeline..."):
            try:
                # 1. Construct EventInput model
                event_inp = EventInput(
                    event_name=name.strip(),
                    event_category=category,
                    event_date=event_date.strftime("%Y-%m-%d"),
                    city_location=city.strip(),
                    venue_type=venue_type,
                    guest_count=int(guest_count),
                    total_budget=float(total_budget),
                    currency=currency,
                    preferred_theme=preferred_theme.strip() if preferred_theme else "",
                    food_preference=food_preference,
                    special_requirements=special_reqs.strip() if special_reqs else "",
                    additional_notes=additional_notes.strip() if additional_notes else ""
                )

                # 2. Call Gemini service (or fallback demo)
                model_to_use = st.session_state.get("configured_model", None)
                blueprint = generate_ai_event_blueprint(event_inp, model_name=model_to_use)

                # 3. Deterministically compute budget allocations (NEVER LLM FOR MATH)
                allocations = generate_initial_allocations(event_inp.total_budget, event_inp.event_category)

                # 4. Generate preparation timeline based on event date
                tasks = generate_baseline_tasks(event_inp)

                # 5. Assemble FullEventPlan
                event_id = str(uuid.uuid4())[:8]
                full_plan = FullEventPlan(
                    id=event_id,
                    input_details=event_inp,
                    overview=blueprint["overview"],
                    creative=blueprint["creative"],
                    budget_allocations=allocations,
                    expenses=[],
                    tasks=tasks,
                    day_schedule=blueprint["day_schedule"],
                    vendor_guidance=blueprint["vendor_guidance"],
                    vendors=[],
                    guests=[GuestItem(id=str(uuid.uuid4())[:8], name="Primary Host (You)", rsvp_status="Attending", plus_ones=1)],
                    risks_and_contingencies=blueprint["risks_and_contingencies"],
                    assumptions=blueprint["assumptions"],
                    rescue_history=[]
                )

                # 6. Save to database
                save_full_event(full_plan)
                st.session_state["active_event_id"] = event_id

                ai_flag = "Live Google Gemini AI" if blueprint["used_live_ai"] else "Demonstration Planning Engine"
                st.success(f"🎉 Success! '{name}' created using {ai_flag}. Redirecting to Dashboard...")
                st.session_state["nav_selection"] = "Dashboard"
                st.rerun()

            except Exception as e:
                st.error(f"Failed to create event: {str(e)}")
