# FestiWise AI — Hack2Skill Challenge 5 Submission Document

**Hack2Skill PromptWars | Challenge 5: Celebration & Event Planner**  
**Project Name:** FestiWise AI  
**Tagline:** *Every celebration, perfectly planned.*  
**Signature Feature:** Plan Rescue Mode  

---

## 1. Submission Metadata & Links

- **Application Name:** FestiWise AI
- **Repository URL:** `[INSERT GITHUB REPOSITORY LINK HERE e.g. https://github.com/your-username/festiwise-ai]`
- **Live Deployed Application URL:** `[INSERT STREAMLIT COMMUNITY CLOUD LINK HERE e.g. https://festiwise-ai.streamlit.app]`
- **Demonstration Video Link:** `[INSERT YOUTUBE OR DRIVE VIDEO LINK HERE]`
- **Technology Stack:** Python 3.13, Streamlit, Google GenAI SDK (`google-genai`), Pydantic v2, SQLite 3, Plotly Express, Pytest
- **Cloud Credits Requirement:** **Zero** (100% Free-tier compatible; requires no GCP billing or credits)

---

## 2. Executive Summary & Core Value Proposition

FestiWise AI is a complete, production-ready, Generative AI-powered celebration and event planning web application. Designed for weddings, milestone birthdays, college festivals, community gatherings, and corporate celebrations, it transforms high-level event concepts into an executable master blueprint. 

Unlike conventional chatbots that hallucinate financial arithmetic, FestiWise AI enforces a strict **Financial Calculation Rule**: all budgets, category percentages, variances, and cost-per-guest calculations are computed deterministically in Python code. 

When real-world disruptions strike (such as sudden venue cancellations, bad weather, budget cuts, or guest surges), FestiWise AI activates its signature differentiator: **Plan Rescue Mode**. The engine assesses the impact against the user's saved event, calculates the exact mathematical deficit, queries Gemini for strategic recovery alternatives with pros, cons, and trade-offs, and lets the organizer review an interactive before-and-after diff before updating the saved plan.

---

## 3. Mandatory Challenge Form Answers

### Answer 1 — Project Overview (For Challenge Submission Form)
> **Problem:**  
> Planning celebrations (weddings, birthdays, college fests, community events) is fragmented, stressful, and error-prone. Organizers juggle chaotic spreadsheets, vendor calls, and unformatted notes. Generic chatbots fail because they hallucinate arithmetic and generate static, generic advice that shatters the moment an inevitable crisis occurs.
> 
> **Solution & Target Users:**  
> FestiWise AI is an intelligent full-stack celebration planner designed for students, families, community coordinators, and event organizers. It combines Google Gemini’s creative intelligence with a deterministic financial arithmetic engine and local SQLite persistence.
> 
> **Core Capabilities:**  
> 1. **AI Event Blueprint Creator:** Generates personalized themes, cultural rationales, day-of itineraries, and risk assessments.  
> 2. **Deterministic Smart Budget Engine:** Python code (zero LLM math) computes allocations, tracks verified vs. estimated expenses, detects overspending, and rebalances budgets.  
> 3. **Dynamic Timeline & Tasks:** Date-scaled milestone checklists with interactive completion tracking and day-of schedules.  
> 4. **Vendor Organizer & AI Guidance:** Evaluation checklists, key questions to ask, and caution red flags before paying deposits.  
> 5. **Creative Studio & Guest Management:** Original invitation wording, palette swatches, menu pairings, and RSVP capacity trackers.  
> 6. **Plan Rescue Mode (Signature Feature):** Intelligently mitigates real-world disruptions (venue price hikes, bad weather, guest surges) by calculating the mathematical impact, presenting strategic alternatives with trade-offs, and applying an approved diff to the active plan.

---

### Answer 2 — GenAI Implementation and Innovation (For Challenge Submission Form)
> **How Generative AI is Integrated Beyond a Basic Chatbot:**  
> Rather than a freeform conversational prompt box, FestiWise AI integrates the official **Google GenAI SDK (`google-genai`)** using structured Pydantic schemas (`response_mime_type="application/json"`). The model output is strictly validated into strongly typed objects for themes, invitation copy, category questions, and risk matrices. If credentials are unset or quota is exhausted, the application gracefully activates an intelligent demonstration engine without crashing.
> 
> **Separation of LLM Intelligence vs. Programmatic Arithmetic:**  
> Generative AI is used exclusively for what it does best: creative ideation, cultural context adaptation, strategic trade-off analysis, and risk synthesis. All financial calculations—totals, category ratios, expense commitments, budget variances, per-guest averages, and disruption deficits—are calculated deterministically in Python (`budget_service.py`).
> 
> **Plan Rescue Mode Innovation:**  
> Plan Rescue Mode operates directly on the user’s existing saved relational event state (loaded from SQLite). When a crisis is reported (e.g., venue cost spikes by ₹15,000 and 20 unexpected guests RSVP), the system:
> 1. Computes the direct category delta and guest-variable catering cost in code.
> 2. Queries Gemini with the exact quantitative delta to formulate strategic recovery alternatives, their pros, cons, and practical compromises.
> 3. Displays an interactive **Plan Diff** table contrasting current vs. proposed values.
> 4. Upon user approval, programmatically patches the saved event budget, adjusts allocations, and injects high-priority contingency tasks into the timeline.

---

## 4. Verification & Testing Summary

- **Automated Test Results:** **20 passed in 8.12 seconds** via `pytest -v tests`
- **Coverage Areas:**
  - `test_schemas.py`: Valid and invalid input validations, Pydantic type constraints.
  - `test_budget.py`: Initial allocation sums, expense commitment logic, overflow detection, proportional rebalancing.
  - `test_timeline.py`: Date-scaled milestone ordering, completion percentages, schedule validation.
  - `test_db.py`: SQLite roundtrips, foreign key cascades, task updates, expense CRUD.
  - `test_rescue.py`: Financial impact formulas, guest surge math, diff generation, revision persistence.
  - `test_gemini.py`: Credential missing checks, graceful demo mode, API 429/malformed error fallback.
- **Application Startup Verification:** Streamlit v1.66.1 initializes cleanly, renders the custom SaaS celebratory theme, loads the pre-seeded wedding demonstration event, and handles full interactive navigation across all 10 modules.

---

## 5. Deployment Instructions for Free Tier

1. Fork or push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect the repository, set main file to `app.py`.
4. In **Advanced Settings -> Secrets**, provide:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   GEMINI_MODEL = "gemini-3.8-flash"
   DEFAULT_CURRENCY = "INR"
   ```
5. Deploy without requiring any credit card or Google Cloud billing prerequisites.
