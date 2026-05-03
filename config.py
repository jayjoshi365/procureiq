# config.py
# Constants and configuration for ProcureIQ

DIMENSIONS = [
    "Price / TCO",
    "SLA Strength",
    "Execution Risk",
    "Stakeholder Confidence",
    "Strategic Alignment",
    "Innovation Capacity",
    "Relationship Depth",
    "Commercial Flexibility",
    "ESG / Sustainability",
    "Supplier Diversity",
]

CURRENT_DIMS = [
    "Price / TCO",
    "SLA Strength",
    "Execution Risk",
    "Stakeholder Confidence",
]

FUTURE_DIMS = [
    "Strategic Alignment",
    "Innovation Capacity",
    "Relationship Depth",
    "Commercial Flexibility",
    "ESG / Sustainability",
    "Supplier Diversity",
]

# ── Per-subcategory scoring rubrics ───────────────────────────────────────────
# For each dimension, defines what "Strong/High", "Moderate/Medium", "Weak/Low" means
# in the context of each core subcategory. Eliminates false precision from opinion sliders.
SCORING_RUBRICS = {
    "HRIS / HCM Platform": {
        "SLA Strength": {
            "Strong":   "Documented 99.9%+ uptime SLA with service credit schedule, root-cause reporting within 24h, and dedicated incident commander during pay-cycle windows.",
            "Moderate": "99.5% uptime SLA with quarterly reporting; credits available but not automatic; no payroll-window priority.",
            "Weak":     "General uptime language only; no credits defined; no distinction between business-critical and non-critical downtime.",
        },
        "Execution Risk": {
            "Low":    "Supplier has completed 5+ implementations of comparable size in 12 months; named PM assigned; go-live playbook documented.",
            "Medium": "2–4 comparable implementations; implementation methodology documented but PM not yet assigned.",
            "High":   "First implementation of this size/complexity; implementation plan is generic; no dedicated PM.",
        },
        "ESG / Sustainability": {
            "Strong":   "Published annual sustainability report (GRI/SASB); Science-Based Targets committed; supplier code of conduct with ESG audit rights.",
            "Moderate": "Internal ESG policy exists; some public reporting; no third-party verification.",
            "Weak":     "No published ESG commitments; no supplier code of conduct; no audit rights.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified diverse-owned (WBENC, NMSDC, VOSB, or equivalent) OR has documented Tier 2 diversity spend reporting with >10% diverse sub-spend.",
            "Moderate": "Supplier diversity policy exists; tracks diverse spend but does not report Tier 2.",
            "Weak":     "No supplier diversity program; no tracking of diverse spend.",
        },
    },
    "Payroll Processing": {
        "SLA Strength": {
            "Strong":   "Documented error rate <0.01% per pay cycle; penalty clause for late payroll; 4-hour response for critical issues during pay runs.",
            "Moderate": "Error rate tracked but not contractually committed; standard support SLA; no pay-run priority tier.",
            "Weak":     "No error rate data provided; standard support only; no differentiated response for payroll failures.",
        },
        "Execution Risk": {
            "Low":    "SOX-compliant with annual audit evidence; disaster recovery tested quarterly; parallel run offered for transition.",
            "Medium": "SOX controls in place; DR plan documented but not recently tested; parallel run on request.",
            "High":   "No SOX audit evidence; DR plan not tested; no parallel run capability.",
        },
        "ESG / Sustainability": {
            "Strong":   "ISO 14001 certified; Science-Based Targets; net-zero roadmap published.",
            "Moderate": "Sustainability policy published; no third-party certification.",
            "Weak":     "No sustainability disclosures.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified diverse-owned OR >15% diverse Tier 2 spend with annual reporting.",
            "Moderate": "Tracks diverse spend; no Tier 2 reporting.",
            "Weak":     "No diversity tracking.",
        },
    },
    "Cybersecurity (EDR / SIEM / SOC)": {
        "SLA Strength": {
            "Strong":   "MTTD <15min and MTTR <4h for Sev-1 contractually committed; financial remedies for SLA breach; named incident commander.",
            "Moderate": "MTTD/MTTR targets stated but not contractually binding; remedies advisory only.",
            "Weak":     "No MTTD/MTTR commitments; best-effort response language only.",
        },
        "Execution Risk": {
            "Low":    "SOC 2 Type II + ISO 27001 current; NIST CSF mapping documented; 24/7 analyst coverage with backup team.",
            "Medium": "SOC 2 Type II in progress or expired; partial NIST alignment; on-call coverage with gaps.",
            "High":   "No SOC 2; no formal framework mapping; business-hours coverage only.",
        },
        "ESG / Sustainability": {
            "Strong":   "CDP disclosure; renewable energy commitment >50%; supply chain ESG audit program.",
            "Moderate": "Internal sustainability goals; partial renewable energy; no CDP.",
            "Weak":     "No ESG disclosures.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified diverse-owned OR documented >10% diverse Tier 2 spend.",
            "Moderate": "Diversity policy; spend tracked but not reported.",
            "Weak":     "No diversity program.",
        },
    },
    "Cloud Infrastructure (AWS / Azure / GCP)": {
        "SLA Strength": {
            "Strong":   "99.99% compute SLA with auto-credits; multi-region failover included; dedicated TAM with 15-min Sev-1 response.",
            "Moderate": "99.9% SLA; credits require manual claim; shared TAM; 1-hour Sev-1 response.",
            "Weak":     "Standard 99.5% SLA; credit process manual and disputed; support tier basic.",
        },
        "Execution Risk": {
            "Low":    "Proven enterprise migration team; dedicated migration architect; rollback plan documented; no egress surprise history.",
            "Medium": "Migration methodology exists; shared team; rollback possible but not pre-tested.",
            "High":   "First migration of this size; no dedicated team; rollback not planned.",
        },
        "ESG / Sustainability": {
            "Strong":   "100% renewable energy matched (RECs or PPAs); net-zero commitment with Science-Based Target; public carbon dashboard.",
            "Moderate": "Partial renewable match; carbon neutral claims without SBT verification.",
            "Weak":     "No renewable energy commitment; no public carbon data.",
        },
        "Supplier Diversity": {
            "Strong":   "Marketplace and partner ecosystem includes certified diverse ISVs; procurement team tracks diverse Tier 2 spend.",
            "Moderate": "Diversity goals stated; Tier 2 not tracked.",
            "Weak":     "No diversity commitments.",
        },
    },
    "ERP System (SAP / Oracle / etc.)": {
        "SLA Strength": {
            "Strong":   "Month-end close window guaranteed uptime; named functional SME per module; remedies for implementation delays.",
            "Moderate": "Standard SaaS uptime SLA; functional support shared; delay remedies advisory.",
            "Weak":     "Best-effort SLA; no module-specific support; no delay remedies.",
        },
        "Execution Risk": {
            "Low":    "Fixed-fee implementation with scope guardrails; named SI with 10+ comparable go-lives; hypercare period ≥90 days.",
            "Medium": "T&M implementation; SI has 3–5 comparable go-lives; hypercare 30 days.",
            "High":   "T&M with no cap; SI first implementation of this complexity; hypercare undefined.",
        },
        "ESG / Sustainability": {
            "Strong":   "Published CSRD-ready sustainability module; GRI reporting; Science-Based Target.",
            "Moderate": "Sustainability reporting available as add-on; no SBT.",
            "Weak":     "No sustainability reporting capability.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified WBENC or NMSDC; SI partner program includes diverse implementation partners.",
            "Moderate": "Diversity goals stated; diverse SI partners not formally tracked.",
            "Weak":     "No diversity program.",
        },
    },
    "Truckload (TL) / Full Truckload": {
        "SLA Strength": {
            "Strong":   "On-time pickup and delivery >97% with financial penalty for failure; claims ratio <0.5% with 30-day resolution SLA.",
            "Moderate": "OTP/OTD >93%; claims ratio <1.5%; 60-day resolution; no penalty clause.",
            "Weak":     "OTP/OTD not contractually committed; claims process undocumented.",
        },
        "Execution Risk": {
            "Low":    "Surge capacity commitment in writing; backup carrier pool ≥3; driver shortage plan documented.",
            "Medium": "Surge capacity mentioned but not committed; 1 backup carrier; no driver contingency.",
            "High":   "No surge commitment; no backup; capacity availability discretionary.",
        },
        "ESG / Sustainability": {
            "Strong":   "SmartWay certified; EV/CNG fleet >20%; GHG Scope 1 reported annually; emissions per mile tracked.",
            "Moderate": "SmartWay partner; partial GHG reporting; no fleet electrification commitment.",
            "Weak":     "No SmartWay; no GHG reporting.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified WBENC/NMSDC/VOSB carrier OR ≥15% diverse sub-carrier spend tracked annually.",
            "Moderate": "Diversity goal stated; no sub-carrier tracking.",
            "Weak":     "No diversity program.",
        },
    },
    "401(k) / Retirement Platform": {
        "SLA Strength": {
            "Strong":   "Named fiduciary (3(21) or 3(38)) with documented liability acceptance; recordkeeping error rate <0.01%; ERISA audit support included.",
            "Moderate": "Co-fiduciary role; error rate tracked but not contractually committed; ERISA audit support on request.",
            "Weak":     "No fiduciary role accepted; error rate not disclosed; audit support ad hoc.",
        },
        "Execution Risk": {
            "Low":    "SSAE 18 SOC 1 Type II current; cybersecurity framework (NIST) mapped; DOL audit defense included in fee.",
            "Medium": "SOC 1 in progress; partial NIST; DOL support billable.",
            "High":   "No SOC 1; no NIST mapping; DOL audit not supported.",
        },
        "ESG / Sustainability": {
            "Strong":   "ESG investment options available with proxy voting transparency; UNPRI signatory; annual sustainability report.",
            "Moderate": "Some ESG fund options; proxy voting policy exists but not published.",
            "Weak":     "No ESG investment options; no proxy voting transparency.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified diverse-owned recordkeeper OR ≥15% diverse Tier 2 spend with annual report.",
            "Moderate": "Diversity policy; no Tier 2 tracking.",
            "Weak":     "No diversity program.",
        },
    },
    "Outside Counsel (Law Firm)": {
        "SLA Strength": {
            "Strong":   "Alternative Fee Arrangement (AFA) committed for ≥50% of matter types; budget-to-actual variance reported monthly; e-billing platform used.",
            "Moderate": "AFA available on request; quarterly budget review; e-billing capable but not default.",
            "Weak":     "Hourly only; no budget commitment; no e-billing.",
        },
        "Execution Risk": {
            "Low":    "Named partner guarantee with key-person coverage; conflict check automated; matter management platform with real-time reporting.",
            "Medium": "Primary partner named; conflicts checked manually; reporting on request.",
            "High":   "Team staffing flexible; conflicts checked informally; reporting ad hoc.",
        },
        "ESG / Sustainability": {
            "Strong":   "Published DEI scorecard >30% diverse attorneys on team; pro bono >3% billable hours; GHG reporting published.",
            "Moderate": "DEI goals published; pro bono program; no GHG.",
            "Weak":     "No DEI data shared; no pro bono commitment; no sustainability disclosures.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified WBENC/NAMWOLF member firm OR ≥40% women/minority equity partners on matter team.",
            "Moderate": "DEI hiring goals; diverse attorneys available but not guaranteed.",
            "Weak":     "No diversity commitments for staffing.",
        },
    },
    "Contract Manufacturing / OEM": {
        "SLA Strength": {
            "Strong":   "ISO 9001 / IATF 16949 certified; defect rate <500 PPM contractually; corrective action within 24h; on-time delivery >98%.",
            "Moderate": "ISO 9001 only; defect rate tracked; corrective action within 5 days; OTD >95%.",
            "Weak":     "No certification; defect rate not disclosed; corrective action timeline undefined.",
        },
        "Execution Risk": {
            "Low":    "Dual-source raw material; geographic redundancy across 2+ regions; business continuity plan tested annually.",
            "Medium": "Single-source with backup supplier identified; 1 geographic location; BCP documented but untested.",
            "High":   "Single-source raw material; single site; no BCP.",
        },
        "ESG / Sustainability": {
            "Strong":   "RBA/EICC member; conflict minerals (3TG) reporting (CMRT); Science-Based Target; third-party supplier audits.",
            "Moderate": "Conflict minerals policy; some environmental reporting; no SBT.",
            "Weak":     "No conflict minerals reporting; no environmental commitments.",
        },
        "Supplier Diversity": {
            "Strong":   "Certified diverse manufacturer (NMSDC/WBENC) OR ≥15% diverse Tier 2 material suppliers tracked.",
            "Moderate": "Diversity policy; no Tier 2 tracking.",
            "Weak":     "No diversity program.",
        },
    },
}

