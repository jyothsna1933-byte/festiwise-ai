# FestiWise AI

> **Every celebration, perfectly planned.**

*Hack2Skill PromptWars | Challenge 5: Celebration & Event Planner*

---
## 🚀 Live Demo

- **Live Application:** https://festiwise-ai-jyothsna.streamlit.app
- **Source Code:** https://github.com/jyothsna1933-byte/festiwise-ai
- **Demo Video:** https://youtu.be/yPTgFBGboo0
Explore the event dashboard, budget planner, timeline and tasks, Creative Studio, guest management, and Plan Rescue Mode.

*Note: The deployed application uses Streamlit Community Cloud. Data persistence and AI availability may be affected by the hosting environment and API availability.*

## 1. Problem Statement

Planning celebrations—weddings, milestone birthdays, college cultural fests, religious festivals, and community gatherings—is notoriously chaotic, stressful, and fragmented. Organizers juggle disconnected spreadsheets, vendor phone calls, unformatted notes, and fluctuating guest headcounts. 

Existing solutions fail in two major ways:
1. **Generic AI Chatbots:** Produce generic walls of text, hallucinate arithmetic calculations, and cannot adapt when circumstances change.
2. **Static Event Software:** Require manual entry of hundreds of items and immediately break when an inevitable crisis hits (e.g., vendor cancellations, torrential rain at an outdoor venue, sudden budget cuts, or guest surges).

---

## 2. Proposed Solution: FestiWise AI

**FestiWise AI** is an intelligent, full-stack celebration planning assistant that unites **Google Gemini Generative AI** with a **deterministic programmatic calculation engine** and local **relational persistence (SQLite)**. 

Instead of treating event planning as static forms or disconnected chats, FestiWise AI generates a living, cohesive blueprint with:
- **Personalized Event Blueprint:** Culturally attuned themes, rationales, day-of chronological schedules, and risk assessments.
- **Deterministic Smart Budget Planner:** Real financial calculation engine where **Python code** (never the LLM) computes totals, category shares, committed spends, variances, and per-guest costs.
- **Dynamic Milestone Timeline & Tasks:** Date-aware preparation milestones with interactive checkboxes and day-of minute-by-minute itinerary.
- **Vendor Organizer & AI Interrogation Checklists:** Category checklists and red flags to protect organizers before transferring deposits.
- **Creative Studio:** Original invitation copy, harmonious color palettes, decor concepts, menu pairings, and sustainable low-waste alternatives.
- **Guest & RSVP Management:** Headcount capacity tracking, dietary requirement summaries, and plus-one registers.
- **Signature Differentiator — Plan Rescue Mode:** An interactive crisis-recovery engine that accepts real-world disruptions (venue price shocks, guest surges, bad weather, vendor drops), programmatically calculates the financial and logisitical impacts on the active plan, queries Gemini for strategic alternatives and trade-offs, and lets users inspect an interactive before/after diff before applying changes.

---

## 3. Target Users

- **Families & Couples:** Planning weddings, anniversaries, baby showers, and milestone birthdays.
- **College Student Committees:** Organizing annual cultural festivals, tech hackathons, and fresher welcome parties.
- **Community & Religious Coordinators:** Managing neighborhood festivals, sports days, and public feasts.
- **Freelance Event Planners:** Rapidly prototyping client blueprints and running crisis mitigation.

---

## 4. Key Differentiators: What Makes FestiWise AI Different

| Feature | Standard Event Apps / Chatbots | FestiWise AI |
| :--- | :--- | :--- |
| **Budget Calculations** | Hallucinated LLM math or manual excel tables | **Strict Financial Calculation Rule:** Deterministic Python engine computes all totals, percentages, burn rates, and variances. |
| **Unexpected Disruptions** | System breaks; user must start over from scratch | **Plan Rescue Mode:** Operates directly on the saved event state, computes financial deltas, generates trade-offs, and presents a reviewable diff. |
| **Vendor Support** | Fake sponsored listings or unverified directories | **AI Interrogation Checklists:** Tactical contract questions and red flags to protect organizers before paying deposits. |
| **Resilience & Fallback** | Hard crash if API key is missing or quota runs out | **Dual-Engine Architecture:** Seamless live Gemini integration with high-fidelity built-in fallback mode. |
| **Cloud Prerequisites** | Requires paid Google Cloud credits or billing setups | **Zero Credit Prerequisite:** 100% free-tier compatible with local SQLite persistence and free Gemini API Studio tier. |

---

## 5. Technology Stack

