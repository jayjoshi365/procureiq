# rfp.py
# RFP question generation for ProcureIQ

import re
from typing import List, Dict
from config import DEFAULT_RFP_QUESTIONS

# RFP questions by subcategory
RFP_QUESTIONS_BY_SUBCATEGORY = {
    "HRIS / HCM Platform": [
        "What is your system's uptime SLA and how is it measured and reported?",
        "Describe your data migration methodology and who owns data during transition.",
        "How do you handle payroll integration — what APIs and connectors are supported?",
        "What security certifications do you hold (SOC 2 Type II, ISO 27001, FedRAMP)?",
        "How do you manage product roadmap visibility — what is your release cadence?",
        "Describe your implementation methodology and typical time-to-value.",
        "What is your approach to data residency and cross-border data transfer?",
        "How do you handle regulatory changes (e.g., state-level employment law updates)?",
        "Describe your support model — dedicated CSM, SLA tiers, escalation path.",
        "What are your contract renewal terms and rate increase caps?",
    ],
    "Payroll Processing": [
        "What is your error rate on payroll processing and how do you measure it?",
        "How do you handle tax filing for multi-state and international employees?",
        "Describe your SOX compliance controls and audit trail capabilities.",
        "What is your SLA for correcting payroll errors once identified?",
        "How do you handle payroll continuity during a system outage or disaster?",
        "Describe your data security model — encryption at rest and in transit.",
        "What is your implementation timeline for a company of our size?",
        "How do you handle garnishments, levies, and deduction complexity?",
        "What integrations do you support with HRIS and ERP systems?",
        "What are your penalties if you miss a payroll deadline due to your error?",
    ],
    "Cybersecurity (EDR / SIEM / SOC)": [
        "What is your mean time to detect (MTTD) and mean time to respond (MTTR) by incident severity?",
        "Describe your threat intelligence sources and how they feed into detection rules.",
        "What compliance frameworks do you support (SOC 2, NIST CSF, ISO 27001, PCI DSS)?",
        "How do you handle false positive reduction — what is your current false positive rate?",
        "Describe your incident response process for a Severity 1 event.",
        "How do you handle coverage gaps between EDR, SIEM, and SOC functions?",
        "What is your data retention policy for logs and security events?",
        "How do you handle zero-day vulnerabilities — what is your average patch timeline?",
        "Describe your onboarding process and typical time to full visibility.",
        "What SLA remedies apply if you fail to meet response time commitments?",
    ],
    "Cloud Infrastructure (AWS / Azure / GCP)": [
        "What committed spend discounts are available and what are the under-utilization penalties?",
        "Describe your data residency options and sovereign cloud capabilities.",
        "How do you handle egress costs — what is the pricing model for data transfer?",
        "What FinOps tooling do you provide natively for cost visibility and anomaly detection?",
        "Describe your SLA for compute availability and what credits apply for downtime.",
        "How do you handle multi-cloud portability — what lock-in risks should we assess?",
        "What security controls are shared responsibility vs your responsibility?",
        "Describe your enterprise support tiers and response time commitments.",
        "How do you handle capacity reservation for peak workloads?",
        "What are your enterprise agreement term options and renewal flexibility?",
    ],
    "ERP System (SAP / Oracle / etc.)": [
        "Describe your implementation methodology — waterfall, agile, or hybrid?",
        "What is your average implementation timeline for a company of our size and complexity?",
        "How do you handle customizations — and what happens to them during upgrades?",
        "Describe your data migration approach and who owns the migration plan.",
        "What are your go-live support commitments and hypercare period terms?",
        "How do you handle integration with legacy systems during transition?",
        "What is your upgrade cadence and what is the cost impact of major version upgrades?",
        "Describe your licensing model — named user, concurrent, module-based?",
        "What training is included and what are the costs for additional enablement?",
        "How do you handle implementation failure — what contractual remedies exist?",
    ],
    "Truckload (TL) / Full Truckload": [
        "What is your on-time pickup and delivery performance for the past 12 months?",
        "How do you handle capacity shortfalls during peak seasons or market disruptions?",
        "Describe your carrier qualification and safety rating requirements.",
        "What accessorial charges apply and how are they calculated and capped?",
        "How do you handle freight claims — what is your claims ratio and resolution timeline?",
        "Describe your tracking and visibility capabilities and API integration options.",
        "What are your fuel surcharge methodology and adjustment frequency?",
        "How do you handle driver shortages — what backup capacity commitments can you make?",
        "Describe your dedicated vs spot market balance and how you manage our freight.",
        "What are your invoicing audit capabilities and billing accuracy guarantees?",
    ],
    "401(k) / Retirement Platform": [
        "Describe your fiduciary support model — what fiduciary liability do you accept?",
        "What is your investment menu construction process and fee transparency policy?",
        "How do you handle ERISA compliance monitoring and reporting?",
        "Describe your participant education and enrollment experience.",
        "What is your recordkeeping error rate and correction process?",
        "How do you handle plan compliance testing (ADP/ACP, top-heavy)?",
        "What cybersecurity controls protect participant account data?",
        "Describe your transition process from a prior provider.",
        "What are your fee structures — explicit vs revenue sharing?",
        "How do you handle DOL audit support if the plan is selected for review?",
    ],
    "Outside Counsel (Law Firm)": [
        "How do you manage billing transparency — what technology do you use for e-billing?",
        "Describe your conflict of interest check process for new matters.",
        "What alternative fee arrangements (AFAs) are you willing to commit to?",
        "How do you staff matters — what is the partner-to-associate leverage ratio?",
        "Describe your matter management and reporting cadence.",
        "What technology do you use for document review and discovery?",
        "How do you handle staffing continuity if a key attorney leaves?",
        "What is your approach to legal project management on complex matters?",
        "How do you handle budget-to-actual variance — what triggers a conversation?",
        "Describe your DEI data for the team that would staff our matters.",
    ],
    "Contract Manufacturing / OEM": [
        "Describe your capacity planning process and how you handle demand fluctuations.",
        "What quality management system do you operate (ISO 9001, IATF 16949, etc.)?",
        "How do you handle tooling ownership, maintenance, and insurance?",
        "Describe your supply chain transparency — what tier-2 supplier visibility do you provide?",
        "What is your non-conformance reporting and corrective action process?",
        "How do you protect customer IP — describe your confidentiality controls.",
        "What is your geographic footprint and how do you handle business continuity?",
        "Describe your engineering change request (ECR) process and timeline.",
        "What are your lead time commitments and how do you handle expedite requests?",
        "How do you handle price changes for raw material fluctuations?",
    ],
}

