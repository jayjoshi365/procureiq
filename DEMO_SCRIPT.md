# ProcureIQ — Demo Scripts

Two formats: a **2-minute video cut** for recordings and LinkedIn, and a **5-minute live version** for interviews and recruiter calls.

---

## 2-Minute Video Script

**Setup:** Login complete, Intake already filled (HR Tech RFP, Strategic, $1.2M), 3 suppliers loaded via CSV (Workday $1.2M, SAP SuccessFactors $950K, Oracle HCM $1.1M).

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

- Click Decision Brief tab.
- Show the hero strip: recommended supplier, score, confidence label.
- Scroll to **CFO Challenge**. Read one Q&A aloud.
- Say: *"This section pre-loads the hardest questions a CFO will ask in a sourcing committee
  and gives structured, sourced answers. Q5 calls out if switching cost data wasn't captured
  in intake. Q3 flags when fewer than 40% of dimensions were actively scored."*
- Scroll to **Evidence & Assumptions**. Show the 3-column table.
- Say: *"Every data source, scoring assumption, and unvalidated input is listed here.
  This is the audit trail — it's what makes the recommendation defensible."*

---

**[1:30–2:00] — Close**

- Show **Export to Excel** or **Export HTML One-Pager**.
- Say: *"The output is a CFO-ready decision brief — not a dashboard, not a report. It's the
  document that gets approved in a sourcing committee. The scoring is a transparent weighted
  average anyone can audit. The financial health is sourced from SEC filings. The risks are
  flagged before the contract goes out."*

---

---

## 5-Minute Live Demo Script

Use for live demos, interviews, or recruiter walkthroughs. ~5 minutes at a normal speaking pace.

---

### Setup (before you start)

1. Ensure `auth_config.yaml` exists (copy from `auth_config.yaml.example` if not).
   Demo credentials: **admin / demoAdmin2025!** (or whichever you set in `auth_config.yaml`).
2. Run `streamlit run app.py`
3. Log in — the "Demo Login Required" disclaimer is intentional.
4. Have a sourcing scenario ready. Recommended: **HR Tech RFP — HRIS Platform, Strategic, $1.2M**
5. Optional: set `ANTHROPIC_API_KEY` in your environment for live LLM features.
   Without a key, the app runs in illustrative mode (clearly labeled).

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
- Click **Intake** tab.
- Set:
  - Category: **Human Resources**
  - Subcategory: **HRIS / HCM Platform**
  - Kraljic posture: **Strategic**
  - Annual spend: **$1,200,000**
  - Event name: **HR Tech RFP 2025**
  - Switching cost: **High — embedded workflows, data portability risk**
- Show the Kraljic posture selector and explain:
  *"Strategic means high business impact, few alternatives. This changes how we weight the evaluation dimensions — and it surfaces in the CFO Challenge later."*

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
- Show one supplier card. Highlight: Why Included, Key Differentiator, Illustrative badge if present.

**What to say:**
> "The discovery agent categorizes suppliers into shortlist, longlist, and watchlist — the same
> tiers a category manager would use. Each supplier has a distinct rationale, not a copy-paste."

---

### Scene 4 — Supplier Evaluation (75 sec)

**What to do:**
- Click **Supplier Evaluation** tab.
- **Option A — CSV import (fastest):** Click "📥 Import Suppliers from CSV", download the template,
  show 3 rows pre-filled (Workday / SAP / Oracle), upload, click Import. Slots populate instantly.
- **Option B — manual:** Enter Workday $1.2M, SAP SuccessFactors $950K, Oracle HCM $1.1M.
- Adjust 2–3 dimension sliders to show differentiation.
- Point to the financial health section:
  - For Workday and Oracle (public): EDGAR score auto-populated. Show the **freshness badge** —
    green ≤12 months, amber 13–18, red >18. Show the "Why this score?" expander.
  - Say: *"If the filing is stale, the Decision Brief won't render until the assessor acknowledges
    the data age — that's an audit gate, not a warning they can scroll past."*
  - For SAP (private): fill in 2–3 qualitative fields instead.
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

- Show the **Active Weights** chips. Point to ESG and Supplier Diversity dimensions.

---

### Scene 5 — Decision Brief (75 sec)

**What to do:**
- Click **Decision Brief** tab.
- Show the hero strip: recommended supplier, composite score, confidence label, score gap.
- Point to the **EDGAR freshness gate** if triggered (amber/stale banner requiring acknowledgment
  before the brief renders).
- Scroll to **CFO Challenge**. Read one Q&A aloud — e.g.:
  *"Why are we paying 26% more for Workday when SAP SuccessFactors covers the basics?"*
  Then read the structured answer. Note: *"The answer cites the EDGAR period end date,
  the weakest dimension score, and the switching cost classification from intake."*
- Show **Risk Flags** — point to a HIGH flag if present. Note the three-tier structure: HIGH / MEDIUM / LOW.
- Show **Evidence & Assumptions**. Point to the 3-column table: Source, What It Drives, Validation Flag.
  Say: *"This is the audit trail. Every data source and scoring assumption is listed — including
  any dimension that was left at the default midpoint."*
- Show **90-Day Action Plan**.

**What to say:**
> "The CFO Challenge pre-loads the hardest questions any finance committee will ask and gives
> structured, sourced answers. The Evidence & Assumptions section is what makes the recommendation
> defensible to an auditor, not just an executive."

- Click **Export to Excel** or **Export HTML One-Pager**.

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
> procurement professional can audit and explain — no black box. The CFO Challenge Q&A is
> template-driven, sourced from live evaluation state, not generated by the LLM."

**Q: What are the limitations?**
> "SQLite backend, single-user architecture, manual data entry, and LLM outputs that require
> human review. Sanctions screening is illustrative — not certified compliance tooling.
> See LIMITATIONS.md for the full list. This is portfolio-grade software, not production-ready."
