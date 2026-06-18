import re
from .constants import DIVISION_DISTRICTS, BTRC_DIVISION_DATA, DISTRICT_OPERATOR_OVERRIDES

def parse_number(value):
    text = str(value or "").replace(",", "").replace("-", "").strip()
    text = re.sub(r"[^0-9.]", "", text)
    return float(text) if text else 0.0

def normalize_division_name(name):
    key = re.sub(r"[^a-z]", "", str(name or "").lower())
    aliases = {
        "barisal": "Barishal",
        "barishal": "Barishal",
        "chattogram": "Chattogram",
        "chittagong": "Chattogram",
        "khulna": "Khulna",
        "mymensing": "Mymensingh",
        "mymensingh": "Mymensingh",
        "rajshahi": "Rajshahi",
        "rangpur": "Rangpur",
        "sylhet": "Sylhet",
        "dhaka": "Dhaka",
    }
    return aliases.get(key)

def normalize_district_name(name):
    key = re.sub(r"[^a-z]", "", str(name or "").lower())
    aliases = {
        "barisal": "Barishal",
        "brahamanbaria": "Brahmanbaria",
        "brahmanbaria": "Brahmanbaria",
        "chittagong": "Chattogram",
        "chattogram": "Chattogram",
        "comilla": "Cumilla",
        "cumilla": "Cumilla",
        "coxcbazar": "Cox's Bazar",
        "coxsbazar": "Cox's Bazar",
        "khagrachhari": "Khagrachari",
        "khagrachari": "Khagrachari",
        "maulvibazar": "Moulvibazar",
        "moulvibazar": "Moulvibazar",
        "netrakona": "Netrokona",
        "netrokona": "Netrokona",
        "nawabganj": "Chapai Nawabganj",
        "chapainawabganj": "Chapai Nawabganj",
    }
    return aliases.get(key, str(name or "").strip())

def get_district_division(district_name):
    normalized = normalize_district_name(district_name)
    for div, districts in DIVISION_DISTRICTS.items():
        if normalized in districts:
            return div
    return "Dhaka"

def get_dominant_operator(district_name, division_name):
    normalized = normalize_district_name(district_name)
    return DISTRICT_OPERATOR_OVERRIDES.get(
        normalized,
        BTRC_DIVISION_DATA.get(division_name, {}).get("dominant_operator", "N/A")
    )

def indicator_display_name(token):
    return token.split("_")[0].replace("-", " ").title()
