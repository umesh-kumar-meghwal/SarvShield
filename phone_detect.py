# phone_detect.py
import os
import requests

ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY")

def normalize_phone(phone: str):
    raw_phone = str(phone or "").strip()
    clean_digits = "".join(c for c in raw_phone if c.isdigit())
    if not clean_digits:
        return None, None
    if len(clean_digits) == 10:
        return f"+91{clean_digits}", clean_digits
    elif len(clean_digits) == 12 and clean_digits.startswith("91"):
        return f"+{clean_digits}", clean_digits[2:]
    elif len(clean_digits) == 11 and clean_digits.startswith("0"):
        return f"+91{clean_digits[1:]}", clean_digits[1:]
    return f"+{clean_digits}", clean_digits[-10:]


def phone_detect(supabase, phone: str, language: str = "English") -> dict:
    normalized_phone, national_number = normalize_phone(phone)
    if not normalized_phone:
        return {
            "found": False, "score": 0, "status": "UNKNOWN", "reputation": "UNKNOWN",
            "valid": False, "carrier": "Unknown", "line_type": "Unknown", "country": "Unknown",
            "report_count": 0, "reasons": ["Invalid or empty phone number."]
        }

    spam_reports = 0
    repeat_checks = 0
    blacklisted = False
    database_found = False

    try:
        db_result = supabase.table("spam_numbers").select("*").eq("phone", normalized_phone).limit(1).execute()
        rows = db_result.data or []
        if rows:
            database_found = True
            spam_reports = int(rows[0].get("report_count") or 0)
            if str(rows[0].get("reputation") or "").upper() == "BLACKLISTED":
                blacklisted = True
    except Exception:
        pass

    try:
        check_result = supabase.table("scam_checks").select("id").eq("phone", normalized_phone).execute()
        repeat_checks = len(check_result.data or [])
    except Exception:
        pass

    if blacklisted:
        risk = 100
    elif spam_reports >= 5:
        risk = 90
    elif spam_reports >= 3:
        risk = 60
    elif spam_reports >= 1:
        risk = 40
    else:
        risk = 0

    if repeat_checks >= 3:
        risk += 10
    final_score = min(100, risk)

    # Clean reasons format (used as input signal by safe_next and fingerprint engines to translate universally)
    reasons = [f"Community spam reports found: {spam_reports}."] if spam_reports > 0 else ["No prior community complaints found in database."]
    if repeat_checks >= 3:
        reasons.append(f"Frequent lookup frequency detected ({repeat_checks} checks).")

    return {
        "found": database_found,
        "score": final_score,
        "risk_score": final_score,
        "status": "High Risk" if final_score >= 60 else "Suspicious" if final_score >= 30 else "Low Risk",
        "reputation": "High Risk" if final_score >= 60 else "Low Risk",
        "valid": True,
        "carrier": "Cellular Network",
        "line_type": "Mobile",
        "country": "India" if normalized_phone.startswith("+91") else "Unknown",
        "report_count": spam_reports,
        "repeat_checks": repeat_checks,
        "phone": normalized_phone,
        "reasons": reasons
    }