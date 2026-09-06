# phone_detect.py
import os
import requests

ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY")

# Major Country Codes Mapping (Fallback if API is unavailable)
COUNTRY_DIAL_CODES = {
    "1": "USA / Canada",
    "44": "United Kingdom",
    "91": "India",
    "971": "United Arab Emirates",
    "92": "Pakistan",
    "880": "Bangladesh",
    "977": "Nepal",
    "61": "Australia",
    "65": "Singapore",
    "49": "Germany",
    "33": "France",
    "86": "China",
    "81": "Japan",
    "7": "Russia",
    "966": "Saudi Arabia",
    "234": "Nigeria",
    "254": "Kenya",
    "62": "Indonesia",
    "63": "Philippines",
    "39": "Italy",
    "34": "Spain"
}


def normalize_phone(phone: str):
    """
    Normalizes phone numbers of ANY country in the world
    and generates all candidate string formats to match Supabase records.
    """
    raw_phone = str(phone or "").strip()
    if not raw_phone:
        return None, None, []

    has_plus = raw_phone.startswith("+")
    clean_digits = "".join(c for c in raw_phone if c.isdigit())

    if not clean_digits or len(clean_digits) < 6:
        return None, None, []

    candidates = set()
    candidates.add(raw_phone)
    candidates.add(clean_digits)
    candidates.add(f"+{clean_digits}")

    detected_country = "Unknown"

    # CASE 1: User explicitly provided '+' with country code (Any international country)
    if has_plus:
        normalized = f"+{clean_digits}"
        national = clean_digits
        # Detect Country from prefix
        for code_len in (3, 2, 1):
            prefix = clean_digits[:code_len]
            if prefix in COUNTRY_DIAL_CODES:
                detected_country = COUNTRY_DIAL_CODES[prefix]
                national = clean_digits[code_len:]
                break

    # CASE 2: Indian 10-digit standard mobile (Starts with 6, 7, 8, 9)
    elif len(clean_digits) == 10 and clean_digits[0] in "6789":
        normalized = f"+91{clean_digits}"
        national = clean_digits
        detected_country = "India"
        candidates.add(normalized)
        candidates.add(f"0{clean_digits}")

    # CASE 3: Indian 11-digit starting with 0
    elif len(clean_digits) == 11 and clean_digits.startswith("0") and clean_digits[1] in "6789":
        national = clean_digits[1:]
        normalized = f"+91{national}"
        detected_country = "India"
        candidates.add(normalized)
        candidates.add(national)

    # CASE 4: Indian 12-digit starting with 91
    elif len(clean_digits) == 12 and clean_digits.startswith("91"):
        national = clean_digits[2:]
        normalized = f"+{clean_digits}"
        detected_country = "India"
        candidates.add(normalized)
        candidates.add(national)

    # CASE 5: Any other international number without '+'
    else:
        normalized = f"+{clean_digits}"
        national = clean_digits
        for code_len in (3, 2, 1):
            prefix = clean_digits[:code_len]
            if prefix in COUNTRY_DIAL_CODES:
                detected_country = COUNTRY_DIAL_CODES[prefix]
                national = clean_digits[code_len:]
                break

    # Add spacing variations that might be stored in database
    candidates.add(f"{normalized[:3]} {national}")
    
    return normalized, national, list(candidates), detected_country


