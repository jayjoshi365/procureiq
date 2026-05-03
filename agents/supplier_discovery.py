"""
Agent: Supplier Discovery — Procurement Decision Intelligence
============================================================
Transforms raw company search into a senior category manager's sourcing brief.

Three output tiers:
  A. Executive Shortlist   (5–10)  — RFI/RFP ready
  B. Expanded Longlist     (10–25) — screening candidates
  C. Emerging Watchlist    (open)  — VC-backed, private disruptors, niche specialists

Seven scoring dimensions (0–100 each):
  1. Market Leadership       — analyst recognition, revenue scale, enterprise adoption
  2. Category Fit            — subcategory alignment, geography, procurement use-case
  3. Financial Strength      — stability, funding, profitability signals
  4. Execution Capability    — delivery maturity, geographic coverage, enterprise track record
  5. Innovation Strength     — AI/automation, patents, platform differentiation
  6. Risk Profile            — lock-in, concentration, compliance, delivery risk (higher = safer)
  7. Strategic Procurement Fit — negotiation leverage, pricing transparency, scalability

Source credibility hierarchy:
  Tier 1: Gartner, Forrester, IDC, Everest, ISG, Spend Matters, G2 Enterprise Grid
           Public 10-Ks, investor presentations, verified case studies
  Tier 2: Crunchbase, PitchBook, LinkedIn, press releases, partnership announcements
  Tier 3: Reviews, articles, conference appearances, job postings

Red-flag logic: auto-flags suppliers for enterprise scale mismatch, weak financials,
lock-in risk, hype-driven growth, geographic concentration, limited implementation,
and low evidence quality.
"""
import json
import re
import os
import time
import requests
from typing import List, Dict, Any, Optional

try:
    import anthropic as _ant
    _AVAILABLE = True
except ImportError:
    _ant = None
    _AVAILABLE = False