# ── AI Governance Disclosure ──────────────────────────────────────────────────
AI_DISCLOSURE_BANNER = (
    "⚠ AI-Generated Content — This analysis was produced by Claude AI (Anthropic) "
    "using data you entered. It reflects your inputs, not independently verified facts. "
    "It is not a substitute for legal, financial, or professional procurement judgment. "
    "Review all outputs before use in a business decision. EU AI Act Art. 52 transparency notice."
)

POSITION_COLORS = {
    "Champion": "#22C55E",
    "Supporter": "#3B82F6",
    "Neutral": "#94A3B8",
    "Skeptic": "#F59E0B",
    "Blocker": "#EF4444",
}

KRALJIC_INFO = {
    "Strategic": {
        "axis": "High Value · High Supply Risk",
        "desc": "Prioritize resilience, governance, executive alignment, and future-fit protections.",
        "color": "#EF4444",
        "bg": "#1A0A0A",
        "accent": "#FF6B6B",
    },
    "Leverage": {
        "axis": "High Value · Low Supply Risk",
        "desc": "Use competitive pressure to improve pricing, terms, and performance commitments.",
        "color": "#22C55E",
        "bg": "#0A1A0A",
        "accent": "#4ADE80",
    },
    "Bottleneck": {
        "axis": "Low Value · High Supply Risk",
        "desc": "Protect continuity and operational stability before optimizing price.",
        "color": "#F59E0B",
        "bg": "#1A1200",
        "accent": "#FCD34D",
    },
    "Non-Critical": {
        "axis": "Low Value · Low Supply Risk",
        "desc": "Simplify, standardize, and reduce administration burden.",
        "color": "#94A3B8",
        "bg": "#0F1520",
        "accent": "#CBD5E1",
    },
}

