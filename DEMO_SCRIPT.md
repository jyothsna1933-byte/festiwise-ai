# FestiWise AI — Hack2Skill Video Demo Script & Recording Plan

**Challenge 5:** Celebration & Event Planner  
**Target Video Duration:** 2 Minutes 30 Seconds to 3 Minutes  
**Video Resolution:** 1080p (Full HD)  
**Audio:** Clear microphone voiceover with crisp delivery  

---

## 1. Pre-Recording Checklist

- [ ] Browser window sized to 1920x1080 (100% zoom).
- [ ] Streamlit application running (`streamlit run app.py`).
- [ ] Database initialized with the default demo wedding event.
- [ ] Browser tabs prepared (FestiWise AI tab open on Dashboard).
- [ ] Microphone tested with ambient noise suppression.
- [ ] Recording tool open (OBS Studio / Loom / Clipchamp).

---

## 2. Minute-by-Minute Walkthrough & Narration Script

### Scene 1: Introduction & Landing Page (0:00 - 0:25)
* **Visual on screen:** Show the FestiWise AI Dashboard. Point out the hero banner, celebratory color palette, metric tiles (Total Budget, Committed Expenses, Guests, Progress), and the active celebration pill.
* **Voiceover:**
  > *"Hello everyone! Welcome to FestiWise AI: Every celebration, perfectly planned. Built for Hack2Skill PromptWars Challenge 5. 
  > Planning a wedding, milestone birthday, or community fest is usually stressful and chaotic. Generic chatbots hallucinate budget math, while traditional spreadsheets shatter the minute something changes. 
  > FestiWise AI solves this by uniting Google Gemini Generative AI with strict programmatic financial calculations and our signature differentiator: Plan Rescue Mode."*

---

### Scene 2: Event Creation Workflow (0:25 - 0:50)
* **Visual on screen:** Click **"Plan New Celebration"** in the sidebar. Show the form inputs: Celebration Name (*"Ananya's 25th Neon Carnival Birthday"*), Category (*Birthday*), Date, City (*Bangalore*), Guests (*60*), Budget (*₹75,000*), Theme preference (*Neon Glow & Arcade*). Click **"Generate FestiWise Blueprint"**. Show the spinner and the immediate generated plan.
* **Voiceover:**
  > *"Let's plan a celebration. We enter our event specifications—category, date, venue preference, budget, and dietary wishes. 
  > FestiWise AI validates the inputs, calls the Google GenAI API to craft a personalized blueprint, and instantly generates culturally attuned themes, day-of schedules, and risk assessments."*

---

### Scene 3: Deterministic Smart Budget Planner (0:50 - 1:15)
* **Visual on screen:** Navigate to **"Budget Planner"**. Show the metric cards (Total Budget Cap, Planned Allocations, Committed Expenses, Remaining Budget). Switch to **"Visual Analytics"** to display the Plotly pie chart of category allocations and the planned vs. committed spend bar chart. Add a quick expense in the **"Expense Tracker"** tab.
* **Voiceover:**
  > *"Here in the Smart Budget Planner, we adhere strictly to the Financial Calculation Rule: zero LLM math. All category allocations, percentages, committed expenses, and per-guest costs are calculated deterministically in Python code. 
  > You can track actual vendor receipts versus AI estimates, identify variances, and view interactive visual breakdowns."*

---

### Scene 4: Interactive Timeline & Vendor Guidance (1:15 - 1:40)
* **Visual on screen:** Navigate to **"Timeline & Tasks"**. Show the progress bar, toggle a milestone task checkbox to "Completed" (observe the progress bar update dynamically). Switch to **"Day-Of Schedule"**. Then briefly click **"Vendors"** to show the **AI Interrogation Checklists** (questions to ask and caution red flags).
* **Voiceover:**
  > *"In the Timeline, preparation milestones are dynamically calculated relative to your event date. As tasks are completed, progress updates in real time. 
  > In the Vendors module, rather than fake marketplace quotes, FestiWise AI arms organizers with vital interrogation checklists and caution red flags to protect you before paying deposits."*

---

### Scene 5: SIGNATURE DIFFERENTIATOR — Plan Rescue Mode (1:40 - 2:20)
* **Visual on screen:** Navigate to **"Plan Rescue Mode"**. 
  - Select Disruption: *"Venue cancellation or sudden fee increase"*.
  - Enter Details: *"Lawn venue price spiked by ₹15,000 and 20 extra guests confirmed!"*
  - Enter Additional Guests: `20`.
  - Enter Price Increase: `15000`.
  - Click **"Run Plan Rescue Assessment"**.
  - Show the Programmatic Financial Impact cards (Cost Impact, Projected Required, Budget Deficit).
  - Expand Option 1 (Strategic Alternatives & Trade-offs).
  - Scroll to the **Proposed Plan Diff table** showing old vs. new values.
  - Click **"Approve & Apply Revised Plan"**.
* **Voiceover:**
  > *"Now, for our signature differentiator: Plan Rescue Mode. What happens when the unexpected strikes? Suppose our venue fees spike by ₹15,000 and 20 unexpected guests RSVP. 
  > Most tools force you to start over. FestiWise AI loads the active plan, computes the exact financial deficit in Python code, and queries Gemini for context-aware recovery strategies—complete with pros, cons, and trade-offs. 
  > We inspect the clear before-and-after diff. When we click 'Approve & Apply', FestiWise AI automatically rebalances the budget, updates guest counts, and injects crisis tasks into our timeline!"*

---

### Scene 6: Saved Event Verification & Conclusion (2:20 - 2:45)
* **Visual on screen:** Navigate to **"My Events"** to show the updated celebration with the new budget and rescue badge. Show the **"Export JSON"** button. Finally, click **"Settings"** to show the system diagnostics and free-tier compatibility.
* **Voiceover:**
  > *"Everything is safely persisted in our relational SQLite database. You can export clean JSON backups, switch between events, or configure your Gemini API key anytime. 
  > FestiWise AI requires zero GCP credits, passes all 20 automated tests, and runs completely free on Streamlit Community Cloud. 
  > Thank you, and may every celebration be perfectly planned with FestiWise AI!"*

---

## 3. Post-Recording Quality Checklist

- [ ] Audio levels are balanced and intelligible throughout.
- [ ] Plan Rescue Mode diff table was clearly visible on screen.
- [ ] Programmatic budget recalculation was highlighted.
- [ ] Video duration is between 2:00 and 3:00 minutes.
- [ ] Exported as MP4 format and uploaded to YouTube (Unlisted) or Google Drive (Public view).