# ── Known market leaders per category (seeds the LLM's discovery) ─────
# These are injected into the prompt so the agent starts from leaders,
# then expands outward. Kept as hints only — not hard-coded output.
# "suppliers" maps name → {why, evidence, diff, use_case} for illustrative mode.
_CATEGORY_LEADERS: Dict[str, Dict] = {
    "IT": {
        "leaders": ["Microsoft", "IBM", "Accenture", "Infosys", "Wipro", "TCS", "HCL", "Cognizant"],
        "challengers": ["Rackspace", "Kyndryl", "DXC Technology", "NTT Data"],
        "niche": ["Presidio", "Logicalis", "Insight Direct"],
        "analyst_sources": ["Gartner Magic Quadrant for IT Services", "Everest PEAK Matrix", "ISG Provider Lens"],
        "suppliers": {
            "Microsoft": {"why": "Dominant enterprise cloud (Azure) with native M365 integration; highest platform stickiness of any IT vendor.", "evidence": "Gartner Leader in Cloud Infrastructure & Platform Services; 95%+ Fortune 500 adoption of M365.", "diff": "Broadest product surface area — cloud, productivity, security, AI in one contract.", "use_case": "Organizations standardizing on Microsoft stack seeking unified commercial terms."},
            "IBM": {"why": "Deep regulated-industry expertise (BFSI, healthcare, government) with strong services capability post-Kyndryl split.", "evidence": "Gartner Leader in IT Services; $60B+ revenue; Watson AI embedded across product lines.", "diff": "Strongest hybrid cloud consulting practice for regulated enterprises needing on-prem control.", "use_case": "Financial services or government organizations with complex compliance and hybrid cloud requirements."},
            "Accenture": {"why": "Largest global IT and business transformation partner; preferred system integrator for SAP, Oracle, and Salesforce.", "evidence": "Everest Group PEAK Matrix Leader; $64B revenue; 700K+ consultants globally.", "diff": "Broadest implementation capability across all major platforms with deep change management practice.", "use_case": "Large-scale ERP or cloud transformation programs requiring both strategy and delivery."},
            "Infosys": {"why": "Cost-competitive offshore delivery with strong BFSI and manufacturing verticals and a growing cloud practice.", "evidence": "ISG Provider Lens Leader; $18B+ revenue; recognized for delivery quality in banking and insurance.", "diff": "Best price-to-quality ratio among Tier 1 Indian IT firms with strong North America delivery governance.", "use_case": "Application development, maintenance, and infrastructure managed services for cost-conscious enterprises."},
            "Wipro": {"why": "Mid-market pricing with solid North America and Europe delivery and strong manufacturing vertical expertise.", "evidence": "Gartner Challenger in IT Services; $11B revenue; strong in industrial and consumer goods sectors.", "diff": "More agile contracting and transition processes than larger peers; competitive in mid-sized deals.", "use_case": "IT outsourcing and digital transformation for mid-to-large enterprises seeking alternatives to top-tier pricing."},
            "TCS": {"why": "Scale leader in global IT services with the lowest TCO among Tier 1 Indian IT firms and the largest talent pool.", "evidence": "Everest Group PEAK Matrix Leader; $27B+ revenue; largest IT employer globally with 600K+ staff.", "diff": "Unmatched scale for high-volume, multi-geography programs; strongest attrition management in the industry.", "use_case": "Large outsourcing programs requiring proven delivery at scale across multiple geographies."},
        },
    },
    "HR": {
        "leaders": ["ADP", "Workday", "SAP SuccessFactors", "Oracle HCM", "Ceridian", "Paylocity"],
        "challengers": ["UKG", "Rippling", "Gusto", "BambooHR"],
        "niche": ["Lattice", "Culture Amp", "Lever", "Greenhouse"],
        "analyst_sources": ["Gartner Magic Quadrant for HCM", "Forrester HR Tech Wave"],
        "suppliers": {
            "ADP": {"why": "Market-share leader in payroll with the broadest global compliance coverage across 140+ countries.", "evidence": "Gartner Leader in Cloud HCM; processes payroll for 1-in-6 US workers; $18B revenue.", "diff": "Unmatched compliance engine for multi-country payroll; deepest tax and regulatory update coverage.", "use_case": "Organizations prioritizing payroll accuracy and compliance over a unified HCM experience."},
            "Workday": {"why": "Strongest unified HCM suite for enterprise; single data model spanning HR, finance, and planning.", "evidence": "Gartner Leader in Cloud HCM for 9 consecutive years; 10,000+ customers; $7B+ revenue.", "diff": "True single-platform architecture — no data reconciliation between HR and Finance modules.", "use_case": "Mid-to-large enterprise seeking a unified people and financial planning platform with premium UX."},
            "SAP SuccessFactors": {"why": "Best fit for organizations already on SAP ERP — integration advantage offsets the UI gap vs. Workday.", "evidence": "Gartner Leader in Cloud HCM; 250M+ users across SAP ecosystem; deep S/4HANA integration.", "diff": "Native integration with SAP ERP eliminates costly middleware; strong for manufacturing and supply chain.", "use_case": "SAP-ERP shops requiring tight HR-finance integration without a full platform migration."},
            "Oracle HCM": {"why": "Strongest for large, global organizations running Oracle ERP with deep workforce analytics.", "evidence": "Gartner Leader in Cloud HCM; 30M+ users; strong in financial services and public sector.", "diff": "Deepest workforce analytics and planning capability among the four major HCM vendors.", "use_case": "Oracle ERP customers seeking unified people analytics and talent management without a platform change."},
            "Ceridian": {"why": "Single-database real-time processing architecture eliminates batch delays; strong healthcare and retail depth.", "evidence": "Gartner Leader in Cloud HCM; 6,000+ customers; recognized for product innovation in continuous pay.", "diff": "Only HCM vendor with true real-time payroll calculation — no end-of-period batch runs.", "use_case": "Organizations with complex scheduling, variable pay, or real-time pay requirements in hourly-heavy industries."},
            "Paylocity": {"why": "Best value for mid-market (50–2,000 employees) with strong employee engagement and communication tools.", "evidence": "Gartner Visionary in Cloud HCM; 37,000+ customers; recognized for modern UX and engagement features.", "diff": "Community and social collaboration features drive measurably higher employee platform adoption than peers.", "use_case": "Mid-market organizations prioritizing employee experience and total cost of ownership over global scale."},
        },
    },
    "Finance": {
        "leaders": ["Workday Financials", "SAP S/4HANA", "Oracle NetSuite", "BlackLine", "Coupa"],
        "challengers": ["Sage Intacct", "Ramp", "Brex", "Expensify"],
        "niche": ["FloQast", "Vena Solutions", "Planful"],
        "analyst_sources": ["Gartner Magic Quadrant for Cloud Financial Management", "Forrester Finance Wave"],
        "suppliers": {
            "Workday Financials": {"why": "Strongest cloud financial management for enterprise; unified with HR for a single source of truth on people and money.", "evidence": "Gartner Leader in Cloud Financial Management; deployed at 50%+ of Fortune 500 companies alongside Workday HCM.", "diff": "Only platform where HR headcount, finance budgets, and actuals live in one data model with no reconciliation.", "use_case": "Enterprise organizations seeking a unified finance and HR platform to eliminate cross-system reporting gaps."},
            "SAP S/4HANA": {"why": "Market-share leader for complex manufacturing, supply chain, and multi-entity finance at global scale.", "evidence": "Gartner Leader in Cloud ERP; 27,000+ customers globally; deepest industry-specific functionality of any ERP.", "diff": "Unmatched depth in multi-entity consolidation, transfer pricing, and supply chain finance for complex organizations.", "use_case": "Multinational manufacturers or distributors needing deep ERP functionality that other platforms cannot replicate."},
            "Oracle NetSuite": {"why": "Dominant mid-market ERP with fast implementation cycles and strong e-commerce and subscription billing integrations.", "evidence": "Gartner Leader in Cloud Financial Management; 36,000+ customers; fastest-growing ERP in mid-market segment.", "diff": "Pre-built connectors for Shopify, Salesforce, and common tech stack tools reduce integration cost significantly.", "use_case": "Growth-stage and mid-market companies needing a scalable ERP without the complexity and cost of SAP or Oracle."},
            "BlackLine": {"why": "Category creator in financial close automation; reduces close cycle by 30–50% for enterprise finance teams.", "evidence": "Gartner Leader in Financial Close and Consolidation; 4,000+ customers; trusted by 8 of the top 10 global banks.", "diff": "Purpose-built for the close — not an ERP add-on; integrates with SAP, Oracle, and Workday without replacing them.", "use_case": "CFOs targeting faster, auditable close cycles and reduced manual reconciliation risk."},
            "Coupa": {"why": "Best-in-class procure-to-pay with the largest Business Spend Management network; preferred by procurement teams.", "evidence": "Gartner Leader in Procure-to-Pay; $3T+ in spend managed on platform; strong NPS among procurement professionals.", "diff": "BSM community network drives supplier onboarding speed and pricing benchmarks unavailable on other platforms.", "use_case": "Procurement-led finance transformations seeking P2P automation and spend visibility alongside financial control."},
        },
    },
    "Marketing": {
        "leaders": ["Salesforce Marketing Cloud", "Adobe Experience Cloud", "HubSpot", "Marketo"],
        "challengers": ["Klaviyo", "Iterable", "Braze", "Sprout Social"],
        "niche": ["Bazaarvoice", "Yotpo", "Attentive"],
        "analyst_sources": ["Gartner Magic Quadrant for Marketing Automation", "Forrester B2B Marketing Wave"],
        "suppliers": {
            "Salesforce Marketing Cloud": {"why": "Largest marketing ecosystem with the broadest CRM-to-campaign integration; standard in enterprise B2C.", "evidence": "Gartner Leader in Marketing Automation for 7+ years; $8B+ marketing cloud revenue; 150,000+ customers.", "diff": "Tightest integration with Salesforce CRM — contact data, opportunity data, and campaign ROI in one view.", "use_case": "Salesforce CRM shops seeking to unify customer data and campaign execution without a separate CDP."},
            "Adobe Experience Cloud": {"why": "Strongest for content-led B2C experiences with best-in-class analytics, personalization, and asset management.", "evidence": "Gartner Leader in Digital Experience Platforms; $5B+ DX revenue; preferred by media, retail, and financial services.", "diff": "Only platform combining creative (Photoshop/AEM), data (Analytics), and activation (Target) in one vendor contract.", "use_case": "Enterprise B2C brands where content quality, personalization at scale, and analytics depth are primary priorities."},
            "HubSpot": {"why": "Best mid-market inbound marketing platform; fastest time-to-ROI for B2B demand generation teams.", "evidence": "G2 Leader in Marketing Automation; 194,000+ customers; recognized for ease of use and onboarding speed.", "diff": "All-in-one CRM, marketing, sales, and service platform eliminates integration overhead for teams under 500.", "use_case": "Mid-market B2B organizations building an inbound motion without the cost and complexity of Salesforce+Marketo."},
            "Marketo": {"why": "Enterprise-grade lead management with the deepest B2B marketing operations and CRM integration capabilities.", "evidence": "Gartner Leader in B2B Marketing Automation; acquired by Adobe; 5,000+ enterprise customers.", "diff": "Most powerful lead scoring and nurture workflow engine available; preferred by enterprise B2B marketing ops teams.", "use_case": "Enterprise B2B organizations with complex lead lifecycles, multi-touch attribution, and large marketing ops teams."},
        },
    },
    "Logistics": {
        "leaders": ["FedEx", "UPS", "DHL", "XPO Logistics", "Coyote Logistics", "Echo Global"],
        "challengers": ["Transplace", "GlobalTranz", "Arrive Logistics"],
        "niche": ["project44", "FourKites", "Flexport"],
        "analyst_sources": ["Gartner Magic Quadrant for Real-Time Transportation Visibility", "Everest Logistics PEAK Matrix"],
        "suppliers": {
            "FedEx": {"why": "Largest US domestic express network; best time-definite SLAs for urgent shipments.", "evidence": "$90B+ revenue; 220+ countries served; industry-leading on-time delivery performance for express.", "diff": "Strongest express and overnight capability; unmatched US suburban last-mile density.", "use_case": "Organizations requiring guaranteed next-day or time-definite delivery for high-value or urgent goods."},
            "UPS": {"why": "Broadest global ground and freight network with the strongest cold chain and healthcare logistics capability.", "evidence": "$100B+ revenue; leading in healthcare, high-tech, and retail logistics; strongest B2B ground network.", "diff": "Healthcare logistics subsidiary (Marken, Polar Speed) and temperature-controlled network unmatched by peers.", "use_case": "Healthcare, pharma, or high-value B2B organizations needing reliable ground delivery and cold chain compliance."},
            "DHL": {"why": "Dominant in international freight and customs brokerage; best partner for complex cross-border logistics programs.", "evidence": "$110B+ revenue; #1 global freight forwarder; strongest customs brokerage network across 220+ countries.", "diff": "Unmatched international customs and compliance capability — critical for organizations with cross-border complexity.", "use_case": "Importers and exporters with complex multi-country supply chains requiring a single logistics partner."},
            "XPO Logistics": {"why": "Top asset-based LTL carrier with strong North American coverage and a technology-forward tracking platform.", "evidence": "Top 5 US LTL carrier; $8B+ revenue; strong on-time delivery performance for pallet-level freight.", "diff": "LTL-focused with owned assets — more reliable than broker-only models for consistent pallet freight.", "use_case": "Organizations with regular pallet-quantity domestic freight needing reliability over spot-market savings."},
            "Coyote Logistics": {"why": "UPS-backed broker with a strong spot-market technology platform and nationwide carrier network.", "evidence": "Top 10 US freight broker; backed by UPS; recognized for technology and carrier relationship depth.", "diff": "Technology platform and UPS backing create pricing leverage and capacity access smaller brokers cannot match.", "use_case": "Organizations needing flexible truckload capacity with technology-enabled shipment visibility."},
        },
    },
    "Legal": {
        "leaders": ["LexisNexis", "Thomson Reuters", "Wolters Kluwer", "Relativity", "Kroll"],
        "challengers": ["Ironclad", "ContractPodAi", "LinkSquares"],
        "niche": ["Evisort", "Luminance", "Conga"],
        "analyst_sources": ["Gartner Legal Tech Report", "Forrester Contract Lifecycle Management Wave"],
        "suppliers": {
            "LexisNexis": {"why": "Market-leading legal research and compliance database; standard in 90% of AmLaw 200 law firms.", "evidence": "$4B+ revenue; deepest case law and regulatory database; preferred for litigation and compliance research.", "diff": "Broadest regulatory and case law database coverage including state-level and international jurisdictions.", "use_case": "Legal teams requiring comprehensive research coverage for litigation, compliance, and regulatory matters."},
            "Thomson Reuters": {"why": "Westlaw and Practical Law are the gold standard for litigation research and regulatory change tracking.", "evidence": "Gartner Leader in Legal Research; $6B+ legal revenue; Westlaw used by virtually every major law firm.", "diff": "Practical Law practice guides are uniquely valuable for corporate counsel and transactional work.", "use_case": "Corporate legal departments handling transactional work, contracts, and regulatory compliance."},
            "Wolters Kluwer": {"why": "Leading for regulatory compliance, tax, and audit workflows with deep corporate legal integrations.", "evidence": "$5B+ revenue; dominant in tax compliance (CCH) and corporate law filing and entity management.", "diff": "CCH SureTax and entity management tools are preferred by tax and corporate secretarial teams.", "use_case": "Finance and legal teams managing tax compliance, entity governance, and regulatory filing obligations."},
            "Relativity": {"why": "Market-standard e-discovery platform; required by most litigation support vendors and outside counsel.", "evidence": "Used in 90%+ of major US litigation matters; 200,000+ legal professionals on platform globally.", "diff": "De facto standard for document review in major litigation — required to collaborate with most outside counsel.", "use_case": "Organizations in active litigation or requiring e-discovery capability for regulatory investigations."},
            "Kroll": {"why": "Leading forensic investigation and due diligence firm; preferred for M&A, restructuring, and regulatory responses.", "evidence": "$2B+ revenue; 50+ years in forensic and risk advisory; trusted in high-stakes regulatory and litigation matters.", "diff": "Combines forensic accounting, cyber investigation, and M&A due diligence in one firm — rare capability bundle.", "use_case": "Organizations facing M&A transactions, regulatory investigations, or requiring independent forensic expertise."},
        },
    },
    "Facilities": {
        "leaders": ["CBRE", "JLL", "Cushman & Wakefield", "Sodexo", "ABM Industries", "Aramark"],
        "challengers": ["Colliers", "Avison Young", "Envoy"],
        "niche": ["Planon", "FM:Systems", "OfficeSpace Software"],
        "analyst_sources": ["Gartner Magic Quadrant for IWMS", "Verdantix FM Market Report"],
        "suppliers": {
            "CBRE": {"why": "Largest global commercial real estate and integrated FM firm; strongest for complex portfolio management.", "evidence": "$30B+ revenue; manages 3B+ sq ft globally; Gartner Leader in IWMS ecosystem.", "diff": "Broadest advisory, transaction, and FM capability bundle — can handle portfolio strategy to janitorial.", "use_case": "Large enterprises managing multi-site real estate portfolios requiring advisory and operational FM."},
            "JLL": {"why": "Strong integrated FM and workplace technology practice; preferred by tech sector and innovation-driven occupiers.", "evidence": "$20B+ revenue; strong in technology, life sciences, and government sectors; recognized for sustainability.", "diff": "JLL Spark venture arm and tech-forward FM platform attract organizations prioritizing workplace innovation.", "use_case": "Technology companies and innovation-driven organizations seeking a FM partner with a digital workplace focus."},
            "Sodexo": {"why": "Global leader in integrated workplace services including catering, cleaning, and FM across 55+ countries.", "evidence": "$25B+ revenue; 420,000+ employees; leading in healthcare, education, and corporate campus environments.", "diff": "Bundled soft services (catering + cleaning + FM) under one contract reduces vendor management overhead.", "use_case": "Organizations seeking a single integrated soft services provider across multiple locations."},
            "ABM Industries": {"why": "US market leader in facility services including janitorial, HVAC, electrical, and parking management.", "evidence": "$8B+ revenue; 100,000+ employees; leading in aviation, commercial real estate, and education.", "diff": "Self-performs technical FM services (HVAC, electrical) rather than subcontracting — stronger accountability.", "use_case": "US organizations seeking owned-service delivery for technical and soft FM rather than a broker model."},
        },
    },
    "Professional Services": {
        "leaders": ["McKinsey", "Deloitte", "PwC", "EY", "KPMG", "BCG", "Accenture"],
        "challengers": ["Gartner", "Huron Consulting", "FTI Consulting"],
        "niche": ["West Monroe", "Slalom", "Guidehouse"],
        "analyst_sources": ["Kennedy Vanguard Report", "Source Global Research", "ALM Intelligence"],
        "suppliers": {
            "McKinsey": {"why": "Highest-prestige strategic advisory for board-level transformation; appropriate only where CEO sponsorship exists.", "evidence": "Revenue $15B+; serves 90% of Fortune 100; recognized as #1 strategy firm globally by Source Global Research.", "diff": "Unmatched access to senior C-suite practitioners and proprietary benchmarking data sets.", "use_case": "CEO/board-sponsored transformation mandates where market signal and credibility matter as much as output."},
            "Deloitte": {"why": "Broadest professional services capability (strategy, implementation, audit, tax); largest global firm by revenue.", "evidence": "$65B+ revenue; 415,000+ professionals; Gartner Leader in multiple IT advisory categories.", "diff": "One-firm model allows strategy, implementation, and audit under one relationship — reduces coordination overhead.", "use_case": "Large organizations seeking end-to-end transformation support from a single firm with global delivery."},
            "PwC": {"why": "Strong in regulatory, risk, ESG, and financial advisory; most trusted in financial services and government.", "evidence": "$53B+ revenue; #1 in financial services advisory and ESG reporting by market share.", "diff": "Deepest regulatory and compliance advisory bench — preferred when a regulator is involved.", "use_case": "Regulated industries (banking, insurance, government) requiring audit, risk, and compliance advisory."},
            "EY": {"why": "Leading in transaction advisory, M&A due diligence, and sustainability reporting across global markets.", "evidence": "$49B+ revenue; #1 in transaction advisory market share; strong ESG assurance practice.", "diff": "Transaction Services practice is the largest standalone M&A advisory practice of any Big Four firm.", "use_case": "Organizations undergoing M&A, divestitures, or requiring independent ESG assurance."},
            "KPMG": {"why": "Competitive alternative to Big Three for audit and tax; strongest in government, public sector, and mid-market.", "evidence": "$36B+ revenue; government advisory leader in 40+ countries; strong healthcare and education vertical.", "diff": "Better price competitiveness than MBB and other Big Four for comparable quality in audit and risk advisory.", "use_case": "Government, public sector, and mid-market organizations seeking Big Four credibility at better commercial terms."},
        },
    },
    "Direct Materials": {
        "leaders": ["3M", "Honeywell", "Parker Hannifin", "Emerson Electric", "Avnet", "Arrow Electronics"],
        "challengers": ["Flex", "Jabil", "Celestica"],
        "niche": ["Plexus", "Benchmark Electronics", "IEC Electronics"],
        "analyst_sources": ["Gartner Supply Chain Top 25", "IDC Manufacturing Insights"],
        "suppliers": {
            "3M": {"why": "Diversified industrial materials supplier with a strong patent moat across 60,000+ products and multiple industries.", "evidence": "$33B+ revenue; 100,000+ patents; Gartner Supply Chain Top 25 consistent leader.", "diff": "Widest product breadth of any industrial materials supplier — single source for adhesives, abrasives, and safety.", "use_case": "Manufacturers seeking to consolidate industrial materials and safety products under fewer supplier agreements."},
            "Honeywell": {"why": "Industrial automation, process controls, and safety equipment with deep energy and aerospace vertical expertise.", "evidence": "$36B+ revenue; dominant in building automation, process controls, and connected worker safety.", "diff": "Honeywell Connected Plant platform enables predictive maintenance integration — not available from pure-play distributors.", "use_case": "Process manufacturers and energy companies integrating automation, safety, and industrial IoT."},
            "Parker Hannifin": {"why": "Market leader in motion and control technologies; critical sole-source supplier for many precision manufacturing OEMs.", "evidence": "$19B+ revenue; 50+ divisions; dominant in hydraulics, pneumatics, and filtration for OEM applications.", "diff": "Engineering depth and custom-specification capability makes it difficult to replace in existing OEM designs.", "use_case": "OEMs and manufacturers requiring custom-engineered motion control and fluid systems with deep technical support."},
            "Avnet": {"why": "Largest electronic components distributor globally; essential for semiconductor and PCB supply chain management.", "evidence": "$25B+ revenue; authorized distributor for 2,000+ suppliers; largest electronic component inventory globally.", "diff": "Authorized distribution model provides counterfeit risk mitigation unavailable through spot-market channels.", "use_case": "Electronics manufacturers requiring reliable supply of semiconductors and components at scale."},
        },
    },
    "Operations / MRO": {
        "leaders": ["Grainger", "Fastenal", "MSC Industrial", "HD Supply", "Anixter"],
        "challengers": ["Zoro Tools", "Global Industrial", "Würth Group"],
        "niche": ["Encompass", "Novatek International", "SDI Industries"],
        "analyst_sources": ["Spend Matters MRO Analysis", "Aberdeen Group MRO Report"],
        "suppliers": {
            "Grainger": {"why": "Largest US MRO distributor with 1.5M+ SKUs; best for facilities requiring broad, same-day availability.", "evidence": "$15B+ revenue; #1 US MRO distributor by market share; 99%+ next-day fill rate from 9 US DCs.", "diff": "Unmatched SKU breadth and emergency delivery capability — highest total cost of unplanned downtime coverage.", "use_case": "Industrial and commercial facilities needing broad MRO availability with same-day emergency sourcing."},
            "Fastenal": {"why": "Strongest vending machine and on-site inventory management for manufacturing — eliminates emergency buys.", "evidence": "$6B+ revenue; 3,300+ on-site locations; recognized for vending-based inventory management ROI.", "diff": "On-site stocking model drives 20–40% MRO cost reduction by eliminating emergency purchases and indirect spend.", "use_case": "Manufacturers with high-velocity fastener and safety PPE consumption seeking on-site inventory optimization."},
            "MSC Industrial": {"why": "Deep metalworking and machining supply expertise; preferred supplier to precision manufacturers and machine shops.", "evidence": "$4B+ revenue; 1.5M+ items; dominant in metalworking for aerospace, defense, and precision manufacturing.", "diff": "Metalworking technical specialists provide application engineering support that generalist distributors cannot.", "use_case": "Precision manufacturers, machine shops, and aerospace suppliers needing technical supply expertise."},
            "HD Supply": {"why": "Leading facilities maintenance supplier for commercial real estate, hospitality, and healthcare environments.", "evidence": "$6B+ revenue; preferred by REITs, hotel operators, and healthcare facilities for MRO and FF&E.", "diff": "Specialized in facilities and property management categories with deeper stock depth than general MRO distributors.", "use_case": "Property management firms, hotel operators, and healthcare facilities managing recurring maintenance supply."},
        },
    },
    "Travel & Meetings": {
        "leaders": ["American Express Global Business Travel", "CWT (Carlson Wagonlit)", "BCD Travel", "FCM Travel", "Egencia"],
        "challengers": ["Navan (TripActions)", "TravelPerk", "SAP Concur"],
        "niche": ["Spotnana", "Routemaster", "Meetings & Incentives Worldwide"],
        "analyst_sources": ["Phocuswire TMC Market Report", "BTN Group Managed Travel Survey", "GBTA Annual Report"],
        "suppliers": {
            "American Express Global Business Travel": {"why": "Largest TMC by volume; best for Fortune 500 with global programs requiring duty-of-care and risk management.", "evidence": "$30B+ managed travel volume; serves 19 of Fortune 25 companies; leading duty-of-care and traveler tracking.", "diff": "Global footprint and 24/7 traveler support in 140+ countries — critical for organizations with geopolitical risk.", "use_case": "Enterprises with high international travel volumes requiring duty-of-care, risk management, and global support."},
            "CWT (Carlson Wagonlit)": {"why": "Strong in energy, government, and project-based travel programs with competitive pricing for high-volume accounts.", "evidence": "$18B+ managed volume; leading in oil & gas and government travel; strong in Europe and Asia-Pacific.", "diff": "RoomIt hotel program and energy-sector specialization drive cost savings for project-based travel programs.", "use_case": "Energy, government, or project-based organizations with high-volume and geographically concentrated travel patterns."},
            "BCD Travel": {"why": "Mid-market sweet spot with strong reporting, traveler satisfaction, and program optimization capability.", "evidence": "$28B+ managed volume; 4,600 customers; consistently highest traveler satisfaction scores in independent surveys.", "diff": "DecisionSource analytics platform provides spend visibility and savings recommendations beyond basic reporting.", "use_case": "Mid-to-large organizations seeking strong program management, traveler experience, and data-driven optimization."},
            "FCM Travel": {"why": "Technology-forward TMC with strong AI-driven booking recommendations and high mobile adoption rates.", "evidence": "Part of Flight Centre Travel Group; $20B+ managed volume; recognized for technology innovation and UX.", "diff": "FCM Platform's AI recommendations and mobile-first design drive 30%+ online booking tool adoption vs. industry average.", "use_case": "Technology-oriented organizations seeking high booking tool adoption and modern traveler experience."},
            "Egencia": {"why": "Expedia-backed OBT with best TCO for self-service mid-market programs; strong content and pricing leverage.", "evidence": "Expedia Group-owned; $10B+ managed volume; leading mid-market OBT by adoption in tech sector.", "diff": "Expedia content access provides pricing advantages on hotels and air not available to smaller independent TMCs.", "use_case": "Mid-market organizations with tech-savvy travelers seeking a self-service model at a lower management fee."},
        },
    },
    "Healthcare & Benefits": {
        "leaders": ["Aon", "Mercer (Marsh McLennan)", "Willis Towers Watson", "Gallagher", "Buck Consultants"],
        "challengers": ["NFP", "OneDigital", "HUB International"],
        "niche": ["Benefitfocus", "PlanSource", "Businessolver"],
        "analyst_sources": ["Kaiser Family Foundation Employer Health Benefits Survey", "Gartner Benefits Administration Hype Cycle", "Forrester Employee Benefits Wave"],
        "suppliers": {
            "Aon": {"why": "Broadest benefits consulting capability with leading actuarial and global benefit harmonization expertise.", "evidence": "$13B+ revenue; serves 90% of Fortune 500; leading broker for complex self-insured benefit programs.", "diff": "Active Health Exchange and Health Risk Assessment platforms reduce benefits cost trend for large employers.", "use_case": "Large employers managing self-insured health plans requiring actuarial consulting and global benefit harmonization."},
            "Mercer (Marsh McLennan)": {"why": "Strongest compensation and benefits benchmarking data used by 70%+ of CHRO functions for market pricing.", "evidence": "$7B+ benefits consulting revenue; largest compensation benchmarking database globally; Marsh McLennan backed.", "diff": "Mercer Total Remuneration Survey covers 150+ countries — only broker with this geographic benchmarking depth.", "use_case": "CHROs benchmarking total rewards against market and seeking strategic benefits design consulting."},
            "Willis Towers Watson": {"why": "Leading actuarial and risk consulting for large self-insured benefit programs with deep defined benefit expertise.", "evidence": "$9B+ revenue; leading in pension risk transfer and actuarial consulting for Fortune 1000 employers.", "diff": "Strongest pension and defined benefit consulting practice — critical for employers with legacy DB obligations.", "use_case": "Employers with defined benefit pension obligations or complex self-insured health arrangements requiring actuarial rigor."},
            "Gallagher": {"why": "Competitive on brokerage fees with strong vertical depth in construction, education, healthcare, and nonprofit.", "evidence": "$8B+ revenue; 45,000+ employees; recognized for middle-market benefits brokerage and specialty industries.", "diff": "Better fee competitiveness than top-3 brokers for comparable quality; strong vertical specialists in niche industries.", "use_case": "Mid-market organizations in construction, education, or nonprofit seeking Big Three alternatives at better pricing."},
        },
    },
    "Energy & Utilities": {
        "leaders": ["EDF Energy Services", "Shell Energy", "BP Energy", "Constellation Energy", "NRG Energy"],
        "challengers": ["Ameresco", "Schneider Electric Energy", "Arcadia Power"],
        "niche": ["3Degrees", "Sterling Planet", "REConnect Energy"],
        "analyst_sources": ["Wood Mackenzie Corporate Energy Procurement Report", "BloombergNEF Corporate Clean Energy Buying", "Verdantix Energy Management Software"],
        "suppliers": {
            "EDF Energy Services": {"why": "Leading renewable PPA structuring and C&I energy supply; preferred by sustainability-committed buyers.", "evidence": "Part of EDF Group ($95B+ revenue); largest clean energy supplier to US commercial and industrial customers.", "diff": "Deepest renewable energy product portfolio — physical PPAs, virtual PPAs, RECs, and green tariffs in one supplier.", "use_case": "Organizations with public renewable energy commitments seeking a structured clean energy supply agreement."},
            "Shell Energy": {"why": "Competitive natural gas and electricity supply with strong hedging, risk management, and sustainability products.", "evidence": "Shell plc ($380B+ revenue); global energy supplier with enterprise C&I supply capability in major markets.", "diff": "Trading desk access enables more sophisticated hedging and price management than smaller energy retailers.", "use_case": "Large industrial buyers with complex energy price risk seeking sophisticated hedging alongside supply."},
            "Constellation Energy": {"why": "Largest US commercial and industrial energy supplier with the broadest product range and nuclear-backed baseload.", "evidence": "$23B+ revenue; largest carbon-free energy producer in the US; serves 2M+ commercial accounts.", "diff": "Nuclear-backed baseload supply provides 24/7 carbon-free energy unavailable from solar- or wind-only suppliers.", "use_case": "Organizations requiring 24/7 carbon-free electricity to meet Science Based Targets or RE100 commitments."},
            "NRG Energy": {"why": "Strong retail energy brand with direct customer relationships and competitive spot and fixed pricing.", "evidence": "$30B+ revenue; largest competitive retail electricity provider in the US by customer count.", "diff": "Strong retail pricing team and direct customer relationships enable faster deal execution than wholesale-only suppliers.", "use_case": "Organizations seeking competitive retail electricity pricing in deregulated US markets with straightforward supply needs."},
        },
    },
    "Construction & Capital Projects": {
        "leaders": ["Turner Construction", "Skanska", "Jacobs Engineering", "AECOM", "Bechtel", "Fluor"],
        "challengers": ["Clark Construction", "McCarthy Building Companies", "Gilbane Building Company"],
        "niche": ["Procore Technologies", "Autodesk Construction Cloud", "Oracle Construction"],
        "analyst_sources": ["ENR Top Contractors List", "CBRE Capital Markets Construction Cost Report", "JLL Construction Outlook"],
        "suppliers": {
            "Turner Construction": {"why": "#1 US contractor by revenue with unmatched scale for mission-critical, healthcare, and data center builds.", "evidence": "$16B+ annual revenue; ENR #1 US contractor; led 25%+ of Fortune 500 major capital projects.", "diff": "Scale and supply chain leverage drives material cost savings unavailable to smaller contractors on large programs.", "use_case": "Large capital programs ($100M+) in healthcare, data centers, commercial office, or mission-critical facilities."},
            "Skanska": {"why": "European-origin quality standards and safety culture with a strong US commercial, healthcare, and education portfolio.", "evidence": "$18B+ global revenue; ENR Top 5 contractor; consistently highest safety ratings in the US market.", "diff": "Strongest safety culture and zero-accident performance record — critical for liability-sensitive healthcare builds.", "use_case": "Healthcare systems, universities, and public institutions prioritizing safety and long-term contractor relationships."},
            "Jacobs Engineering": {"why": "Leading program management and engineering for government and large infrastructure megaprojects globally.", "evidence": "$16B+ revenue; preferred by US DoD, UK MoD, and major transit authorities for complex infrastructure.", "diff": "Program management-first model — can manage multiple contractors under one PM umbrella for complex programs.", "use_case": "Government agencies and infrastructure owners requiring independent program management over multiple contractors."},
            "AECOM": {"why": "Largest global design-build firm preferred for complex infrastructure, transportation, and environmental projects.", "evidence": "$14B+ revenue; ENR #1 Design Firm; dominant in transit, highways, water, and environmental remediation.", "diff": "Design-build capability at global scale reduces owner coordination cost between designer and contractor.", "use_case": "Public agencies and infrastructure owners procuring design-build delivery for complex transportation or utility projects."},
            "Bechtel": {"why": "Dominant in energy, industrial, and megaproject delivery with the strongest track record in complex $1B+ builds.", "evidence": "$21B+ revenue; delivered 25,000+ projects in 160 countries; preferred for LNG, nuclear, and mining megaprojects.", "diff": "Unmatched project financing and international delivery capability for sovereign and industrial megaprojects.", "use_case": "Energy, mining, and industrial companies developing large capital projects requiring lump-sum or EPC delivery."},
        },
    },
}


