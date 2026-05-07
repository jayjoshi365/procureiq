# ProcureIQ — Demo Scripts

Two formats: a **2-minute video cut** for recordings and LinkedIn, and a **5-minute live version** for interviews and recruiter calls.

---

## 2-Minute Video Script

**Setup:** Click **"▶ Open Live Demo"** on the login screen. The HRIS evaluation (Workday $480K · Rippling $390K · UKG Pro $365K) loads automatically — no CSV, no API key.

---

**[0:00–0:20] — Open on Supplier Evaluation**

> "This is ProcureIQ — a procurement decision engine I built to take a sourcing event from intake
> through executive recommendation. I'll show you three things: the scoring model, the financial
> health verification, and the Decision Brief."

- Show the Supplier Evaluation tab with 3 suppliers loaded.
- Point to the **Active Weights** chips.
- Say: *"Weights auto-shift by Kraljic posture. Strategic HRIS weights Execution Risk and SLA above Price."*

---

**[0:20–0:50] — Financial Health + EDGAR**

- Click into Workday's financial section.
- Show the EDGAR score auto-populated: score, freshness badge, period end date.
- Say: *"For public companies, financial health pulls directly from SEC EDGAR/XBRL annual filings.
  The freshness badge tells you exactly how current the data is — green within 12 months, amber
  at 13–18, red beyond that. If it's stale, the Decision Brief gates until you acknowledge it."*
- Show the **Supplier Comparison** bar chart.

---

**[0:50–1:30] — Decision Brief**

- Click **Decision Brief** tab.
- Show the hero strip: recommended supplier, score, confidence label, score gap, and the
  **Executive Defensibility Score** (0–100).
- Say: *"The Defensibility Score is a deterministic signal — no LLM — built from six components:
  evaluation completeness, score gap, risk flags, financial data quality, stakeholder alignment,
  and the weakest dimension floor. It tells you before the meeting how well this brief will hold
  up under challenge."*
- Scroll to **Why Other Suppliers Were Not Selected**. Point to the Rippling card.
  Say: *"For each supplier not awarded, the brief shows exactly what separated them — score gap,
  price comparison, and the single dimension with the largest deficit. This is the question
  every CFO asks: 'Why not the cheaper one?'"*
- Scroll to **CFO Challenge**. Read one Q&A aloud.
  Say: *"Six questions, built deterministically from evaluation data. No API key required."*
- Scroll to **Conditions of Award**. Point to the REQUIRED items.
  Say: *"Pre-award checklist derived live from the evaluation — HIGH risk flags, blocker presence,
  data staleness, weak dimensions. Everything that must be resolved before the PO is issued."*
- Scroll to **Evidence & Assumptions**. Show the 3-column table.
  Say: *"Every data source, scoring assumption, and unvalidated input is listed here.
  This is the audit trail — it's what makes the recommendation defensible."*

---

**[1:30–2:00] — Close**

- Show **Export HTML One-Pager**.
- Say: *"The export includes everything — the Defensibility Score, Why Not Selected, Conditions
  of Award, risk flags, and action plan. A CFO-ready brief, not a dashboard. The scoring is a
  transparent weighted average anyone can audit. The financial health is sourced from SEC filings.
  The risks are flagged before the contract goes out."*

---

---

## 5-Minute Live Demo Script

Use for live demos, interviews, or recruiter walkthroughs. ~5 minutes at a normal speaking pace.

---

### Setup (before you start)

**Option A — One-click demo (recommended, no API key needed):**
1. Run `streamlit run app.py`
2. On the login screen, click **"▶ Open Live Demo"**
3. The HRIS evaluation (Workday · Rippling · UKG Pro) loads automatically.
4. Navigate directly to the Decision Brief tab — the brief renders in one click.

**Option B — Credentialed login:**
1. Ensure `auth_config.yaml` exists. Demo credentials: **admin / demoAdmin2025!**
2. Run `streamlit run app.py` and log in.
3. Optionally set `ANTHROPIC_API_KEY` for live LLM features. Without a key, the app runs
   in illustrative mode (clearly labeled).

---

### Scene 1 — Problem Setup (30 sec)

**What to say:**
> "Procurement teams spend weeks building sourcing decisions that are never fully defensible.
> ProcureIQ structures that process end-to-end — from market intelligence through stakeholder
> management to an executive-ready output. Let me show you a live HR Tech evaluation."

