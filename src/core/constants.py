DIVISION_DISTRICTS = {
    "Dhaka":      ["Dhaka","Gazipur","Narayanganj","Narsingdi","Manikganj","Munshiganj","Faridpur","Madaripur","Gopalganj","Shariatpur","Rajbari","Kishoreganj","Tangail"],
    "Chattogram": ["Chattogram","Cox's Bazar","Rangamati","Bandarban","Khagrachari","Feni","Noakhali","Lakshmipur","Chandpur","Cumilla","Brahmanbaria"],
    "Rajshahi":   ["Rajshahi","Natore","Naogaon","Chapai Nawabganj","Pabna","Sirajganj","Bogra","Joypurhat"],
    "Khulna":     ["Khulna","Bagerhat","Satkhira","Jessore","Jhenaidah","Narail","Magura","Chuadanga","Meherpur","Kushtia"],
    "Barishal":   ["Barishal","Patuakhali","Barguna","Pirojpur","Jhalokati","Bhola"],
    "Sylhet":     ["Sylhet","Moulvibazar","Habiganj","Sunamganj"],
    "Rangpur":    ["Rangpur","Dinajpur","Thakurgaon","Panchagarh","Nilphamari","Lalmonirhat","Kurigram","Gaibandha"],
    "Mymensingh": ["Mymensingh","Jamalpur","Sherpur","Netrokona"],
}

BTRC_DIVISION_DATA = {
    "Dhaka":      {"total_subscribers_m": 23.1, "2g_pct": 18.2, "3g_pct": 28.4, "4g_pct": 53.4, "5g_available": True,  "dominant_operator": "GP"},
    "Chattogram": {"total_subscribers_m": 16.2, "2g_pct": 22.1, "3g_pct": 31.6, "4g_pct": 46.3, "5g_available": False, "dominant_operator": "Robi"},
    "Rajshahi":   {"total_subscribers_m": 11.7, "2g_pct": 28.4, "3g_pct": 32.1, "4g_pct": 39.5, "5g_available": False, "dominant_operator": "GP"},
    "Khulna":     {"total_subscribers_m": 7.9,  "2g_pct": 31.2, "3g_pct": 34.1, "4g_pct": 34.7, "5g_available": False, "dominant_operator": "BL"},
    "Barishal":   {"total_subscribers_m": 4.6,  "2g_pct": 38.4, "3g_pct": 33.2, "4g_pct": 28.4, "5g_available": False, "dominant_operator": "GP"},
    "Sylhet":     {"total_subscribers_m": 5.3,  "2g_pct": 24.1, "3g_pct": 30.2, "4g_pct": 45.7, "5g_available": False, "dominant_operator": "Robi"},
    "Rangpur":    {"total_subscribers_m": 8.6,  "2g_pct": 34.2, "3g_pct": 32.8, "4g_pct": 33.0, "5g_available": False, "dominant_operator": "GP"},
    "Mymensingh": {"total_subscribers_m": 4.3,  "2g_pct": 40.1, "3g_pct": 31.2, "4g_pct": 28.7, "5g_available": False, "dominant_operator": "GP"},
}

DISTRICT_OPERATOR_OVERRIDES = {
    "Chattogram": "Robi", "Cumilla": "Robi", "Cox's Bazar": "Robi",
    "Noakhali": "Robi", "Feni": "Robi", "Lakshmipur": "Robi",
    "Sylhet": "Robi", "Moulvibazar": "Robi", "Habiganj": "Robi", "Sunamganj": "Robi",
    "Khulna": "BL", "Jessore": "BL", "Satkhira": "BL", "Bagerhat": "BL",
    "Jhenaidah": "BL", "Kushtia": "BL", "Magura": "BL", "Narail": "BL",
}

COST_PER_ACTION = {
    "tower": {"unit": "BDT Crore per tower", "cost": 1.2, "time_months": 6},
    "fiber": {"unit": "BDT Crore per km", "cost": 0.08, "time_months": 3},
    "4g_upgrade": {"unit": "BDT Crore per site", "cost": 0.45, "time_months": 4},
    "digital_literacy": {"unit": "BDT Crore per 10k people", "cost": 0.15, "time_months": 2},
    "device_subsidy": {"unit": "BDT Crore per 1k devices", "cost": 0.3, "time_months": 1},
}

LOWER_IS_BETTER_TERMS = (
    "dropped-call", "unsuccessful-call", "packet-latency", "fault-resolution",
    "service-activation-time", "basket", "expenditure", "tariff", "price", "cost"
)