# ── Data source implementations ───────────────────────────────────────

def _search_usaspending(keyword: str, limit: int = 12) -> Dict:
    payload = {
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"],
            "keywords": [keyword],
            "time_period": [{"start_date": "2021-01-01", "end_date": "2025-12-31"}],
        },
        "fields": [
            "Recipient Name", "Award Amount", "Awarding Agency Name",
            "Place of Performance City Name", "Place of Performance State Code",
        ],
        "page": 1, "limit": limit, "sort": "Award Amount", "order": "desc",
    }
    try:
        r = requests.post(
            "https://api.usaspending.gov/api/v2/search/spending_by_award/",
            json=payload, timeout=20,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code == 200:
            seen: set = set()
            suppliers = []
            for row in r.json().get("results", []):
                name = str(row.get("Recipient Name") or "").strip()
                if name and name not in seen:
                    seen.add(name)
                    suppliers.append({
                        "name": name,
                        "federal_award_amount": row.get("Award Amount", 0),
                        "agency": row.get("Awarding Agency Name", ""),
                        "location": (
                            f"{row.get('Place of Performance City Name', '')} "
                            f"{row.get('Place of Performance State Code', '')}".strip()
                        ),
                        "source": "USASpending.gov",
                        "source_tier": 2,
                        "enterprise_evidence": "Federal contract awardee — enterprise delivery proven",
                    })
            return {"suppliers": suppliers, "total": len(suppliers)}
    except Exception as e:
        return {"error": str(e), "suppliers": []}
    return {"suppliers": [], "total": 0}


def _search_sec_edgar(query: str) -> Dict:
    try:
        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{query}"', "dateRange": "custom",
                    "startdt": "2022-01-01", "forms": "10-K"},
            timeout=12,
            headers={"User-Agent": "ProcureIQ contact@procureiq.app"},
        )
        if r.status_code == 200:
            hits = r.json().get("hits", {}).get("hits", [])
            seen: set = set()
            companies = []
            for h in hits[:12]:
                src = h.get("_source", {})
                display_names = src.get("display_names") or []
                name = display_names[0].get("name", "") if display_names else src.get("entity_name", "")
                ticker = display_names[0].get("ticker", "") if display_names else ""
                if name and name not in seen:
                    seen.add(name)
                    companies.append({
                        "name": name,
                        "ticker": ticker,
                        "form": src.get("form_type", "10-K"),
                        "filed": src.get("file_date", ""),
                        "public": True,
                        "source": "SEC EDGAR (10-K filer)",
                        "source_tier": 1,
                        "enterprise_evidence": "Public 10-K filer — financials transparent and audited",
                    })
            return {"companies": companies, "total": len(companies)}
    except Exception as e:
        return {"error": str(e), "companies": []}
    return {"companies": [], "total": 0}


