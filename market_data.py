# market_data.py
# Market leaders data for ProcureIQ

import json
import os
from typing import List, Dict

_MARKET_DATA_AVAILABLE = True

# Market leaders by subcategory
MARKET_LEADERS = {
    "Cloud Infrastructure (AWS / Azure / GCP)": [
        {"name": "Amazon Web Services (AWS)", "market_share": "31%", "strength": "Broadest service catalog (200+ services), deepest enterprise penetration, strongest partner ecosystem", "watch": "Egress costs and committed spend penalties if consumption falls short", "ticker": "AMZN"},
        {"name": "Microsoft Azure", "market_share": "24%", "strength": "Best-in-class hybrid cloud and M365/Teams integration, dominant in regulated industries", "watch": "Licensing complexity; bundles can obscure true cost", "ticker": "MSFT"},
        {"name": "Google Cloud Platform (GCP)", "market_share": "12%", "strength": "Leading AI/ML capabilities, Kubernetes (invented here), competitive pricing on compute", "watch": "Smaller enterprise sales motion; less mature professional services", "ticker": "GOOGL"},
        {"name": "Oracle Cloud Infrastructure (OCI)", "market_share": "4%", "strength": "Aggressive pricing vs AWS, strong for Oracle ERP workloads, bare-metal performance", "watch": "Smaller ecosystem; strong negotiating leverage if you're an Oracle shop", "ticker": "ORCL"},
        {"name": "IBM Cloud", "market_share": "3%", "strength": "Regulated industry expertise (banking, healthcare), Red Hat OpenShift leadership", "watch": "Growth has lagged hyperscalers; evaluate roadmap carefully", "ticker": "IBM"},
    ],
    "Cybersecurity (EDR / SIEM / SOC)": [
        {"name": "CrowdStrike", "market_share": "18%", "strength": "Industry-leading EDR (Falcon platform), AI-native threat detection, fastest MTTD in independent tests", "watch": "July 2024 outage — evaluate contractual SLA and incident response commitments carefully", "ticker": "CRWD"},
        {"name": "Palo Alto Networks", "market_share": "15%", "strength": "Broadest platform (Cortex XDR, SIEM, SOAR), strong in large enterprise, consolidation play", "watch": "Platform bundling can create over-reliance; evaluate each module independently", "ticker": "PANW"},
        {"name": "Microsoft Sentinel (SIEM)", "market_share": "13%", "strength": "Native M365 integration, consumption pricing model, strong for Microsoft-heavy environments", "watch": "Costs can escalate rapidly with data volume; model ingestion costs carefully", "ticker": "MSFT"},
        {"name": "SentinelOne", "market_share": "10%", "strength": "Autonomous AI response, strong threat hunting, competitive on price vs CrowdStrike", "watch": "Smaller SOC services bench vs incumbents", "ticker": "S"},
        {"name": "Splunk (Cisco)", "market_share": "9%", "strength": "Gold standard for SIEM in large enterprises, deepest logging and analytics capabilities", "watch": "Now Cisco-owned; evaluate roadmap continuity and pricing post-acquisition", "ticker": "CSCO"},
    ],
    "HRIS / HCM Platform": [
        {"name": "Workday", "market_share": "22%", "strength": "Best-in-class for large enterprise HCM, financial planning integration, strong analytics", "watch": "High implementation cost and timeline; evaluate SI partner quality carefully", "ticker": "WDAY"},
        {"name": "SAP SuccessFactors", "market_share": "18%", "strength": "Global compliance depth, strongest for complex multi-country payroll, SAP ecosystem integration", "watch": "UI maturity lags Workday; change management investment is significant", "ticker": "SAP"},
        {"name": "Oracle HCM Cloud", "market_share": "14%", "strength": "Strong for Oracle ERP shops, deep workforce analytics, global payroll breadth", "watch": "Complex licensing; evaluate cloud vs on-premise migration path", "ticker": "ORCL"},
        {"name": "UKG (Ultimate Kronos Group)", "market_share": "11%", "strength": "Workforce management leader, strong in manufacturing and healthcare, time & attendance depth", "watch": "Recent merger integration; evaluate product roadmap consolidation progress", "ticker": "Private"},
        {"name": "ADP Workforce Now / Vantage", "market_share": "10%", "strength": "Payroll reliability, compliance track record, strong SMB to enterprise breadth", "watch": "Legacy architecture in some modules; evaluate cloud-native roadmap", "ticker": "ADP"},
    ],
    "ERP System (SAP / Oracle / etc.)": [
        {"name": "SAP S/4HANA", "market_share": "24%", "strength": "Global standard for large manufacturers, deepest supply chain and finance modules, strongest regulatory compliance library", "watch": "2027 ECC end-of-support deadline creates migration urgency — use as leverage", "ticker": "SAP"},
        {"name": "Oracle Fusion Cloud ERP", "market_share": "18%", "strength": "Strong financials, procurement (Fusion), and HCM in one suite, continuous quarterly updates", "watch": "Licensing model complexity; negotiate carefully on module bundling", "ticker": "ORCL"},
        {"name": "Microsoft Dynamics 365", "market_share": "14%", "strength": "Best value for mid-market, deep M365 integration, strong partner ecosystem for implementation", "watch": "Less mature for complex manufacturing vs SAP; evaluate fit for your industry", "ticker": "MSFT"},
        {"name": "Workday Financials", "market_share": "9%", "strength": "Best-in-class for finance and HR unified platform, fast-growing in large enterprise", "watch": "Supply chain and procurement modules less mature than SAP/Oracle", "ticker": "WDAY"},
        {"name": "Infor CloudSuite", "market_share": "7%", "strength": "Industry-specific ERP depth (food & beverage, aerospace, healthcare), strong for regulated manufacturing", "watch": "Smaller ecosystem; evaluate local SI partner quality in your region", "ticker": "Private"},
    ],
    "Payroll Processing": [
        {"name": "ADP TotalSource / Vantage", "market_share": "25%", "strength": "Most trusted payroll brand, strongest multi-state compliance, deepest regulatory update cadence", "watch": "Higher price point; negotiate SLA credits for processing errors explicitly", "ticker": "ADP"},
        {"name": "Ceridian Dayforce", "market_share": "14%", "strength": "Single unified platform for payroll, HCM, and WFM, real-time payroll processing", "watch": "Implementation complexity for large orgs; validate reference checks carefully", "ticker": "CDAY"},
        {"name": "Paychex Flex", "market_share": "12%", "strength": "Strong SMB/mid-market, broad HR services bundle, solid compliance track record", "watch": "Less competitive for large enterprise complex payroll scenarios", "ticker": "PAYX"},
        {"name": "Workday Payroll", "market_share": "10%", "strength": "Best for existing Workday HCM clients, single data model eliminates integration risk", "watch": "Narrower geographic coverage outside US/Canada/UK vs ADP", "ticker": "WDAY"},
        {"name": "UKG Ready / Pro", "market_share": "9%", "strength": "Strong workforce management integration, manufacturing and healthcare depth", "watch": "Post-merger product consolidation still in progress — validate roadmap", "ticker": "Private"},
    ],
    "CRM Platform (Salesforce / HubSpot)": [
        {"name": "Salesforce Sales Cloud", "market_share": "23%", "strength": "Industry standard CRM, deepest ecosystem (AppExchange), strongest enterprise capabilities", "watch": "Highest TCO in category; auto-renewal at 7-10% increases is standard — negotiate hard", "ticker": "CRM"},
        {"name": "Microsoft Dynamics 365 Sales", "market_share": "15%", "strength": "Best M365/Teams/LinkedIn integration, strong value if already in Microsoft ecosystem", "watch": "Less mature than Salesforce for complex sales ops; evaluate use-case fit", "ticker": "MSFT"},
        {"name": "HubSpot CRM", "market_share": "12%", "strength": "Best SMB/growth-stage value, fastest time-to-value, marketing integration strength", "watch": "Enterprise scalability limits; evaluate at 500+ user scale", "ticker": "HUBS"},
        {"name": "Oracle CX Sales", "market_share": "8%", "strength": "Strong for Oracle ERP shops, deep configure-price-quote (CPQ) capabilities", "watch": "Lagging innovation vs Salesforce; evaluate roadmap carefully", "ticker": "ORCL"},
        {"name": "SAP Sales Cloud", "market_share": "6%", "strength": "Best for SAP S/4HANA-integrated environments, strong in manufacturing sales ops", "watch": "UI maturity and ecosystem breadth trail category leaders", "ticker": "SAP"},
    ],
    "Third-Party Logistics (3PL) / Warehousing": [
        {"name": "XPO Logistics", "market_share": "8%", "strength": "Largest dedicated contract logistics in North America, strong technology platform, broad network", "watch": "High customer concentration risk; validate service levels with references in your vertical", "ticker": "XPO"},
        {"name": "DHL Supply Chain", "market_share": "7%", "strength": "Global network, strongest international capability, deep regulated industry experience", "watch": "Premium price point; negotiate SLA penalties for pick/pack accuracy explicitly", "ticker": "DPW.DE"},
        {"name": "Ryder System", "market_share": "6%", "strength": "Strong dedicated transportation + warehousing integration, fleet management expertise", "watch": "North America focus; limited global capability", "ticker": "R"},
        {"name": "GXO Logistics", "market_share": "5%", "strength": "Technology-led 3PL, strong automation investment, e-commerce fulfillment excellence", "watch": "Newer standalone company (spun from XPO 2021); evaluate financial stability", "ticker": "GXO"},
        {"name": "Geodis", "market_share": "4%", "strength": "Strong European and Asia-Pacific network, good value for omnichannel retail logistics", "watch": "Less dominant in US market vs XPO/Ryder; validate capacity in your region", "ticker": "Private"},
    ],
    "Truckload (TL) / Full Truckload": [
        {"name": "J.B. Hunt Transport", "market_share": "5%", "strength": "Largest TL carrier, Intermodal leadership, strong technology platform (J.B. Hunt 360)", "watch": "Premium pricing; strong negotiating position if you offer lane density", "ticker": "JBHT"},
        {"name": "Werner Enterprises", "market_share": "3%", "strength": "Strong temperature-controlled and dedicated TL, solid safety record", "watch": "Smaller spot capacity than J.B. Hunt; evaluate dedicated vs for-hire balance", "ticker": "WERN"},
        {"name": "Schneider National", "market_share": "3%", "strength": "Intermodal + TL breadth, strong in industrial and manufacturing verticals", "watch": "Driver retention challenges industrywide affect capacity reliability", "ticker": "SNDR"},
        {"name": "Knight-Swift", "market_share": "4%", "strength": "Largest TL company by revenue post-merger, broad capacity, strong dedicated fleet", "watch": "Post-merger integration complexity; validate service consistency with references", "ticker": "KNX"},
        {"name": "C.H. Robinson (brokerage)", "market_share": "6%", "strength": "Largest freight broker, access to 85,000+ carriers, Navisphere TMS platform", "watch": "Broker model — carrier quality can vary; negotiate carrier vetting requirements", "ticker": "CHRW"},
    ],
    "Managed Print Services (MPS)": [
        {"name": "Xerox", "market_share": "19%", "strength": "Largest dedicated MPS provider, strongest mid-market fleet management, deep analytics platform", "watch": "Hardware commoditization pressures margins — evaluate service quality vs. hardware strategy", "ticker": "XRX"},
        {"name": "HP Inc. (Managed Print)", "market_share": "16%", "strength": "Widest device compatibility, JetAdvantage platform, strong A3/A4 portfolio, dealer network depth", "watch": "Transition to HP+ subscription model creates lock-in — evaluate exit terms carefully", "ticker": "HPQ"},
        {"name": "Konica Minolta", "market_share": "12%", "strength": "Strong color printing, IT services integration (Workplace Hub), competitive TCO for mid-enterprise", "watch": "Slower digital transformation roadmap vs. pure-play IT vendors", "ticker": "KMALY"},
        {"name": "Ricoh", "market_share": "11%", "strength": "Strong document workflow automation, competitive in healthcare and legal verticals", "watch": "Japan-headquartered — validate local support capacity and parts lead times in your region", "ticker": "RICOY"},
        {"name": "Lexmark", "market_share": "8%", "strength": "Best security posture for sensitive environments (government, legal, healthcare), IoT-enabled devices", "watch": "Now Chinese-owned (Apex) — evaluate data sovereignty risk for regulated industries", "ticker": "Private"},
    ],
    "Benefits Administration": [
        {"name": "Aon (Aon Hewitt)", "market_share": "20%", "strength": "Largest benefits outsourcing firm, strongest actuary analytics, deepest compliance library across 100+ countries", "watch": "Premium pricing — validate scope carefully, cost can escalate with added modules", "ticker": "AON"},
        {"name": "Mercer (Marsh McLennan)", "market_share": "17%", "strength": "Global benchmarking data, strong in health and wealth benefits design, M&A benefits integration expertise", "watch": "Consulting-heavy model — separate advisory from admin to avoid scope creep", "ticker": "MMC"},
        {"name": "WTW (Willis Towers Watson)", "market_share": "14%", "strength": "Benefits software (Benefits Access) + consulting combined, strong for large complex benefits portfolios", "watch": "Post-merger integration with Willis ongoing — validate delivery consistency", "ticker": "WTW"},
        {"name": "Businessolver", "market_share": "8%", "strength": "Best-in-class benefits administration SaaS, highest employee engagement scores, strong AI-driven enrollment", "watch": "Smaller firm — validate implementation capacity for large-scale rollouts", "ticker": "Private"},
        {"name": "Benefitfocus (Voya)", "market_share": "6%", "strength": "Strong marketplace model, Voya financial integration, good for employer + insurer coordination", "watch": "Acquisition by Voya creates roadmap uncertainty — validate product investment timeline", "ticker": "VOYA"},
    ],
    "Recruitment Process Outsourcing (RPO)": [
        {"name": "Manpower Group (Experis)", "market_share": "14%", "strength": "Broadest global reach (75+ countries), strongest IT talent pipeline, permanent + contingent integration", "watch": "Scale can mean less customization — define SLAs by role level and geography explicitly", "ticker": "MAN"},
        {"name": "Korn Ferry", "market_share": "11%", "strength": "Executive and leadership search leadership, talent advisory integration, strong succession planning capability", "watch": "Premium pricing — evaluate for senior roles; less cost-competitive for high-volume hiring", "ticker": "KFY"},
        {"name": "Randstad Sourceright", "market_share": "10%", "strength": "Integrated RPO + MSP model, strong data analytics, competitive for hybrid workforce programs", "watch": "Ownership complexity (Randstad + Sourceright brand) — confirm single delivery governance", "ticker": "RANJY"},
        {"name": "Cielo Talent", "market_share": "8%", "strength": "Pure-play RPO specialist, highest client satisfaction in RPO benchmarks, strong Employer of Record integration", "watch": "Narrower scope than generalist HR firms — validate capacity for non-corporate functions", "ticker": "Private"},
        {"name": "AMS (Alexander Mann Solutions)", "market_share": "7%", "strength": "Strong technology-led RPO, Talent Mosaic platform, good for tech-forward hiring environments", "watch": "Post-acquisition by OMERS Private Equity — validate investment and stability", "ticker": "Private"},
    ],
    "Corporate Travel Management": [
        {"name": "American Express Global Business Travel (Amex GBT)", "market_share": "22%", "strength": "Largest corporate travel manager globally, strongest airline/hotel negotiation leverage, Neo platform", "watch": "Merger with CWT (pending regulatory review) will reshape the market — evaluate post-merger service continuity", "ticker": "GBTG"},
        {"name": "BCD Travel", "market_share": "12%", "strength": "Strong mid-market focus, TripSource platform, best value for regional programs, employee satisfaction scores", "watch": "Less global reach than Amex GBT — validate coverage in emerging markets", "ticker": "Private"},
        {"name": "Egencia (Expedia for Business)", "market_share": "9%", "strength": "Technology-first model, lowest cost platform, strong for SMB and tech-native companies", "watch": "Consumer-grade Expedia UX can create compliance gaps for complex corporate programs", "ticker": "EXPE"},
        {"name": "FCM Travel (Flight Centre)", "market_share": "7%", "strength": "Strong in Asia-Pacific and Australia, human-led service model, good for complex itinerary management", "watch": "Premium service model — evaluate whether your travel profile warrants the cost vs. self-service", "ticker": "FLT.AX"},
        {"name": "TravelPerk", "market_share": "4%", "strength": "Best UX in category, fastest-growing platform, FlexiPerk cancellation guarantee, strong SMB/startup fit", "watch": "Smaller corporate hotel and airline negotiating leverage vs. incumbents", "ticker": "Private"},
    ],
    "Software License Management (SAM)": [
        {"name": "ServiceNow (HAM/SAM)", "market_share": "18%", "strength": "Best platform integration for ITSM + SAM in one suite, AI-powered discovery, strongest enterprise deployment", "watch": "Licensing costs escalate with modules — scope the SAM build carefully to avoid over-deployment", "ticker": "NOW"},
        {"name": "Flexera", "market_share": "15%", "strength": "Deepest software intelligence data (Technopedia), strongest compliance risk management, multi-cloud visibility", "watch": "Complex implementation — allocate 3-6 months for enterprise rollout with dedicated SAM team", "ticker": "Private"},
        {"name": "Snow Software (Raynet)", "market_share": "12%", "strength": "Strong SaaS management layer, good cost optimization analytics, competitive vs. Flexera for mid-market", "watch": "Post-acquisition by private equity — validate product roadmap and support commitment", "ticker": "Private"},
        {"name": "USU Software", "market_share": "8%", "strength": "Strong in European regulated environments, SAP license optimization depth, competitive pricing", "watch": "Lower North American presence — validate local support capacity", "ticker": "USU.DE"},
        {"name": "Certero", "market_share": "5%", "strength": "Best mid-market value, strong Microsoft and Oracle compliance modules, faster deployment than Tier 1 vendors", "watch": "Smaller vendor — validate financial stability and implementation partner ecosystem", "ticker": "Private"},
    ],
    "Facilities Management (Integrated)": [
        {"name": "CBRE Group (Facilities)", "market_share": "15%", "strength": "Largest integrated FM provider globally, strongest data analytics (Host platform), real estate + FM integration", "watch": "Real estate advisory conflict — ensure FM scope is ring-fenced from brokerage incentives", "ticker": "CBRE"},
        {"name": "JLL (Jones Lang LaSalle)", "market_share": "13%", "strength": "Strong technology platform (Corrigo CMMS), sustainability reporting depth, global footprint in 80+ countries", "watch": "Premium pricing for integrated FM — negotiate KPIs and savings commitments explicitly", "ticker": "JLL"},
        {"name": "Cushman & Wakefield", "market_share": "10%", "strength": "Competitive pricing vs. CBRE/JLL, strong for multi-site corporate portfolios, good sustainability integration", "watch": "High leadership turnover in recent years — validate account team stability before award", "ticker": "CWK"},
        {"name": "ISS (International Service System)", "market_share": "9%", "strength": "Strongest self-perform capability in cleaning and catering, 500,000+ employees globally, sustainability leader", "watch": "Less technology-forward than CBRE/JLL — evaluate for service-heavy vs. data-heavy requirements", "ticker": "ISS.CO"},
        {"name": "Sodexo (FM Services)", "market_share": "8%", "strength": "Food services + FM integrated model, quality of life focus, strong in healthcare and education verticals", "watch": "Higher cost for integrated bundled model — unbundle if food services are not in scope", "ticker": "SW.PA"},
    ],
    "Marketing Technology (MarTech)": [
        {"name": "Salesforce Marketing Cloud", "market_share": "22%", "strength": "Broadest MarTech suite (email, SMS, social, journey builder), deepest CRM integration, strongest analytics", "watch": "Very high TCO — licenses, implementation, and ongoing admin costs are substantial; model carefully", "ticker": "CRM"},
        {"name": "Adobe Experience Cloud", "market_share": "18%", "strength": "Gold standard for content management (AEM) + analytics (Adobe Analytics), strongest B2B and digital commerce fit", "watch": "Complex implementation — plan 6-12 months for enterprise rollout; SI partner quality is critical", "ticker": "ADBE"},
        {"name": "HubSpot Marketing Hub", "market_share": "12%", "strength": "Best SMB/growth-stage value, fastest time-to-value, strong inbound + CRM integration, freemium entry point", "watch": "Enterprise scalability limits — evaluate at 1,000+ marketing contacts scale", "ticker": "HUBS"},
        {"name": "Oracle Eloqua / CX Marketing", "market_share": "8%", "strength": "Deep B2B demand generation, best for Oracle ERP-integrated environments, strong lead scoring", "watch": "Lagging UX vs. Salesforce/HubSpot; post-Oracle acquisition roadmap needs validation", "ticker": "ORCL"},
        {"name": "Klaviyo", "market_share": "6%", "strength": "Best-in-class for e-commerce email/SMS, fastest growing platform, deepest Shopify integration", "watch": "E-commerce focus — less suited for B2B enterprise marketing programs", "ticker": "KVYO"},
    ],
    "Legal Services (Outside Counsel)": [
        {"name": "Baker McKenzie", "market_share": "4%", "strength": "Best global legal network (77 offices, 46 countries), deepest cross-border M&A and regulatory experience", "watch": "Premium rates — negotiate AFAs (alternative fee arrangements) for predictable spend", "ticker": "Private"},
        {"name": "Linklaters", "market_share": "3%", "strength": "Top-tier Magic Circle firm, strongest capital markets and finance practice, deep regulatory compliance library", "watch": "London-centric model — validate local partner availability for your primary jurisdiction", "ticker": "Private"},
        {"name": "Dentons", "market_share": "3%", "strength": "Largest firm by headcount globally (12,000+ attorneys), best value for emerging market legal work", "watch": "Swiss verein structure creates quality variance — validate each office independently for complex matters", "ticker": "Private"},
        {"name": "Eversheds Sutherland", "market_share": "2%", "strength": "Strong corporate, employment, and IP practice, competitive rates vs. Magic Circle for routine matters", "watch": "Less depth in specialized niches (fintech, pharma regulatory) vs. dedicated boutiques", "ticker": "Private"},
        {"name": "Axiom Law (Alternative Legal)", "market_share": "5%", "strength": "Best value legal talent outsourcing, 10-40% cost reduction vs. law firms for high-volume legal work, embedded model", "watch": "Not a law firm — cannot opine on complex novel legal questions; use alongside outside counsel", "ticker": "Private"},
    ],
    "Freight / Air Cargo": [
        {"name": "FedEx Freight / Express", "market_share": "18%", "strength": "Largest U.S. freight network, strongest time-definite delivery, deepest air cargo global capacity", "watch": "Premium pricing vs. UPS — negotiate hard on volume commitments and fuel surcharge caps", "ticker": "FDX"},
        {"name": "UPS Freight / Supply Chain", "market_share": "16%", "strength": "Best-in-class reliability metrics, strongest healthcare cold-chain, deep supply chain services integration", "watch": "2023 Teamsters contract increased cost structure — model rate escalation over contract term", "ticker": "UPS"},
        {"name": "DHL Express", "market_share": "15%", "strength": "Strongest international air express (220+ countries), best emerging market coverage, GoGreen carbon program", "watch": "Less competitive on domestic U.S. vs. FedEx/UPS — evaluate lane mix carefully", "ticker": "DPW.DE"},
        {"name": "Lufthansa Cargo", "market_share": "5%", "strength": "Best pharma/life sciences certified air cargo, strong Europe-Asia corridor, strong cool-chain network", "watch": "Alliance with Air France/KLM cargo creates capacity dependencies — monitor during disruptions", "ticker": "LHAG.DE"},
        {"name": "Kuehne+Nagel (Air Logistics)", "market_share": "7%", "strength": "Global freight forwarding leader, strong spot + contract air cargo, digital booking platform (KN FreightNet)", "watch": "Forwarder model — capacity is bought from carriers, not owned; validate during peak season surges", "ticker": "KNIN.SW"},
    ],
    "Temporary Staffing (Light Industrial)": [
        {"name": "Adecco Group", "market_share": "12%", "strength": "World's largest staffing firm, strongest light industrial capacity globally, deepest compliance infrastructure", "watch": "Scale can create impersonal service — define dedicated account manager and local branch SLAs", "ticker": "ADEN.SW"},
        {"name": "ManpowerGroup / Manpower", "market_share": "10%", "strength": "Broad skill coverage (assembly, warehouse, driving), strong right-to-hire programs, global compliance track record", "watch": "Premium pricing vs. regional players — evaluate whether national scale is worth the cost premium", "ticker": "MAN"},
        {"name": "Randstad (Industrial)", "market_share": "9%", "strength": "Technology-led matching (Randstad Digital), strong volume scalability, competitive for multi-site programs", "watch": "Staffing quality varies by branch — benchmark against fill rate, retention, and ATS integration", "ticker": "RANJY"},
        {"name": "Allegis Group (Aerotek)", "market_share": "8%", "strength": "Strongest skilled trades and manufacturing, deep aerospace and defense placement, specialized recruiters", "watch": "Private firm — validate financial stability and surge capacity commitment in contract", "ticker": "Private"},
        {"name": "Tradesmen International", "market_share": "4%", "strength": "Specialized skilled trades (electricians, welders, pipefitters), union and non-union options, project staffing expertise", "watch": "Narrower scope (trades only) — not a general industrial staffing play", "ticker": "Private"},
    ],
    "Procurement Technology (P2P/S2P)": [
        {"name": "SAP Ariba", "market_share": "28%", "strength": "Largest S2P installed base globally, deepest ERP integration (S/4HANA), Ariba Network (4M+ suppliers)", "watch": "High TCO and implementation complexity — 12-18 month deployments are common; SI partner selection is critical", "ticker": "SAP"},
        {"name": "Coupa Software", "market_share": "16%", "strength": "Best UX in category, fastest time-to-value, strongest community benchmarking (Coupa Advantage), AI-native", "watch": "Post-Vista Equity acquisition — validate product roadmap and pricing strategy continuity", "ticker": "Private"},
        {"name": "Ivalua", "market_share": "8%", "strength": "Highest configurability in S2P, no-code customization, strong for complex procurement requirements", "watch": "Longer implementation vs. Coupa — plan 9-15 months for full S2P deployment", "ticker": "Private"},
        {"name": "Jaggaer", "market_share": "7%", "strength": "Strong in higher education, research, and manufacturing verticals, good supplier management module", "watch": "Post-merger integration (Determine + BravoSolution + Jaggaer) creates product complexity", "ticker": "Private"},
        {"name": "GEP (SMART by GEP)", "market_share": "6%", "strength": "Cloud-native S2P, fastest implementation timeline, strong AI roadmap, good for mid-market and emerging enterprise", "watch": "Less installed base than SAP/Coupa — validate reference sites in your industry and scale", "ticker": "Private"},
    ],
    "Fleet Management": [
        {"name": "Enterprise Fleet Management", "market_share": "20%", "strength": "Largest managed fleet in North America, deepest service network, competitive TCO for mixed fleet programs", "watch": "Consumer rental focus of parent (Enterprise Holdings) can create conflict with commercial fleet priorities", "ticker": "Private"},
        {"name": "ARI / Holman", "market_share": "14%", "strength": "Strongest analytics platform for fleet optimization, competitive driver safety programs, good for large corporate fleets", "watch": "Private firm — validate technology investment roadmap and data security posture", "ticker": "Private"},
        {"name": "Wheels / LeasePlan (Element Fleet)", "market_share": "12%", "strength": "Best EV fleet transition support, strong fuel and maintenance programs, data analytics platform", "watch": "LeasePlan/Wheels merger creates integration risk — validate service continuity in your region", "ticker": "EFN.TO"},
        {"name": "Mike Albert Fleet Solutions", "market_share": "5%", "strength": "Best SMB fleet value, competitive leasing rates, personalized service model, strong telematics integration", "watch": "Regional strength (Midwest US) — validate coverage for national fleet programs", "ticker": "Private"},
        {"name": "Geotab (Telematics)", "market_share": "15%", "strength": "World's largest commercial telematics platform (4M+ devices), deepest open API ecosystem, compliance reporting depth", "watch": "Hardware + software + reseller model can fragment support — define single point of accountability in contract", "ticker": "Private"},
    ],
    "Professional Employer Organization (PEO)": [
        {"name": "ADP TotalSource (PEO)", "market_share": "22%", "strength": "Largest PEO by worksite employees, strongest compliance infrastructure, deepest benefits purchasing power", "watch": "Higher cost vs. regional PEOs — model the benefits savings offset vs. admin fee premium", "ticker": "ADP"},
        {"name": "Insperity", "market_share": "13%", "strength": "Best service model (dedicated HR specialist per client), strongest mid-market fit, high client retention", "watch": "Premium pricing — justify with service quality; evaluate if dedicated HR model fits your size", "ticker": "NSP"},
        {"name": "TriNet", "market_share": "11%", "strength": "Best for industry-specific PEO (tech, professional services, nonprofits), competitive benefits pool", "watch": "ESAC and IRS PEO certification — verify compliance before contracting", "ticker": "TNET"},
        {"name": "Justworks", "market_share": "4%", "strength": "Best UX in PEO category, fastest onboarding, competitive for startups and growing SMBs", "watch": "Less depth for complex multi-state compliance situations vs. established PEOs", "ticker": "JW"},
        {"name": "Oasis (Paychex PEO)", "market_share": "6%", "strength": "Strong Paychex payroll integration, competitive benefits pricing, good for Paychex ecosystem clients", "watch": "Less standalone brand identity — validate dedicated PEO service team vs. Paychex generalist", "ticker": "PAYX"},
    ],
}

