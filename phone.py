import os
import requests
from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY", "").strip()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()


# =========================================================
# DEFAULT PHONE NUMBER
# =========================================================

DEFAULT_PHONE = "9116640818"


# =========================================================
# NORMALIZE PHONE NUMBER
# =========================================================

def normalize_phone(phone):

    raw_phone = str(phone or "").strip()

    clean_digits = "".join(
        filter(str.isdigit, raw_phone)
    )

    if not clean_digits:
        return None, None

    if len(clean_digits) < 7:
        return None, None

    # India 10 digit number
    if len(clean_digits) == 10:

        normalized_phone = f"+91{clean_digits}"
        national_number = clean_digits

    # 91XXXXXXXXXX
    elif (
        len(clean_digits) == 12
        and clean_digits.startswith("91")
    ):

        normalized_phone = f"+{clean_digits}"
        national_number = clean_digits[2:]

    # Already international
    else:

        normalized_phone = f"+{clean_digits}"
        national_number = clean_digits[-10:]

    return normalized_phone, national_number


# =========================================================
# SUPABASE REQUEST
# =========================================================

def supabase_get(table, params):

    if not SUPABASE_URL:

        print("❌ SUPABASE_URL is missing.")

        return []

    if not SUPABASE_KEY:

        print("❌ SUPABASE_KEY is missing.")

        return []

    url = f"{SUPABASE_URL}/rest/v1/{table}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:

            print(
                "\n❌ Supabase HTTP Error:",
                response.status_code
            )

            print(response.text)

            return []

        return response.json()

    except requests.exceptions.Timeout:

        print("❌ Supabase request timed out.")

        return []

    except Exception as e:

        print(
            "❌ Supabase Error:",
            repr(e)
        )

        return []


# =========================================================
# ABSTRACT PHONE INTELLIGENCE API
# =========================================================