TRUSTED_SOURCES = [
    {"url": "https://btrc.gov.bd/", "name": "BTRC", "tier": 1, "category": "Regulator"},
    {"url": "https://btrc.gov.bd/site/view/news", "name": "BTRC News", "tier": 1, "category": "Regulator"},
    {"url": "https://btrc.gov.bd/site/view/press_release", "name": "BTRC Press", "tier": 1, "category": "Regulator"},
    {"url": "https://www.ptd.gov.bd/", "name": "Posts & Telecom Division", "tier": 1, "category": "Government"},
    {"url": "https://bdnews24.com/topic/Telecommunications", "name": "bdnews24 Telecom", "tier": 2, "category": "Bangladesh News"},
    {"url": "https://bdnews24.com/topic/Technology", "name": "bdnews24 Technology", "tier": 2, "category": "Bangladesh News"},
    {"url": "https://www.tbsnews.net/bangladesh/telecom", "name": "TBS Telecom", "tier": 2, "category": "Bangladesh News"},
    {"url": "https://www.thedailystar.net/business/economy", "name": "Daily Star Economy", "tier": 2, "category": "Bangladesh News"},
    {"url": "https://thefinancialexpress.com.bd/trade", "name": "Financial Express", "tier": 2, "category": "Bangladesh News"},
    {"url": "https://bssnews.net/news-flash", "name": "BSS", "tier": 2, "category": "Bangladesh News"},
    {"url": "https://www.thedailystar.net/tags/bangladesh-army", "name": "Daily Star Defense", "tier": 2, "category": "Defense"},
    {"url": "https://www.bdmilitary.com/", "name": "BDMilitary", "tier": 3, "category": "Defense"},
    {"url": "https://www.defensenews.com/global/asia-pacific/", "name": "Defense News Asia-Pacific", "tier": 3, "category": "Regional Defense"},
    {"url": "https://thediplomat.com/category/security/", "name": "The Diplomat Security", "tier": 3, "category": "Regional Security"},
]

GOOGLE_NEWS_SOURCES = [
    {"url": "https://news.google.com/rss/search?q=site:bdnews24.com+Bangladesh+telecom+OR+BTRC+OR+internet&hl=en&gl=BD&ceid=BD:en", "name": "bdnews24 via News", "tier": 2, "category": "Bangladesh News"},
    {"url": "https://news.google.com/rss/search?q=site:btrc.gov.bd+BTRC+telecom+internet+spectrum&hl=en&gl=BD&ceid=BD:en", "name": "BTRC via News", "tier": 1, "category": "Regulator"},
    {"url": "https://news.google.com/rss/search?q=Bangladesh+telecom+policy+license+spectrum+fiber&hl=en&gl=BD&ceid=BD:en", "name": "Telecom Policy News", "tier": 2, "category": "Policy"},
    {"url": "https://news.google.com/rss/search?q=Bangladesh+army+telecom+fiber+satellite+cyber+network&hl=en&gl=BD&ceid=BD:en", "name": "Bangladesh Defense Network News", "tier": 2, "category": "Defense"},
    {"url": "https://news.google.com/rss/search?q=India+Myanmar+Bay+of+Bengal+defense+cyber+satellite+submarine+cable&hl=en&gl=BD&ceid=BD:en", "name": "Neighbour Defense News", "tier": 3, "category": "Regional Defense"},
    {"url": "https://news.google.com/rss/search?q=South+Asia+cybersecurity+satellite+submarine+cable+telecom+decision&hl=en&gl=BD&ceid=BD:en", "name": "Regional Network Decisions", "tier": 3, "category": "Regional Policy"},
]

TELECOM_KEYWORDS = [
    "telecom", "broadband", "internet", "mobile", "4g", "5g", "digital", "connectivity",
    "btrc", "fiber", "bandwidth", "spectrum", "tower", "subscriber", "smartphone",
    "ict", "e-governance", "digital divide", "rural connectivity", "network",
    "grameenphone", "robi", "banglalink", "teletalk", "coverage",
    "defense", "defence", "army", "navy", "air force", "satellite", "cyber",
    "submarine cable", "national security", "resilience", "disaster", "border",
    "india", "myanmar", "china", "bay of bengal", "spectrum policy", "license",
]

SOURCE_QUOTAS = {
    "Regulator": 2,
    "Government": 1,
    "Bangladesh News": 3,
    "Policy": 2,
    "Defense": 2,
    "Regional Defense": 2,
    "Regional Policy": 2,
}

DISTRICT_MODIFIERS = {
    "Bandarban": -0.35, "Rangamati": -0.32, "Khagrachari": -0.30,
    "Sunamganj": -0.28, "Kurigram": -0.27, "Panchagarh": -0.25,
    "Sherpur": -0.22, "Netrokona": -0.20, "Barguna": -0.18,
    "Patuakhali": -0.16, "Satkhira": -0.15, "Bagerhat": -0.14,
    "Dhaka": 0.25, "Gazipur": 0.20, "Narayanganj": 0.18,
    "Chattogram": 0.22, "Sylhet": 0.15, "Rajshahi": 0.12,
}