def phone_detect(supabase, phone: str, language: str = "English") -> dict:
    normalized_phone, national_number, candidate_formats, fallback_country = normalize_phone(phone)
    target_lang = str(language or "English").strip().lower()

    if not normalized_phone:
        return {
            "found": False, "score": 0, "status": "UNKNOWN", "reputation": "UNKNOWN",
            "valid": False, "carrier": "Unknown", "line_type": "Unknown", "country": "Unknown",
            "report_count": 0, "reasons": ["Invalid or empty phone number."]
        }

    spam_reports = 0
    repeat_checks = 0
    blacklisted = False
    whitelisted = False
    database_found = False

    # ========================================================
    # 1. SUPABASE DATABASE CHECK (MULTI-FORMAT MATCHING)
    # ========================================================
    try:
        # Matches ANY format present in database (with +, without +, raw, etc.)
        db_result = (
            supabase.table("spam_numbers")
            .select("phone, report_count, reputation, score")
            .in_("phone", candidate_formats)
            .limit(1)
            .execute()
        )
        rows = db_result.data or []
        if rows:
            database_found = True
            row = rows[0]
            spam_reports = int(row.get("report_count") or 0)
            db_rep = str(row.get("reputation") or "").upper()
            if db_rep == "BLACKLISTED":
                blacklisted = True
            elif db_rep == "WHITELISTED":
                whitelisted = True
            print(f"[PHONE DB MATCH] Found: {row.get('phone')} with {spam_reports} reports")
    except Exception as e:
        print("[PHONE] Supabase spam_numbers lookup error:", repr(e))

    # ========================================================
    # 2. CHECK REPEAT SCANS IN SCAM_CHECKS
    # ========================================================
    try:
        check_result = (
            supabase.table("scam_checks")
            .select("id")
            .in_("phone", candidate_formats)
            .execute()
        )
        repeat_checks = len(check_result.data or [])
    except Exception as e:
        print("[PHONE] scam_checks lookup error:", repr(e))

    # ========================================================
    # 3. ABSTRACT API TELECOM LOOKUP (FOR ANY COUNTRY)
    # ========================================================
    carrier = "Cellular Network" if database_found else "Unknown"
    line_type = "Mobile" if database_found else "Unknown"
    country = fallback_country
    is_valid = True if database_found else None

    if ABSTRACT_API_KEY:
        try:
            response = requests.get(
                "https://phoneintelligence.abstractapi.com/v1/",
                params={"api_key": ABSTRACT_API_KEY, "phone": normalized_phone},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                val = data.get("phone_validation", {})
                if "is_valid" in val:
                    is_valid = bool(val.get("is_valid"))
                
                carrier_info = data.get("phone_carrier", {})
                if carrier_info.get("name"):
                    carrier = str(carrier_info.get("name"))
                if carrier_info.get("line_type"):
                    line_type = str(carrier_info.get("line_type"))

                loc = data.get("phone_location", {})
                if loc.get("country_name"):
                    country = str(loc.get("country_name"))
                elif loc.get("country"):
                    country = str(loc.get("country"))
        except Exception as e:
            print("[PHONE] Abstract API error:", repr(e))

    # ========================================================
    # 4. RISK SCORING ENGINE
    # ========================================================
    if blacklisted:
        risk = 100
    elif whitelisted:
        risk = 0
    elif spam_reports >= 5:
        risk = 90
    elif spam_reports >= 3:
        risk = 60
    elif spam_reports >= 1:
        risk = 45
    else:
        risk = 0

    if is_valid is False:
        risk += 40

    if "voip" in line_type.lower():
        risk += 20

    if repeat_checks >= 3:
        risk += 10

    final_score = max(0, min(100, risk))

    # Status label
    if final_score >= 60:
        status = "High Risk"
    elif final_score >= 30:
        status = "Suspicious"
    else:
        status = "Low Risk"

    # ========================================================
    # 5. MULTI-LANGUAGE REASONS GENERATOR
    # ========================================================
    reasons = []

    if target_lang in ["hindi", "hi"]:
        if spam_reports > 0:
            reasons.append(f"इस नंबर के खिलाफ डेटाबेस में {spam_reports} स्पैम शिकायतें दर्ज हैं।")
        else:
            reasons.append("सामुदायिक डेटाबेस में कोई सक्रिय शिकायत नहीं मिली।")
        if is_valid is False:
            reasons.append("यह नंबर टेलीकॉम सत्यापन में अमान्य पाया गया है।")
        if repeat_checks >= 3:
            reasons.append(f"इस नंबर को पहले भी कई बार ({repeat_checks} बार) स्कैन किया गया है।")

    elif target_lang in ["marathi", "mr"]:
        if spam_reports > 0:
            reasons.append(f"डेटाबेसमध्ये या नंबरविरुद्ध {spam_reports} फसवणुकीच्या तक्रारी आहेत.")
        else:
            reasons.append("या नंबरविरुद्ध कोणतीही सक्रिय स्पॅम तक्रार आढळली नाही.")
        if repeat_checks >= 3:
            reasons.append(f"हा नंबर अनेक वेळा ({repeat_checks} वेळा) तपासला गेला आहे.")

    elif target_lang in ["punjabi", "pa"]:
        if spam_reports > 0:
            reasons.append(f"ਇਸ ਨੰਬਰ ਵਿਰੁੱਧ ਡਾਟਾਬੇਸ ਵਿੱਚ {spam_reports} ਸ਼ਿਕਾਇਤਾਂ ਮੌਜੂਦ ਹਨ।")
        else:
            reasons.append("ਕੋਈ ਪੁਰਾਣੀ ਧੋਖਾਧੜੀ ਦੀ ਸ਼ਿਕਾਇਤ ਨਹੀਂ ਮਿਲੀ।")

    elif target_lang in ["urdu", "ur"]:
        if spam_reports > 0:
            reasons.append(f"اس فون نمبر کے خلاف ڈیٹا بیس میں {spam_reports} شکایات درج ہیں۔")
        else:
            reasons.append("ڈیٹا بیس میں کوئی فعال شکایت نہیں پائی گئی۔")

    else:  # Default English
        if spam_reports > 0:
            reasons.append(f"Found {spam_reports} verified community spam complaint(s) in database.")
        else:
            reasons.append("No active community scam complaints reported for this number.")
        if is_valid is False:
            reasons.append("Phone number failed telecom verification (unassigned or spoofed).")
        if repeat_checks >= 3:
            reasons.append(f"High check frequency detected ({repeat_checks} repeat scans).")

    return {
        "found": database_found,
        "score": final_score,
        "risk_score": final_score,
        "status": status,
        "reputation": status,
        "valid": is_valid,
        "carrier": carrier,
        "line_type": line_type,
        "country": country,
        "report_count": spam_reports,
        "repeat_checks": repeat_checks,
        "phone": normalized_phone,
        "reasons": reasons
    }