USE_CASE_TEMPLATES = {
    "Neutral Template": {
        "category": "",
        "kraljic": "Strategic",
        "weights": {
            "Price / TCO": 7,
            "SLA Strength": 8,
            "Execution Risk": 9,
            "Stakeholder Confidence": 8,
            "Strategic Alignment": 8,
            "Innovation Capacity": 6,
            "Relationship Depth": 6,
            "Commercial Flexibility": 7,
            "ESG / Sustainability": 6,
            "Supplier Diversity": 5,
        },
    },
    "IT Sourcing": {
        "category": "IT Technology",
        "kraljic": "Strategic",
        "weights": {
            "Price / TCO": 6,
            "SLA Strength": 9,
            "Execution Risk": 9,
            "Stakeholder Confidence": 8,
            "Strategic Alignment": 8,
            "Innovation Capacity": 7,
            "Relationship Depth": 6,
            "Commercial Flexibility": 6,
            "ESG / Sustainability": 7,
            "Supplier Diversity": 5,
        },
    },
    "HR Sourcing": {
        "category": "HR Technology",
        "kraljic": "Strategic",
        "weights": {
            "Price / TCO": 7,
            "SLA Strength": 8,
            "Execution Risk": 9,
            "Stakeholder Confidence": 8,
            "Strategic Alignment": 8,
            "Innovation Capacity": 6,
            "Relationship Depth": 6,
            "Commercial Flexibility": 7,
            "ESG / Sustainability": 7,
            "Supplier Diversity": 6,
        },
    },
    "Finance Sourcing": {
        "category": "Finance Software",
        "kraljic": "Strategic",
        "weights": {
            "Price / TCO": 7,
            "SLA Strength": 8,
            "Execution Risk": 10,
            "Stakeholder Confidence": 8,
            "Strategic Alignment": 7,
            "Innovation Capacity": 5,
            "Relationship Depth": 6,
            "Commercial Flexibility": 6,
            "ESG / Sustainability": 6,
            "Supplier Diversity": 5,
        },
    },
    "Marketing Sourcing": {
        "category": "Marketing Services",
        "kraljic": "Leverage",
        "weights": {
            "Price / TCO": 8,
            "SLA Strength": 7,
            "Execution Risk": 8,
            "Stakeholder Confidence": 7,
            "Strategic Alignment": 6,
            "Innovation Capacity": 7,
            "Relationship Depth": 5,
            "Commercial Flexibility": 8,
            "ESG / Sustainability": 6,
            "Supplier Diversity": 5,
        },
    },
}

