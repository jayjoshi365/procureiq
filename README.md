# ProcureIQ

A portfolio-grade procurement decision support tool built with Python and Streamlit. ProcureIQ structures the pre-award sourcing process: intake, market intelligence, supplier evaluation, stakeholder analysis, and executive-ready outputs — all in one workflow.

> **Positioning:** This is a decision support tool, not an enterprise procurement suite. It is not a replacement for SAP Ariba, Coupa, Ivalua, or Jaggaer. It is designed to complement them by accelerating the judgment-intensive work that those platforms do not do well.

---

## What ProcureIQ Does

- **Guided intake** — Captures sourcing event context (category, subcategory, Kraljic position, spend, stakeholders)
- **Supplier evaluation** — 10-dimensional weighted scoring across Price/TCO, SLA, Execution Risk, Strategic Alignment, ESG, Supplier Diversity, and more; financial health auto-populated from SEC EDGAR/XBRL for public companies; CSV import to pre-populate up to 20 supplier slots
- **Market intelligence** — Subcategory-specific market context; live data via Alpha Vantage and SEC EDGAR when API keys are configured
- **Stakeholder analysis** — Power/interest mapping, position tracking, talk-track coaching per stakeholder
- **Decision Brief** — Executive summary, CFO challenge Q&A, risk flags, 90-day action plan, and confidence score
- **Portfolio dashboard** — Cross-event view of saved evaluations with Kraljic distribution and category breakdown
- **Exports** — Excel and HTML one-pager for offline sharing

---

## What ProcureIQ Is Not

- **Not an ERP connector** — No live SAP, Coupa, or Oracle integration. Spend data is entered manually or via Excel upload.
- **Not a compliance tool** — Sanctions screening is illustrative. Do not use for actual OFAC/SAM.gov screening without a certified data source.
- **Not legal advice** — Recommendations, risk flags, and contract language suggestions are informational only.
- **Not production-ready** — SQLite backend, single-process architecture, no multi-tenancy. Built for portfolio demonstration and personal use.
- **Not a certified AI system** — LLM outputs require human review. Financial health scores for public companies are derived from SEC EDGAR/XBRL filings; for private companies they reflect qualitative user inputs, not audited financials.

---

## Key Features

### Supplier Evaluation
- 10-dimension weighted scoring (configurable by Kraljic position and subcategory)
- Financial health score from SEC EDGAR/XBRL for public companies; qualitative signals for private
- CSV import to pre-populate supplier name, ticker, price, and financial fields (up to 20 suppliers)
- Sensitivity analysis and confidence scoring
- Radar and bar chart visualization

### Market Intelligence
- 15 procurement categories, 179 subcategories with default Kraljic postures
- Subcategory-specific evaluation weight recommendations
- Live data integration (Alpha Vantage, SEC EDGAR, USASpending.gov, BLS PPI) when API keys are present
- Illustrative fallback data clearly labeled when no API key is configured

### Stakeholder Analysis
- Power/interest matrix
- Position tracking (Champion, Supporter, Neutral, Skeptic, Blocker)
- Per-stakeholder talk-track coaching
- Likely-blocker detection

### Decision Brief
- Executive summary with Kraljic framing
- CFO-ready challenge Q&A
- Risk flags (HIGH / MEDIUM / LOW tiers)
- 90-day action plan
- Score confidence label

### Security (demo-grade)
- **Streamlit login gate** — custom `auth.py` login form using `bcrypt.checkpw()` directly; blocks all app access; credentials in `auth_config.yaml` (gitignored); session via `st.session_state` (not cookie-based — does not persist across browser refreshes)
- JWT authentication for the optional FastAPI layer (requires `SECRET_KEY` environment variable)
- Password hashing via `bcrypt` directly in `auth.py`; bcrypt also available via `passlib` in `security.py` for FastAPI layer
- Session management in SQLite (portfolio and evaluation data)
- Audit log table (schema present; active logging requires `AuditLogger` wiring)
- **Not suitable for production multi-user deployment without additional hardening**

---

## Architecture

```
ProcureIQ/
├── app.py                    # Main Streamlit application (~13,000 lines; monolith by design for portfolio)
├── auth.py                   # Streamlit login gate (custom bcrypt form, no third-party auth library)
├── auth_config.yaml.example  # Credential template — copy to auth_config.yaml (gitignored) and fill in
├── database.py               # SQLite with WAL mode, session management, discovery cache
├── evaluation.py             # Scoring engine: weighted average, financial health, subcategory weights
├── agents/                   # LLM-backed agents (supplier discovery, intake, sanctions stub)
├── services/                 # Thin orchestration layer over agents
├── taxonomy.py               # 15-category, 179-subcategory procurement taxonomy
├── config.py                 # DIMENSIONS, Kraljic rules, scoring rubrics
├── market_data.py            # Static market data + live API integrations
├── security.py               # Auth utilities (JWT, hashing, audit logger)
├── rfp.py                    # RFP question templates
├── utils.py                  # Helper functions
└── tests/                    # 130 unit tests
```

**Database:** SQLite (WAL mode). Suitable for single-user and demo use. Not suitable for concurrent multi-user production deployment.

**ML/Analytics:** `evaluation.py` includes optional scikit-learn models (`RandomForestRegressor`, `MLPRegressor`) for advanced supplier performance prediction. These are supplementary — the primary scoring mechanism is a transparent weighted average that procurement professionals can audit and explain.

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
   # Edit auth_config.yaml — set real bcrypt-hashed passwords, then restart.
   # See auth_config.yaml.example for instructions on generating bcrypt hashes.
   ```
   Alternatively, use environment variables (useful for hosted deployments):
   ```bash
   export PROCUREIQ_DEMO_USER=demo
   export PROCUREIQ_DEMO_PASS=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())")
   export PROCUREIQ_COOKIE_KEY="some-random-32-char-string"
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

6. **Optional: FastAPI layer** (for API access, requires `SECRET_KEY`)
   ```bash
   uvicorn app:app_api --host 0.0.0.0 --port 8000
   ```

---

## Without API Keys

The app is fully usable without any API keys. When no Anthropic key is configured:
- Supplier discovery returns clearly labeled **illustrative / static data** from a curated knowledge base
- An "AI features unavailable" banner is shown
- All evaluation, scoring, stakeholder analysis, and export features work normally

**Claude is required for AI agents.** The Settings panel supports alternative providers (OpenAI, DeepSeek, Grok) for basic text generation, but supplier discovery, CFO narrative generation, and all tool-use agents only work with Claude. Alternative providers are marked "LIMITED — AGENTS DISABLED" in the UI.

---

## Running Tests

```bash
python -m pytest tests/ -q
```

130 tests covering evaluation logic, financial health scoring (qualitative + EDGAR/XBRL paths), CFO challenge generation, risk flag logic, executive summary construction, and CSV supplier import.

---

## Limitations

See [LIMITATIONS.md](LIMITATIONS.md) for a full list. Key limitations:

- SQLite — not suitable for concurrent multi-user use
- No live ERP data — spend and supplier data entered manually
- Fallback market data is illustrative, not real-time research
- LLM outputs are not validated against external sources
- Financial health scores for public companies are sourced from SEC EDGAR/XBRL; private companies require manual qualitative input — neither is a substitute for credit checks or audited financials
- Sanctions screening is a stub — not a replacement for certified compliance tooling

---

## License

Proprietary — All rights reserved.
