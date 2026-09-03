# phone_detecte.py

import os
import requests
from supabase import create_client


# ============================================================
# CONFIG
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY")


# ============================================================
# SUPABASE CLIENT
# ============================================================

def get_supabase():

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_URL or SUPABASE_KEY is missing."
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


# ============================================================
# PHONE NORMALIZATION
# ============================================================

def normalize_phone(phone):

    raw_phone = str(phone or "").strip()

    clean_digits = "".join(
        c for c in raw_phone
        if c.isdigit()
    )

    if not clean_digits:
        return None, None

    # Indian 10 digit number
    if len(clean_digits) == 10:

        normalized = f"+91{clean_digits}"
        national = clean_digits

    # 91XXXXXXXXXX
    elif (
        len(clean_digits) == 12
        and clean_digits.startswith("91")
    ):

        normalized = f"+{clean_digits}"
        national = clean_digits[2:]

    # 0XXXXXXXXXX
    elif (
        len(clean_digits) == 11
        and clean_digits.startswith("0")
    ):

        national = clean_digits[1:]
        normalized = f"+91{national}"

    else:

        normalized = f"+{clean_digits}"
        national = clean_digits[-10:]

    return normalized, national


# ============================================================
# MAIN PHONE DETECTOR
# ============================================================

def phone_detect(supabase, phone):

    normalized_phone, national_number = normalize_phone(
        phone
    )

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
            "reasons": [
                "Invalid or empty phone number."
            ]
        }

    print()
    print("=" * 65)
    print("             SARVSHIELD PHONE DETECTOR")
    print("=" * 65)

    print(f"📱 Input Phone : {phone}")
    print(f"📞 Normalized  : {normalized_phone}")

    # ========================================================
    # VARIABLES
    # ========================================================

    spam_reports = 0
    repeat_checks = 0

    blacklisted = False
    whitelisted = False

    database_found = False

    # ========================================================
    # 1. SUPABASE DATABASE CHECK FIRST
    # ========================================================

    print()
    print("-" * 65)
    print("1️⃣  CHECKING SUPABASE COMMUNITY DATABASE")
    print("-" * 65)

    try:

        db_result = (
            supabase
            .table("spam_numbers")
            .select(
                "phone, report_count, reputation, score"
            )
            .eq(
                "phone",
                normalized_phone
            )
            .limit(1)
            .execute()
        )

        rows = db_result.data or []

        if rows:

            database_found = True

            row = rows[0]

            spam_reports = int(
                row.get("report_count") or 0
            )

            db_reputation = str(
                row.get("reputation") or ""
            ).upper()

            if db_reputation == "BLACKLISTED":
                blacklisted = True

            if db_reputation == "WHITELISTED":
                whitelisted = True

            print("✅ NUMBER FOUND IN SUPABASE")
            print(
                f"📊 Report Count : {spam_reports}"
            )
            print(
                f"🚨 Reputation   : {db_reputation}"
            )

        else:

            print(
                "❌ NUMBER NOT FOUND IN SUPABASE"
            )

            print(
                "➡️ Going to Abstract Phone Intelligence..."
            )

    except Exception as e:

        print(
            "❌ SUPABASE ERROR:",
            repr(e)
        )

        # DB failed = do NOT pretend it was a clean number
        print(
            "⚠️ Database lookup failed."
        )

    # ========================================================
    # 2. PREVIOUS SCAM CHECK COUNT
    # ========================================================

    try:

        check_result = (
            supabase
            .table("scam_checks")
            .select("id")
            .eq(
                "phone",
                normalized_phone
            )
            .execute()
        )

        repeat_checks = len(
            check_result.data or []
        )

        print(
            f"🔎 Previous Checks : {repeat_checks}"
        )

    except Exception as e:

        print(
            "⚠️ scam_checks lookup failed:",
            repr(e)
        )

    # ========================================================
    # 3. IF NUMBER EXISTS IN SUPABASE
    # ========================================================
    #
    # User wanted:
    #
    # DATABASE FIRST
    #       ↓
    # FOUND → use DB result
    #       ↓
    # NOT FOUND → Abstract API
    #
    # ========================================================

    if database_found:

        print()
        print("-" * 65)
        print("2️⃣  SUPABASE RESULT")
        print("-" * 65)

        reasons = []

        # ----------------------------------------------------
        # BLACKLISTED
        # ----------------------------------------------------

        if blacklisted:

            risk = 100

            status = "High Risk"

            reasons.append(
                "Number is blacklisted in the community database."
            )

        # ----------------------------------------------------
        # WHITELISTED
        # ----------------------------------------------------

        elif whitelisted:

            risk = 0

            status = "Low Risk"

            reasons.append(
                "Number is present in the trusted whitelist."
            )

        # ----------------------------------------------------
        # 5+ REPORTS
        # ----------------------------------------------------

        elif spam_reports >= 5:

            risk = 90

            status = "High Risk"

            reasons.append(
                f"This phone number has {spam_reports} "
                "community complaints."
            )

            reasons.append(
                "Multiple community reports indicate "
                "high spam/scam risk."
            )

        # ----------------------------------------------------
        # 3-4 REPORTS
        # ----------------------------------------------------

        elif spam_reports >= 3:

            risk = 60

            status = "Suspicious"

            reasons.append(
                f"This phone number has {spam_reports} "
                "community reports."
            )

            reasons.append(
                "Multiple users have flagged this number."
            )

        # ----------------------------------------------------
        # 1-2 REPORTS
        # ----------------------------------------------------

        elif spam_reports >= 1:

            risk = 40

            status = "Suspicious"

            reasons.append(
                f"This phone number has {spam_reports} "
                "community report(s)."
            )

        # ----------------------------------------------------
        # 0 REPORT
        # ----------------------------------------------------

        else:

            risk = 0

            status = "Low Risk"

            reasons.append(
                "Number exists in database but "
                "has no active complaints."
            )

        # ----------------------------------------------------
        # REPEATED CHECKS
        # ----------------------------------------------------

        if repeat_checks >= 3:

            risk += 10

            reasons.append(
                f"High check frequency detected "
                f"({repeat_checks} scans)."
            )

        final_score = max(
            0,
            min(100, risk)
        )

        print(
            f"🎯 Risk Score : {final_score}/100"
        )

        print(
            f"🚨 Status     : {status}"
        )

        print(
            f"📊 Reports    : {spam_reports}"
        )

        print()
        print("📝 Reasons:")

        for reason in reasons:

            print(
                f"   • {reason}"
            )

        print("=" * 65)

        return {
            "found": True,
            "score": final_score,
            "risk_score": final_score,
            "status": status,
            "reputation": status,
            "valid": None,
            "carrier": "Community Database",
            "line_type": "Unknown",
            "country": (
                "India"
                if normalized_phone.startswith("+91")
                else "Unknown"
            ),
            "report_count": spam_reports,
            "repeat_checks": repeat_checks,
            "source": "supabase",
            "phone": normalized_phone,
            "reasons": reasons
        }

    # ========================================================
    # 4. ABSTRACT PHONE INTELLIGENCE
    # ========================================================

    print()
    print("-" * 65)
    print("2️⃣  ABSTRACT PHONE INTELLIGENCE API")
    print("-" * 65)

    if not ABSTRACT_API_KEY:

        print(
            "❌ ABSTRACT_API_KEY is not configured."
        )

        return {
            "found": False,
            "score": 0,
            "risk_score": 0,
            "status": "UNKNOWN",
            "reputation": "UNKNOWN",
            "valid": None,
            "carrier": "Unknown",
            "line_type": "Unknown",
            "country": "India",
            "report_count": 0,
            "repeat_checks": repeat_checks,
            "source": "none",
            "phone": normalized_phone,
            "reasons": [
                "Phone number was not found "
                "in community database.",
                "Abstract API key is missing."
            ]
        }

    is_valid = None
    carrier = "Unknown"
    line_type = "Unknown"
    country = (
        "India"
        if normalized_phone.startswith("+91")
        else "Unknown"
    )

    is_voip = False

    api_success = False

    try:

        print(
            "🌐 Calling Phone Intelligence API..."
        )

        response = requests.get(
            "https://phoneintelligence.abstractapi.com/v1/",
            params={
                "api_key": ABSTRACT_API_KEY,
                "phone": normalized_phone
            },
            timeout=10
        )

        print(
            "API HTTP Status:",
            response.status_code
        )

        if response.status_code == 200:

            api_success = True

            data = response.json()

            print("✅ Abstract API response received.")

            # =================================================
            # PHONE VALIDATION
            # =================================================

            validation = data.get(
                "phone_validation",
                {}
            )

            if "is_valid" in validation:

                is_valid = bool(
                    validation.get("is_valid")
                )

            # =================================================
            # CARRIER
            # =================================================

            carrier_data = data.get(
                "phone_carrier",
                {}
            )

            if carrier_data.get("name"):

                carrier = str(
                    carrier_data.get("name")
                )

            # =================================================
            # LINE TYPE
            # =================================================

            if carrier_data.get("line_type"):

                line_type = str(
                    carrier_data.get("line_type")
                )

            # Some API responses may expose it
            # directly in validation.

            if (
                line_type == "Unknown"
                and validation.get("line_type")
            ):

                line_type = str(
                    validation.get("line_type")
                )

            # =================================================
            # VOIP
            # =================================================

            is_voip = bool(
                validation.get(
                    "is_voip",
                    False
                )
            )

            # =================================================
            # LOCATION
            # =================================================

            location = data.get(
                "phone_location",
                {}
            )

            if location.get("country_name"):

                country = str(
                    location.get("country_name")
                )

            elif location.get("country"):

                country = str(
                    location.get("country")
                )

            print()
            print("📡 PHONE INTELLIGENCE RESULT")
            print(
                f"✔️ Valid     : {is_valid}"
            )
            print(
                f"🏢 Carrier   : {carrier}"
            )
            print(
                f"📞 Line Type : {line_type}"
            )
            print(
                f"🌍 Country   : {country}"
            )

        else:

            print(
                "❌ Abstract API Error:"
            )

            print(
                response.text
            )

    except requests.exceptions.Timeout:

        print(
            "❌ Abstract API timeout."
        )

    except requests.exceptions.RequestException as e:

        print(
            "❌ Abstract API request error:",
            repr(e)
        )

    except Exception as e:

        print(
            "❌ Abstract API error:",
            repr(e)
        )

    # ========================================================
    # 5. TELECOM + RISK ENGINE
    # ========================================================

    print()
    print("-" * 65)
    print("3️⃣  TELECOM & RISK ENGINE (LAYER 1 + 2)")
    print("-" * 65)

    risk = 0

    reasons = []

    # ========================================================
    # VALIDITY
    # ========================================================

    if is_valid is True:

        reasons.append(
            "Phone number passed telecom validation."
        )

    elif is_valid is False:

        risk += 50

        reasons.append(
            "Phone number failed telecom validation."
        )

    else:

        reasons.append(
            "Phone validation result is unavailable."
        )

    # ========================================================
    # LINE TYPE
    # ========================================================

    line_lower = line_type.lower()

    if is_voip or "voip" in line_lower:

        risk += 25

        reasons.append(
            "Line type is VoIP."
        )

    elif "landline" in line_lower:

        risk += 10

        reasons.append(
            "Line type is landline."
        )

    elif "mobile" in line_lower:

        reasons.append(
            "Standard cellular mobile connection."
        )

    else:

        reasons.append(
            f"Line type: {line_type}."
        )

    # ========================================================
    # COMMUNITY REPORTS
    # ========================================================

    if spam_reports > 0:

        risk += 40

        reasons.append(
            f"Number has {spam_reports} "
            "community spam report(s)."
        )

    else:

        reasons.append(
            "No previous community spam reports found."
        )

    # ========================================================
    # REPEATED CHECKS
    # ========================================================

    if repeat_checks >= 3:

        risk += 10

        reasons.append(
            f"High check frequency detected "
            f"({repeat_checks} scans)."
        )

    # ========================================================
    # BLACKLIST
    # ========================================================

    if blacklisted:

        risk += 100

        reasons.append(
            "Number is blacklisted."
        )

    # ========================================================
    # WHITELIST
    # ========================================================

    if whitelisted:

        risk -= 100

        reasons.append(
            "Number is trusted by whitelist."
        )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    final_score = max(
        0,
        min(100, risk)
    )

    # ========================================================
    # STATUS
    # ========================================================

    if final_score >= 70:

        status = "High Risk"

    elif final_score >= 40:

        status = "Spam Risk"

    elif final_score >= 20:

        status = "Suspicious"

    else:

        status = "Low Risk"

    # ========================================================
    # FINAL SOURCE
    # ========================================================

    if api_success:

        source = "abstract_phone_intelligence"

    else:

        source = "none"

    # ========================================================
    # FINAL TERMINAL RESULT
    # ========================================================

    print()
    print("=" * 65)
    print("                    FINAL RESULT")
    print("=" * 65)

    print(
        f"📱 Phone       : {normalized_phone}"
    )

    print(
        f"📡 Source      : {source}"
    )

    print(
        f"🎯 Risk Score  : {final_score}/100"
    )

    print(
        f"🚨 Status      : {status}"
    )

    print(
        f"📊 Reports     : {spam_reports}"
    )

    if is_valid is True:

        validity_text = "✓ Valid Number"

    elif is_valid is False:

        validity_text = "✗ Invalid Number"

    else:

        validity_text = "⚠ Validation Unavailable"

    print(
        f"✔️ Valid       : {validity_text}"
    )

    print(
        f"🏢 Carrier     : {carrier}"
    )

    print(
        f"📞 Line Type   : {line_type}"
    )

    print(
        f"🌍 Country     : {country}"
    )

    print()
    print("📝 Reasons:")

    for reason in reasons:

        print(
            f"   • {reason}"
        )

    print("=" * 65)

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
        "report_count": spam_reports,
        "repeat_checks": repeat_checks,
        "source": source,
        "phone": normalized_phone,
        "reasons": reasons
    }


# ============================================================
# DIRECT TERMINAL TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("             SARVSHIELD PHONE TEST")
    print("=" * 65)

    # --------------------------------------------------------
    # REAL SUPABASE
    # --------------------------------------------------------

    try:

        supabase = get_supabase()

        print("✅ Supabase connected.")

    except Exception as e:

        print()
        print(
            "❌ Supabase connection failed:"
        )

        print(
            repr(e)
        )

        print()
        print(
            "Set these variables first:"
        )

        print(
            "SUPABASE_URL"
        )

        print(
            "SUPABASE_KEY"
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # REAL PHONE INPUT
    # --------------------------------------------------------

    test_phone = input(
        "\n📱 Enter phone number: "
    ).strip()

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    result = phone_detect(
        supabase,
        test_phone
    )

    print()
    print("Python Return Object:")
    print(result)