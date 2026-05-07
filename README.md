# ProcureIQ

**ProcureIQ structures and defends enterprise sourcing decisions before supplier award.**

A structured evaluation record system for technology vendor selection. Score suppliers across 10 weighted dimensions, verify financial health from SEC EDGAR/XBRL, and generate a CFO-ready Decision Brief with challenge Q&A, risk flags, and a complete Evidence & Assumptions audit trail — in one click.

Built to demonstrate what AI-assisted procurement looks like when it's auditable, not just impressive.

---

## The Problem

Enterprise procurement teams spend weeks assembling sourcing recommendations that collapse in 20-minute executive meetings. The evaluation lives in a spreadsheet. The financial data is in a separate tab. The CFO questions nobody anticipated. The rationale that justified the award disappears when the procurement manager leaves.

ProcureIQ fills the gap between "we need to evaluate vendors" and "we issue the PO" — the gap where sourcing decisions currently live in PowerPoint files nobody can find.

---

## What ProcureIQ Does

- **Guided intake** — Captures sourcing event context: category, subcategory, Kraljic position, spend, stakeholders, switching cost, and business urgency
- **Supplier evaluation** — 10-dimensional weighted scoring across Price/TCO, SLA, Execution Risk, Financial Health, Strategic Alignment, ESG, Supplier Diversity, and more; financial health auto-populated from SEC EDGAR/XBRL for public companies; CSV import to pre-populate up to 20 supplier slots
- **Market intelligence** — Subcategory-specific market context; live data via SEC EDGAR and BLS PPI when configured
- **Stakeholder analysis** — Power/interest mapping, position tracking (Champion → Blocker), likely-blocker detection, talk-track coaching per stakeholder
- **Decision Brief** — Executive summary, CFO challenge Q&A (deterministic — no API call required), risk flags, 90-day action plan, score confidence, Evidence & Assumptions audit trail, Why Not Selected analysis per rejected supplier, Conditions of Award checklist, and Executive Defensibility Score
- **Portfolio dashboard** — Cross-event view of saved evaluations with Kraljic distribution, category breakdown, and data provenance risk heat map
- **Exports** — Excel and HTML one-pager for offline sharing

---

## Key Features

### Supplier Evaluation
- 10-dimension weighted scoring (configurable by Kraljic position and subcategory)
- Financial health score from SEC EDGAR/XBRL for public companies; qualitative signals for private companies
- Sigmoid price normalisation (k=4) — prevents outlier collapse in competitive bids
- CSV import to pre-populate supplier name, ticker, price, financial fields, and all dimension scores (up to 20 suppliers)

### SEC EDGAR Financial Health
- For public companies: revenue growth, profit margin, and debt-to-assets ratio pulled from SEC EDGAR/XBRL 10-K filings
- Freshness gate: amber badge (12–18 months old) and red gate (>18 months) require explicit acknowledgment before brief renders
- Score labeled "SEC EDGAR/XBRL" — sourced from a primary regulatory filing, not vendor-provided data
- Score card displays filing period date so the CFO knows exactly what period the data covers

### Stakeholder Analysis
- Power/interest matrix
- Position tracking (Champion, Supporter, Neutral, Skeptic, Blocker)
- Per-stakeholder talk-track coaching
- Likely-blocker detection and escalation guidance

### Decision Brief
- Executive summary with Kraljic framing
- CFO challenge Q&A — six questions built deterministically from evaluation data (no API key required)
- **Executive Defensibility Score** — deterministic 0–100 signal grading the brief across six components: evaluation completeness, score gap, HIGH risk flag count, financial data freshness, stakeholder alignment, and weakest dimension floor; no LLM call
- **Why Other Suppliers Were Not Selected** — per-supplier section showing score deficit, price comparison story, and largest dimension gap vs the recommended supplier
- **Conditions of Award** — deterministic pre-award checklist derived from HIGH risk flags, blocker presence, EDGAR staleness, weakest dimension score, and score gap; REQUIRED vs STANDARD tiers
- Evidence & Assumptions section — data sources, scoring assumptions, and pre-award validation flags
- Risk flags (HIGH / MEDIUM / LOW tiers)
- 90-day action plan
- Score confidence label
- AI-assisted CFO narrative (optional, requires Anthropic API key, collapsed by default)

### Security (demo-grade)
- **Streamlit login gate** — custom `auth.py` login form using `bcrypt.checkpw()` directly; blocks all app access; credentials in `auth_config.yaml` (gitignored)
- JWT authentication for the optional FastAPI layer (requires `SECRET_KEY` environment variable)
- Session management in SQLite; audit log table present
- **Not suitable for production multi-user deployment without additional hardening**

