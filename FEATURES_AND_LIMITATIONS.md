# FestiWise AI — Features, Verification Status & Limitations Matrix

**Hack2Skill PromptWars | Challenge 5: Celebration & Event Planner**

---

## 1. Feature Implementation & Verification Status

| Feature / Capability | Implementation Details | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| **Full-Stack SaaS Interface** | Streamlit multi-page app with custom celebratory CSS, metric tiles, responsive layout, and sidebar navigation | **VERIFIED** | Tested with custom styling, glass cards, and status tags. |
| **Event Blueprint Creator** | Collects category, date, city, venue type, guest count, budget, currency, theme, diet, and requirements | **VERIFIED** | Form inputs strictly validated via Pydantic (`EventInput`). Tested with valid and invalid inputs. |
| **GenAI Blueprint Generation** | Google GenAI SDK (`google-genai` v1.0+) calling `gemini-3.8-flash` with structured JSON schema | **VERIFIED** | Tested live and with comprehensive unit tests for graceful fallback when credentials are absent or quota exhausted. |
| **Deterministic Smart Budget Engine** | Python code calculates totals, category percentages, variances, committed expenses, and per-guest costs | **VERIFIED** | 100% test coverage in `tests/test_budget.py`. Zero LLM math. |
| **Budget Overflow & Variance Detection** | Identifies when expenses or allocations exceed budget cap and offers one-click proportional rebalancing | **VERIFIED** | Tested with deliberate overspending scenarios in unit tests. |
| **Expense Tracking Register** | Records actual vs. estimated expenses, payment status, vendor names, and verification flags | **VERIFIED** | Tested with SQLite persistence, add/delete operations. |
| **Milestone Timeline Checklist** | Generates preparation tasks scaled to the event date; interactive completion toggles | **VERIFIED** | Tested status updates, chronological sorting, and progress bar recalculation. |
| **Day-Of Chronological Itinerary** | Minute-by-minute schedule with duration and notes; schedule contradiction warnings | **VERIFIED** | Tested schedule validation in `tests/test_timeline.py`. |
| **Vendor Organizer & AI Guidance** | Contact tracker, quotation manager, AI questions checklist, and caution red flags | **VERIFIED** | Tested guidance generation and vendor CRUD operations. |
| **Plan Rescue Mode (Signature Feature)** | Disruption evaluation (venue drops, weather threats, guest surges, budget shocks), programmatic delta calculation, Gemini strategic options with trade-offs, interactive before/after diff review, and revision application | **VERIFIED** | 100% test coverage in `tests/test_rescue.py`. Evaluates real state deltas and patches saved event. |
| **Creative Studio** | Personalized themes, rationale, color palette cards, original invitation wording copywriter, menu ideas, games, and eco-friendly tips | **VERIFIED** | Fully rendered across categories with copy-to-clipboard code blocks. |
| **Guest & RSVP Management** | Attendee headcount capacity vs. confirmed attendees, plus-ones, dietary tags, table groups | **VERIFIED** | Tested capacity surge alerts and guest status updates. |
| **Database Persistence** | SQLite 3 relational schema with foreign key cascading and JSON serialization | **VERIFIED** | Full CRUD verified in `tests/test_db.py` on temporary database. |
| **Settings & Diagnostics** | In-app API key verification tool, model selector, currency selector, and system info | **VERIFIED** | Tested API verification flow and session preference persistence. |
| **Automated Testing Suite** | 20 automated unit & integration tests covering budget, schemas, timeline, SQLite, rescue, and Gemini | **VERIFIED** | 20 passed out of 20 tests in 8.12 seconds via pytest. |

---

## 2. Known Limitations & Technical Constraints

1. **Ephemeral Local Storage on Free-Tier Hosting:**
   - When deployed on platforms such as Streamlit Community Cloud without persistent volume attachments, the SQLite database (`festiwise.db`) persists across user reloads within an active container session, but may be reset if the container is recycled or put to sleep after inactivity.
   - **Mitigation:** FestiWise AI includes an **Export JSON** feature on the *My Celebrations* page so users can back up their entire celebration blueprint locally.

2. **No Paid Live Vendor Scraping:**
   - FestiWise AI intentionally does not scrape unverified live marketplace directories or fabricate fake vendor contact numbers or quotes. It functions as a structured **Vendor Organizer and AI Question Advisor** to empower users during vendor negotiations.

3. **Live Weather API Integration:**
   - FestiWise AI does not claim to check live satellite weather feeds unless a weather API key is explicitly configured. Instead, in outdoor weather emergencies, it offers conditional, actionable indoor hall pivots and marquee canopy rental contingencies.

4. **Single-Tenant Demonstration Scope:**
   - As built for Challenge 5, authentication is session-based and designed for individual organizers or demo evaluations. It does not include enterprise role-based multi-user login (RBAC).