def _search_opencorporates(query: str, jurisdiction_code: str = "") -> Dict:
    api_key = os.getenv("OPENCORPORATES_API_KEY", "")
    if not api_key:
        return {"skipped": True, "companies": [],
                "error": "OPENCORPORATES_API_KEY not set — skipping registry search"}
    params: Dict[str, Any] = {"q": query, "format": "json", "per_page": 12, "api_token": api_key}
    if jurisdiction_code:
        params["jurisdiction_code"] = jurisdiction_code.lower()
    try:
        r = requests.get("https://api.opencorporates.com/v0.4/companies/search",
                         params=params, timeout=12)
        if r.status_code == 200:
            companies = r.json().get("results", {}).get("companies", [])
            return {
                "companies": [
                    {
                        "name": c["company"].get("name", ""),
                        "jurisdiction": c["company"].get("jurisdiction_code", ""),
                        "status": c["company"].get("current_status", ""),
                        "incorporated": c["company"].get("incorporation_date", ""),
                        "source": "Open Corporates",
                        "source_tier": 3,
                    }
                    for c in companies[:12]
                ],
                "total": len(companies),
            }
        elif r.status_code == 401:
            return {"error": "OpenCorporates API key invalid.", "companies": []}
        elif r.status_code == 429:
            return {"error": "OpenCorporates rate limit.", "companies": []}
    except Exception as e:
        return {"error": str(e), "companies": []}
    return {"companies": [], "total": 0}