def abstract_phone_intelligence(phone):

    if not ABSTRACT_API_KEY:

        print(
            "\n❌ ABSTRACT_API_KEY is missing."
        )

        return None

    print(
        "\n🌐 Calling Abstract Phone Intelligence API..."
    )

    url = "https://phoneintelligence.abstractapi.com/v1/"

    params = {
        "api_key": ABSTRACT_API_KEY,
        "phone": phone
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print(
            "📡 Abstract API HTTP Status:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "❌ Abstract API Error:"
            )

            print(response.text)

            return None

        data = response.json()

        return data

    except requests.exceptions.Timeout:

        print(
            "❌ Abstract API request timed out."
        )

        return None

    except Exception as e:

        print(
            "❌ Abstract API Error:",
            repr(e)
        )

        return None


# =========================================================
# DATABASE RESULT SCORING
# =========================================================

def database_result(row, normalized_phone):

    report_count = int(
        row.get("report_count") or 0
    )

    database_reputation = str(
        row.get("reputation") or ""
    ).upper()

    reasons = []

    # -----------------------------------------------------
    # BLACKLIST
    # -----------------------------------------------------

    if database_reputation == "BLACKLISTED":

        score = 100

        status = "SPAM / SCAM"

        reasons.append(
            "Number is blacklisted in the community database."
        )

    # -----------------------------------------------------
    # WHITELIST
    # -----------------------------------------------------

    elif database_reputation == "WHITELISTED":

        score = 0

        status = "VERIFIED"

        reasons.append(
            "Number is present in the safe whitelist."
        )

    # -----------------------------------------------------
    # 5+ REPORTS
    # -----------------------------------------------------

    elif report_count >= 5:

        score = 90

        status = "SPAM / SCAM"

        reasons.extend([
            f"This phone number has {report_count} community complaints.",
            "Multiple reports indicate high scam/spam risk."
        ])

    # -----------------------------------------------------
    # 3-4 REPORTS
    # -----------------------------------------------------

    elif report_count >= 3:

        score = 60

        status = "SUSPICIOUS"

        reasons.extend([
            f"This phone number has {report_count} community reports.",
            "Multiple users have flagged this number as suspicious."
        ])

    # -----------------------------------------------------
    # 1-2 REPORTS
    # -----------------------------------------------------

    elif report_count >= 1:

        score = 30

        status = "SUSPICIOUS"

        reasons.extend([
            f"This phone number has {report_count} report(s).",
            "Number has limited community abuse history."
        ])

    # -----------------------------------------------------
    # 0 REPORTS
    # -----------------------------------------------------

    else:

        score = 0

        status = "VERIFIED"

        reasons.append(
            "No active complaints recorded."
        )

    return {
        "phone": normalized_phone,
        "source": "supabase",
        "found": True,
        "score": score,
        "risk_score": score,
        "reputation": status,
        "status": status,
        "valid": None,
        "carrier": "Not checked",
        "line_type": "Not checked",
        "country": "Not checked",
        "report_count": report_count,
        "reasons": reasons
    }


# =========================================================
# ABSTRACT API RESULT SCORING
# =========================================================

def api_result(data, normalized_phone):

    # =====================================================
    # GET VALIDATION DATA
    # =====================================================

    valid = data.get("valid")

    carrier = data.get("carrier") or "Unknown"

    line_type = data.get("line_type") or "Unknown"

    # Country can be string or object
    country_data = data.get("country")

    if isinstance(country_data, dict):

        country = (
            country_data.get("name")
            or country_data.get("code")
            or "Unknown"
        )

    else:

        country = country_data or "Unknown"

    # =====================================================
    # RISK SCORE
    # =====================================================

    score = 0

    reasons = [
        "No scam reports found in the community database."
    ]

    # -----------------------------------------------------
    # INVALID NUMBER
    # -----------------------------------------------------

    if valid is False:

        score += 50

        reasons.append(
            "Phone number failed telecom validation."
        )

    elif valid is True:

        reasons.append(
            "Phone number passed telecom validation."
        )

    # -----------------------------------------------------
    # LINE TYPE
    # -----------------------------------------------------

    line_type_lower = str(
        line_type
    ).lower()

    if "voip" in line_type_lower:

        score += 25

        reasons.append(
            "Number uses a VoIP line."
        )

    elif "landline" in line_type_lower:

        score += 10

        reasons.append(
            "Number is registered as a landline."
        )

    elif "mobile" in line_type_lower:

        reasons.append(
            "Number is registered as a mobile line."
        )

    # -----------------------------------------------------
    # LIMIT SCORE
    # -----------------------------------------------------

    score = min(
        max(score, 0),
        100
    )

    # =====================================================
    # FINAL STATUS
    # =====================================================

    if score >= 40:

        status = "SPAM / SCAM"

    elif score >= 20:

        status = "SUSPICIOUS"

    elif valid is True:

        status = "VERIFIED"

    else:

        status = "LOW RISK"

    return {
        "phone": normalized_phone,
        "source": "abstract_api",
        "found": False,
        "score": score,
        "risk_score": score,
        "reputation": status,
        "status": status,
        "valid": valid,
        "carrier": carrier,
        "line_type": line_type,
        "country": country,
        "report_count": 0,
        "reasons": reasons
    }


# =========================================================
# MAIN PHONE DETECTOR
# =========================================================

def phone_detect(phone):

    print()
    print("=" * 65)
    print("              SARVSHIELD PHONE DETECTOR")
    print("=" * 65)

    print(
        f"\n📱 Input Phone: {phone}"
    )

    # =====================================================
    # NORMALIZE
    # =====================================================

    normalized_phone, national_number = normalize_phone(
        phone
    )

    if not normalized_phone:

        result = {
            "phone": phone,
            "source": "none",
            "found": False,
            "score": 0,
            "risk_score": 0,
            "reputation": "UNKNOWN",
            "status": "UNKNOWN",
            "valid": False,
            "carrier": "Unknown",
            "line_type": "Unknown",
            "country": "Unknown",
            "report_count": 0,
            "reasons": [
                "Invalid or incomplete phone number provided."
            ]
        }

        print_result(result)

        return result

    print(
        f"📞 Normalized: {normalized_phone}"
    )

    # =====================================================
    # STEP 1 — SUPABASE FIRST
    # =====================================================

    print()
    print("-" * 65)
    print("1️⃣  SUPABASE COMMUNITY DATABASE CHECK")
    print("-" * 65)

    spam_rows = supabase_get(
        "spam_numbers",
        {
            "phone": f"eq.{normalized_phone}",
            "select": "phone,report_count,reputation,score"
        }
    )

    # =====================================================
    # DATABASE FOUND
    # =====================================================

    if spam_rows:

        print(
            "\n✅ NUMBER FOUND IN DATABASE"
        )

        result = database_result(
            spam_rows[0],
            normalized_phone
        )

        # IMPORTANT:
        # API WILL NOT BE CALLED

        print(
            "\n🚫 ABSTRACT API SKIPPED"
        )

        print(
            "Reason: Number already exists in spam_numbers."
        )

        print_result(result)

        return result

    # =====================================================
    # DATABASE NOT FOUND
    # =====================================================

    print(
        "\n❌ NUMBER NOT FOUND IN DATABASE"
    )

    print(
        "➡️ Moving to Abstract API..."
    )

    # =====================================================
    # STEP 2 — ABSTRACT API
    # =====================================================

    api_data = abstract_phone_intelligence(
        normalized_phone
    )

    # =====================================================
    # API FAILED
    # =====================================================

    if api_data is None:

        result = {
            "phone": normalized_phone,
            "source": "none",
            "found": False,
            "score": 0,
            "risk_score": 0,
            "reputation": "UNKNOWN",
            "status": "UNKNOWN",
            "valid": None,
            "carrier": "Unknown",
            "line_type": "Unknown",
            "country": "Unknown",
            "report_count": 0,
            "reasons": [
                "Number was not found in community database.",
                "Abstract Phone Intelligence API failed."
            ]
        }

        print_result(result)

        return result

    # =====================================================
    # API SUCCESS
    # =====================================================

    print(
        "\n✅ Abstract API response received."
    )

    result = api_result(
        api_data,
        normalized_phone
    )

    print_result(result)

    return result


# =========================================================
# PRINT FINAL RESULT
# =========================================================

def print_result(result):

    print()
    print("=" * 65)
    print("                    FINAL RESULT")
    print("=" * 65)

    print(
        f"📱 Phone       : {result.get('phone')}"
    )

    print(
        f"📡 Source      : {result.get('source')}"
    )

    print(
        f"🎯 Risk Score  : {result.get('score')}/100"
    )

    print(
        f"🚨 Status      : {result.get('status')}"
    )

    print(
        f"📊 Reports     : {result.get('report_count')}"
    )

    print(
        f"✔️ Valid       : {result.get('valid')}"
    )

    print(
        f"🏢 Carrier     : {result.get('carrier')}"
    )

    print(
        f"📞 Line Type   : {result.get('line_type')}"
    )

    print(
        f"🌍 Country     : {result.get('country')}"
    )

    print("\n📝 Reasons:")

    for reason in result.get("reasons", []):

        print(
            f"   • {reason}"
        )

    print("=" * 65)


# =========================================================
# RUN PHONE.PY DIRECTLY
# =========================================================

if __name__ == "__main__":

    print(
        "\n🔧 Configuration:"
    )

    print(
        "   Supabase URL :",
        "OK" if SUPABASE_URL else "MISSING"
    )

    print(
        "   Supabase Key :",
        "OK" if SUPABASE_KEY else "MISSING"
    )

    print(
        "   Abstract Key :",
        "OK" if ABSTRACT_API_KEY else "MISSING"
    )

    # -----------------------------------------------------
    # CHANGE THIS NUMBER WHEN YOU WANT TO TEST ANOTHER ONE
    # -----------------------------------------------------

    phone_detect(DEFAULT_PHONE)