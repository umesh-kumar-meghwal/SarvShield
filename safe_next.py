import json
from ai_helper import call_openrouter


# =========================================================
# DEFAULT SAFE NEXT
# AI fail / quota / invalid response hone par ye chalega
# =========================================================

DEFAULT_SAFE_NEXT = {
    "recommended_action": "संदिग्ध संदेश या लिंक से तुरंत इंटरैक्ट करना बंद करें।",

    "why_dangerous": (
        "यह गतिविधि धोखाधड़ी, निजी जानकारी चोरी या आर्थिक नुकसान का "
        "जोखिम पैदा कर सकती है। जब तक संदेश भेजने वाले और वेबसाइट की "
        "स्वतंत्र रूप से पुष्टि न हो जाए, कोई संवेदनशील जानकारी साझा न करें।"
    ),

    "immediate_steps": [
        "संदिग्ध लिंक न खोलें और अनजान फाइल डाउनलोड न करें।",
        "OTP, पासवर्ड, PIN, UPI, बैंकिंग या KYC जानकारी किसी के साथ साझा न करें।",
        "संदेश भेजने वाले की पहचान आधिकारिक वेबसाइट या ऐप से स्वयं सत्यापित करें।",
        "अगर आपसे तुरंत पैसे या संवेदनशील जानकारी देने के लिए कहा जा रहा है, तो बातचीत रोक दें।"
    ],

    "recovery_steps": [
        "अगर आपने पासवर्ड साझा कर दिया है, तो संबंधित पासवर्ड तुरंत बदलें और 2FA चालू करें।",
        "अगर बैंकिंग जानकारी साझा की है या पैसे का नुकसान हुआ है, तो अपने बैंक के आधिकारिक चैनल से तुरंत संपर्क करें।",
        "अगर साइबर फ्रॉड हुआ है, तो भारत में 1930 पर संपर्क करें और cybercrime.gov.in पर शिकायत दर्ज करें।"
    ],

    "helplines": [
        "National Cyber Crime Helpline: 1930",
        "National Cyber Crime Reporting Portal: cybercrime.gov.in"
    ]
}


# =========================================================
# HINDI TEXT CLEANER
# =========================================================

def clean_hindi_list(value, fallback):
    """
    AI ने गलत format दिया तो fallback इस्तेमाल होगा।
    """

    if not isinstance(value, list):
        return fallback

    cleaned = []

    for item in value:
        if isinstance(item, str):
            item = item.strip()

            if item:
                cleaned.append(item)

    return cleaned if cleaned else fallback


# =========================================================
# SAFE NEXT GENERATOR
# =========================================================

