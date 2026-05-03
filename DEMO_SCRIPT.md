# ProcureIQ — 5-Minute Demo Script

Use this script for live demos, LinkedIn recordings, or interview walkthroughs.
Total runtime: ~5 minutes at a normal speaking pace.

---

## Setup (before you start)

1. Ensure `auth_config.yaml` exists (copy from `auth_config.yaml.example` if not).
   Demo credentials: **admin / demoAdmin2025!** (or whichever you set in `auth_config.yaml`).
2. Run `streamlit run app.py`
3. Log in when the login form appears. You'll see the "Demo Login Required" disclaimer — this is intentional.
4. Have a sourcing scenario ready. Recommended: **"HR Tech RFP — HRIS Platform, Strategic"**
5. Optional: Set `ANTHROPIC_API_KEY` in your environment for live LLM features.
   Without a key, the app runs fully in illustrative mode (clearly labeled).

---

## Scene 1 — Problem Setup (30 sec)

**What to say:**
> "Procurement teams spend weeks building sourcing decisions that are never fully defensible.
> ProcureIQ structures that process end-to-end — from market intelligence through stakeholder
> management to an executive-ready output. Let me show you a live HR Tech evaluation."

**What to do:**
- Open the app. Show the Overview tab.
- Point to the 4-step guide: *"Intake → Market Intelligence → Supplier Evaluation → Decision Brief."*
- Note: *"Every tab feeds the next. This is a deliberate workflow, not a dashboard."*

---

## Scene 2 — Intake (45 sec)

**What to do:**
- Click **Intake** tab.
- Set:
  - Category: **Human Resources**
  - Subcategory: **HRIS / HCM Platform**
  - Kraljic posture: **Strategic**
  - Annual spend: **$1,200,000**
  - Event name: **HR Tech RFP 2025**
- Show the Kraljic posture selector and explain briefly:
  *"Strategic means high business impact, few alternatives. This changes how we weight the evaluation dimensions."*

---

## Scene 3 — Market Intelligence (60 sec)

**What to do:**
- Click **Market Intelligence** tab.
- Show the subcategory intelligence card: contract type, default posture, typical event.
- Click **Run Supplier Discovery**.
  - If no API key: the ILLUSTRATIVE banner appears. Point to it:
    *"When no AI key is configured, the app loads known market leaders from a curated knowledge base
    and labels everything as illustrative — no fake live data."*
  - If API key set: show live scoring running.
- Show one supplier card. Highlight:
  - Why Included (now per-supplier, not templated)
  - Key Differentiator
  - Illustrative badge (if in fallback mode)

**What to say:**
> "The discovery agent categorizes suppliers into shortlist, longlist, and watchlist — the same
> tiers a category manager would use. Each supplier has a distinct rationale, not a copy-paste."

---

## Scene 4 — Supplier Evaluation (75 sec)

**What to do:**
- Click **Supplier Evaluation** tab.
- **Option A — CSV import (fastest):** Click "📥 Import Suppliers from CSV", download the template,
  show 3 rows pre-filled (Workday/SAP/Oracle), upload, click Import. Slots populate instantly.
- **Option B — manual entry:** Enter 3 suppliers: **Workday**, **SAP SuccessFactors**, **Oracle HCM**,
  set prices $1.2M, $950K, $1.1M.
- Adjust a few dimension sliders to show differentiation.
- Point to the financial health section — for Workday and Oracle (public companies), the tool fetches
  their SEC EDGAR/XBRL score automatically. Show the **freshness badge** next to the score (green
  pill = data within 12 months; amber = 13–18 months; red = stale). Show the "Why this score?" expander.
  For a private supplier, fill in 2–3 qualitative fields instead.
- Show the **Supplier Comparison chart** (horizontal bar chart — sorted by leader's scores).

**What to say:**
> "This is a 10-dimension weighted scoring model. Weights auto-adjust by Kraljic posture and
> subcategory — Strategic HRIS weights Execution Risk and SLA higher than Price. For public
> companies the financial health score comes straight from their SEC annual filing — not my opinion.
> CFOs push back on that; I'll show you how the tool handles it."

- Show the **Active Weights** chips. Point to the ESG and Supplier Diversity dimensions.

---

## Scene 5 — Decision Brief (75 sec)

**What to do:**
- Click **Decision Brief** tab.
- Show the hero strip: recommended supplier, score, confidence label, score gap.
- Scroll to **CFO Challenge** section. Read one Q&A aloud:
  *"Why are we paying 26% more for Workday when SAP SuccessFactors covers the basics?"*
  Then read the structured answer.
- Show **Risk Flags** — point to a HIGH flag if present.
- Show **90-Day Action Plan**.

**What to say:**
> "The CFO Challenge section pre-loads the hardest questions any CFO will ask in a sourcing committee
> and gives the procurement team structured answers. This is the section that wins internal approval."

- Click **Export to Excel** or **Export HTML One-Pager**.

---

## Scene 6 — Positioning Close (30 sec)

**What to say:**
> "ProcureIQ doesn't replace SAP Ariba or Coupa. It handles the judgment-intensive work those
> platforms don't do: market intelligence, multi-criteria evaluation, stakeholder coaching, and
> executive-ready outputs. It's the layer between spreadsheets and your ERP."

**Optional — show Portfolio Dashboard:**
- Click **Spend & Risk** tab. If events are saved, show the Kraljic distribution and category breakdown.
- *"This is a cross-event portfolio view — you can see your sourcing posture across all active categories."*

---

## Common Questions and Answers

**Q: Is this connected to real data?**
> "For public companies, financial health pulls directly from SEC EDGAR/XBRL annual filings — no API
> key required. Each score shows a freshness badge with the filing date so you always know how current
> it is. Live stock data and company overviews require Alpha Vantage. AI scoring requires
> an Anthropic (Claude) key — Claude is the only provider that supports the tool-use agents.
> Without those keys the app runs in illustrative mode and labels everything clearly.
> For a demo, illustrative mode is sufficient to show the full workflow."

**Q: Can I import existing supplier data instead of entering everything manually?**
> "Yes — there's a CSV import in the Supplier Evaluation tab. Download the template, fill in supplier
> names, tickers, prices, and any known financial fields, then upload. It pre-populates all slots
> instantly. Dimension scores still need to be set manually — those are judgment calls, not data."

**Q: Does it connect to SAP or Coupa?**
> "Not currently. The API layer is designed for integration, but there's no live ERP connector today.
> The positioning is as a pre-award decision support tool, not a replacement for P2P systems."

**Q: What's the AI doing?**
> "The LLM handles supplier discovery (categorization, scoring rationale, risk flags) and the
> conversational intake. The scoring engine itself is a transparent weighted average that any
> procurement professional can audit and explain — no black box."

**Q: What are the limitations?**
> "SQLite backend, single-user architecture, manual data entry, and LLM outputs that require human
> review. See LIMITATIONS.md for the full list. This is portfolio-grade software, not production-ready."