CATEGORY_RULES = {
    "technology": {
        "type": "Indirect",
        "tag": "Technology / SaaS",
        "requirements": "Define scope, implementation milestones, accountable owners, integration responsibilities, data migration obligations, security requirements, and acceptance criteria.",
        "assurance": "Protect continuity through uptime commitments, transition support, disaster recovery, incident response, and notice for major platform changes.",
        "quality": "Use measurable SLA language, incident severity definitions, root-cause expectations, service credits, and issue-resolution timelines.",
        "service": "Clarify support model, severity definitions, response times, escalation paths, reporting cadence, and governance structure.",
        "cost": "Specify user/module/usage pricing logic, implementation fees, renewal caps, pass-through restrictions, and billing transparency.",
        "innovation": "Tie roadmap visibility, product release transparency, and future capability support to periodic executive reviews.",
        "rfp_stakeholders": {
            "must": ["CIO / VP Technology", "Information Security", "Procurement Lead", "Legal Counsel"],
            "recommended": ["Finance / Budget Owner", "End-User Representative", "IT Architecture"],
            "nice": ["Change Management", "Data Privacy Officer"],
        },
    },
    "hr": {
        "type": "Indirect",
        "tag": "HR / People Services",
        "requirements": "Clarify deliverables, implementation milestones, employee-impact boundaries, data ownership, service scope, and business ownership.",
        "assurance": "Protect service continuity, support coverage, transition duties, disruption management, and employee-impact recovery plans.",
        "quality": "Focus on service reliability, response quality, issue resolution, employee experience impact, and performance reviews.",
        "service": "Define communication cadence, escalation structure, account ownership, stakeholder reviews, and service-level expectations.",
        "cost": "Clarify pricing structure, renewal controls, implementation costs, change-order logic, and scaling as usage grows.",
        "innovation": "Tie improvement commitments to workforce experience, automation, reporting, and operating-model evolution.",
        "rfp_stakeholders": {
            "must": ["CHRO / VP People", "HR Operations Lead", "Procurement Lead", "Legal Counsel"],
            "recommended": ["Finance / Budget Owner", "IT (data/integration)", "Employee Experience"],
            "nice": ["DEI Lead", "Communications"],
        },
    },
    "finance": {
        "type": "Indirect",
        "tag": "Finance Software / Services",
        "requirements": "Define scope, approval workflows, data ownership, implementation milestones, control requirements, reporting needs, and acceptance criteria.",
        "assurance": "Protect business continuity, reporting availability, audit support, transition support, and critical-process coverage.",
        "quality": "Use measurable controls, audit support, issue resolution timelines, reporting accuracy, and service accuracy expectations.",
        "service": "Clarify account governance, escalation paths, reporting cadence, finance stakeholder support, and service ownership.",
        "cost": "Clarify subscription structure, renewal caps, implementation fees, change orders, pass-through costs, and billing transparency.",
        "innovation": "Tie roadmap commitments to automation, controls improvement, analytics, and process efficiency.",
        "rfp_stakeholders": {
            "must": ["CFO / VP Finance", "Controller", "Procurement Lead", "Legal / Compliance"],
            "recommended": ["Internal Audit", "IT Architecture", "Finance Operations"],
            "nice": ["Tax", "Treasury"],
        },
    },
    "marketing": {
        "type": "Indirect",
        "tag": "Marketing Services",
        "requirements": "Define campaign scope, deliverables, timelines, usage rights, approval workflows, ownership, and acceptance criteria.",
        "assurance": "Protect continuity through staffing commitments, backup account coverage, transition support, and continuity planning.",
        "quality": "Use measurable output expectations, revision rights, performance reporting, and remediation steps.",
        "service": "Clarify account management, response expectations, reporting cadence, escalation process, and stakeholder communication.",
        "cost": "Define rate cards, media pass-through rules, markup transparency, scope-change logic, and renewal limits.",
        "innovation": "Tie improvement commitments to creative performance, channel testing, analytics, and campaign optimization.",
        "rfp_stakeholders": {
            "must": ["CMO / VP Marketing", "Brand Lead", "Procurement Lead", "Legal / IP Counsel"],
            "recommended": ["Finance", "Digital / Analytics", "Creative Director"],
            "nice": ["PR / Communications", "Product Marketing"],
        },
    },
    "services": {
        "type": "Indirect",
        "tag": "Professional Services",
        "requirements": "Define scope, staffing assumptions, deliverables, role ownership, timeline, and acceptance standards tightly.",
        "assurance": "Protect staffing continuity, substitution rules, knowledge transfer, transition support, and documentation ownership.",
        "quality": "Use milestone quality, output standards, remediation rights, and acceptance criteria instead of vague satisfaction language.",
        "service": "Clarify governance, reporting cadence, communication norms, escalation points, and stakeholder alignment.",
        "cost": "Define rate cards, out-of-scope work, change-request logic, rate-increase boundaries, and expense rules.",
        "innovation": "Require practical problem-solving, process improvement, and improvement contribution over the contract term.",
        "rfp_stakeholders": {
            "must": ["Executive Sponsor", "Project Owner", "Procurement Lead", "Legal Counsel"],
            "recommended": ["Finance", "IT (if technical)", "End Users"],
            "nice": ["PMO", "Risk / Compliance"],
        },
    },
    "packaging": {
        "type": "Direct",
        "tag": "Packaging / Direct Material",
        "requirements": "Specify tolerances, MOQ, artwork/specification control, tooling assumptions, approved materials, and change-control rules.",
        "assurance": "Protect continuity through capacity commitments, lead-time expectations, interruption notice, safety stock, and backup supply expectations.",
        "quality": "Use defect thresholds, traceability expectations, corrective action timing, audit rights, and incoming-quality requirements.",
        "service": "Focus on delivery performance, shortage communication, production coordination, and operational escalation.",
        "cost": "Clarify indexation, resin/commodity pass-through, freight treatment, volume tiers, tooling charges, and surcharge triggers.",
        "innovation": "Emphasize redesign, sustainability options, cost-down support, waste reduction, and material optimization.",
        "rfp_stakeholders": {
            "must": ["Supply Chain / Operations", "Engineering / R&D", "Procurement Lead", "Quality"],
            "recommended": ["Finance", "Sustainability", "Marketing (brand specs)"],
            "nice": ["Legal", "Logistics"],
        },
    },
    "manufacturing": {
        "type": "Direct",
        "tag": "Manufacturing / Direct Material",
        "requirements": "Define specs, tolerances, engineering change handling, qualification rules, approved materials, and production constraints.",
        "assurance": "Protect continuity through capacity commitments, geographic risk visibility, dual-source logic, and lead-time commitments.",
        "quality": "Use non-conformance logic, incoming-quality expectations, corrective-action timelines, traceability, and audit rights.",
        "service": "Focus on shortage response, production communication, operational escalation, and supplier responsiveness.",
        "cost": "Clarify commodity exposure, cost transparency, indexation, productivity expectations, and surcharge discipline.",
        "innovation": "Use process improvement, manufacturability support, cost-down, quality improvement, and resilience improvements.",
        "rfp_stakeholders": {
            "must": ["VP Operations / Plant Manager", "Engineering", "Procurement Lead", "Quality"],
            "recommended": ["Finance", "Supply Chain Planning", "Logistics"],
            "nice": ["Sustainability", "Legal"],
        },
    },
    "logistics": {
        "type": "Indirect",
        "tag": "Logistics / Transportation",
        "requirements": "Define lane scope, equipment needs, reporting requirements, shipment visibility, and carrier accountability.",
        "assurance": "Protect continuity through surge coverage, backup options, disruption response, and coverage commitments.",
        "quality": "Measure on-time performance, claims, exceptions, damage rates, service recovery, and issue resolution.",
        "service": "Define dispatch responsiveness, communication cadence, escalation behavior, and reporting expectations.",
        "cost": "Clarify fuel treatment, accessorials, lane assumptions, surcharge triggers, and invoice audit rights.",
        "innovation": "Focus on optimization, visibility, route efficiency, emissions reporting, and continuous improvement.",
        "rfp_stakeholders": {
            "must": ["VP Supply Chain", "Transportation Manager", "Procurement Lead", "Operations"],
            "recommended": ["Finance", "Customer Service", "IT (TMS/visibility)"],
            "nice": ["Sustainability", "Legal"],
        },
    },
}