# ── Tool schema ───────────────────────────────────────────────────────

_TOOLS = [
    {
        "name": "search_usaspending",
        "description": (
            "Search USASpending.gov for companies that received US federal contracts in this category. "
            "Federal contract history is Tier 2 evidence — proves real delivery capability at scale. "
            "Call with 2–3 keyword variations (e.g. 'IT managed services', 'managed IT services', 'IT outsourcing')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Category keyword (2–4 words)"},
                "limit": {"type": "integer", "description": "Results to return (default 12)"},
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "search_sec_edgar",
        "description": (
            "Search SEC EDGAR 10-K filings for publicly traded companies in this category. "
            "Public 10-K filers are Tier 1 evidence — audited financials and transparent operations. "
            "Call with 2–3 search terms to maximize coverage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Category or product keyword for 10-K search"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_opencorporates",
        "description": (
            "Search Open Corporates global company registry. Tier 3 evidence — useful for regional "
            "specialists and private companies. Only call if the key is available; skip if skipped=true."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Company or category keywords"},
                "jurisdiction_code": {"type": "string", "description": "Optional 2-letter country/state code"},
            },
            "required": ["query"],
        },
    },
]


# ── System prompt ─────────────────────────────────────────────────────

def _build_system_prompt(category: str, known_leaders: Dict) -> str:
    leaders_block = ""
    if known_leaders:
        leaders_block = f"""
Known market leaders for this category (START your analysis from these, then expand):
- Established leaders: {', '.join(known_leaders.get('leaders', [])[:6])}
- Challenger brands: {', '.join(known_leaders.get('challengers', [])[:4])}
- Niche specialists: {', '.join(known_leaders.get('niche', [])[:4])}
- Key analyst sources to reference: {', '.join(known_leaders.get('analyst_sources', [])[:3])}
"""
    return f"""\
You are a senior category manager and procurement intelligence analyst with 15+ years sourcing experience.
You advise CPOs, CFOs, and COOs. Your analysis must be defensible, evidence-based, and senior-leader ready.

Category context: {category}
{leaders_block}

DISCOVERY STRATEGY:
1. Establish market leaders first from known industry data (Gartner, Forrester, IDC, Everest)
2. Use tools to find additional suppliers — call each tool 2-3 times with different keywords
3. Expand from leaders into: direct competitors → adjacent players → niche specialists → private disruptors → VC-backed startups
4. Maintain the established shortlist as your anchor; treat emerging suppliers as the watchlist

SOURCE CREDIBILITY HIERARCHY — weight evidence accordingly:
Tier 1 (highest confidence): Gartner Magic Quadrant, Forrester Wave, IDC MarketScape, Everest PEAK Matrix,
  ISG Provider Lens, Spend Matters rankings, G2 Enterprise Grid, public 10-K filings, investor presentations
Tier 2 (strong signal): Crunchbase funding data, PitchBook, LinkedIn employee growth, press releases,
  major customer wins, federal contract awards (USASpending.gov), partnership announcements
Tier 3 (supporting): Review platforms, industry articles, conference speaker lists, job postings

SCORING DIMENSIONS (each 0–100):
1. market_leadership: Analyst recognition, revenue scale, customer count, category reputation, enterprise adoption
2. category_fit: Subcategory specificity, geography match, procurement use-case alignment
3. financial_strength: Public financials, funding runway, ownership stability, profitability signals
4. execution_capability: Implementation track record, geographic coverage, support maturity, enterprise-grade SLAs
5. innovation_strength: AI/automation capabilities, patents, product roadmap, platform differentiation
6. risk_profile: Score HIGHER for LOWER risk. Penalize: lock-in risk, client concentration, regulatory gaps, hype-driven growth, weak financials
7. strategic_procurement_fit: Negotiation leverage, pricing transparency, contract flexibility, switching feasibility

RED FLAG TRIGGERS — flag a supplier if ANY apply:
- Too small for enterprise scale (< 500 employees, < $50M revenue for enterprise category)
- Lacks category-specific proof (broad generalist, no vertical specialization)
- Weak financial health (burning cash, no funding path, no public financials)
- Hype-driven growth (marketing claims, no enterprise logos, no analyst recognition)
- Geographically concentrated (single country risk for global procurement)
- Limited implementation capability (no SI partners, no professional services practice)
- Vendor lock-in risk (proprietary data formats, no export capability, API-only integration)
- Too broad and not specialized enough for the category
- Private with low external visibility (no funding history, no case studies, no press)
- Evidence quality is weak (Tier 3 only, inconsistent across sources)

CONFIDENCE LOGIC — do not pretend certainty:
- High: Multiple Tier 1 sources, consistent evidence, recent (< 2 years), directly relevant
- Medium: One Tier 1 or multiple Tier 2 sources, mostly consistent, somewhat recent
- Low: Tier 3 sources only, limited evidence, older data, or tangential relevance

PROCUREMENT DECISION FRAMING:
For every shortlisted supplier, answer these CPO/CFO challenges:
- Why this supplier? (specific, evidence-based)
- Why not the bigger incumbent? (honest tradeoff)
- Why not the cheaper niche player? (honest tradeoff)
- What risk are we accepting?
- What would we ask in the RFI/RFP?
- What would a CFO or CPO challenge?

OUTPUT: Return ONLY valid JSON in this exact structure (no markdown, no explanation):
{{
  "category_inference": {{
    "inferred_category": "string",
    "inferred_subcategory": "string",
    "confidence": "High|Medium|Low",
    "reasoning": "string"
  }},
  "executive_shortlist": [
    {{
      "name": "Company Name",
      "public": true,
      "ticker": "TICK or null",
      "ownership": "Public|Private|VC-backed|PE-backed|Bootstrapped",
      "location": "City, Country",
      "why_included": "2-3 sentence evidence-based rationale",
      "leadership_evidence": "Specific analyst recognitions, customer logos, revenue indicators",
      "key_differentiator": "What makes this supplier uniquely valuable",
      "best_fit_use_case": "The exact procurement scenario where this supplier wins",
      "major_risks": "Top 2 risks a CPO would need to manage",
      "cfp_challenge": "What a CFO would ask about this supplier",
      "cpo_challenge": "What a CPO would challenge",
      "recommendation": "Invite to RFP|Invite to RFI|Monitor only|Exclude for now",
      "confidence": "High|Medium|Low",
      "source_tier": "Tier 1|Tier 2|Tier 3",
      "sources": ["source1", "source2"],
      "red_flags": [],
      "scores": {{
        "market_leadership": 0,
        "category_fit": 0,
        "financial_strength": 0,
        "execution_capability": 0,
        "innovation_strength": 0,
        "risk_profile": 0,
        "strategic_procurement_fit": 0
      }},
      "overall_score": 0,
      "federal_experience": false,
      "federal_award_amount": 0,
      "notes": "One-line summary for the supplier card"
    }}
  ],
  "expanded_longlist": [ /* same structure, 10-25 suppliers */ ],
  "emerging_watchlist": [ /* same structure — VC-backed startups, private disruptors, niche specialists */ ],
  "executive_summary": {{
    "headline": "One sentence portfolio assessment for VP/CPO",
    "top_recommendation": "Name of recommended supplier and concise why",
    "key_tradeoffs": "2-3 sentence honest tradeoff analysis",
    "risk_summary": "Portfolio-level risk observation",
    "cfo_challenge": "What a CFO would challenge about this entire supplier landscape",
    "cpo_challenge": "What a CPO would push back on",
    "recommended_next_step": "Specific, actionable next step (RFI, RFP, benchmark, pilot)"
  }},
  "search_summary": "What was searched and found, in one sentence",
  "total_found": 0
}}

Aim for:
- Executive shortlist: 5–10 suppliers (only the most procurement-ready)
- Expanded longlist: 10–20 additional suppliers (worth screening)
- Emerging watchlist: 3–10 disruptors and niche leaders (optional add to pool)

Score honestly. A supplier with no enterprise proof should score < 50 on execution_capability.
A supplier creating lock-in should score < 40 on risk_profile.
A category-adjacent player should score < 60 on category_fit.
"""