DEFAULT_MARKET_LEADERS = [
    {"name": "No market leader data available for this subcategory", "market_share": "—", "strength": "Use this as a starting point for your own market research.", "watch": "Search Gartner Magic Quadrant or Forrester Wave for this category.", "ticker": ""},
]

# Ensure all market leader entries also expose a description field for UI and tests
for leaders in MARKET_LEADERS.values():
    for leader in leaders:
        if "description" not in leader:
            description = leader.get("strength", "")
            watch = leader.get("watch")
            if watch:
                description = f"{description} Watch: {watch}" if description else watch
            leader["description"] = description
for leader in DEFAULT_MARKET_LEADERS:
    if "description" not in leader:
        description = leader.get("strength", "")
        watch = leader.get("watch")
        if watch:
            description = f"{description} Watch: {watch}" if description else watch
        leader["description"] = description

# Extended market leaders — delegate to Market_data.py which has all 100 subcategories
MARKET_LEADERS_EXTENDED = {}
try:
    import Market_data as _ML_EXT_MODULE
    MARKET_LEADERS_EXTENDED = getattr(_ML_EXT_MODULE, "MARKET_LEADERS_EXTENDED", {})
except Exception:
    pass

def get_market_leaders(subcategory_name: str) -> List[Dict]:
    result = MARKET_LEADERS.get(subcategory_name)
    if result is None and MARKET_LEADERS_EXTENDED:
        result = MARKET_LEADERS_EXTENDED.get(subcategory_name)
    return result if result is not None else DEFAULT_MARKET_LEADERS