DEFAULT_RFP_STAKEHOLDERS = {
    "must": ["Executive Sponsor", "Business Owner", "Procurement Lead", "Legal Counsel"],
    "recommended": ["Finance / Budget Owner", "IT (if applicable)", "End Users"],
    "nice": ["Risk / Compliance", "Communications"],
}

FINANCIAL_FIELDS = {
    "Years in Business": {
        "options": ["<3 years", "3–10 years", "10–25 years", "25+ years"],
        "scores": {"<3 years": 20, "3–10 years": 55, "10–25 years": 80, "25+ years": 95},
    },
    "Ownership Structure": {
        "options": ["Publicly traded", "Private equity-backed", "Founder/private", "Subsidiary"],
        "scores": {"Publicly traded": 85, "Private equity-backed": 55, "Founder/private": 70, "Subsidiary": 80},
    },
    "Revenue Trajectory": {
        "options": ["Growing 15%+", "Growing 5–15%", "Flat", "Declining", "Unknown"],
        "scores": {"Growing 15%+": 95, "Growing 5–15%": 78, "Flat": 55, "Declining": 25, "Unknown": 40},
    },
    "Recent M&A Activity": {
        "options": ["None in 2 years", "Acquired a company", "Being acquired", "Recently spun off"],
        "scores": {"None in 2 years": 85, "Acquired a company": 65, "Being acquired": 35, "Recently spun off": 45},
    },
    "Payment Terms Offered": {
        "options": ["Net 90+", "Net 60", "Net 30", "Net 15 or less"],
        "scores": {"Net 90+": 90, "Net 60": 75, "Net 30": 60, "Net 15 or less": 40},
    },
    "Workforce Changes (12mo)": {
        "options": ["Significant hiring", "Stable", "Minor layoffs <5%", "Major layoffs >10%"],
        "scores": {"Significant hiring": 90, "Stable": 80, "Minor layoffs <5%": 55, "Major layoffs >10%": 25},
    },
}