# ── No-key fallback ───────────────────────────────────────────────────

def _build_no_key_fallback(category: str, subcategory: str) -> Dict[str, Any]:
    """Return known market leaders when no LLM key is available."""
    leaders_data = _CATEGORY_LEADERS.get(category, {})
    leaders = leaders_data.get("leaders", [])
    challengers = leaders_data.get("challengers", [])
    niche = leaders_data.get("niche", [])

    _sup_details = leaders_data.get("suppliers", {})

    def _make_supplier(name: str, score_base: int, ownership: str = "Public",
                       recommendation: str = "Invite to RFI", confidence: str = "Medium") -> Dict:
        d = _sup_details.get(name, {})
        return {
            "name": name,
            "public": ownership == "Public",
            "ticker": None,
            "ownership": ownership,
            "location": "United States",
            "why_included": d.get("why", f"Established market leader in {category} with broad enterprise adoption and analyst recognition."),
            "leadership_evidence": d.get("evidence", f"Recognized by Gartner, Forrester, or equivalent analyst reports as a leader or major player in {category}."),
            "key_differentiator": d.get("diff", f"Proven enterprise delivery capability and scale in {category}."),
            "best_fit_use_case": d.get("use_case", f"Enterprise {subcategory} sourcing requiring a vendor with proven implementation track record."),
            "major_risks": "Pricing premium; potential lock-in with long-term contracts.",
            "cfp_challenge": "Are we paying market rate or a premium for brand recognition?",
            "cpo_challenge": "Do we have sufficient negotiation leverage with an incumbent this large?",
            "recommendation": recommendation,
            "confidence": confidence,
            "source_tier": "Tier 2",
            "sources": [
                "Static market knowledge — configure an Anthropic API key for live AI-scored discovery",
                "Scores and rankings are illustrative estimates based on known market position only",
            ],
            "red_flags": [],
            "scores": {
                "market_leadership": score_base,
                "category_fit": max(score_base - 5, 50),
                "financial_strength": max(score_base - 8, 45),
                "execution_capability": score_base,
                "innovation_strength": max(score_base - 10, 40),
                "risk_profile": max(score_base - 12, 38),
                "strategic_procurement_fit": max(score_base - 5, 45),
            },
            "overall_score": score_base,
            "federal_experience": False,
            "federal_award_amount": 0,
            "notes": (
                f"⚠️ ILLUSTRATIVE — Market leader in {category} based on static industry knowledge. "
                "Scores are estimates only. Configure an AI API key for live evidence-based scoring."
            ),
            "_is_illustrative": True,
        }

    shortlist = [_make_supplier(n, 78 - i * 3, "Public", "Invite to RFI", "Medium")
                 for i, n in enumerate(leaders[:6])]
    longlist  = [_make_supplier(n, 65 - i * 2, "Public", "Monitor only", "Low")
                 for i, n in enumerate(challengers[:4])]
    watchlist = [_make_supplier(n, 58 - i * 2, "Private", "Monitor only", "Low")
                 for i, n in enumerate(niche[:3])]

    return {
        "executive_shortlist": shortlist,
        "expanded_longlist": longlist,
        "emerging_watchlist": watchlist,
        "executive_summary": {
            "headline": (
                f"⚠️ ILLUSTRATIVE DATA — Known market leaders for {category} loaded from static knowledge. "
                "Configure an AI API key to run live evidence-based scoring."
            ),
            "top_recommendation": (
                f"{leaders[0]} (illustrative — based on general market knowledge, not live analysis)"
                if leaders else "—"
            ),
            "key_tradeoffs": (
                "All scores, rankings, and recommendations shown here are ESTIMATES derived from "
                "static industry knowledge. They have not been validated against live data sources "
                "(USASpending.gov, SEC EDGAR, or analyst databases). "
                "Do not use these scores to support a sourcing decision without running a live discovery."
            ),
            "risk_summary": (
                "Live financial health, red flag detection, and evidence tiering are UNAVAILABLE "
                "without an API key. Every supplier shown here requires independent validation "
                "before being included in an RFI or RFP."
            ),
            "cfo_challenge": (
                "These scores are not evidence-based — what validation has been done? "
                "Verify actual pricing and financial stability before committing to any supplier."
            ),
            "cpo_challenge": (
                "Illustrative rankings favour well-known incumbents. Run a live discovery scan "
                "to surface emerging challengers, private disruptors, and niche specialists "
                "that may offer better TCO or negotiation leverage."
            ),
            "recommended_next_step": (
                "Add an Anthropic API key in the AI Settings panel, then click 'Run Discovery' "
                "to replace these illustrative rankings with live AI-scored intelligence."
            ),
        },
        "search_summary": (
            f"Illustrative market leaders for {category} loaded from static knowledge. "
            "No live data sources were queried. API key required for live discovery."
        ),
        "total_found": len(shortlist) + len(longlist) + len(watchlist),
        "suppliers": shortlist + longlist + watchlist,  # backward compat
        "_fallback": True,
    }