# ── RAG corpus — all questions flattened with subcategory metadata ────────────
_RFP_CORPUS: List[Dict] = []
for _sub, _qs in RFP_QUESTIONS_BY_SUBCATEGORY.items():
    for _q in _qs:
        _RFP_CORPUS.append({"question": _q, "subcategory": _sub})
for _q in DEFAULT_RFP_QUESTIONS:
    _RFP_CORPUS.append({"question": _q, "subcategory": "_default"})

# Precompute TF-IDF matrix on module load (fast — ~200 questions)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    corpus_texts = [
        f"{c['subcategory']} {c['question']}"
        for c in _RFP_CORPUS
    ]
    _RFP_TFIDF_VEC = TfidfVectorizer(
        analyzer="word", ngram_range=(1, 2),
        stop_words="english", max_features=2000,
    )
    _RFP_TFIDF_MATRIX = _RFP_TFIDF_VEC.fit_transform(corpus_texts)
    _SKLEARN_AVAILABLE = True
except ImportError:
    _RFP_TFIDF_VEC = None
    _RFP_TFIDF_MATRIX = None
    _SKLEARN_AVAILABLE = False


def get_rfp_questions(subcategory_name: str, context: str = "") -> List[str]:
    """
    RAG-enhanced RFP question retrieval.
    1. If exact subcategory match exists → return those questions (highest precision)
    2. Otherwise use TF-IDF cosine similarity to find the most relevant questions
       from the full corpus, ranked by relevance to subcategory + evaluation context.
    This means every subcategory gets intelligent questions, not just the 9 hardcoded ones.
    """
    # Tier 1: exact match
    if subcategory_name in RFP_QUESTIONS_BY_SUBCATEGORY:
        return RFP_QUESTIONS_BY_SUBCATEGORY[subcategory_name]

    # Tier 2: TF-IDF RAG retrieval
    if _SKLEARN_AVAILABLE and _RFP_TFIDF_VEC is not None and _RFP_TFIDF_MATRIX is not None:
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            query = f"{subcategory_name} {context}".strip()
            query_vec = _RFP_TFIDF_VEC.transform([query])
            scores = cosine_similarity(query_vec, _RFP_TFIDF_MATRIX).flatten()
            # Get top 10 unique questions by score
            ranked_idx = scores.argsort()[::-1]
            seen = set()
            retrieved = []
            for idx in ranked_idx:
                q = _RFP_CORPUS[idx]["question"]
                if q not in seen:
                    seen.add(q)
                    retrieved.append(q)
                if len(retrieved) >= 10:
                    break
            if retrieved:
                return retrieved
        except Exception:
            pass

    # Tier 3: default fallback
    return DEFAULT_RFP_QUESTIONS