RFP_TIMELINE = {
    "Strategic": [
        {"week": "Week 1–2", "phase": "Align", "tasks": ["Define scope and business requirements", "Confirm stakeholder team and executive sponsor", "Establish evaluation criteria and weighting", "Brief legal on category risk profile"]},
        {"week": "Week 3–4", "phase": "Launch", "tasks": ["Issue RFP to shortlisted suppliers", "Host supplier briefing / Q&A session", "Set scoring committee and conflict-of-interest check", "Define clarification and scoring process"]},
        {"week": "Week 5–6", "phase": "Evaluate", "tasks": ["Score responses against weighted criteria", "Run supplier clarification sessions", "Complete financial and risk diligence", "Build recommendation narrative"]},
        {"week": "Week 7–8", "phase": "Negotiate", "tasks": ["Enter best-and-final with top 1–2 suppliers", "Close weakest-dimension gaps in contract", "Confirm stakeholder alignment before award", "Finalize commercial and legal terms"]},
        {"week": "Week 9", "phase": "Award", "tasks": ["Present recommendation to executive sponsor", "Communicate award and decline decisions", "Execute contract", "Kick off transition / implementation planning"]},
    ],
    "Leverage": [
        {"week": "Week 1", "phase": "Align", "tasks": ["Define scope and required outcomes", "Identify competitive supplier pool (3–5)", "Set price and performance benchmarks"]},
        {"week": "Week 2–3", "phase": "Launch", "tasks": ["Issue RFP with competitive intent visible", "Run structured Q&A", "Set scoring and scoring ownership"]},
        {"week": "Week 4", "phase": "Evaluate", "tasks": ["Score responses", "Identify leverage gaps and negotiation targets", "Short-list to 2 finalists"]},
        {"week": "Week 5", "phase": "Negotiate", "tasks": ["Run competitive negotiation", "Lock pricing, SLA, and renewal logic", "Close commercial terms"]},
        {"week": "Week 6", "phase": "Award", "tasks": ["Award and notify", "Execute contract", "Begin transition"]},
    ],
    "Bottleneck": [
        {"week": "Week 1", "phase": "Align", "tasks": ["Map current supply risk and single-source exposure", "Identify backup or secondary options", "Define continuity as primary criteria"]},
        {"week": "Week 2–3", "phase": "Launch", "tasks": ["Issue RFP with continuity requirements explicit", "Probe supplier capacity and backup coverage", "Assess financial stability closely"]},
        {"week": "Week 4", "phase": "Evaluate", "tasks": ["Score with continuity weighted highest", "Flag any capacity or financial risk signals", "Do not sacrifice continuity for price"]},
        {"week": "Week 5", "phase": "Negotiate", "tasks": ["Lock interruption handling and notice terms", "Establish safety stock or backup obligations", "Secure transition support language"]},
        {"week": "Week 6", "phase": "Award", "tasks": ["Award and confirm backup coverage plan", "Execute contract", "Build continuity review cadence"]},
    ],
    "Non-Critical": [
        {"week": "Week 1", "phase": "Align", "tasks": ["Define scope and confirm low complexity", "Identify 2–3 qualified suppliers", "Keep evaluation criteria simple"]},
        {"week": "Week 2", "phase": "Launch & Evaluate", "tasks": ["Issue short RFQ (not full RFP)", "Score on price, lead time, and ease of doing business"]},
        {"week": "Week 3", "phase": "Negotiate & Award", "tasks": ["Short negotiation on price and terms", "Execute standard agreement or PO", "Minimize admin overhead"]},
    ],
}

