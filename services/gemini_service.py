"""Google Gemini Generative AI service for FestiWise AI.

Uses the official google-genai SDK (v1.0+) with structured JSON outputs.
Never exposes keys. Gracefully falls back to rich built-in demo data
when credentials are unset or quota is exhausted.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple, List

from config import get_gemini_api_key, DEFAULT_GEMINI_MODEL
from models.schemas import (
    EventInput,
    CreativeConcepts,
    VendorCategoryGuidance,
    EventScheduleItem,
    PlanRescueRequest,
    PlanRescueRecommendation,
    PlanRescueAlternative
)

logger = logging.getLogger(__name__)


def _clean_json_text(text: str) -> Dict[str, Any]:
    """Clean and parse JSON from model response text, stripping markdown blocks if present."""
    if not text:
        raise ValueError("Empty response text from model.")
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


def is_gemini_available() -> Tuple[bool, str]:
    """Check whether Gemini SDK is installed and an API key is present."""
    key = get_gemini_api_key()
    if not key:
        return False, "GEMINI_API_KEY is not configured in environment or Streamlit secrets."
    try:
        from google import genai
        return True, "Gemini API client ready."
    except ImportError:
        return False, "google-genai package is not installed."


def get_gemini_client():
    """Create and return configured genai.Client instance."""
    key = get_gemini_api_key()
    if not key:
        raise ValueError("Missing Gemini API Key.")
    from google import genai
    return genai.Client(api_key=key)


def generate_ai_event_blueprint(
    event_input: EventInput,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """Generate structured event blueprint using Gemini or high-fidelity demo fallback.
    
    Returns a dictionary containing:
    - overview: str
    - creative: CreativeConcepts
    - day_schedule: List[EventScheduleItem]
    - vendor_guidance: List[VendorCategoryGuidance]
    - risks_and_contingencies: List[str]
    - assumptions: List[str]
    - used_live_ai: bool
    - model_used: str
    """
    model = model_name or DEFAULT_GEMINI_MODEL
    key_available, reason = is_gemini_available()
    
    if key_available:
        try:
            client = get_gemini_client()
            from google.genai import types

            prompt = f"""
            You are FestiWise AI, an expert event planner. Create a personalized, comprehensive, culturally aware event blueprint.
            
            EVENT SPECIFICATIONS:
            - Name: {event_input.event_name}
            - Category: {event_input.event_category}
            - Date: {event_input.event_date}
            - Location: {event_input.city_location} ({event_input.venue_type} venue)
            - Guest Count: {event_input.guest_count}
            - Budget: {event_input.currency} {event_input.total_budget:,.2f}
            - Theme Preference: {event_input.preferred_theme or 'Best suited to event'}
            - Food Preference: {event_input.food_preference}
            - Crucial Requirements: {event_input.special_requirements or 'None'}
            - Additional Notes: {event_input.additional_notes or 'None'}

            Output MUST be valid JSON adhering strictly to this JSON schema:
            {{
              "overview": "Detailed 2-3 paragraph personalized executive summary",
              "creative": {{
                "recommended_theme": "Evocative theme name",
                "theme_rationale": "Why this theme works for this specific guest count, location, and budget",
                "color_palette": ["Color 1", "Color 2", "Color 3", "Color 4"],
                "decor_concepts": ["Specific decor concept 1", "Concept 2", "Concept 3"],
                "invitation_wording": "Original, warm, celebratory invitation text with placeholders [Host], [Date], [Venue]",
                "menu_suggestions": ["Appetizer idea", "Main course highlight", "Signature beverage", "Dessert option"],
                "activities_and_games": ["Activity 1 tailored to audience", "Activity 2"],
                "music_entertainment": ["Style / Playlist concept 1", "Entertainment idea 2"],
                "eco_friendly_tips": ["Sustainable idea 1", "Low-waste tip 2"]
              }},
              "day_schedule": [
                {{"start_time": "10:00 AM", "activity_name": "Activity name", "duration_minutes": 60, "notes": "Context notes"}}
              ],
              "vendor_guidance": [
                {{
                  "category": "Catering",
                  "key_questions": ["Question 1", "Question 2"],
                  "evaluation_checklist": ["Checklist item 1", "Checklist item 2"],
                  "caution_red_flags": ["Red flag warning 1"]
                }}
              ],
              "risks_and_contingencies": ["Risk 1 & realistic backup plan", "Risk 2 & backup plan"],
              "assumptions": ["Assumption 1 regarding venue logistics or timing", "Assumption 2"]
            }}
            """

            candidate_models = [model]
            if model != "gemini-3.5-flash-lite":
                candidate_models.append("gemini-3.5-flash-lite")

            for attempt_model in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=attempt_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.6,
                        )
                    )

                    if response and response.text:
                        data = _clean_json_text(response.text)
                        return {
                            "overview": data.get("overview", "Personalized event plan created by FestiWise AI."),
                            "creative": CreativeConcepts(**data["creative"]),
                            "day_schedule": [EventScheduleItem(**s) for s in data.get("day_schedule", [])],
                            "vendor_guidance": [VendorCategoryGuidance(**g) for g in data.get("vendor_guidance", [])],
                            "risks_and_contingencies": data.get("risks_and_contingencies", []),
                            "assumptions": data.get("assumptions", []),
                            "used_live_ai": True,
                            "model_used": attempt_model,
                        }
                except Exception as model_err:
                    logger.warning(f"Live Gemini API call failed on {attempt_model}: {model_err}. Trying fallback.")
        except Exception as e:
            logger.warning(f"Live Gemini setup failed: {e}. Falling back to demo generator.")

    # Graceful demo fallback generator
    return _generate_demo_event_blueprint(event_input)


def _generate_demo_event_blueprint(event_input: EventInput) -> Dict[str, Any]:
    """Generate high-quality, category-tailored blueprint when API credentials are absent."""
    cat = event_input.event_category
    city = event_input.city_location
    name = event_input.event_name
    guests = event_input.guest_count
    curr = event_input.currency
    budget = event_input.total_budget

    if cat == "Wedding":
        overview = (
            f"A magnificent, deeply memorable wedding celebration for {name} in {city}. "
            f"Designed for {guests} esteemed guests with an optimized budget allocation of {curr} {budget:,.2f}. "
            f"The celebration harmonizes timeless ceremonial grace with contemporary guest hospitality."
        )
        creative = CreativeConcepts(
            recommended_theme=event_input.preferred_theme or "Timeless Royal Elegance & Marigold Hues",
            theme_rationale=f"Accentuates the cultural beauty of {city} with rich festive textures, ambient candlelight, and warm floral marigold accents.",
            color_palette=["Royal Maroon", "Warm Gold", "Marigold Amber", "Ivory Silk"],
            decor_concepts=[
                "Grand floral mandap / stage backdrop with fairy light draping",
                "Traditional brass urns (urulis) with floating rose petals and diya accents at guest entry",
                "Personalized guest welcome lounge with artisanal brass lantern pathways"
            ],
            invitation_wording=(
                f"Together with their families, you are cordially invited to celebrate the joyful union of {name}. "
                f"Join us for an auspicious day of love, music, and feast on {event_input.event_date} at [Venue], {city}. "
                f"Your presence and blessings will make our special day complete."
            ),
            menu_suggestions=[
                f"Artisanal welcome coolers (Kokum Spritzer & Spiced Mango Panna)",
                f"Interactive live chaat counter & steamed dim-sum stations",
                f"Grand buffet dinner featuring signature regional specialties ({event_input.food_preference})",
                f"Warm Gulab Jamun with saffron rabri and artisanal kulfi station"
            ],
            activities_and_games=[
                "Live acoustic Shehnai & Sitar welcoming segment",
                "Choreographed family Sangeet dance performances",
                "Interactive photo-booth with vintage polaroids and guest wishes book"
            ],
            music_entertainment=[
                "Sufi-Bollywood fusion live ensemble during dinner",
                "DJ set featuring high-energy celebratory folk and dance tracks"
            ],
            eco_friendly_tips=[
                "Plantable seed paper RSVP cards and zero single-use plastics",
                "Surplus food tie-up with local verified food rescue NGOs in " + city,
                "Repurposing daytime floral decor for evening dining tables"
            ]
        )
        day_schedule = [
            EventScheduleItem(start_time="03:00 PM", activity_name="Vendor Setup & Sound Check", duration_minutes=90, notes="Verify sound, mandap flowers, and cooling"),
            EventScheduleItem(start_time="05:00 PM", activity_name="Baraat / Guest Arrival & Refreshments", duration_minutes=60, notes="Live dhol and welcome coolers"),
            EventScheduleItem(start_time="06:15 PM", activity_name="Main Ceremony & Vows Exchange", duration_minutes=75, notes="Photographer front angles"),
            EventScheduleItem(start_time="07:30 PM", activity_name="Stage Photos & Family Congratulatory Meet", duration_minutes=60, notes="Water bottles for stage hosts"),
            EventScheduleItem(start_time="08:30 PM", activity_name="Gourmet Dinner Feast", duration_minutes=90, notes="Buffet open, acoustic lounge music"),
            EventScheduleItem(start_time="10:00 PM", activity_name="Celebration Dance & Send-Off", duration_minutes=60, notes="DJ finale & parting gift distribution")
        ]
        vendor_guidance = [
            VendorCategoryGuidance(
                category="Catering & Drinks",
                key_questions=[
                    "What is your live staff-to-guest ratio for " + str(guests) + " guests?",
                    "Do you provide real-time food temperature replenishment chafing dishes?",
                    "What are your contractual policies for unexpected guests or late arrivals?",
                    "Can you provide ingredient certificates for dietary requirements?"
                ],
                evaluation_checklist=[
                    "Schedule mandatory in-person food tasting session",
                    "Verify hygiene license and kitchen safety certifications",
                    "Confirm exact water dispenser and waste disposal protocol"
                ],
                caution_red_flags=["Refusal of food tasting", "Hidden delivery and plate breakage surcharge clauses"]
            ),
            VendorCategoryGuidance(
                category="Photography & Video",
                key_questions=[
                    "Will the principal photographer shoot in person or assign junior associates?",
                    "What is the turnaround time for the teaser reel and full edited album?",
                    "How many candid vs traditional photographers are included?"
                ],
                evaluation_checklist=[
                    "Review full past wedding album gallery, not just Instagram highlights",
                    "Ensure backup camera bodies and dual SD-card slot equipment are specified in contract"
                ],
                caution_red_flags=["Vague delivery timelines without penalty clauses", "No contract or written invoice"]
            )
        ]
    elif cat == "Birthday":
        overview = (
            f"An exhilarating, joyful birthday celebration for {name} in {city}. "
            f"Tailored for {guests} guests with a budget of {curr} {budget:,.2f}. "
            f"Prioritizes vibrant entertainment, unforgettable photo moments, and engaging games."
        )
        creative = CreativeConcepts(
            recommended_theme=event_input.preferred_theme or "Neon Carnival & Starlight Glow",
            theme_rationale=f"Dynamic and festive atmosphere designed for high engagement among {guests} guests in an {event_input.venue_type.lower()} setting.",
            color_palette=["Electric Blue", "Neon Coral", "Bright Sunshine", "Midnight Violet"],
            decor_concepts=[
                "Organic balloon arch with personalized LED neon name sign",
                "Illuminated starlight photo backdrop with instant photo station",
                "Themed table centerpieces with customized favor boxes"
            ],
            invitation_wording=(
                f"Get ready to celebrate! Join us as we celebrate {name}'s unforgettable birthday party! "
                f"Date: {event_input.event_date} | Time: [Time] | Venue: [Venue], {city}. "
                f"Come for the laughter, stay for the games and cake!"
            ),
            menu_suggestions=[
                "Mini sliders & crispy finger-food platters",
                "Custom artisan multi-tier birthday cake",
                "Mocktail slush bar with fruit popping boba",
                "Warm churros / brownie sundaes"
            ],
            activities_and_games=[
                "Custom birthday trivia challenge with spot prizes",
                "Interactive musical games and freeze dance",
                "DIY craft or cookie decoration counter"
            ],
            music_entertainment=["Upbeat pop and trending celebration soundtrack"],
            eco_friendly_tips=[
                "Biodegradable latex balloons and paper confetti",
                "Reusable wooden cutlery and bamboo fiber plates"
            ]
        )
        day_schedule = [
            EventScheduleItem(start_time="04:30 PM", activity_name="Decor & Music Setup Complete", duration_minutes=30, notes="Cake placed in cold storage"),
            EventScheduleItem(start_time="05:00 PM", activity_name="Guest Arrival & Welcome Slushies", duration_minutes=30, notes="Collect birthday cards and coats"),
            EventScheduleItem(start_time="05:30 PM", activity_name="Interactive Games & Activities", duration_minutes=60, notes="Host leads group games"),
            EventScheduleItem(start_time="06:30 PM", activity_name="Cake Cutting Ceremony & Photos", duration_minutes=30, notes="Cue birthday track and candles"),
            EventScheduleItem(start_time="07:00 PM", activity_name="Dinner Feast & Snacks Buffet", duration_minutes=60, notes="Serve hot food"),
            EventScheduleItem(start_time="08:00 PM", activity_name="Dance Session & Return Favors", duration_minutes=45, notes="Distribute party favor bags")
        ]
        vendor_guidance = [
            VendorCategoryGuidance(
                category="Catering & Cake",
                key_questions=[
                    "Does cake price include temperature-controlled delivery to venue?",
                    "Can you cater to nut-free or dietary restrictions safely?"
                ],
                evaluation_checklist=["Verify cake delivery box insulation", "Confirm exact serving size breakdown"],
                caution_red_flags=["No refrigeration capability during transit"]
            )
        ]
    else:
        # College / Festival / Community / Custom
        overview = (
            f"A vibrant {cat.lower()} celebration titled '{name}' in {city}. "
            f"Curated for {guests} participants with a structured budget of {curr} {budget:,.2f}. "
            f"Engineered for crowd safety, maximum participation, and high festive spirit."
        )
        creative = CreativeConcepts(
            recommended_theme=event_input.preferred_theme or f"Unity & Celebration Festival",
            theme_rationale=f"Optimized for high-footfall community camaraderie and memorable shared experiences.",
            color_palette=["Festive Saffron", "Peacock Teal", "Goldenrod", "Crisp White"],
            decor_concepts=[
                "Central commemorative gateway arch with event banner",
                "Community art installation and message wall",
                "Festive hanging fairy canopy across gathering zone"
            ],
            invitation_wording=(
                f"We are thrilled to welcome you to '{name}'! "
                f"Mark your calendar for {event_input.event_date} at [Venue], {city}. "
                f"Join our community celebration featuring performances, delicious food, and fun activities."
            ),
            menu_suggestions=[
                "Community refreshment counter with hot chai and coolers",
                "Local street food stalls / catered buffet meal",
                "Assorted festive sweets and seasonal fruit cups"
            ],
            activities_and_games=[
                "Opening cultural performance and welcoming address",
                "Community open mic / talent showcase",
                "Raffle draw / recognition ceremony"
            ],
            music_entertainment=["Live sound reinforcement with festive folk / instrumental tracks"],
            eco_friendly_tips=[
                "Segregated recycling bins clearly marked for organic and dry waste",
                "Digital programs via QR code to avoid paper wastage"
            ]
        )
        day_schedule = [
            EventScheduleItem(start_time="09:00 AM", activity_name="Volunteer & Committee Briefing", duration_minutes=45, notes="Assign zones and safety lanyards"),
            EventScheduleItem(start_time="10:00 AM", activity_name="Gates Open & Welcome Refreshments", duration_minutes=45, notes="Audio announcements"),
            EventScheduleItem(start_time="11:00 AM", activity_name="Inaugural Ceremony & Speeches", duration_minutes=60, notes="Stage mic ready"),
            EventScheduleItem(start_time="12:30 PM", activity_name="Community Lunch Feast", duration_minutes=90, notes="Monitor queue flow"),
            EventScheduleItem(start_time="02:30 PM", activity_name="Cultural Competitions & Activities", duration_minutes=120, notes="Judges scoring sheets"),
            EventScheduleItem(start_time="05:00 PM", activity_name="Awards & Closing Ceremony", duration_minutes=60, notes="Trophy and certificates")
        ]
        vendor_guidance = [
            VendorCategoryGuidance(
                category="Stage, Sound & Lights",
                key_questions=[
                    "Do you supply backup generator (silent DG set) in case of grid power cuts?",
                    "Are wireless microphones and technician standby included throughout the event?"
                ],
                evaluation_checklist=["Verify audio cables taped down for trip hazard prevention", "Confirm decibel level compliance"],
                caution_red_flags=["No on-site technician during performance hours"]
            )
        ]

    risks = [
        "Unforeseen weather change affecting outdoor area: Contingency canopy or immediate shift to indoor covered hall.",
        "Guest count exceeding projection by 10-15%: 10% food buffer clause with caterer pre-arranged.",
        "Audio / microphone technical glitch: Dedicated secondary wired microphone and sound technician on standby."
    ]
    assumptions = [
        f"Venue in {city} permits music within local municipality noise deadline regulations.",
        "Basic electrical connections and primary restroom facilities are provided by venue management.",
        "Invitations dispatched at least 3 weeks prior to ensure RSVP accuracy."
    ]

    return {
        "overview": overview,
        "creative": creative,
        "day_schedule": day_schedule,
        "vendor_guidance": vendor_guidance,
        "risks_and_contingencies": risks,
        "assumptions": assumptions,
        "used_live_ai": False,
        "model_used": "Demonstration Engine (Built-in)",
    }


def generate_plan_rescue_advice(
    request: PlanRescueRequest,
    event_data: Dict[str, Any],
    budget_impact: Dict[str, Any],
    model_name: Optional[str] = None
) -> Tuple[PlanRescueRecommendation, bool, str]:
    """Generate strategic, context-aware recovery solutions using Gemini or demo engine.
    
    Returns:
    - PlanRescueRecommendation
    - used_live_ai (bool)
    - model_used (str)
    """
    model = model_name or DEFAULT_GEMINI_MODEL
    key_available, _ = is_gemini_available()
    
    if key_available:
        try:
            client = get_gemini_client()
            from google.genai import types

            prompt = f"""
            You are FestiWise AI Plan Rescue Mode, an elite crisis mitigation planner.
            An unexpected disruption has occurred to an existing event. Provide practical, strategic recovery alternatives.

            CURRENT SAVED EVENT:
            - Event Name: {event_data.get('name')}
            - Category: {event_data.get('category')}
            - Date: {event_data.get('event_date')}
            - Location: {event_data.get('city')} ({event_data.get('venue_type')})
            - Current Guest Count: {event_data.get('guest_count')}
            - Current Total Budget: {event_data.get('currency')} {event_data.get('total_budget')}

            DISRUPTION REPORTED:
            - Disruption Type: {request.disruption_type}
            - Details: {request.disruption_details}
            - Requested Additional Guests: {request.additional_guests or 0}
            - Requested Budget Cap: {request.new_budget or 'Unchanged'}

            PROGRAMMATIC FINANCIAL IMPACT (CALCULATED BY PYTHON CODE):
            - Direct category cost increase: {budget_impact.get('total_direct_delta', 0)}
            - Additional guest variable cost: {budget_impact.get('guest_variable_delta', 0)}
            - Total projected cost increase: {budget_impact.get('total_cost_increase', 0)}
            - Rebalancing deficit needed to cut: {budget_impact.get('cut_amount_needed', 0)}

            Provide a comprehensive, empathetic, actionable recovery plan.
            Output MUST be valid JSON adhering strictly to this schema:
            {{
              "disruption_summary": "Concise summary of the situation and immediate risks",
              "affected_tasks": ["Task that must be paused/rescheduled 1", "Task 2"],
              "affected_vendors": ["Vendor category directly affected 1", "Category 2"],
              "recommended_alternatives": [
                {{
                  "title": "Alternative Option 1 (e.g., Rebalance & Repurpose)",
                  "description": "Clear step-by-step recovery strategy",
                  "advantages": ["Advantage 1", "Advantage 2"],
                  "disadvantages": ["Drawback 1", "Drawback 2"],
                  "trade_offs": "What is compromised or substituted",
                  "estimated_cost_delta": 0.0
                }},
                {{
                  "title": "Alternative Option 2 (e.g., Hybrid Pivot)",
                  "description": "Secondary strategic path",
                  "advantages": ["Advantage 1"],
                  "disadvantages": ["Drawback 1"],
                  "trade_offs": "Trade-off details",
                  "estimated_cost_delta": 0.0
                }}
              ],
              "contingency_steps": [
                "Immediate step 1 (Next 2 hours)",
                "Action step 2 (Next 24 hours)",
                "Action step 3 (Day before event)"
              ],
              "rebalancing_strategy": "Concrete recommendations on where to trim expenses without ruining guest satisfaction."
            }}
            """

            candidate_models = [model]
            if model != "gemini-3.5-flash-lite":
                candidate_models.append("gemini-3.5-flash-lite")

            for attempt_model in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=attempt_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.5,
                        )
                    )

                    if response and response.text:
                        data = _clean_json_text(response.text)
                        alternatives = [
                            PlanRescueAlternative(**alt) for alt in data.get("recommended_alternatives", [])
                        ]
                        rec = PlanRescueRecommendation(
                            disruption_summary=data.get("disruption_summary", "Disruption analysis complete."),
                            quantitative_impact=budget_impact,
                            affected_tasks=data.get("affected_tasks", []),
                            affected_vendors=data.get("affected_vendors", []),
                            recommended_alternatives=alternatives,
                            contingency_steps=data.get("contingency_steps", []),
                            rebalancing_strategy=data.get("rebalancing_strategy", ""),
                        )
                        return rec, True, attempt_model
                except Exception as model_err:
                    logger.warning(f"Plan rescue live API call failed on {attempt_model}: {model_err}. Trying fallback.")
        except Exception as e:
            logger.warning(f"Plan rescue live API setup failed: {e}. Falling back to demo rescue engine.")

    # High quality demo rescue fallback
    return _generate_demo_rescue_advice(request, event_data, budget_impact)


def _generate_demo_rescue_advice(
    request: PlanRescueRequest,
    event_data: Dict[str, Any],
    budget_impact: Dict[str, Any]
) -> Tuple[PlanRescueRecommendation, bool, str]:
    """Generate high-quality recovery recommendation when API key is not present."""
    dtype = request.disruption_type
    curr = event_data.get("currency", "INR")
    cut_needed = budget_impact.get("cut_amount_needed", 0.0)
    extra_guests = request.additional_guests or 0

    if "weather" in dtype.lower():
        summary = (
            f"Adverse weather threat detected for outdoor venue in {event_data.get('city')}. "
            "High risk of rain, waterlogging, or wind damage to outdoor staging, electricals, and food counters."
        )
        affected_tasks = ["Setup outdoor lighting & lawn decor", "Arrange lawn guest seating", "Outdoor sound check"]
        affected_vendors = ["Venue & Infrastructure", "Decor & Flowers", "Sound & Production"]
        alternatives = [
            PlanRescueAlternative(
                title="Immediate Indoor Banquet Hall Pivot",
                description="Coordinate with venue administration to shift setup into the adjacent covered banquet hall or covered portico.",
                advantages=["100% dry and climate controlled", "Zero audio equipment damage risk", "Guest comfort secured"],
                disadvantages=["Slightly tighter floor layout than open lawn"],
                trade_offs="Sacrifices open-sky lawn ambiance in exchange for guaranteed rain protection and zero delays.",
                estimated_cost_delta=0.0
            ),
            PlanRescueAlternative(
                title="Rapid Waterproof German Hanger / Canopy Tent Rental",
                description="Install industrial waterproof marquee canopy over key dining and stage areas on the lawn.",
                advantages=["Preserves outdoor garden aesthetic", "Shelters buffet and stage"],
                disadvantages=["Additional tent rental fee", "Requires 4-6 hours setup window"],
                trade_offs="Increases infrastructure cost but allows outdoor event continuation.",
                estimated_cost_delta=cut_needed if cut_needed > 0 else 5000.0
            )
        ]
        contingency_steps = [
            "Contact venue manager immediately to reserve backup indoor banquet hall hall key.",
            "Instruct sound vendor to bag all amplifiers and elevate extension cords off grass.",
            "Send broadcast message to core team and guests confirming covered venue pavilion."
        ]
        rebalance = (
            "If canopy tent rental incurs extra cost, absorb from the Emergency Reserve "
            "and trim discretionary paper favors and extra floral photo-booths."
        )
    elif "venue" in dtype.lower():
        summary = (
            f"Venue disruption/cancellation reported for {event_data.get('name')}. "
            "Primary location is compromised and requires immediate relocation or renegotiation."
        )
        affected_tasks = ["Lock Venue & Date", "Stage and decor delivery", "Caterer kitchen access"]
        affected_vendors = ["Venue & Rentals", "Decor & Staging", "Catering"]
        alternatives = [
            PlanRescueAlternative(
                title="Partner Venue Rebooking via Verified Local Network",
                description="Activate alternative certified banquet spaces or community centers within a 5km radius.",
                advantages=["Keeps original date and schedule intact", "Minimal guest transit confusion"],
                disadvantages=["Requires re-measuring floor plan for decor fit"],
                trade_offs="Room dimensions may differ; stage backdrop must be resized.",
                estimated_cost_delta=0.0
            ),
            PlanRescueAlternative(
                title="Boutique Hotel Rooftop / Open Lawn Switch",
                description="Relocate to a boutique property with bundled dining packages.",
                advantages=["High quality hospitality and existing infrastructure"],
                disadvantages=["May require adjusting outside catering rules"],
                trade_offs="May need to adopt in-house kitchen menu.",
                estimated_cost_delta=cut_needed
            )
        ]
        contingency_steps = [
            "Request immediate written cancellation and deposit refund from original venue.",
            "Inspect shortlist of 2 immediate available substitute venues today.",
            "Update vendors with new delivery gate address once locked."
        ]
        rebalance = f"Reallocate up to {curr} {cut_needed:,.2f} from lower-priority decor accents to cover any venue deposit differential."
    elif extra_guests > 0 or "guest" in dtype.lower():
        summary = (
            f"Unexpected guest surge: +{extra_guests} additional attendees requested (Total now: {budget_impact.get('new_guest_count')}). "
            f"Projected additional expenditure: {curr} {budget_impact.get('total_cost_increase', 0):,.2f}."
        )
        affected_tasks = ["Confirm Final Guest RSVP Headcount", "Caterer final food quantity order", "Table & chair count"]
        affected_vendors = ["Catering & Drinks", "Venue Seating & Rentals"]
        alternatives = [
            PlanRescueAlternative(
                title="Buffer Expansion with Menu Rebalancing",
                description="Increase caterer headcount while replacing expensive individual plate items with crowd-pleasing live buffet stations.",
                advantages=["Every guest gets ample delicious food", "No guest feels under-accommodated"],
                disadvantages=["Buffet lines may require 1 additional serving counter"],
                trade_offs="Swaps 2 premium appetizers for high-volume crowd favorites to protect total budget.",
                estimated_cost_delta=0.0
            ),
            PlanRescueAlternative(
                title="Tiered Seating & Standing Cocktail Tables",
                description="Introduce 6 high-top cocktail tables alongside seated family round tables to comfortably absorb extra footfall.",
                advantages=["Prevents overcrowded feeling", "Encourages lively guest mingling"],
                disadvantages=["Fewer reserved seats per guest"],
                trade_offs="More dynamic standing space rather than 100% formal table seating.",
                estimated_cost_delta=0.0
            )
        ]
        contingency_steps = [
            f"Notify catering supervisor to scale food portions by +{extra_guests} units immediately.",
            "Order 2 additional dining tables and 15 extra chairs from rental supplier.",
            "Update name tags and welcoming desk register."
        ]
        rebalance = (
            f"To absorb the projected {curr} {cut_needed:,.2f} difference, reduce entertainment DJ lighting truss "
            f"and trim non-essential printed physical signage."
        )
    else:
        # Budget increase or generic emergency
        summary = (
            f"Budget / emergency disruption: {request.disruption_details}. "
            f"Financial deficit of {curr} {cut_needed:,.2f} identified."
        )
        affected_tasks = ["Vendor payment schedule", "Budget allocation review"]
        affected_vendors = ["Discretionary decor", "Media production"]
        alternatives = [
            PlanRescueAlternative(
                title="Strategic Rebalancing & Trimming",
                description="Rebalance flexible category allocations programmatically to absorb the cost shock.",
                advantages=["Keeps event on original budget cap", "No debt or overspending"],
                disadvantages=["Minor aesthetic concessions"],
                trade_offs="Prioritizes food and guest comfort over excessive decor elements.",
                estimated_cost_delta=0.0
            )
        ]
        contingency_steps = [
            "Review verified expenses vs estimated quotes to locate immediate savings.",
            "Negotiate 10% courtesy discount with core vendors in exchange for prompt settlement.",
            "Lock the updated revised budget allocations."
        ]
        rebalance = f"Apply programmatic rebalancing to trim flexible categories by {curr} {cut_needed:,.2f}."

    rec = PlanRescueRecommendation(
        disruption_summary=summary,
        quantitative_impact=budget_impact,
        affected_tasks=affected_tasks,
        affected_vendors=affected_vendors,
        recommended_alternatives=alternatives,
        contingency_steps=contingency_steps,
        rebalancing_strategy=rebalance
    )
    return rec, False, "Demonstration Crisis Engine (Built-in)"