---

## Live Demo

A preloaded HRIS vendor evaluation (Workday vs. Rippling vs. UKG Pro) is available from the login screen — no API key required. The demo loads a complete evaluation with EDGAR-backed financial health for Workday and generates the full Decision Brief in one click.

Click **"▶ Open Live Demo"** on the login page.

---

## Architecture

```
ProcureIQ/
├── app.py                    # Main Streamlit application (~14,000 lines)
├── auth.py                   # Streamlit login gate (custom bcrypt form, no third-party auth library)
├── auth_config.yaml.example  # Credential template — copy to auth_config.yaml (gitignored) and fill in
├── database.py               # SQLite with WAL mode, session management, discovery cache
├── evaluation.py             # Scoring engine: weighted average, financial health, subcategory weights
├── agents/                   # LLM-backed agents (supplier discovery, intake coaching, enrichment)
├── services/                 # Thin orchestration layer over agents
├── taxonomy.py               # 15-category, 179-subcategory procurement taxonomy
├── config.py                 # DIMENSIONS, Kraljic rules, scoring rubrics
├── market_data.py            # Static market data + live API integrations (SEC EDGAR, BLS PPI)
├── security.py               # Auth utilities (JWT, hashing, audit logger)
├── rfp.py                    # RFP question templates
├── utils.py                  # Helper functions
└── tests/                    # 150 unit tests
```

**Database:** SQLite (WAL mode). Suitable for single-user and demo use. Not suitable for concurrent multi-user production deployment.

**AI:** All AI agents require Claude (Anthropic). The CFO Challenge Q&A and executive summary are generated deterministically from evaluation data — no API key required for the core Decision Brief.

---

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd procureiq
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure authentication** (required — the app will not start without credentials)
   ```bash
   cp auth_config.yaml.example auth_config.yaml
   # Edit auth_config.yaml — set bcrypt-hashed passwords, then restart.
   # See auth_config.yaml.example for instructions on generating bcrypt hashes.
   ```
   Alternatively, use environment variables:
   ```bash
   export PROCUREIQ_DEMO_USER=demo
   export PROCUREIQ_DEMO_PASS=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())")
   ```

4. **Configure API keys** (all optional — app runs without them)
   ```bash
   # Enables LLM-backed supplier discovery and intake agent (Claude required for all AI agents)
   export ANTHROPIC_API_KEY="your_key"

   # Enables live stock data and company overviews
   export ALPHA_VANTAGE_API_KEY="your_key"

   # Enables procurement news feed
   export NEWS_API_KEY="your_key"

   # Required only if using the FastAPI JWT endpoints
   export SECRET_KEY="random-string-min-32-chars"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

---

## Without API Keys

The app is fully usable without any API keys:
- The preloaded HRIS demo runs entirely without an API key
- All evaluation, scoring, stakeholder analysis, and export features work normally
- Supplier discovery returns clearly labeled **illustrative / static data** from a curated knowledge base
- The CFO Challenge Q&A and executive summary are generated deterministically — no API call required

**Claude is required for AI agents.** Supplier discovery, intake coaching, contract drafting, and the optional AI-assisted CFO narrative require an Anthropic API key.

---

## Running Tests

```bash
python -m pytest tests/ -q
```

150 tests covering evaluation logic, financial health scoring (qualitative + EDGAR/XBRL paths), CFO challenge generation, risk flag logic, executive summary construction, live scoring functions, EDGAR staleness handling, and CSV supplier import.

---

## What ProcureIQ Is Not

- **Not an ERP connector** — No live SAP, Coupa, or Oracle integration. Spend data is entered manually or via CSV import.
- **Not a compliance tool** — Sanctions screening is not performed by this tool. Before awarding any contract, screen against OFAC SDN at sanctionslistservice.ofac.treas.gov using a certified process.
- **Not legal advice** — Recommendations, risk flags, and contract language suggestions are informational only.
- **Not production-ready** — SQLite backend, single-process architecture, no multi-tenancy. Built for single-user use and demonstration.
- **Not a certified AI system** — LLM outputs require human review. Financial health scores for public companies are derived from SEC EDGAR/XBRL filings; for private companies they reflect qualitative user inputs, not audited financials.

See [LIMITATIONS.md](LIMITATIONS.md) for the full limitations list.

---

## License

Proprietary — All rights reserved.
