import os
import requests

ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY")

# Comprehensive Country Codes & Expected National Digit Lengths
COUNTRY_METADATA = {
    "91": {"country": "India", "min_len": 10, "max_len": 10, "high_risk": False},
    "86": {"country": "China", "min_len": 11, "max_len": 11, "high_risk": True},
    "234": {"country": "Nigeria", "min_len": 10, "max_len": 10, "high_risk": True},
    "92": {"country": "Pakistan", "min_len": 10, "max_len": 10, "high_risk": True},
    "855": {"country": "Cambodia", "min_len": 8, "max_len": 9, "high_risk": True},
    "95": {"country": "Myanmar", "min_len": 8, "max_len": 10, "high_risk": True},
    "84": {"country": "Vietnam", "min_len": 9, "max_len": 10, "high_risk": True},
    "254": {"country": "Kenya", "min_len": 9, "max_len": 10, "high_risk": True},
    "1": {"country": "USA / Canada", "min_len": 10, "max_len": 10, "high_risk": False},
    "44": {"country": "United Kingdom", "min_len": 10, "max_len": 10, "high_risk": False},
    "971": {"country": "United Arab Emirates", "min_len": 9, "max_len": 9, "high_risk": False},
    "880": {"country": "Bangladesh", "min_len": 10, "max_len": 10, "high_risk": False},
    "977": {"country": "Nepal", "min_len": 10, "max_len": 10, "high_risk": False},
    "61": {"country": "Australia", "min_len": 9, "max_len": 9, "high_risk": False},
    "65": {"country": "Singapore", "min_len": 8, "max_len": 8, "high_risk": False},
    "49": {"country": "Germany", "min_len": 10, "max_len": 11, "high_risk": False},
    "33": {"country": "France", "min_len": 9, "max_len": 9, "high_risk": False},
    "81": {"country": "Japan", "min_len": 10, "max_len": 10, "high_risk": False},
    "7": {"country": "Russia", "min_len": 10, "max_len": 10, "high_risk": False},
    "966": {"country": "Saudi Arabia", "min_len": 9, "max_len": 9, "high_risk": False},
    "62": {"country": "Indonesia", "min_len": 9, "max_len": 12, "high_risk": False},
    "63": {"country": "Philippines", "min_len": 10, "max_len": 10, "high_risk": False}
}


def normalize_and_parse_phone(phone: str):
    """
    Normalizes phone numbers, detects country code, checks digit length validity,
    and flags foreign/international numbers.
    """
    raw_phone = str(phone or "").strip()
    if not raw_phone:
        return None, None, [], "Unknown", "0", False, False, False

    has_plus = raw_phone.startswith("+")
    clean_digits = "".join(c for c in raw_phone if c.isdigit())

    if not clean_digits or len(clean_digits) < 5:
        return None, None, [], "Unknown", "0", False, False, True

    candidates = {raw_phone, clean_digits, f"+{clean_digits}"}

    detected_country = "International / Unknown"
    dial_code = ""
    national_digits = clean_digits
    is_foreign = True
    is_high_risk_country = False
    length_invalid = False

    # CASE 1: Standard Indian 10-digit mobile (Starts with 6, 7, 8, 9) without country code
    if not has_plus and len(clean_digits) == 10 and clean_digits[0] in "6789":
        dial_code = "91"
        detected_country = "India"
        national_digits = clean_digits
        normalized = f"+91{clean_digits}"
        is_foreign = False
        candidates.add(normalized)
        candidates.add(f"0{clean_digits}")

    # CASE 2: Indian 11-digit starting with 0
    elif not has_plus and len(clean_digits) == 11 and clean_digits.startswith("0") and clean_digits[1] in "6789":
        dial_code = "91"
        detected_country = "India"
        national_digits = clean_digits[1:]
        normalized = f"+91{national_digits}"
        is_foreign = False
        candidates.add(normalized)
        candidates.add(national_digits)

    # CASE 3: Explicit country code match (e.g. +86, +91, +234, +1, etc.)
    else:
        # Check prefix from length 3 down to 1
        matched = False
        for code_len in (3, 2, 1):
            prefix = clean_digits[:code_len]
            if prefix in COUNTRY_METADATA:
                dial_code = prefix
                meta = COUNTRY_METADATA[prefix]
                detected_country = meta["country"]
                is_high_risk_country = meta["high_risk"]
                national_digits = clean_digits[code_len:]
                is_foreign = (prefix != "91")
                matched = True

                # Check expected national length
                if len(national_digits) < meta["min_len"] or len(national_digits) > meta["max_len"]:
                    length_invalid = True
                break

        if not matched:
            dial_code = clean_digits[:2]
            national_digits = clean_digits[2:]
            is_foreign = True
            # General fallback check: most countries have 8-11 national digits
            if len(clean_digits) < 8 or len(clean_digits) > 13:
                length_invalid = True

        normalized = f"+{clean_digits}"

    candidates.add(f"{normalized[:3]} {national_digits}")

    # Specific Indian length check (e.g., 9-digit or 8-digit Indian number is definitely spoofed)
    if not is_foreign and len(national_digits) != 10:
        length_invalid = True

    return (
        normalized,
        national_digits,
        list(candidates),
        detected_country,
        dial_code,
        is_foreign,
        is_high_risk_country,
        length_invalid
    )