**What to do:**
- Open the app. Show the Overview tab.
- Point to the 4-step guide: *"Intake → Market Intelligence → Supplier Evaluation → Decision Brief."*
- Note: *"Every tab feeds the next. This is a deliberate workflow, not a dashboard."*

---

### Scene 2 — Intake (45 sec)

**What to do:**
- Click **Intake** tab. (In demo mode, this is pre-filled — walk through the values.)
- Point to:
  - Category: **Human Resources** / Subcategory: **HRIS / HCM Platform**
  - Kraljic posture: **Strategic**
  - Annual spend: **$1,200,000**
  - Event name: **HR Tech RFP 2025**
  - Switching cost: **High**
- Explain the Kraljic posture selector:
  *"Strategic means high business impact, few alternatives. This changes how we weight the
  evaluation dimensions — and it surfaces in the CFO Challenge later."*

---

### Scene 3 — Market Intelligence (60 sec)

**What to do:**
- Click **Market Intelligence** tab.
- Show the subcategory intelligence card: contract type, default posture, typical event.
- Click **Run Supplier Discovery**.
  - No API key: point to the ILLUSTRATIVE banner. Say: *"When no AI key is configured, the app
    loads known market leaders from a curated knowledge base and labels everything illustrative —
    no fake live data."*
  - API key present: show live scoring running.
- Show one supplier card. Highlight: Why Included, Key Differentiator.

**What to say:**
> "The discovery agent categorizes suppliers into shortlist, longlist, and watchlist — the same
> tiers a category manager would use. Each supplier has a distinct rationale, not a copy-paste."

---

### Scene 4 — Supplier Evaluation (75 sec)

**What to do:**
- Click **Supplier Evaluation** tab.
- In demo mode, three suppliers are pre-loaded: **Workday $480K**, **Rippling $390K**, **UKG Pro $365K**.
  If doing a manual demo: enter these values or use CSV import (download template → fill 3 rows → upload).
- Adjust 2–3 dimension sliders to show differentiation.
- Point to the financial health section:
  - **Workday** (public, ticker: WDAY): EDGAR score auto-populated from SEC 10-K. Show the
    **freshness badge** — green ≤12 months, amber 13–18, red >18. Show the "Why this score?" expander.
    Say: *"If the filing is stale, the Decision Brief won't render until the assessor acknowledges
    the data age — that's an audit gate, not a warning they can scroll past."*
  - **Rippling / UKG Pro** (private, no ticker): show the qualitative fields instead.
    Say: *"For private companies, we capture qualitative signals — years in business, revenue
    trajectory, M&A activity. The score is labeled 'User Assessment' so the CFO knows exactly
    what it's based on."*
- Open the **TCO Model** expander. Show benchmark defaults auto-populated from contract value —
  implementation 10%, integration 6%, switching cost 15%.
  Say: *"These are Gartner / Hackett Group benchmarks scaled to the contract value. The assessor
  adjusts to actuals — the model just ensures nothing gets left at zero."*
- Show the **Supplier Comparison** bar chart.

**What to say:**
> "10-dimension weighted scoring. Weights auto-adjust by Kraljic posture and subcategory. Strategic
> HRIS weights Execution Risk and SLA higher than Price. For public companies, financial health
> comes from their SEC annual filing — not my opinion. CFOs push back on that. I'll show you how
> the tool handles it."

---

### Scene 5 — Decision Brief (90 sec)

**What to do:**
- Click **Decision Brief** tab.
- Show the **hero strip**: recommended supplier, composite score, confidence label, score gap,
  and the **Executive Defensibility Score**.
  - Say: *"The Defensibility Score is deterministic — no LLM call. Six components: evaluation
    completeness, score gap, HIGH risk flags, EDGAR data freshness, stakeholder alignment, and
    the weakest dimension floor. It scores the brief itself, not the supplier."*
  - Point to the **breakdown card** below the dimension bars — each component shows earned vs max.
- Point to the **EDGAR freshness gate** if triggered (amber/stale banner requiring acknowledgment).
- Scroll to **Why Other Suppliers Were Not Selected**.
  - Say: *"For each non-recommended supplier, the brief shows exactly what separated them:
    score gap, price comparison story, and the single dimension with the largest deficit.
    This pre-empts the 'why not the cheaper one?' question before anyone asks it."*
  - Point to the Rippling card: UKG Pro is $115K cheaper than Workday — this section shows
    exactly where it lost ground.
