# phone_detect.py
import os
import requests
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY")


def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def normalize_phone(phone: str):
    raw_phone = str(phone or "").strip()
    clean_digits = "".join(c for c in raw_phone if c.isdigit())
    if not clean_digits:
        return None, None

    if len(clean_digits) == 10:
        normalized = f"+91{clean_digits}"
        national = clean_digits
    elif len(clean_digits) == 12 and clean_digits.startswith("91"):
        normalized = f"+{clean_digits}"
        national = clean_digits[2:]
    elif len(clean_digits) == 11 and clean_digits.startswith("0"):
        national = clean_digits[1:]
        normalized = f"+91{national}"
    else:
        normalized = f"+{clean_digits}"
        national = clean_digits[-10:]

    return normalized, national


def phone_detect(supabase, phone: str, language: str = "english") -> dict:
    normalized_phone, national_number = normalize_phone(phone)
    if not normalized_phone:
        return {
            "found": False,
            "score": 0,
            "risk_score": 0,
            "status": "UNKNOWN",
            "reputation": "UNKNOWN",
            "valid": False,
            "carrier": "Unknown",
            "line_type": "Unknown",
            "country": "Unknown",
            "report_count": 0,
            "source": "none",
            "reasons": ["Invalid or empty phone number provided."]
        }

    spam_reports = 0
    repeat_checks = 0
    blacklisted = False
    whitelisted = False
    database_found = False

    # 1. Supabase lookup
    try:
        db_result = (
            supabase.table("spam_numbers")
            .select("phone, report_count, reputation, score")
            .eq("phone", normalized_phone)
            .limit(1)
            .execute()
        )
        rows = db_result.data or []
        if rows:
            database_found = True
            row = rows[0]
            spam_reports = int(row.get("report_count") or 0)
            db_reputation = str(row.get("reputation") or "").upper()
            if db_reputation == "BLACKLISTED":
                blacklisted = True
            if db_reputation == "WHITELISTED":
                whitelisted = True
    except Exception as e:
        print("[PHONE] Supabase lookup error:", repr(e))

    # 2. History check
    try:
        check_result = (
            supabase.table("scam_checks")
            .select("id")
            .eq("phone", normalized_phone)
            .execute()
        )
        repeat_checks = len(check_result.data or [])
    except Exception as e:
        print("[PHONE] Scam checks history lookup error:", repr(e))

    # 3. Handle Database Match
    if database_found:
        reasons = []
        if blacklisted:
            risk = 100
            status = "High Risk"
            reasons.append("Phone number is blacklisted in community fraud records.")
        elif whitelisted:
            risk = 0
            status = "Low Risk"
            reasons.append("Phone number is present in verified whitelist.")
        elif spam_reports >= 5:
            risk = 90
            status = "High Risk"
            reasons.append(f"Number has {spam_reports} community spam complaints registered.")
        elif spam_reports >= 3:
            risk = 60
            status = "Suspicious"
            reasons.append(f"Number has {spam_reports} community complaints.")
        elif spam_reports >= 1:
            risk = 40
            status = "Suspicious"
            reasons.append(f"Number reported by {spam_reports} users as potential spam.")
        else:
            risk = 0
            status = "Low Risk"
            reasons.append("Number found in database with no active complaints.")

        if repeat_checks >= 3:
            risk += 10
            reasons.append(f"High scan frequency detected ({repeat_checks} checks).")

        final_score = max(0, min(100, risk))
        return {
            "found": True,
            "score": final_score,
            "risk_score": final_score,
            "status": status,
            "reputation": status,
            "valid": True,
            "carrier": "Community Database",
            "line_type": "Cellular",
            "country": "India" if normalized_phone.startswith("+91") else "Unknown",
            "report_count": spam_reports,
            "repeat_checks": repeat_checks,
            "source": "supabase",
            "phone": normalized_phone,
            "reasons": reasons
        }

    # 4. Abstract API Fallback
    if not ABSTRACT_API_KEY:
        return {
            "found": False,
            "score": 0,
            "risk_score": 0,
            "status": "UNKNOWN",
            "reputation": "UNKNOWN",
            "valid": None,
            "carrier": "Unknown",
            "line_type": "Unknown",
            "country": "India" if normalized_phone.startswith("+91") else "Unknown",
            "report_count": 0,
            "repeat_checks": repeat_checks,
            "source": "none",
            "phone": normalized_phone,
            "reasons": ["Number not found in community database; telecom verification unavailable."]
        }

    is_valid = None
    carrier = "Unknown"
    line_type = "Unknown"
    country = "India" if normalized_phone.startswith("+91") else "Unknown"
    is_voip = False
    api_success = False

    try:
        response = requests.get(
            "https://phoneintelligence.abstractapi.com/v1/",
            params={"api_key": ABSTRACT_API_KEY, "phone": normalized_phone},
            timeout=10
        )
        if response.status_code == 200:
            api_success = True
            data = response.json()
            val = data.get("phone_validation", {})
            is_valid = bool(val.get("is_valid"))
            is_voip = bool(val.get("is_voip", False))
            carrier_data = data.get("phone_carrier", {})
            carrier = str(carrier_data.get("name") or "Unknown")
            line_type = str(carrier_data.get("line_type") or val.get("line_type") or "Unknown")
            loc = data.get("phone_location", {})
            country = str(loc.get("country_name") or loc.get("country") or country)
    except Exception as e:
        print("[PHONE] Abstract API exception:", repr(e))

    risk = 0
    reasons = []

    if is_valid is True:
        reasons.append("Phone number passed telecom verification.")
    elif is_valid is False:
        risk += 50
        reasons.append("Phone number failed telecom validation (invalid or unassigned).")
    else:
        reasons.append("Telecom verification result unavailable.")

    line_lower = line_type.lower()
    if is_voip or "voip" in line_lower:
        risk += 25
        reasons.append("Line type is virtual VoIP (often leveraged in call-spoofing).")
    elif "landline" in line_lower:
        risk += 10
        reasons.append("Line type is standard fixed landline.")
    elif "mobile" in line_lower or "cellular" in line_lower:
        reasons.append("Standard cellular mobile line.")
    else:
        reasons.append(f"Line connection type: {line_type}.")

    if repeat_checks >= 3:
        risk += 10
        reasons.append(f"High check frequency detected ({repeat_checks} checks).")

    final_score = max(0, min(100, risk))
    status = "High Risk" if final_score >= 70 else "Spam Risk" if final_score >= 40 else "Suspicious" if final_score >= 20 else "Low Risk"

    return {
        "found": False,
        "score": final_score,
        "risk_score": final_score,
        "status": status,
        "reputation": status,
        "valid": is_valid,
        "carrier": carrier,
        "line_type": line_type,
        "country": country,
        "report_count": 0,
        "repeat_checks": repeat_checks,
        "source": "abstract_phone_intelligence" if api_success else "none",
        "phone": normalized_phone,
        "reasons": reasons
    }