def phone_detect(supabase, phone: str, language: str = "English") -> dict:
    (
        normalized_phone,
        national_number,
        candidate_formats,
        detected_country,
        dial_code,
        is_foreign,
        is_high_risk_country,
        length_invalid
    ) = normalize_and_parse_phone(phone)

    target_lang = str(language or "English").strip().lower()

    if not normalized_phone:
        return {
            "found": False, "score": 0, "status": "UNKNOWN", "reputation": "UNKNOWN",
            "valid": False, "carrier": "Unregistered", "line_type": "Invalid", "country": "Unknown",
            "report_count": 0, "reasons": ["Invalid or incomplete phone number format."]
        }

    spam_reports = 0
    repeat_checks = 0
    blacklisted = False
    whitelisted = False
    database_found = False

    # ========================================================
    # 1. SUPABASE DATABASE CHECK
    # ========================================================
    try:
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
    except Exception as e:
        print("[PHONE] Supabase spam_numbers lookup error:", repr(e))

    # ========================================================
    # 2. CHECK REPEAT SCANS
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
    # 3. TELECOM & CARRIER RESOLUTION (No ugly "Unknown")
    # ========================================================
    # Intelligent default carrier based on country rather than "Unknown"
    default_carrier = f"Cellular Network ({detected_country})" if is_foreign else "Mobile Network"
    default_line_type = "Mobile Line"

    carrier = default_carrier
    line_type = default_line_type
    country = detected_country
    is_valid = not length_invalid

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
                if carrier_info.get("name") and str(carrier_info.get("name")).lower() != "unknown":
                    carrier = str(carrier_info.get("name"))
                if carrier_info.get("line_type") and str(carrier_info.get("line_type")).lower() != "unknown":
                    line_type = str(carrier_info.get("line_type"))

                loc = data.get("phone_location", {})
                if loc.get("country_name"):
                    country = str(loc.get("country_name"))
        except Exception as e:
            print("[PHONE] Abstract API notice:", repr(e))

    # ========================================================
    # 4. INTELLIGENT THREAT & RISK SCORING ENGINE
    # ========================================================
    risk = 0

    if blacklisted:
        risk = 100
    elif whitelisted:
        risk = 0
    elif spam_reports >= 5:
        risk = 90
    elif spam_reports >= 3:
        risk = 70
    elif spam_reports >= 1:
        risk = 50
    else:
        # Base risk for unknown numbers
        risk = 0

    # THREAT FACTOR 1: Abnormal / Invalid Digit Length (e.g. 9 digits instead of 10/11)
    if length_invalid or (is_valid is False):
        risk = max(risk, 45) + 15  # Score automatically becomes 60 (High Risk / Suspicious)

    # THREAT FACTOR 2: International / Chinese / Foreign Origin Numbers
    # (Scam syndicates frequently use international VOIP / foreign numbers for task scams & digital arrest)
    if is_high_risk_country:
        # China (+86), Nigeria (+234), Cambodia (+855), Myanmar (+95), Pakistan (+92), etc.
        risk = max(risk, 55)  # Automatic SUSPICIOUS / HIGH RISK
    elif is_foreign:
        # Any other unsolicited international number
        risk = max(risk, 40)  # Automatic SUSPICIOUS (never 0 / Low Risk)

    # THREAT FACTOR 3: Virtual VOIP line
    if "voip" in line_type.lower():
        risk += 20

    # THREAT FACTOR 4: High repeat check frequency
    if repeat_checks >= 3:
        risk += 10

    final_score = max(0, min(100, risk))

    # Clean Status Label
    if final_score >= 60:
        status = "High Risk"
    elif final_score >= 30:
        status = "Suspicious"
    else:
        status = "Low Risk"

    # ========================================================
    # 5. MULTI-LANGUAGE DETAILED REASONS GENERATOR
    # ========================================================
    reasons = []
    is_hi = target_lang in ["hindi", "hi", "hinglish"]
    is_mr = target_lang in ["marathi", "mr"]
    is_pa = target_lang in ["punjabi", "pa"]
    is_ur = target_lang in ["urdu", "ur"]

    # 1. Abnormal digit length alert
    if length_invalid or (is_valid is False):
        if is_hi:
            reasons.append(f"अमान्य डिजिट लंबाई / फर्जी नंबर: इस नंबर में {len(national_number)} डिजिट हैं जो {detected_country} के मानक प्रारूप से मेल नहीं खाते (स्पूफ़्ड कॉलर आईडी का जोखिम)।")
        elif is_mr:
            reasons.append(f"अवैध नंबर फॉरमॅट: या नंबरमध्ये {len(national_number)} अंक आहेत, जे {detected_country} च्या मानकांशी जुळत नाहीत.")
        else:
            reasons.append(f"Abnormal Digit Length ({len(national_number)} digits): Does not match standard telecom length for {detected_country} (High spoofing risk).")

    # 2. International / Foreign Number Alert
    if is_high_risk_country:
        if is_hi:
            reasons.append(f"उच्च जोखिम अंतरराष्ट्रीय नंबर: यह नंबर {detected_country} (+{dial_code}) से है। साइबर अपराधी ऐसे विदेशी नंबरों का उपयोग डिजिटल अरेस्ट, पार्ट-टाइम टास्क और टेलीग्राम फ्रॉड के लिए करते हैं।")
        elif is_mr:
            reasons.append(f"धोकादायक आंतरराष्ट्रीय नंबर: हा नंबर {detected_country} (+{dial_code}) चा आहे, जो सायबर गुन्ह्यांसाठी वापरला जातो.")
        else:
            reasons.append(f"High-Risk International Origin: Originates from {detected_country} (+{dial_code}), a recognized corridor for cross-border task scams and digital arrest coercion.")
    elif is_foreign:
        if is_hi:
            reasons.append(f"अंतरराष्ट्रीय नंबर चेतावनी: यह नंबर {detected_country} (+{dial_code}) से है। बिना पूर्व पहचान के विदेशी नंबरों से संपर्क संदिग्ध माना जाता है।")
        elif is_mr:
            reasons.append(f"आंतरराष्ट्रीय नंबर इशारा: हा नंबर {detected_country} (+{dial_code}) चा आहे. अनोळखी परदेशी संपर्क संशयास्पद मानला जातो.")
        else:
            reasons.append(f"International Outreach Alert: Originates from {detected_country} (+{dial_code}). Unsolicited foreign calls or messages carry inherent social engineering risks.")

    # 3. Community Reports Status (Clear and informative)
    if spam_reports > 0:
        if is_hi:
            reasons.append(f"डेटाबेस शिकायतें: इस नंबर के खिलाफ हमारे डेटाबेस में {spam_reports} सक्रिय स्पैम/धोखाधड़ी की शिकायतें दर्ज हैं।")
        elif is_mr:
            reasons.append(f"नोंदणीकृत तक्रारी: या नंबरविरुद्ध डेटाबेसमध्ये {spam_reports} फसवणुकीच्या तक्रारी आहेत.")
        else:
            reasons.append(f"Community Reports: Found {spam_reports} verified spam/fraud complaint(s) reported against this number.")
    else:
        if is_hi:
            reasons.append("सामुदायिक रिपोर्ट: इस नंबर के खिलाफ वर्तमान में कोई सक्रिय स्पैम रिपोर्ट दर्ज नहीं है।")
        elif is_mr:
            reasons.append("कम्युनिटी रिपोर्ट: या नंबरविरुद्ध सध्या कोणतीही सक्रिय स्पॅम तक्रार नोंदवलेली नाही.")
        elif is_pa:
            reasons.append("ਕਮਿਊਨਿਟੀ ਰਿਪੋਰਟ: ਇਸ ਨੰਬਰ ਵਿਰੁੱਧ ਹਾਲੇ ਕੋਈ ਸਪੈਮ ਰਿਪੋਰਟ ਦਰਜ ਨਹੀਂ ਹੈ।")
        elif is_ur:
            reasons.append("کمیونٹی رپورٹ: اس نمبر کے خلاف فی الحال کوئی فعال اسپام رپورٹ درج نہیں ہے۔")
        else:
            reasons.append("Community Reports: This number does not have any reported community spam complaints yet.")

    # 4. VOIP Alert
    if "voip" in line_type.lower():
        if is_hi:
            reasons.append("वर्चुअल वीओआईपी (VOIP) लाइन: यह नंबर सिम कार्ड के बजाय इंटरनेट वीओआईपी सेवा पर चल रहा है, जिसका उपयोग पहचान छुपाने के लिए किया जाता है।")
        else:
            reasons.append("Virtual VOIP Line: Operated over internet calling protocols rather than a physical SIM card, commonly used to mask real identity.")

    # 5. Check Frequency
    if repeat_checks >= 3:
        if is_hi:
            reasons.append(f"बार-बार स्कैन: इस नंबर को पहले भी उपयोगकर्ताओं द्वारा {repeat_checks} बार सुरक्षा जांच के लिए स्कैन किया गया है।")
        else:
            reasons.append(f"High Check Frequency: Previously analyzed {repeat_checks} times by users on our security platform.")

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