PHASE_COLORS = {
    "Align": "#3B82F6",
    "Launch": "#8B5CF6",
    "Evaluate": "#F59E0B",
    "Negotiate": "#EF4444",
    "Award": "#22C55E",
    "Launch & Evaluate": "#8B5CF6",
    "Negotiate & Award": "#22C55E",
}

AUCTION_TYPES = {
    "Reverse Auction (eRA)": {
        "desc": "Electronic Reverse Auction — suppliers compete in real-time by bidding prices down. Used in Coupa and Ariba for commodity or well-specified goods where price is the primary lever and 3+ qualified suppliers exist.",
        "when": "Leverage or Non-Critical · 3+ suppliers · Commodity-like specs · Price weight dominant · Low switching cost",
        "coupa_ariba": "Coupa: Auction Events → Reverse Auction | Ariba: Sourcing → Auction",
        "color": "#4ADE80",
    },
    "Sealed Bid Auction": {
        "desc": "All suppliers submit one-time confidential bids simultaneously. No visibility into competitor pricing. Drives honest first-offer pricing for construction, capital equipment, and public-sector requirements.",
        "when": "Capital projects · Construction · Public procurement mandates · Full spec clarity required",
        "coupa_ariba": "Coupa: Auction Events → Sealed Bid | Ariba: Sourcing → Bid",
        "color": "#94A3B8",
    },
    "Dutch Auction (Descending Price)": {
        "desc": "Price starts high and drops incrementally until a supplier accepts. Used for capacity-constrained supply markets where the buyer needs to find the market-clearing price quickly.",
        "when": "Capacity-constrained supply · Strategic commodities · Allocation events · When supply side sets price floor",
        "coupa_ariba": "Coupa: Auction Events → Dutch Auction | Ariba: Advanced Sourcing",
        "color": "#F59E0B",
    },
    "Rank Auction (Coupa / Ariba Standard)": {
        "desc": "Suppliers see their relative rank (1st, 2nd, 3rd) but not competitors' prices. Encourages iterative improvement without full price transparency. The default sourcing event type for most indirect categories.",
        "when": "Most indirect categories · 3+ suppliers · When you want competition without full transparency · Strategic and Leverage",
        "coupa_ariba": "Coupa: Sourcing Events → Standard Event | Ariba: Sourcing → RFx with Rank",
        "color": "#60A5FA",
    },
    "Negotiated Award (Single Source)": {
        "desc": "Direct negotiation with one or two suppliers. Not an auction — used when supply is concentrated, switching cost is prohibitive, or the incumbent relationship has strategic value that outweighs competitive pricing.",
        "when": "Bottleneck · Very High switching cost · 1–2 viable suppliers · Incumbent renewal · Proprietary solution",
        "coupa_ariba": "Coupa: Contract Request → Negotiated | Ariba: Contract Workbench → Direct Award",
        "color": "#A78BFA",
    },
    "Multi-Round Negotiation (Best and Final)": {
        "desc": "Structured multi-round process ending in Best and Final Offer (BAFO). Used for complex, high-value Strategic categories where commercial terms, SLAs, and contract structure matter as much as price.",
        "when": "Strategic · High value · Complex terms · ERP, Managed Services, Professional Services · When total value > price",
        "coupa_ariba": "Coupa: Sourcing Events → Multi-Round | Ariba: Sourcing → RFx with Rounds",
        "color": "#F87171",
    },
}