- Scroll to **CFO Challenge**. Read one Q&A aloud — e.g.:
  *"Why are we paying more for Workday when Rippling is cheaper?"*
  Then read the structured answer. Note: *"The answer cites the EDGAR period end date,
  the weakest dimension score, and the switching cost classification from intake."*
- Show **Risk Flags** — point to a HIGH flag if present.
- Scroll to **Conditions of Award**.
  - Say: *"Pre-award checklist built live from the evaluation data — HIGH risk flags become
    REQUIRED items, a blocker triggers an endorsement requirement, stale EDGAR data triggers
    a credit check requirement. Every item is derived, not generic."*
- Show **Evidence & Assumptions**. Point to the 3-column table: Source, What It Drives, Validation Flag.
  Say: *"This is the audit trail. Every data source and scoring assumption is listed — including
  any dimension left at the default midpoint."*

**What to say:**
> "The CFO Challenge pre-loads the hardest questions any finance committee will ask and gives
> structured, sourced answers. Why Not Selected pre-empts the obvious objections. Conditions of
> Award turns the risk flags into actionable requirements. The Evidence & Assumptions section is
> what makes the recommendation defensible to an auditor, not just an executive."

- Click **Export HTML One-Pager**. Note: *"The export includes all of this — EDS, Why Not Selected,
  Conditions of Award — not just the summary table."*

---

### Scene 6 — Positioning Close (30 sec)

**What to say:**
> "ProcureIQ doesn't replace SAP Ariba or Coupa. It handles the judgment-intensive work those
> platforms don't do: market intelligence, multi-criteria evaluation, stakeholder coaching, and
> executive-ready outputs. It's the layer between spreadsheets and your ERP."

**Optional — show Portfolio Dashboard:**
- Click **Spend & Risk** tab. If events are saved, show the Kraljic distribution, category breakdown,
  and data provenance risk heat map.
- *"This is a cross-event portfolio view — you can see your sourcing posture and data quality
  across all active categories."*

---

## Common Questions and Answers

**Q: Is this connected to real data?**
> "For public companies, financial health pulls directly from SEC EDGAR/XBRL annual filings —
> no API key required. Each score shows a freshness badge with the filing date so you always
> know how current it is. Live stock data and company overviews require Alpha Vantage. AI scoring
> requires an Anthropic (Claude) key — Claude is the only provider that supports the tool-use agents.
> Without those keys the app runs in illustrative mode and labels everything clearly."

**Q: What is the Executive Defensibility Score?**
> "A deterministic 0–100 score that grades the brief itself — not the supplier. Six components:
> how many dimensions were actively scored, the score gap vs the runner-up, how many HIGH risk
> flags are present, how fresh the financial data is, whether a blocker or champion is identified,
> and the weakest dimension floor. It tells you before the meeting whether this recommendation
> will survive a challenge. No LLM call — pure logic from the evaluation data."

**Q: Can I import existing supplier data?**
> "Yes — CSV import in the Supplier Evaluation tab. Download the template, fill in supplier
> names, tickers, prices, and any known financial fields, then upload. It pre-populates all slots
> instantly. Dimension scores still need to be set manually — those are judgment calls, not data."

**Q: Does it connect to SAP or Coupa?**
> "Not currently. The API layer is designed for integration, but there's no live ERP connector.
> The positioning is as a pre-award decision support tool, not a replacement for P2P systems."

**Q: What's the AI doing?**
> "The LLM handles supplier discovery (categorization, scoring rationale, risk flags) and the
> conversational intake. The scoring engine itself is a transparent weighted average that any
> procurement professional can audit and explain — no black box. The CFO Challenge Q&A,
> Executive Defensibility Score, Why Not Selected, and Conditions of Award are all deterministic —
> built from evaluation data, not generated by the LLM."

**Q: What are the limitations?**
> "SQLite backend, single-user architecture, manual data entry, and LLM outputs that require
> human review. Sanctions screening is not wired to the UI — use a certified OFAC process before
> any real award. See LIMITATIONS.md for the full list. This is portfolio-grade software,
> not production-ready."