- **Programming Language:** Python 3.13 / 3.11+
- **Web Application Framework:** [Streamlit](https://streamlit.io/) (v1.39+)
- **Generative AI SDK:** [Google GenAI SDK (`google-genai`)](https://github.com/googleapis/python-genai) (v1.0+)
- **Primary AI Models:** `gemini-3.6-flash` (Recommended), `gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-2.5-flash`
- **Data Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/)
- **Data Persistence:** SQLite 3 with foreign key cascading and JSON serialization
- **Visual Analytics:** [Plotly Express & Graph Objects](https://plotly.com/python/)
- **Testing Suite:** [pytest](https://docs.pytest.org/) (26 automated unit & integration tests)
- **Deployment Platform:** Streamlit Community Cloud (Free-tier, zero GCP credit requirement)

---

## 6. Architecture Overview

```
                           +---------------------------+
                           |  Streamlit Multi-Page UI  |
                           |   (Custom SaaS Theme CSS) |
                           +-------------+-------------+
                                         |
     +-----------------+-----------------+-----------------+-----------------+
     |                 |                 |                 |                 |
+----+----+      +-----+-----+     +-----+-----+     +-----+-----+     +-----+-----+
| Dashboard |    | Event Plan|     |   Budget   |     | Timeline &|     |   Plan    |
| & Events  |    |  Creator  |     |   Engine   |     |   Tasks   |     |  Rescue   |
+----+----+      +-----+-----+     +-----+-----+     +-----+-----+     +-----+-----+
     |                 |                 |                 |                 |
     +-----------------+-----------------+-----------------+-----------------+
                                         |
                       +-----------------+-----------------+
                       |                                   |
              +--------+--------+                 +--------+--------+
              |   Gemini Service|                 |  SQLite Storage |
              |  (google-genai) |                 |  & Schema Engine|
              |  Structured JSON|                 |  (festiwise.db) |
              +-----------------+                 +-----------------+
```

### Module Responsibilities:
- `app.py`: Application entrypoint, session manager, seed database loader, and sidebar router.
- `config.py`: Environment loader (`.env`), supported Gemini models, currency definitions, and category baseline budget ratios.
- `database/db.py`: Relational persistence for events, allocations, expenses, tasks, day schedules, vendors, guidance, and guests.
- `models/schemas.py`: Pydantic validation schemas enforcing strict types and constraints.
- `services/budget_service.py`: Deterministic financial arithmetic engine (never delegates math to LLMs).
- `services/timeline_service.py`: Chronological preparation milestone generator and schedule conflict validator.
- `services/gemini_service.py`: Official Google GenAI SDK integration with structured outputs and high-fidelity fallback generator.
- `services/rescue_service.py`: Plan Rescue crisis engine computing programmatic deltas, strategic recovery options, and diff patching.
- `ui/`: Modular page renderers with celebratory design palette and reusable components.

---

## 7. Installation & Setup Instructions

### Prerequisites
- Python 3.11, 3.12, or 3.13 installed.
- Git installed.
- (Optional but recommended) A free Gemini API key from [Google AI Studio](https://aistudio.google.com/).

### Step 1: Clone or Open Workspace
```powershell
git clone https://github.com/jyothsna1933-byte/festiwise-ai.git
cd festiwise-ai
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Edit `.env` and add your Gemini API key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
DEFAULT_CURRENCY=INR
```
*(Note: If no API key is provided, the application runs seamlessly in High-Fidelity Demonstration Mode without crashing).*

---

## 8. How to Run Locally

Launch the Streamlit web application:
```powershell
streamlit run app.py
```
Or run directly via Python module:
```powershell
python -m streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 9. How to Run the Automated Test Suite

FestiWise AI includes 25 comprehensive unit and integration tests covering data validation, programmatic budget arithmetic, database persistence, Plan Rescue calculations, full user lifecycle workflows, and GenAI error recovery / model fallback:

```powershell
pytest -v tests
```

Expected output:
```
tests/test_budget.py::test_initial_allocations_sum_to_total PASSED
tests/test_budget.py::test_calculate_budget_summary_normal PASSED
tests/test_budget.py::test_budget_overflow_detection PASSED
tests/test_budget.py::test_rebalance_allocations_to_target PASSED
tests/test_db.py::test_save_and_retrieve_event PASSED
tests/test_db.py::test_task_status_quick_update PASSED
tests/test_db.py::test_delete_event_cascade PASSED
tests/test_gemini.py::test_missing_credentials_graceful_status PASSED
tests/test_gemini.py::test_missing_credentials_fallback_blueprint PASSED
tests/test_gemini.py::test_api_failure_and_malformed_json_fallback PASSED
tests/test_gemini.py::test_plan_rescue_fallback_when_credentials_absent PASSED
tests/test_integration_workflow.py::test_full_user_lifecycle_workflow PASSED
tests/test_rescue.py::test_compute_rescue_budget_delta_direct_and_guests PASSED
tests/test_rescue.py::test_evaluate_and_apply_plan_rescue PASSED
tests/test_schemas.py::test_valid_event_input PASSED
tests/test_schemas.py::test_invalid_event_date_format PASSED
tests/test_schemas.py::test_zero_or_negative_budget PASSED
tests/test_schemas.py::test_zero_guest_count PASSED
tests/test_timeline.py::test_generate_baseline_tasks_ordering PASSED
tests/test_timeline.py::test_calculate_timeline_metrics PASSED
tests/test_timeline.py::test_validate_day_schedule PASSED

============================= 26 passed in 4.55s ==============================
```

---

## 10. Free-Tier Deployment Instructions (Streamlit Community Cloud)

FestiWise AI requires **zero paid cloud credits** and is specifically engineered to deploy for free on **Streamlit Community Cloud**:

1. Push your repository to GitHub (ensure `.env` and `*.db` remain in `.gitignore`).
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **New app** and select your repository, branch (`main` or `master`), and main file path (`app.py`).
4. Click **Advanced settings...**:
   - In the **Secrets** text box, securely enter your Gemini API key:
     ```toml
     GEMINI_API_KEY = "your_actual_gemini_api_key_here"
     GEMINI_MODEL = "gemini-3.8-flash"
     DEFAULT_CURRENCY = "INR"
     ```
5. Click **Deploy!** Your application will be live at `https://<your-subdomain>.streamlit.app`.

---

## 11. Implemented Features Checklist

- [x] **Full-Stack SaaS Interface:** Custom celebratory styling, metric cards, navigation router.
- [x] **Pre-Seeded Demo Event:** Immediate exploration on first launch with rich wedding plan.
- [x] **Event Blueprint Creator:** Multi-step validated form with personalized GenAI output.
- [x] **Deterministic Budget Engine:** Strict financial calculation rule; zero LLM arithmetic hallucinations.
- [x] **Expense Register & Tracking:** Tracks actual invoices vs AI estimates with verification badges.
- [x] **Interactive Preparation Timeline:** Date-relative milestones with checkbox toggling and status updates.
- [x] **Day-Of Chronological Itinerary:** Minute-by-minute schedule with input validation.
- [x] **Vendor Organizer & AI Interrogation Guidance:** Key questions to ask and warning red flags.
- [x] **Plan Rescue Mode (Signature Feature):** Disruption analysis, programmatic cost impact, strategic alternatives with pros/cons/trade-offs, before/after diff review, and revision application.
- [x] **Creative Studio:** Themes, color palettes, original invitation copy, menu suggestions, and low-waste tips.
- [x] **Guest & RSVP Management:** Attendee capacity tracker, dietary requirements, and group seating.
- [x] **Settings & Diagnostics:** Live Gemini API test tool, model switcher, currency preferences.
- [x] **Data Persistence:** Local SQLite database with full CRUD and cascade delete.
- [x] **Automated Test Suite:** 25 passing unit & integration tests.

---

## 12. Known Limitations & Future Enhancements

### Known Limitations
- **Local SQLite Persistence on Ephemeral Containers:** When hosted on free-tier platforms like Streamlit Community Cloud, SQLite database state persists during active sessions but may reset when the container enters deep sleep. An export/import JSON feature is provided to save backups.
- **Vendor Directory:** FestiWise AI functions as an organizer and question advisor. It does not provide live external marketplace booking transactions or live vendor API scrapes without licensed credentials.
- **Live Weather Integration:** FestiWise AI does not query paid meteorological APIs without user-configured weather keys; it provides conditional indoor contingency plans instead.

### Future Enhancements
- **Multi-User Collaboration:** Role-based access control (Bride/Groom, Event Committee members) with Cloud Firestore / Supabase integration.
- **WhatsApp / SMS RSVP Bot:** Automated RSVP collection via Twilio or WhatsApp Business API.
- **QR Code Check-In Desk:** Day-of guest registration and table allocation scanner.

---

## 13. Hackathon Pitch & Summary

> *"Most event planning software treats weddings and celebrations as static spreadsheets that shatter the moment the first vendor cancels or rain clouds appear. FestiWise AI changes that. By combining Google Gemini's creative intelligence with strict programmatic financial calculations and our signature Plan Rescue Mode, FestiWise AI doesn't just help you plan your celebration—it stays by your side when plans change, calculating trade-offs and rescuing your dream event in seconds."*
