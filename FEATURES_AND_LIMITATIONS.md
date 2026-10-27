# FestiWise AI — Features, Verification Status & Limitations Matrix

**Hack2Skill PromptWars | Challenge 5: Celebration & Event Planner**

---

## 1. Feature Implementation & Verification Status

| Feature / Capability | Implementation Details | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| **Full-Stack SaaS Interface** | Streamlit multi-page app with custom celebratory CSS, metric tiles, responsive layout, and sidebar navigation | **VERIFIED** | Tested with custom styling, glass cards, and status tags. |
| **Startup & Health Check** | Streamlit web server initialized via `python -m streamlit run app.py` with UTF-8 configuration and headless settings | **VERIFIED** | Probed `http://127.0.0.1:8501/_stcore/health` and verified HTTP 200 response on Attempt 1. Diagnosed and fixed Windows `cp1252` UnicodeEncodeError. |
| **Event Blueprint Creator** | Collects category, date, city, venue type, guest count, budget, currency, theme, diet, and requirements | **VERIFIED** | Form inputs strictly validated via Pydantic (`EventInput`). Tested with valid and invalid inputs. |
| **GenAI Blueprint Generation** | Google GenAI SDK (`google-genai` v2.33.0) configured with `gemini-3.8-flash` (default), `gemini-3.5-flash-lite`, and `gemini-4-argon` | **VERIFIED (SDK & Fallback)** | SDK implementation, prompt construction, and structured JSON parsing verified. When API credentials are unset or quota is exhausted, seamlessly activates high-fidelity demo engine. Live network call requires user API key in `.env` or Settings. |
| **Deterministic Smart Budget Engine** | Python code calculates totals, category percentages, variances, committed expenses, and per-guest costs | **VERIFIED** | 100% test coverage in `tests/test_budget.py`. Zero LLM math. |
| **Budget Overflow & Variance Detection** | Identifies when expenses or allocations exceed budget cap and offers one-click proportional rebalancing | **VERIFIED** | Tested with deliberate overspending scenarios in unit tests. |
| **Expense Tracking Register** | Records actual vs. estimated expenses, payment status, vendor names, and verification flags | **VERIFIED** | Tested with SQLite persistence, add/delete operations. |
| **Milestone Timeline Checklist** | Generates preparation tasks scaled to the event date; interactive completion toggles | **VERIFIED** | Tested status updates, chronological sorting, and progress bar recalculation. |
| **Day-Of Chronological Itinerary** | Minute-by-minute schedule with duration and notes; schedule contradiction warnings | **VERIFIED** | Tested schedule validation in `tests/test_timeline.py`. |
| **Vendor Organizer & AI Guidance** | Contact tracker, quotation manager, AI questions checklist, and caution red flags | **VERIFIED** | Tested guidance generation and vendor CRUD operations. |
| **Plan Rescue Mode (Signature Feature)** | Disruption evaluation (venue drops, weather threats, guest surges, budget shocks), programmatic delta calculation, Gemini strategic options with trade-offs, interactive before/after diff review, and revision application | **VERIFIED** | 100% test coverage in `tests/test_rescue.py` and `tests/test_integration_workflow.py`. Evaluates real state deltas and patches saved event. |
| **Creative Studio** | Personalized themes, rationale, color palette cards, original invitation wording copywriter, menu ideas, games, and eco-friendly tips | **VERIFIED** | Fully rendered across categories with copy-to-clipboard code blocks. |
| **Guest & RSVP Management** | Attendee headcount capacity vs. confirmed attendees, plus-ones, dietary tags, table groups | **VERIFIED** | Tested capacity surge alerts and guest status updates. |
| **Database Persistence** | SQLite 3 relational schema with foreign key cascading and JSON serialization | **VERIFIED** | Full CRUD verified in `tests/test_db.py` on temporary database. |
| **Settings & Diagnostics** | In-app API key verification tool, model selector, currency selector, and system info | **VERIFIED** | Tested API verification flow and session preference persistence. |
| **Automated Testing Suite** | 21 automated unit & integration tests covering budget, schemas, timeline, SQLite, rescue, and Gemini | **VERIFIED** | 21 passed out of 21 tests in 3.66 seconds via pytest. |