INTAKE_QUESTIONS = [
    {"id": "incumbent", "question": "Is this an incumbent renewal or a new supplier search?", "options": ["New supplier search", "Incumbent renewal", "Incumbent + competitive challenge"], "impact": "Switching cost and transition risk flags"},
    {"id": "switching_cost", "question": "How high is the cost or risk of switching suppliers?", "options": ["Low — easy to switch", "Medium — some disruption expected", "High — significant transition risk", "Very High — near-irreversible"], "impact": "Bottleneck / Strategic posture reinforcement"},
    {"id": "customer_facing", "question": "Is this supplier customer-facing or does it directly affect customer experience?", "options": ["Yes — directly customer-facing", "Indirect — affects internal teams only", "Mixed — depends on the process"], "impact": "Elevates execution risk weight and SLA requirements"},
    {"id": "implementation", "question": "Does this require a significant implementation or onboarding period?", "options": ["Yes — 3+ months of implementation", "Minor setup only", "No implementation required"], "impact": "Adds implementation risk flags and timeline extensions"},
    {"id": "regulatory", "question": "Are there regulatory, data privacy, or ESG obligations tied to this supplier?", "options": ["Yes — significant regulatory exposure", "Partial — some compliance requirements", "No regulatory obligations"], "impact": "Elevates legal stakeholder priority and contract must-haves"},
    {"id": "continuity", "question": "Is supply or service continuity business-critical?", "options": ["Yes — disruption would halt operations", "Yes — significant business impact", "Moderate — manageable disruption", "Low — easily absorbed"], "impact": "Shifts toward Bottleneck / Strategic and activates continuity risk flags"},
]

AI_TOOLS = [
    {"name": "ChatGPT",  "url": "https://chat.openai.com/",   "icon": "🤖", "color": "#10A37F"},
    {"name": "Gemini",   "url": "https://gemini.google.com/", "icon": "✨", "color": "#4285F4"},
    {"name": "Grok",     "url": "https://grok.x.ai/",         "icon": "⚡", "color": "#1DA1F2"},
    {"name": "DeepSeek", "url": "https://chat.deepseek.com/", "icon": "🔍", "color": "#8B5CF6"},
    {"name": "Claude",   "url": "https://claude.ai/",         "icon": "🧠", "color": "#D97706"},
]

AI_PROMPT_MODES = {
    "🎯 Decision Pressure Test": {
        "desc": "Critique the recommendation. Find what's wrong before the meeting does.",
        "guardrails": [
            "Do NOT validate the recommendation — your job is to challenge it.",
            "Do NOT assume the scoring is accurate — question the inputs.",
            "Do NOT ignore stakeholder dynamics — they kill more deals than bad suppliers.",
            "Avoid generic procurement advice — be specific to this subcategory.",
            "Do NOT hallucinate supplier capabilities — only use what's in the context.",
        ],
    },
    "📝 Contract Risk Analysis": {
        "desc": "Identify the 5 contract clauses most likely to create problems post-award.",
        "guardrails": [
            "Do NOT give legal advice — give procurement risk framing.",
            "Avoid boilerplate contract language — focus on this specific subcategory's risk profile.",
            "Do NOT assume standard terms are sufficient — identify gaps.",
            "Avoid abstract risk — every risk must have a specific business consequence.",
            "Do NOT hallucinate specific regulatory requirements — flag what needs legal review.",
        ],
    },
    "🗣️ Stakeholder Battle Plan": {
        "desc": "Tell me exactly how to handle each stakeholder before the presentation.",
        "guardrails": [
            "Do NOT suggest avoiding the blockers — address them directly.",
            "Avoid generic stakeholder management advice — use the specific roles and positions provided.",
            "Do NOT assume all champions will show up — give activation tactics.",
            "Avoid over-relying on data — some stakeholders respond to narrative, not numbers.",
            "Do NOT hallucinate stakeholder motivations — only use what's in the context.",
        ],
    },
    "💰 Negotiation Intelligence": {
        "desc": "Build my BATNA and identify the 5 highest-leverage negotiation points.",
        "guardrails": [
            "Do NOT suggest lowball tactics that damage the relationship.",
            "Avoid focusing only on price — total value is the frame.",
            "Do NOT ignore the weakest dimension — it's the primary negotiation target.",
            "Avoid generic negotiation tactics — tie every point to this specific subcategory.",
            "Do NOT assume the supplier will accept everything — build a concession strategy.",
        ],
    },
    "❓ RFP Question Generator": {
        "desc": "Generate 10 additional capability questions tailored to this exact evaluation.",
        "guardrails": [
            "Do NOT generate generic questions — every question must be specific to this supplier and subcategory.",
            "Avoid yes/no questions — require evidence and metrics.",
            "Do NOT ask about capabilities already proven — focus on the weakest dimension.",
            "Avoid leading questions — they produce useless answers.",
            "Do NOT hallucinate technical specifications — flag where you're inferring.",
        ],
    },
}

DEFAULT_RFP_QUESTIONS = [
    "Describe your company's financial stability and provide audited financials for the past 2 years.",
    "What is your employee count, growth trajectory, and key leadership stability?",
    "Describe your implementation or onboarding process and typical timeline.",
    "What service level commitments can you make for this engagement?",
    "How do you handle service failures — what remedies and credits apply?",
    "Describe your data security controls and relevant certifications.",
    "What are your contract term options and what renewal flexibility do you offer?",
    "How do you handle pricing changes — what rate caps or indexation do you propose?",
    "Describe your account management model — dedicated resources, escalation path.",
    "What references can you provide from similar companies in our industry?",
]