# ── Synthesis-only prompt (Phase 2 — no tools) ───────────────────────

_SYNTHESIS_SYSTEM = """\
You are a JSON API endpoint. Your entire response must be a single raw JSON object.
Begin your response with { and end with }. No markdown. No code fences. No prose. No explanation.
If you add any text outside the JSON object, the system will break. Only output the JSON.

Each supplier object uses these exact keys:
name, public, ticker, ownership, location, why_included, leadership_evidence,
key_differentiator, best_fit_use_case, major_risks, cfp_challenge, cpo_challenge,
recommendation, confidence, source_tier, sources, red_flags, scores, overall_score,
federal_experience, federal_award_amount, notes

scores sub-object keys (each integer 0-100):
market_leadership, category_fit, financial_strength, execution_capability,
innovation_strength, risk_profile, strategic_procurement_fit

overall_score = weighted average:
market_leadership*0.20 + category_fit*0.20 + financial_strength*0.15 +
execution_capability*0.15 + innovation_strength*0.10 + risk_profile*0.10 +
strategic_procurement_fit*0.10

recommendation values (pick exactly one):
"Invite to RFP" | "Invite to RFI" | "Monitor only" | "Exclude for now"

confidence values: "High" | "Medium" | "Low"
ownership values: "Public" | "Private" | "VC-backed" | "PE-backed" | "Bootstrapped"
source_tier values: "Tier 1" | "Tier 2" | "Tier 3"

Limits: executive_shortlist 4-6 items, expanded_longlist 4-8 items, emerging_watchlist 2-4 items.
Keep all string fields under 160 characters. No trailing commas.
"""


