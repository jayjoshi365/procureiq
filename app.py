import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests

st.set_page_config(
    page_title="ProcureIQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# STYLES
# =========================================================
st.markdown("""
<style>
    .main {
        background-color: #F5F4F0;
    }
    .block-container {
        max-width: 1480px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3, h4 {
        color: #0C1A2E;
        letter-spacing: -0.02em;
    }
    .hero {
        background: linear-gradient(135deg, #0C1A2E 0%, #172B45 100%);
        border-radius: 18px;
        padding: 1.25rem 1.4rem;
        color: white;
        margin-bottom: 0.8rem;
        box-shadow: 0 12px 28px rgba(12, 26, 46, 0.20);
    }
    .hero-title {
        font-size: 1.95rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }
    .hero-sub {
        font-size: 0.96rem;
        opacity: 0.9;
    }
    .panel {
        background: white;
        border: 1px solid #DDD9D0;
        border-radius: 16px;
        padding: 1rem 1rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
        margin-bottom: 0.9rem;
    }
    .metric-card {
        background: white;
        border: 1px solid #DDD9D0;
        border-radius: 16px;
        padding: 0.9rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
        text-align: center;
        min-height: 104px;
    }
    .metric-label {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #777;
        margin-bottom: 0.25rem;
        font-weight: 700;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0C1A2E;
        line-height: 1.15;
    }
    .metric-sub {
        font-size: 0.83rem;
        color: #777;
        margin-top: 0.2rem;
    }
    .decision-box {
        background: #EDF3FB;
        border-left: 6px solid #0D3B6E;
        border-radius: 12px;
        padding: 0.95rem 1rem;
    }
    .tradeoff-box {
        background: #FBF3DC;
        border-left: 6px solid #9A6F00;
        border-radius: 12px;
        padding: 0.95rem 1rem;
    }
    .risk-box {
        background: #FDF0F0;
        border-left: 6px solid #9E2A2A;
        border-radius: 12px;
        padding: 0.95rem 1rem;
    }
    .good-box {
        background: #EDF7F1;
        border-left: 6px solid #165C35;
        border-radius: 12px;
        padding: 0.95rem 1rem;
    }
    .chip {
        display: inline-block;
        background: #EDEAE3;
        border: 1px solid #DDD9D0;
        border-radius: 999px;
        padding: 0.25rem 0.6rem;
        font-size: 0.76rem;
        color: #2E2E2E;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
        font-weight: 600;
    }
    .small-muted {
        color: #777;
        font-size: 0.87rem;
    }
    .must-have {
        background: #FDF0F0;
        border-left: 6px solid #9E2A2A;
        padding: 0.85rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.65rem;
    }
    .recommended {
        background: #FDF5E8;
        border-left: 6px solid #8C4F00;
        padding: 0.85rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.65rem;
    }
    .nice-have {
        background: #EDF7F1;
        border-left: 6px solid #165C35;
        padding: 0.85rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.65rem;
    }
    .intel-card {
        background: #F8FAFC;
        border: 1px solid #DCE3EA;
        border-radius: 12px;
        padding: 0.85rem 0.95rem;
        margin-top: 0.6rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 8px 8px 0 0;
        padding-left: 14px;
        padding-right: 14px;
        background: #EDEAE3;
        border: none;
        color: #2E2E2E;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        background: #0C1A2E !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONSTANTS
# =========================================================
DIMENSIONS = [
    "Price / TCO",
    "SLA Strength",
    "Execution Risk",
    "Stakeholder Confidence",
    "Strategic Alignment",
    "Innovation Capacity",
    "Relationship Depth",
    "Commercial Flexibility"
]

CURRENT_DIMS = [
    "Price / TCO",
    "SLA Strength",
    "Execution Risk",
    "Stakeholder Confidence"
]

FUTURE_DIMS = [
    "Strategic Alignment",
    "Innovation Capacity",
    "Relationship Depth",
    "Commercial Flexibility"
]

KRALJIC_INFO = {
    "Strategic": {
        "axis": "High Value · High Supply Risk",
        "desc": "Prioritize resilience, governance, executive alignment, and future-fit protections.",
        "color": "#9E2A2A",
        "bg": "#FDF0F0"
    },
    "Leverage": {
        "axis": "High Value · Low Supply Risk",
        "desc": "Use competitive pressure to improve pricing, terms, and performance commitments.",
        "color": "#165C35",
        "bg": "#EDF7F1"
    },
    "Bottleneck": {
        "axis": "Low Value · High Supply Risk",
        "desc": "Protect continuity and operational stability before optimizing price.",
        "color": "#8C4F00",
        "bg": "#FDF5E8"
    },
    "Non-Critical": {
        "axis": "Low Value · Low Supply Risk",
        "desc": "Simplify, standardize, and reduce administration burden.",
        "color": "#777777",
        "bg": "#F5F4F0"
    }
}

POSITION_COLORS = {
    "Champion": "#165C35",
    "Supporter": "#0D3B6E",
    "Neutral": "#777777",
    "Skeptic": "#8C4F00",
    "Blocker": "#9E2A2A"
}

FINANCIAL_FIELDS = {
    "Years in Business": {
        "options": ["<3 years", "3–10 years", "10–25 years", "25+ years"],
        "scores": {"<3 years": 20, "3–10 years": 55, "10–25 years": 80, "25+ years": 95}
    },
    "Ownership Structure": {
        "options": ["Publicly traded", "Private equity-backed", "Founder/private", "Subsidiary"],
        "scores": {"Publicly traded": 85, "Private equity-backed": 55, "Founder/private": 70, "Subsidiary": 80}
    },
    "Revenue Trajectory": {
        "options": ["Growing 15%+", "Growing 5–15%", "Flat", "Declining", "Unknown"],
        "scores": {"Growing 15%+": 95, "Growing 5–15%": 78, "Flat": 55, "Declining": 25, "Unknown": 40}
    },
    "Recent M&A Activity": {
        "options": ["None in 2 years", "Acquired a company", "Being acquired", "Recently spun off"],
        "scores": {"None in 2 years": 85, "Acquired a company": 65, "Being acquired": 35, "Recently spun off": 45}
    },
    "Payment Terms Offered": {
        "options": ["Net 90+", "Net 60", "Net 30", "Net 15 or less"],
        "scores": {"Net 90+": 90, "Net 60": 75, "Net 30": 60, "Net 15 or less": 40}
    },
    "Workforce Changes (12mo)": {
        "options": ["Significant hiring", "Stable", "Minor layoffs <5%", "Major layoffs >10%"],
        "scores": {"Significant hiring": 90, "Stable": 80, "Minor layoffs <5%": 55, "Major layoffs >10%": 25}
    }
}

CATEGORY_RULES = {
    "technology": {
        "type": "Indirect",
        "tag": "Technology / SaaS",
        "requirements": "Define scope, implementation milestones, accountable owners, integration responsibilities, data migration obligations, and acceptance criteria explicitly.",
        "assurance": "Protect continuity through uptime expectations, support coverage, transition assistance, and notice for major platform changes.",
        "quality": "Use measurable SLA language, incident handling, root-cause expectations, and service credits tied to real failure modes.",
        "service": "Clarify support model, severity definitions, response times, escalation paths, and governance cadence.",
        "cost": "Specify user/module/usage pricing logic, renewal caps, pass-through restrictions, and billing transparency.",
        "innovation": "Tie roadmap visibility and future capability support to periodic review obligations."
    },
    "hr": {
        "type": "Indirect",
        "tag": "HR / People Services",
        "requirements": "Clarify deliverables, implementation milestones, employee-impact boundaries, and business ownership.",
        "assurance": "Protect service continuity, support coverage, transition duties, and disruption management affecting employees.",
        "quality": "Focus on service reliability, response quality, issue resolution, and employee experience impact.",
        "service": "Define communication cadence, escalation structure, and account management expectations.",
        "cost": "Clarify pricing structure, renewal controls, and scaling logic as usage grows.",
        "innovation": "Tie improvement commitments to workforce and operating-model evolution."
    },
    "services": {
        "type": "Indirect",
        "tag": "Professional Services",
        "requirements": "Define scope, staffing assumptions, deliverables, role ownership, and acceptance standards tightly.",
        "assurance": "Protect staffing continuity, substitution rules, knowledge transfer, and transition support.",
        "quality": "Use milestone quality, output standards, and remediation rights instead of vague satisfaction language.",
        "service": "Clarify governance, reporting cadence, communication norms, and escalation points.",
        "cost": "Define rate cards, out-of-scope work, change-request logic, and rate-increase boundaries.",
        "innovation": "Require practical problem-solving and improvement contribution over the term."
    },
    "packaging": {
        "type": "Direct",
        "tag": "Packaging / Direct Material",
        "requirements": "Specify tolerances, MOQ, artwork / specification control, tooling assumptions, and approved material standards.",
        "assurance": "Protect continuity through capacity, lead time, interruption notice, and backup supply expectations.",
        "quality": "Use defect thresholds, traceability expectations, corrective action timing, and audit / incoming-quality rights.",
        "service": "Focus on delivery performance, shortage communication, and logistics coordination rather than white-glove support.",
        "cost": "Clarify indexation, resin / commodity pass-through, freight treatment, volume tiers, and surcharge triggers.",
        "innovation": "Emphasize redesign, sustainability options, and cost-down support."
    },
    "manufacturing": {
        "type": "Direct",
        "tag": "Manufacturing / Direct Material",
        "requirements": "Define specs, tolerances, engineering change handling, qualification rules, and production constraints.",
        "assurance": "Protect continuity through capacity, geographic risk visibility, dual-source logic, and lead-time commitments.",
        "quality": "Use non-conformance logic, incoming-quality expectations, and corrective-action timelines.",
        "service": "Focus on shortage response, production communication, and operational escalation.",
        "cost": "Clarify commodity exposure, cost transparency, indexation, and productivity expectations.",
        "innovation": "Use process improvement and manufacturability support as innovation language."
    },
    "logistics": {
        "type": "Indirect",
        "tag": "Logistics / Transportation",
        "requirements": "Define lane scope, equipment needs, reporting requirements, and carrier accountability clearly.",
        "assurance": "Protect continuity through surge coverage, backup options, and disruption response commitments.",
        "quality": "Measure on-time performance, claims, exception handling, and service-recovery logic.",
        "service": "Define dispatch responsiveness, communication cadence, and escalation behavior.",
        "cost": "Clarify fuel treatment, accessorials, lane assumptions, and surcharge triggers.",
        "innovation": "Focus on optimization, visibility, and efficiency gains."
    }
}

# =========================================================
# FREE PUBLIC-COMPANY ENRICHMENT (SEC)
# =========================================================
SEC_HEADERS = {
    "User-Agent": "ProcureIQ demo contact: procurement-demo@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

@st.cache_data(show_spinner=False, ttl=86400)
def get_sec_ticker_map():
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=SEC_HEADERS, timeout=15)
    r.raise_for_status()
    raw = r.json()
    records = []
    for _, item in raw.items():
        records.append({
            "ticker": str(item.get("ticker", "")).upper(),
            "title": item.get("title", ""),
            "cik": str(item.get("cik_str", "")).zfill(10)
        })
    return pd.DataFrame(records)

@st.cache_data(show_spinner=False, ttl=86400)
def get_sec_company_context(ticker):
    ticker = (ticker or "").upper().strip()
    if not ticker:
        return None

    ticker_map = get_sec_ticker_map()
    row = ticker_map[ticker_map["ticker"] == ticker]
    if row.empty:
        return {"found": False, "message": "Ticker not found in SEC public-company list."}

    cik = row.iloc[0]["cik"]
    title = row.iloc[0]["title"]

    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(submissions_url, headers=SEC_HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    filing_dates = filings.get("filingDate", [])

    recent_items = []
    for i in range(min(5, len(forms), len(filing_dates))):
        recent_items.append(f"{forms[i]} ({filing_dates[i]})")

    return {
        "found": True,
        "ticker": ticker,
        "company_name": title,
        "cik": cik,
        "recent_filings": recent_items
    }

# =========================================================
# HELPERS
# =========================================================
def normalize_weights(weight_dict):
    total = sum(weight_dict.values())
    if total == 0:
        return {k: 1 / len(weight_dict) for k in weight_dict}
    return {k: v / total for k, v in weight_dict.items()}

def score_price(price, all_prices):
    if len(all_prices) <= 1:
        return 80
    mn = min(all_prices)
    mx = max(all_prices)
    if mx == mn:
        return 80
    return round(((mx - price) / (mx - mn)) * 100)

def score_sla(v):
    return {"Strong": 92, "Moderate": 60, "Weak": 28}.get(v, 50)

def score_risk(v):
    return {"Low": 92, "Medium": 58, "High": 24}.get(v, 50)

def score_num_1_to_5(v):
    return round((v / 5) * 100)

def compute_financial_health(fin_dict):
    values = []
    for field_name, field_meta in FINANCIAL_FIELDS.items():
        chosen = fin_dict.get(field_name, "")
        values.append(field_meta["scores"].get(chosen, 50) if chosen else 50)
    return round(sum(values) / len(values))

def financial_risk_label(score):
    if score >= 75:
        return "LOW", "#165C35", "#EDF7F1"
    elif score >= 50:
        return "MEDIUM", "#8C4F00", "#FDF5E8"
    else:
        return "HIGH", "#9E2A2A", "#FDF0F0"

def compute_supplier_scores(supplier, all_prices, fin_score):
    base_exec = score_risk(supplier["Execution Risk"])
    fin_adjustment = round(((fin_score - 50) / 50) * 20)
    exec_risk_adjusted = max(0, min(100, base_exec + fin_adjustment))
    return {
        "Price / TCO": score_price(float(supplier["Raw Price"]), all_prices),
        "SLA Strength": score_sla(supplier["SLA Strength"]),
        "Execution Risk": exec_risk_adjusted,
        "Stakeholder Confidence": score_num_1_to_5(supplier["Stakeholder Confidence"]),
        "Strategic Alignment": score_num_1_to_5(supplier["Strategic Alignment"]),
        "Innovation Capacity": score_num_1_to_5(supplier["Innovation Capacity"]),
        "Relationship Depth": score_num_1_to_5(supplier["Relationship Depth"]),
        "Commercial Flexibility": score_num_1_to_5(supplier["Commercial Flexibility"])
    }

def weighted_score(scores, weights):
    return round(sum(scores[d] * weights[d] for d in DIMENSIONS), 1)

def current_fit(scores):
    return round(sum(scores[d] for d in CURRENT_DIMS) / len(CURRENT_DIMS), 1)

def future_fit(scores):
    return round(sum(scores[d] for d in FUTURE_DIMS) / len(FUTURE_DIMS), 1)

def classify_category(category_text):
    c = (category_text or "").lower()
    for keyword, rule in CATEGORY_RULES.items():
        if keyword in c:
            return rule
    return {
        "type": "Mixed / Unclassified",
        "tag": "General Procurement",
        "requirements": "Define scope, deliverables, owners, milestones, and acceptance logic clearly.",
        "assurance": "Document continuity, interruption handling, transition support, and escalation paths.",
        "quality": "Set measurable performance standards and issue-handling expectations.",
        "service": "Clarify support, communication cadence, and governance structure.",
        "cost": "Make pricing structure, caps, invoicing, and pass-through logic visible.",
        "innovation": "Address improvement and future-state support where relevant."
    }

def stakeholder_action(power, interest, position, priority):
    if power >= 8 and position in ["Skeptic", "Blocker"]:
        return f"High-risk stakeholder: prepare a targeted defense tied to {priority.lower()} before the meeting."
    if power >= 7 and interest >= 7:
        return f"Manage closely: secure visible support and align early using a {priority.lower()} narrative."
    if power >= 7 and interest < 7:
        return f"Keep satisfied: bring concise business-impact updates framed around {priority.lower()}."
    if power < 7 and interest >= 7:
        return f"Keep informed: use as an advocate and pressure-test the recommendation through a {priority.lower()} lens."
    return f"Monitor lightly: maintain visibility but do not overinvest unless their stance changes."

def likely_blocker(stake_df):
    candidates = stake_df[
        ((stake_df["Position"] == "Blocker") | (stake_df["Position"] == "Skeptic")) &
        (stake_df["Power"] >= 7)
    ].copy()
    if candidates.empty:
        return None
    candidates["Rank"] = candidates["Power"] * 2 + candidates["Interest"]
    candidates = candidates.sort_values("Rank", ascending=False)
    row = candidates.iloc[0]
    return row

def make_recommendation_text(leader, runner_up, weakest_dim, kraljic):
    gap_text = ""
    if runner_up is not None:
        gap = round(leader["Weighted Score"] - runner_up["Weighted Score"], 1)
        gap_text = f"The lead over the runner-up is **{gap} points**, which supports a recommendation but still means the room may challenge the trade-off."
    else:
        gap_text = "Only one supplier was entered in enough detail to compare."

    return f"""
**Recommended supplier: {leader['Supplier']}**

This supplier leads on weighted score at **{leader['Weighted Score']} / 100** and shows the strongest balance between current execution strength and future-fit partnership potential.

The recommendation aligns to a **{kraljic}** sourcing posture by balancing delivery confidence with longer-term value instead of reducing the decision to price alone.

**Watch-out:** the weakest dimension for the recommended supplier is **{weakest_dim}**. That should become a visible negotiation and mitigation topic before award.

{gap_text}
"""

def make_tradeoff_text(leader, runner_up):
    if not runner_up:
        return "Not enough suppliers were entered to compare trade-offs."

    leader_price = leader["Raw Price"]
    runner_price = runner_up["Raw Price"]
    pct = 0 if runner_price == 0 else round(((leader_price - runner_price) / runner_price) * 100, 1)

    risk_delta = round(leader["Scores"]["Execution Risk"] - runner_up["Scores"]["Execution Risk"], 1)
    stake_delta = round(leader["Scores"]["Stakeholder Confidence"] - runner_up["Scores"]["Stakeholder Confidence"], 1)
    future_delta = round(leader["Future Fit"] - runner_up["Future Fit"], 1)

    direction = "more" if pct >= 0 else "less"
    return (
        f"Compared with **{runner_up['Supplier']}**, the recommendation is **{abs(pct)}% {direction} expensive**, "
        f"but improves execution-risk score by **{risk_delta} points**, stakeholder-confidence score by **{stake_delta} points**, "
        f"and future-fit score by **{future_delta} points**."
    )

def block_risk_text(blocker_row, leader_name):
    if blocker_row is None:
        return f"No clear high-power blocker is visible yet. The current recommendation for **{leader_name}** looks defendable if the room stays on business criteria."
    return (
        f"The most likely block comes from **{blocker_row['Name']}** ({blocker_row['Role']}). "
        f"They are a **{blocker_row['Position']}** with high power and care most about **{blocker_row['Priority']}**. "
        f"If the recommendation is challenged, expect the conversation to pivot there first."
    )

def alt_supplier_text(leader, runner_up):
    if not runner_up:
        return "No runner-up comparison available."
    return (
        f"If you choose **{runner_up['Supplier']}** instead of **{leader['Supplier']}**, you may gain on one variable like price or flexibility "
        f"but weaken the overall defense narrative. The burden shifts from 'this is the strongest choice' to 'this compromise is worth it.'"
    )

def default_negotiation_points(kraljic, category_rule, weakest_dim):
    points = []
    if kraljic == "Strategic":
        points = [
            "Protect governance, resilience, and executive escalation before chasing cosmetic commercial wins.",
            f"Use the negotiation to directly close the weakest dimension: **{weakest_dim}**.",
            "Push for roadmap visibility and future capability commitments."
        ]
    elif kraljic == "Leverage":
        points = [
            "Use competition to improve pricing, rebate, and benchmark language.",
            "Do not leave annual increase logic vague.",
            "Strengthen service and reporting while leverage is on your side."
        ]
    elif kraljic == "Bottleneck":
        points = [
            "Do not sacrifice continuity protections to save cost.",
            "Prioritize interruption handling, notice periods, and escalation rights.",
            "Use the negotiation to reduce operational fragility."
        ]
    else:
        points = [
            "Keep terms simple and easy to administer.",
            "Avoid unnecessary customization.",
            "Focus on clear pricing and easy renewal / exit control."
        ]
    points.append(f"Category lens: this is **{category_rule['tag']}**, so negotiation should also reflect category-specific protections, not only generic sourcing logic.")
    return points

def category_raqsci(kraljic, category_rule):
    return {
        "Requirements": {
            "must": category_rule["requirements"],
            "recommended": f"Use the {kraljic.lower()} posture to tie requirements tightly to accountability and acceptance logic.",
            "nice": "Add review checkpoints for evolving business needs."
        },
        "Assurance of Supply": {
            "must": category_rule["assurance"],
            "recommended": f"In a {kraljic.lower()} category, define interruption handling and escalation in business terms, not vague generalities.",
            "nice": "Request recurring continuity reviews."
        },
        "Quality": {
            "must": category_rule["quality"],
            "recommended": "Use recurring scorecards or measurable review checkpoints.",
            "nice": "Include improvement expectations over the term."
        },
        "Service": {
            "must": category_rule["service"],
            "recommended": "Make governance and escalation visible in the contract itself.",
            "nice": "Request named contacts or support structure where useful."
        },
        "Cost": {
            "must": category_rule["cost"],
            "recommended": f"Align cost language to the {kraljic.lower()} strategy instead of treating price as a standalone line item.",
            "nice": "Add review or benchmark rights where practical."
        },
        "Innovation": {
            "must": category_rule["innovation"],
            "recommended": "Tie future-state value to visible review or roadmap commitments.",
            "nice": "Include annual improvement sessions."
        }
    }

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## ProcureIQ Setup")
    event_name = st.text_input("Sourcing Event Name", "HR Technology Platform Renewal")
    category = st.text_input("Category", "HR Technology")
    kraljic = st.selectbox("Kraljic Position", ["Strategic", "Leverage", "Bottleneck", "Non-Critical"])

    st.markdown("### Scope")
    num_suppliers = st.slider("Number of Suppliers", 2, 4, 3)
    num_stakeholders = st.slider("Number of Stakeholders", 2, 8, 4)

    st.markdown("### Weighting")
    st.caption("These weights influence the recommendation.")
    weights_raw = {
        "Price / TCO": st.slider("Weight: Price / TCO", 1, 10, 7),
        "SLA Strength": st.slider("Weight: SLA Strength", 1, 10, 8),
        "Execution Risk": st.slider("Weight: Execution Risk", 1, 10, 9),
        "Stakeholder Confidence": st.slider("Weight: Stakeholder Confidence", 1, 10, 8),
        "Strategic Alignment": st.slider("Weight: Strategic Alignment", 1, 10, 8),
        "Innovation Capacity": st.slider("Weight: Innovation Capacity", 1, 10, 6),
        "Relationship Depth": st.slider("Weight: Relationship Depth", 1, 10, 6),
        "Commercial Flexibility": st.slider("Weight: Commercial Flexibility", 1, 10, 7),
    }

weights = normalize_weights(weights_raw)
category_rule = classify_category(category)

# =========================================================
# HERO
# =========================================================
st.markdown(f"""
<div class="hero">
    <div class="hero-title">📊 ProcureIQ</div>
    <div class="hero-sub">
        A procurement decision workspace built to answer three questions fast: which supplier should we choose, how do we defend it, and where will the decision get blocked?
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
tab_overview, tab_suppliers, tab_stakeholders, tab_contracts, tab_meeting, tab_negotiation = st.tabs(
    ["Overview", "Suppliers", "Stakeholders", "Contracts", "Meeting Prep", "Negotiation"]
)

# =========================================================
# SUPPLIER INPUTS
# =========================================================
suppliers = []

with tab_suppliers:
    st.markdown("### Supplier Inputs")
    st.markdown('<div class="small-muted">Designed for both indirect services and direct-material decisions. Public-company enrichment is optional and only works when you enter a valid ticker.</div>', unsafe_allow_html=True)

    for i in range(num_suppliers):
        with st.expander(f"Supplier {i+1}", expanded=(i == 0)):
            left, right = st.columns([1.1, 0.9])

            with left:
                name = st.text_input("Supplier Name", f"Supplier {i+1}", key=f"name_{i}")
                ticker = st.text_input("Public Ticker (Optional)", "", key=f"ticker_{i}", help="Use only for public companies, e.g. ORCL, IBM, ADBE.")
                raw_price = st.number_input("Quoted Price ($)", min_value=0.0, value=float(1000000 + i * 150000), step=1000.0, key=f"raw_price_{i}")
                notes = st.text_area("Notes", "Add concerns, differentiators, or negotiation observations.", key=f"notes_{i}", height=95)

            with right:
                sla = st.selectbox("SLA Strength", ["Strong", "Moderate", "Weak"], index=1, key=f"sla_{i}")
                risk = st.selectbox("Execution Risk", ["Low", "Medium", "High"], index=1, key=f"risk_{i}")
                stake = st.slider("Stakeholder Confidence", 1, 5, 3, key=f"stake_{i}")
                strategic = st.slider("Strategic Alignment", 1, 5, 3, key=f"strategic_{i}")
                innovation = st.slider("Innovation Capacity", 1, 5, 3, key=f"innovation_{i}")
                relationship = st.slider("Relationship Depth", 1, 5, 3, key=f"relationship_{i}")
                flexibility = st.slider("Commercial Flexibility", 1, 5, 3, key=f"flexibility_{i}")

            st.markdown("#### Financial Health")
            fin_col1, fin_col2 = st.columns(2)
            fin_data = {}
            field_names = list(FINANCIAL_FIELDS.keys())
            half = len(field_names) // 2

            for idx, field_name in enumerate(field_names):
                target_col = fin_col1 if idx < half else fin_col2
                with target_col:
                    fin_data[field_name] = st.selectbox(
                        field_name,
                        [""] + FINANCIAL_FIELDS[field_name]["options"],
                        key=f"fin_{field_name}_{i}"
                    )

            sec_context = None
            if ticker.strip():
                try:
                    sec_context = get_sec_company_context(ticker.strip())
                except Exception as e:
                    sec_context = {"found": False, "message": f"SEC lookup failed: {e}"}

            if ticker.strip():
                st.markdown("#### Public Company Context")
                if sec_context and sec_context.get("found"):
                    recent_filings = sec_context.get("recent_filings", [])
                    filings_text = "<br>".join(recent_filings) if recent_filings else "No recent filing list available."
                    st.markdown(f"""
                    <div class="intel-card">
                        <strong>{sec_context['company_name']}</strong> ({sec_context['ticker']})<br>
                        <span class="small-muted">CIK: {sec_context['cik']}</span><br><br>
                        <strong>Recent SEC filing activity</strong><br>
                        {filings_text}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    msg = sec_context.get("message", "No SEC context found.") if sec_context else "No SEC context found."
                    st.markdown(f"""
                    <div class="intel-card">
                        <strong>Public company context unavailable</strong><br>
                        <span class="small-muted">{msg}</span>
                    </div>
                    """, unsafe_allow_html=True)

            suppliers.append({
                "Supplier": name,
                "Ticker": ticker.strip().upper(),
                "Raw Price": raw_price,
                "Notes": notes,
                "SLA Strength": sla,
                "Execution Risk": risk,
                "Stakeholder Confidence": stake,
                "Strategic Alignment": strategic,
                "Innovation Capacity": innovation,
                "Relationship Depth": relationship,
                "Commercial Flexibility": flexibility,
                "Financial Inputs": fin_data,
                "SEC Context": sec_context
            })

if not suppliers:
    for i in range(num_suppliers):
        suppliers.append({
            "Supplier": f"Supplier {i+1}",
            "Ticker": "",
            "Raw Price": float(1000000 + i * 150000),
            "Notes": "",
            "SLA Strength": "Moderate",
            "Execution Risk": "Medium",
            "Stakeholder Confidence": 3,
            "Strategic Alignment": 3,
            "Innovation Capacity": 3,
            "Relationship Depth": 3,
            "Commercial Flexibility": 3,
            "Financial Inputs": {field: "" for field in FINANCIAL_FIELDS},
            "SEC Context": None
        })

all_prices = [float(s["Raw Price"]) for s in suppliers]

scored_suppliers = []
for s in suppliers:
    fin_score = compute_financial_health(s["Financial Inputs"])
    scores = compute_supplier_scores(s, all_prices, fin_score)
    total = weighted_score(scores, weights)
    current = current_fit(scores)
    future = future_fit(scores)
    risk_label, risk_color, risk_bg = financial_risk_label(fin_score)

    scored_suppliers.append({
        "Supplier": s["Supplier"],
        "Ticker": s["Ticker"],
        "Notes": s["Notes"],
        "Raw Price": s["Raw Price"],
        "SEC Context": s["SEC Context"],
        "Financial Health": fin_score,
        "Financial Risk Label": risk_label,
        "Financial Risk Color": risk_color,
        "Financial Risk BG": risk_bg,
        "Scores": scores,
        "Weighted Score": total,
        "Current Fit": current,
        "Future Fit": future
    })

ranked = sorted(scored_suppliers, key=lambda x: x["Weighted Score"], reverse=True)
leader = ranked[0]
runner_up = ranked[1] if len(ranked) > 1 else None
leader_weakest_dim = min(DIMENSIONS, key=lambda d: leader["Scores"][d])

# =========================================================
# STAKEHOLDER INPUTS
# =========================================================
stakeholder_rows = []
with tab_stakeholders:
    st.markdown("### Stakeholder Mapping")
    st.markdown('<div class="small-muted">The goal here is not just to map who is involved. It is to predict where alignment breaks down.</div>', unsafe_allow_html=True)

    for i in range(num_stakeholders):
        with st.expander(f"Stakeholder {i+1}", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                s_name = st.text_input("Stakeholder Name", f"Stakeholder {i+1}", key=f"stake_name_{i}")
                title = st.selectbox(
                    "Role / Title",
                    ["CPO", "CFO", "COO", "CIO", "VP Procurement", "VP Finance",
                     "Business Partner", "Legal Counsel", "Procurement Analyst",
                     "Category Manager", "Director", "Manager", "Other"],
                    key=f"stake_title_{i}"
                )
            with c2:
                power = st.slider("Power (Influence Level)", 1, 10, 6, key=f"stake_power_{i}")
                interest = st.slider("Interest (Engagement Level)", 1, 10, 6, key=f"stake_interest_{i}")
            with c3:
                position = st.selectbox("Position on Decision", ["Champion", "Supporter", "Neutral", "Skeptic", "Blocker"], key=f"stake_position_{i}")
                priority = st.selectbox(
                    "Primary Priority",
                    ["Cost / Savings", "Risk Reduction", "Quality / SLA", "Speed", "Innovation", "Compliance / Legal", "Supplier Relationship"],
                    key=f"stake_priority_{i}"
                )

            stakeholder_rows.append({
                "Name": s_name,
                "Role": title,
                "Power": power,
                "Interest": interest,
                "Position": position,
                "Priority": priority,
                "Action": stakeholder_action(power, interest, position, priority)
            })

if not stakeholder_rows:
    for i in range(num_stakeholders):
        stakeholder_rows.append({
            "Name": f"Stakeholder {i+1}",
            "Role": "Manager",
            "Power": 6,
            "Interest": 6,
            "Position": "Neutral",
            "Priority": "Cost / Savings",
            "Action": stakeholder_action(6, 6, "Neutral", "Cost / Savings")
        })

stake_df = pd.DataFrame(stakeholder_rows)
blocker = likely_blocker(stake_df)

# =========================================================
# OVERVIEW
# =========================================================
with tab_overview:
    st.markdown("### Decision Snapshot")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Recommended Supplier</div>
            <div class="metric-value" style="font-size:1.08rem;">{leader['Supplier']}</div>
            <div class="metric-sub">{event_name}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Overall Score</div>
            <div class="metric-value">{leader['Weighted Score']}</div>
            <div class="metric-sub">weighted result</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current Fit</div>
            <div class="metric-value">{leader['Current Fit']}</div>
            <div class="metric-sub">execution strength</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Future Fit</div>
            <div class="metric-value">{leader['Future Fit']}</div>
            <div class="metric-sub">trajectory</div>
        </div>
        """, unsafe_allow_html=True)

    row1, row2 = st.columns([1.15, 0.85])

    with row1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Recommendation")
        st.markdown(f'<div class="decision-box">{make_recommendation_text(leader, runner_up, leader_weakest_dim, kraljic)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Radar + Recommendation View")
        fig = go.Figure()
        for s in ranked:
            vals = [s["Scores"][d] for d in DIMENSIONS]
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=DIMENSIONS + [DIMENSIONS[0]],
                fill="toself",
                name=s["Supplier"]
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=520,
            margin=dict(l=25, r=25, t=25, b=25),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="small-muted">This is the screenshot worth sharing: recommendation plus trade-off, supported by a shape that shows where the winner is strong and where it is vulnerable.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Supplier Ranking")
        ranking_df = pd.DataFrame([
            {
                "Supplier": s["Supplier"],
                "Overall": s["Weighted Score"],
                "Current": s["Current Fit"],
                "Future": s["Future Fit"],
                "Financial Health": s["Financial Health"]
            } for s in ranked
        ])
        st.dataframe(ranking_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with row2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Trade-off")
        st.markdown(f'<div class="tradeoff-box">{make_tradeoff_text(leader, runner_up)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Block Risk")
        st.markdown(f'<div class="risk-box">{block_risk_text(blocker, leader["Supplier"])}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Category Reality")
        kinfo = KRALJIC_INFO[kraljic]
        st.markdown(f"""
        <div class="good-box">
            <strong>{kraljic}</strong> · {kinfo['axis']}<br><br>
            {kinfo['desc']}<br><br>
            <strong>Detected category type:</strong> {category_rule['type']}<br>
            <strong>Detected lens:</strong> {category_rule['tag']}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### What Drives the Result")
        for d in DIMENSIONS:
            st.markdown(f'<span class="chip">{d}: {round(weights[d] * 100, 1)}%</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# STAKEHOLDERS
# =========================================================
with tab_stakeholders:
    st.markdown("### Stakeholder Strategy Output")

    c1, c2 = st.columns([1.0, 1.0])

    with c1:
        fig_scatter = px.scatter(
            stake_df,
            x="Interest",
            y="Power",
            color="Position",
            text="Name",
            color_discrete_map=POSITION_COLORS,
            height=520
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(
            xaxis=dict(range=[0, 10.5]),
            yaxis=dict(range=[0, 10.5]),
            margin=dict(l=20, r=20, t=20, b=20),
            shapes=[
                dict(type="line", x0=5.5, x1=5.5, y0=0, y1=10.5, line=dict(dash="dash")),
                dict(type="line", x0=0, x1=10.5, y0=5.5, y1=5.5, line=dict(dash="dash"))
            ]
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c2:
        st.markdown("#### Internal Alignment Strategy")
        for _, row in stake_df.iterrows():
            color = POSITION_COLORS.get(row["Position"], "#777777")
            st.markdown(f"""
            <div class="stake-card" style="border-left:6px solid {color};">
                <strong>{row['Name']}</strong> — {row['Role']}<br>
                <span class="small-muted">Position: {row['Position']} | Priority: {row['Priority']}</span><br><br>
                {row['Action']}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### Stakeholder Table")
    st.dataframe(stake_df, use_container_width=True, hide_index=True)

# =========================================================
# CONTRACTS
# =========================================================
with tab_contracts:
    st.markdown("### RAQSCI Contract Guidance")
    st.markdown('<div class="small-muted">This is category-aware and works for indirect services and direct-material decisions. It is still a framework layer, not legal redlining automation.</div>', unsafe_allow_html=True)

    contract_set = category_raqsci(kraljic, category_rule)

    for section_name, content in contract_set.items():
        with st.expander(section_name, expanded=(section_name == "Requirements")):
            st.markdown(f'<div class="must-have"><strong>★ Must-have</strong><br>{content["must"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="recommended"><strong>Strongly recommended</strong><br>{content["recommended"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="nice-have"><strong>Nice to have</strong><br>{content["nice"]}</div>', unsafe_allow_html=True)

    st.markdown("#### What this still does not solve")
    st.markdown("""
- detailed legal redlining
- should-cost modeling
- supplier capacity and plant-level constraints
- commodity index logic by region
- deep live risk intelligence for private suppliers
""")

# =========================================================
# MEETING PREP
# =========================================================
with tab_meeting:
    st.markdown("### Meeting Prep")
    st.markdown("""
    <div class="panel">
        <strong>Public version</strong><br><br>
        This tab stays visible so the product feels complete, but it does not use paid AI.
        In a private demo, this section can generate:
        <ul>
            <li>opening statement for the recommendation meeting</li>
            <li>role-based pushback responses</li>
            <li>which champions to activate first</li>
            <li>one-sentence reset language if the room turns against the recommendation</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### What this tab is really for")
    st.markdown("""
- turning a recommendation into a room-ready narrative
- pre-empting the CFO / Legal / IT objection
- deciding who needs to speak before procurement speaks
- reducing the chance that the best supplier loses politically
""")

# =========================================================
# NEGOTIATION
# =========================================================
with tab_negotiation:
    st.markdown("### Negotiation Position")

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f"#### Recommended Supplier: {leader['Supplier']}")
    for point in default_negotiation_points(kraljic, category_rule, leader_weakest_dim):
        st.markdown(f"- {point}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### If You Pick the Runner-Up Instead")
    st.write(alt_supplier_text(leader, runner_up))
    st.markdown("</div>", unsafe_allow_html=True)

    if leader.get("SEC Context") and leader["SEC Context"].get("found"):
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Public Company Context for Recommended Supplier")
        recent_filings = leader["SEC Context"].get("recent_filings", [])
        if recent_filings:
            for item in recent_filings:
                st.markdown(f"- {item}")
        else:
            st.markdown("No recent filing items displayed.")
        st.markdown('<div class="small-muted">Use this as supporting public-company context, not as a substitute for real supplier due diligence.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)