def get_market_leaders_extended(subcategory_name: str) -> List[Dict]:
    try:
        import Market_data as _ml
        result = _ml.get_market_leaders_extended(subcategory_name)
        if result is not None:
            return result
    except Exception:
        pass
    return MARKET_LEADERS_EXTENDED.get(subcategory_name, DEFAULT_MARKET_LEADERS)

# Live market data integration
try:
    import yfinance as yf
    _YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    _YFINANCE_AVAILABLE = False

def get_market_data_for_supplier(ticker: str) -> Dict:
    """
    Fetch live market data for a supplier's stock ticker.
    Returns current price, market cap, P/E ratio, and recent performance.
    """
    if not _YFINANCE_AVAILABLE or not ticker:
        return {"error": "Market data service unavailable or invalid ticker"}
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get recent data
        hist = stock.history(period="1mo")
        
        data = {
            "ticker": ticker,
            "current_price": info.get("currentPrice", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
            "volume": info.get("volume", "N/A"),
            "avg_volume": info.get("averageVolume", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "beta": info.get("beta", "N/A"),
            "recent_performance": {
                "1d_change": hist["Close"].pct_change().iloc[-1] if len(hist) > 1 else 0,
                "1w_change": hist["Close"].pct_change(5).iloc[-1] if len(hist) > 5 else 0,
                "1m_change": (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) if len(hist) > 1 else 0
            } if len(hist) > 0 else {}
        }
        
        return data
    except Exception as e:
        return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}

def get_supplier_financial_health(ticker: str) -> Dict:
    """
    Analyze supplier's financial health indicators.
    """
    if not _YFINANCE_AVAILABLE or not ticker:
        return {"error": "Market data service unavailable"}
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Financial health indicators
        health = {
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "return_on_equity": info.get("returnOnEquity", "N/A"),
            "profit_margins": info.get("profitMargins", "N/A"),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "earnings_growth": info.get("earningsGrowth", "N/A"),
            "free_cash_flow": info.get("freeCashflow", "N/A"),
            "total_revenue": info.get("totalRevenue", "N/A"),
            "gross_margins": info.get("grossMargins", "N/A")
        }
        
        return health
    except Exception as e:
        return {"error": f"Failed to fetch financial data for {ticker}: {str(e)}"}