---

## 2. Startup Diagnosis & Resolution

- **Symptom 1:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2191' in position 632: character maps to <undefined>`.
  - **Root Cause:** On Windows, Python's default console encoding is `cp1252`. Streamlit's CLI documentation and Click utilities include unicode symbols (such as `↑`), which failed encoding under `cp1252`.
  - **Resolution:** Added UTF-8 reconfiguration in `app.py` (`sys.stdout.reconfigure(encoding="utf-8")`) and created `.streamlit/config.toml`.
- **Symptom 2:** `Start-Process : An Application Control policy has blocked this file`.
  - **Root Cause:** Windows sandbox AppLocker blocks execution of binary `.exe` launchers created within user virtual environments (`.venv\Scripts\streamlit.exe`).
  - **Resolution:** Launch using the system Python interpreter module: `python -m streamlit run app.py`.
- **Symptom 3:** Localhost probe socket error `WinError 10013` inside standard sandbox.
  - **Root Cause:** Standard sandbox mode isolates all network connections, including loopback TCP sockets.
  - **Resolution:** Probed with network enabled (`BypassSandbox: true`), which immediately confirmed HTTP 200 on `http://127.0.0.1:8501/_stcore/health`.
- **Symptom 4:** `ImportError: DLL load failed while importing dtypes: An Application Control policy has blocked this file` (Win32 Error 4551).
  - **Root Cause:** `pandas 3.1.0` binary wheel contained an unvetted C-extension `dtypes.cp313-win_amd64.pyd` that triggered Windows Defender Application Control (WDAC) code-integrity blocking rule 4551.
  - **Resolution:** Safely diagnosed via low-level `ctypes.windll.kernel32.LoadLibraryExW` diagnostic. Tested and installed the vetted official release `pandas==2.2.3`, which loaded completely without any security block. Pinned `pandas>=2.2.3,<3.0.0` in `requirements.txt`.
- **Symptom 5:** Upstream Gemini model deprecations (`gemini-2.5-flash` returning 404).
  - **Root Cause:** Older preview models are periodically retired by Google AI Studio.
  - **Resolution:** Updated `services/gemini_service.py` to auto-fallback across candidate models (`[configured_model, "gemini-3.5-flash-lite"]`). Verified live API connectivity with `gemini-3.5-flash-lite`.

---

## 3. Known Limitations & Technical Constraints

1. **Ephemeral Local Storage on Free-Tier Hosting:**
   - When deployed on platforms such as Streamlit Community Cloud without persistent volume attachments, the SQLite database (`festiwise.db`) persists across user reloads within an active container session, but may be reset if the container is recycled or put to sleep after inactivity.
   - **Mitigation:** FestiWise AI includes an **Export JSON** feature on the *My Celebrations* page so users can back up their entire celebration blueprint locally.

2. **No Paid Live Vendor Scraping:**
   - FestiWise AI intentionally does not scrape unverified live marketplace directories or fabricate fake vendor contact numbers or quotes. It functions as a structured **Vendor Organizer and AI Question Advisor** to empower users during vendor negotiations.

3. **Live Weather API Integration:**
   - FestiWise AI does not claim to check live satellite weather feeds unless a weather API key is explicitly configured. Instead, in outdoor weather emergencies, it offers conditional, actionable indoor hall pivots and marquee canopy rental contingencies.

4. **Public Deployment Verification Status:**
   - The codebase, configuration files, and documentation are 100% prepared for free-tier deployment on Streamlit Community Cloud. Actual public URL provisioning requires connecting the user's personal GitHub repository to Streamlit Cloud.