def _clean_json(text: str) -> str:
    """Strip markdown fences and fix the most common JSON issues from LLM output."""
    # Strip code fences: ```json ... ``` or ``` ... ```
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)

    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([\}\]])", r"\1", text)

    # Remove control characters that break JSON
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text.strip()


def _parse_json_result(text: str, category: str, subcategory: str) -> Optional[Dict]:
    """Try multiple extraction strategies to get valid JSON from model output."""
    # Always clean first
    cleaned = _clean_json(text)

    # Strategy 1: parse the cleaned text directly (works when model outputs pure JSON)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 2: find the outermost { ... } block (handles preamble/postamble text)
    depth = 0
    start = -1
    end = -1
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                end = i
                break

    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Strategy 3: truncated JSON — seal open arrays/objects and retry
    if start != -1:
        fragment = cleaned[start:]
        # Remove any trailing partial token (incomplete string, key, etc.)
        # Walk back to the last complete value boundary: }, ], number, "string"
        last_safe = max(
            fragment.rfind("}"),
            fragment.rfind("]"),
        )
        if last_safe > 0:
            fragment = fragment[: last_safe + 1]

        open_b = fragment.count("{") - fragment.count("}")
        open_sq = fragment.count("[") - fragment.count("]")
        closing = "]" * max(open_sq, 0) + "}" * max(open_b, 0)
        candidate = fragment + closing
        # One more trailing-comma pass after the mechanical close
        candidate = re.sub(r",\s*([\}\]])", r"\1", candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


# ── Main entry point ──────────────────────────────────────────────────

def run_supplier_discovery_agent(
    category: str,
    subcategory: str,
    geography: str = "United States",
    company_size: str = "Enterprise",
    risk_tolerance: str = "Medium",
    sourcing_goal: str = "Cost optimization and risk reduction",
    api_key: str = "",
    max_rounds: int = 6,
) -> Dict[str, Any]:
    """
    Two-phase supplier discovery:
      Phase 1 — Tool use: scrape USASpending, SEC EDGAR, OpenCorporates (max 6 rounds)
      Phase 2 — Synthesis: dedicated no-tools call converts raw data into scored JSON

    This guarantees Phase 2 always gets a clean output turn — the model cannot
    loop into more tool calls during synthesis.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key or not _AVAILABLE:
        return _build_no_key_fallback(category, subcategory)

    known_leaders = _CATEGORY_LEADERS.get(category, {})
    system_prompt = _build_system_prompt(category, known_leaders)
    client = _ant.Anthropic(api_key=key)

    # ── Phase 1: Tool discovery ───────────────────────────────────────
    discovery_messages: List[Dict] = [
        {
            "role": "user",
            "content": (
                f"Discover suppliers for this procurement scenario using the search tools.\n\n"
                f"Category: {category}\n"
                f"Subcategory: {subcategory}\n"
                f"Geography: {geography}\n"
                f"Buyer size: {company_size}\n"
                f"Risk tolerance: {risk_tolerance}\n"
                f"Sourcing goal: {sourcing_goal}\n\n"
                f"Use each tool 1-2 times with different keywords. "
                f"When done, say DISCOVERY_COMPLETE and stop."
            ),
        }
    ]

    tool_map = {
        "search_usaspending": _search_usaspending,
        "search_sec_edgar": _search_sec_edgar,
        "search_opencorporates": _search_opencorporates,
    }

    raw_discovery_data: List[Dict] = []
    tool_call_count = 0

    for _round in range(max_rounds):
        try:
            resp = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
                max_tokens=2000,
                system=system_prompt,
                tools=_TOOLS,
                messages=discovery_messages,
            )
        except Exception as e:
            return {"error": str(e), "executive_shortlist": [], "expanded_longlist": [],
                    "emerging_watchlist": [], "executive_summary": {}, "suppliers": []}

        # If model stopped calling tools, we're done with Phase 1
        if resp.stop_reason == "end_turn":
            break

        if resp.stop_reason != "tool_use":
            break

        discovery_messages.append({"role": "assistant", "content": resp.content})
        tool_results = []

        for block in resp.content:
            if block.type != "tool_use":
                continue
            fn = tool_map.get(block.name)
            result = fn(**block.input) if fn else {"error": f"Unknown tool: {block.name}"}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })
            raw_discovery_data.append({
                "tool": block.name,
                "input": block.input,
                "result": result,
            })
            tool_call_count += 1

        discovery_messages.append({"role": "user", "content": tool_results})

        # Stop tool phase early if we have enough data
        if tool_call_count >= 4:
            break

    # ── Phase 2: Synthesis (no tools — guaranteed output turn) ────────
    # Build a compact summary of what the tools found
    discovered_companies: List[str] = []
    for entry in raw_discovery_data:
        r = entry["result"]
        for co in r.get("suppliers", []) + r.get("companies", []):
            name = co.get("name", "")
            if name and name not in discovered_companies:
                discovered_companies.append(name)

    known = known_leaders.get("leaders", []) + known_leaders.get("challengers", []) + known_leaders.get("niche", [])
    all_candidates = list(dict.fromkeys(known[:12] + discovered_companies[:20]))

    tool_summary_lines = "\n".join(
        f"- {e['tool']}({list(e['input'].values())[0] if e['input'] else ''}): "
        f"{len(e['result'].get('suppliers', e['result'].get('companies', [])))} results"
        for e in raw_discovery_data
    ) or "No tool searches completed — using known market leaders."

    synthesis_prompt = (
        f"Scored supplier brief for:\n"
        f"Category: {category} / {subcategory}\n"
        f"Geography: {geography} | Buyer: {company_size} | Risk: {risk_tolerance}\n"
        f"Goal: {sourcing_goal}\n\n"
        f"Candidate companies (from tools + market knowledge):\n"
        f"{json.dumps(all_candidates[:28])}\n\n"
        f"Tool searches ({tool_call_count} total):\n{tool_summary_lines}\n\n"
        f"Output the raw JSON object now — start your response with {{ and end with }}. "
        f"executive_shortlist: 4-6, expanded_longlist: 4-8, emerging_watchlist: 2-4. "
        f"No markdown. No explanation. Raw JSON only."
    )

    try:
        synth_resp = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
            max_tokens=7000,
            system=_SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )
    except Exception as e:
        return {"error": f"Synthesis failed: {e}", "executive_shortlist": [], "expanded_longlist": [],
                "emerging_watchlist": [], "executive_summary": {}, "suppliers": []}

    synth_text = ""
    for block in synth_resp.content:
        if hasattr(block, "text"):
            synth_text += block.text

    result = _parse_json_result(synth_text, category, subcategory)

    if result:
        result["suppliers"] = (
            result.get("executive_shortlist", [])
            + result.get("expanded_longlist", [])
            + result.get("emerging_watchlist", [])
        )
        result.setdefault("search_summary",
                          f"Scored {len(all_candidates)} candidates via {tool_call_count} searches.")
        result.setdefault("total_found", len(result["suppliers"]))
        return result

    # Final fallback — attach raw text for debugging, return known leaders
    fb = _build_no_key_fallback(category, subcategory)
    fb["_fallback"] = True
    fb["_raw_synthesis"] = synth_text[:800]  # visible in session state for debugging
    fb["error"] = (
        "Synthesis JSON could not be parsed — showing known market leaders. "
        f"Raw (first 200 chars): {synth_text[:200]!r}"
    )
    return fb