def generate_safe_next(
    final_score=0,
    verdict="UNKNOWN",
    message="",
    link_result=None,
    screenshot_result=None,
    phone_result=None,
    fingerprint=None,
    attack_chain=None
):

    # ---------------------------------------------------------
    # Normalize inputs
    # ---------------------------------------------------------

    link_result = link_result or {}
    screenshot_result = screenshot_result or {}
    phone_result = phone_result or {}
    fingerprint = fingerprint or {}
    attack_chain = attack_chain or {}

    # ---------------------------------------------------------
    # Incident Context
    # ---------------------------------------------------------

    incident_report = f"""
INCIDENT CONTEXT

Overall Threat:
{final_score}/100 ({verdict})

User Message:
{message}

Target Link / Domain:
{link_result.get("final_domain") or link_result.get("domain") or "N/A"}

Website Scam Analysis:
{link_result.get("scam_explanation", "")}

Webpage Threat Findings:
{json.dumps(link_result.get("reasons", []), ensure_ascii=False)}

Screenshot OCR:
{screenshot_result.get("detected_text", "")}

Phone Reputation:
{phone_result.get("reputation", "UNKNOWN")}

Scam Fingerprint:
{json.dumps(fingerprint, ensure_ascii=False)}

Attack Chain:
{json.dumps(attack_chain, ensure_ascii=False)}
"""

    # ---------------------------------------------------------
    # AI PROMPT
    # ---------------------------------------------------------

    prompt = f"""
तुम SafeNext AI हो।

तुम एक Cyber Defense और Fraud Incident Recovery Coach हो।

नीचे दिए गए पूरे incident का विश्लेषण करो और उपयोगकर्ता को
सरल, स्पष्ट और सुरक्षित अगले कदम बताओ।

{incident_report}


=========================================================
सबसे महत्वपूर्ण भाषा नियम
=========================================================

उपयोगकर्ता को दिखाई देने वाला पूरा explanation हिंदी में होना चाहिए।

इन सभी fields का content हिंदी में होना अनिवार्य है:

1. recommended_action
2. why_dangerous
3. immediate_steps
4. recovery_steps
5. helplines में explanation/description

English explanation बिल्कुल मत लिखो।

Technical terms English में रह सकते हैं:

OTP
PIN
KYC
UPI
URL
2FA
password
browser
domain
bank
1930

लेकिन इनके आसपास की explanation हिंदी में होनी चाहिए।


=========================================================
EXAMPLE
=========================================================

गलत:

"Multi-signal analysis complete"

सही:

"कई सुरक्षा संकेतों का विश्लेषण पूरा हुआ।"


गलत:

"Pattern analysis verified"

सही:

"संदिग्ध पैटर्न की जांच पूरी हुई।"


गलत:

"Urgency Trigger Detected"

सही:

"तत्कालता का संकेत पाया गया।"


गलत:

"Impersonation Vector Detected"

सही:

"किसी विश्वसनीय व्यक्ति या संस्था की पहचान की नकल करने का संकेत पाया गया।"


=========================================================
THREAT-SPECIFIC RULES
=========================================================

1. अगर banking / KYC / payment scam है:

- बैंक के आधिकारिक चैनल से संपर्क करने को कहो।
- अगर पैसे का नुकसान हुआ है या fraud हुआ है तो 1930 बताओ।
- cybercrime.gov.in बताओ।
- किसी अनजान व्यक्ति को OTP/PIN/UPI जानकारी न देने की सलाह दो।

2. अगर credentials expose हो सकते हैं:

- संबंधित password बदलने को कहो।
- 2FA चालू करने को कहो।
- active sessions/devices की समीक्षा करने को कहो।

3. अगर suspicious website/link मिला है:

- वेबसाइट दोबारा न खोलने को कहो।
- बताओ कि कौन-सी जानकारी जोखिम में हो सकती है।

4. अगर KYC/identity information मांगी गई है:

- अतिरिक्त sensitive information न देने को कहो।

5. अगर screenshot में suspicious content मिला है:

- screenshot में मिले संकेतों के आधार पर explanation दो।

6. अगर phone number suspicious है:

- उस नंबर से संपर्क न करने की सलाह दो।
- OTP या personal information साझा न करने की सलाह दो।

7. अगर threat कम है:

- अनावश्यक डर पैदा मत करो।
- केवल सावधानी बरतने की सलाह दो।

8. Helpline या official portal invent मत करो।

9. केवल वास्तविक और दिए गए official helpline/portal का इस्तेमाल करो।

10. भाषा सामान्य उपयोगकर्ता के लिए आसान रखो।

11. Explanation English में बिल्कुल मत दो।

12. केवल valid JSON return करो।

13. Markdown मत दो।

14. JSON को ```json में wrap मत करो।


=========================================================
OUTPUT FORMAT
=========================================================

ठीक इसी JSON structure में जवाब दो:

{{
    "recommended_action": "हिंदी में छोटा और स्पष्ट मुख्य सुझाव",

    "why_dangerous": "हिंदी में 2-3 वाक्यों में बताएं कि यह खतरा क्यों है और उपयोगकर्ता को क्या नुकसान हो सकता है।",

    "immediate_steps": [
        "हिंदी में पहला तत्काल कदम",
        "हिंदी में दूसरा तत्काल कदम",
        "हिंदी में तीसरा तत्काल कदम",
        "हिंदी में चौथा तत्काल कदम"
    ],

    "recovery_steps": [
        "हिंदी में पहला recovery कदम",
        "हिंदी में दूसरा recovery कदम",
        "हिंदी में तीसरा recovery कदम"
    ],

    "helplines": [
        "National Cyber Crime Helpline: 1930",
        "National Cyber Crime Reporting Portal: cybercrime.gov.in"
    ]
}}
"""

    # ---------------------------------------------------------
    # CALL AI
    # ---------------------------------------------------------

    try:

        data = call_openrouter(prompt)

    except Exception:

        return {
            **DEFAULT_SAFE_NEXT,

            # Frontend compatibility
            "safe_next": DEFAULT_SAFE_NEXT["immediate_steps"],

            # Language indicator
            "language": "hi"
        }

    # ---------------------------------------------------------
    # INVALID AI RESPONSE
    # ---------------------------------------------------------

    if not isinstance(data, dict):

        return {
            **DEFAULT_SAFE_NEXT,

            "safe_next": DEFAULT_SAFE_NEXT["immediate_steps"],

            "language": "hi"
        }

    # ---------------------------------------------------------
    # GET AI FIELDS
    # ---------------------------------------------------------

    recommended_action = data.get("recommended_action")

    if not isinstance(recommended_action, str):
        recommended_action = DEFAULT_SAFE_NEXT["recommended_action"]

    recommended_action = recommended_action.strip()

    if not recommended_action:
        recommended_action = DEFAULT_SAFE_NEXT["recommended_action"]


    # ---------------------------------------------------------
    # WHY DANGEROUS
    # ---------------------------------------------------------

    why_dangerous = data.get("why_dangerous")

    if not isinstance(why_dangerous, str):
        why_dangerous = DEFAULT_SAFE_NEXT["why_dangerous"]

    why_dangerous = why_dangerous.strip()

    if not why_dangerous:
        why_dangerous = DEFAULT_SAFE_NEXT["why_dangerous"]


    # ---------------------------------------------------------
    # IMMEDIATE STEPS
    # ---------------------------------------------------------

    immediate = clean_hindi_list(
        data.get("immediate_steps"),
        DEFAULT_SAFE_NEXT["immediate_steps"]
    )


    # ---------------------------------------------------------
    # RECOVERY STEPS
    # ---------------------------------------------------------

    recovery = clean_hindi_list(
        data.get("recovery_steps"),
        DEFAULT_SAFE_NEXT["recovery_steps"]
    )


    # ---------------------------------------------------------
    # HELPLINES
    # ---------------------------------------------------------

    helplines = clean_hindi_list(
        data.get("helplines"),
        DEFAULT_SAFE_NEXT["helplines"]
    )


    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    return {
        "recommended_action": recommended_action,

        "why_dangerous": why_dangerous,

        "immediate_steps": immediate,

        "recovery_steps": recovery,

        "helplines": helplines,

        # Frontend compatibility
        "safe_next": immediate,

        # Language
        "language": "hi"
    }