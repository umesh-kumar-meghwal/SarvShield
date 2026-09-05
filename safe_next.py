import json
from ai_helper import call_openrouter


# =========================================================
# DEFAULT SAFE NEXT
# AI fail / quota / invalid response hone par ye chalega
# =========================================================

DEFAULT_SAFE_NEXT = {
    "recommended_action": "संदिग्ध संदेश या लिंक से इंटरैक्ट न करें",

    "why_dangerous": (
        "इस तरह की संदिग्ध गतिविधि से आपके अकाउंट, पैसे या निजी जानकारी "
        "को नुकसान पहुंच सकता है। जब तक संदेश भेजने वाले और वेबसाइट की "
        "स्वतंत्र रूप से पुष्टि न हो जाए, कोई संवेदनशील जानकारी साझा न करें।"
    ),

    "immediate_steps": [
        "संदिग्ध लिंक न खोलें और अनजान फाइल डाउनलोड न करें।",
        "OTP, पासवर्ड, PIN, बैंकिंग जानकारी या KYC जानकारी किसी के साथ साझा न करें।",
        "संदेश भेजने वाले की पहचान आधिकारिक वेबसाइट या ऐप से स्वयं सत्यापित करें।",
        "अगर आपसे तुरंत पैसे या संवेदनशील जानकारी देने के लिए कहा जा रहा है, तो बातचीत रोक दें।"
    ],

    "recovery_steps": [
        "अगर आपने अपना पासवर्ड साझा कर दिया है, तो उसे तुरंत बदलें और 2FA चालू करें।",
        "अगर बैंकिंग जानकारी साझा की है या पैसे का नुकसान हुआ है, तो तुरंत अपने बैंक के आधिकारिक चैनल से संपर्क करें।",
        "अगर साइबर फ्रॉड हुआ है, तो भारत में 1930 पर संपर्क करें और cybercrime.gov.in पर शिकायत दर्ज करें।"
    ],

    "helplines": [
        "National Cyber Crime Helpline: 1930",
        "National Cyber Crime Reporting Portal: cybercrime.gov.in"
    ]
}

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
INCIDENT CONTEXT:

- Overall Threat: {final_score}/100 ({verdict})

- User Message:
{message}

- Target Link / Domain:
{link_result.get("final_domain") or link_result.get("domain") or "N/A"}

- Scam Analysis on Site:
{link_result.get("scam_explanation", "")}

- Webpage Threat Findings:
{json.dumps(link_result.get("reasons", []), ensure_ascii=False)}

- Screenshot OCR:
{screenshot_result.get("detected_text", "")}

- Phone Status:
{phone_result.get("reputation", "UNKNOWN")}

- Scam Fingerprint:
{json.dumps(fingerprint, ensure_ascii=False)}

- Attack Chain:
{json.dumps(attack_chain, ensure_ascii=False)}
"""

    # ---------------------------------------------------------
    # AI Prompt
    # ---------------------------------------------------------

    prompt = f"""
You are SafeNext AI, an expert Cyber Defense and Fraud Incident
Recovery Coach.

Analyze the exact scam incident below and provide practical,
safe and actionable guidance.

{incident_report}

LANGUAGE RULE — VERY IMPORTANT:

- ALL user-facing explanations MUST be written in Hindi.
- "why_dangerous" MUST be in Hindi.
- "recommended_action" MUST be in Hindi.
- "immediate_steps" MUST be in Hindi.
- "recovery_steps" MUST be in Hindi.
- "helplines" can contain official names, URLs, numbers and technical
  terms in English where necessary.
- Technical terms such as OTP, PIN, KYC, UPI, 2FA, URL, password,
  bank and 1930 may remain in English.
- Do NOT write the reason/explanation in English.

IMPORTANT RULES:

1. Advice must be tailored to the exact detected threat.

2. If this is a banking/KYC/payment scam:
   - Tell the user to contact their bank through official channels.
   - If money was lost or fraud occurred, mention 1930 and
     cybercrime.gov.in.

3. If credentials may have been exposed:
   - Recommend changing the affected password.
   - Recommend enabling 2FA.
   - Recommend reviewing active sessions/devices.

4. If a suspicious link/site was involved:
   - Tell the user not to revisit it.
   - Explain what information may be at risk.

5. If identity/KYC information was requested:
   - Tell the user not to provide additional sensitive information.

6. Do NOT invent helpline numbers or official portals.

7. Keep the language simple enough for a normal user to understand.

8. Return ONLY valid JSON.
9. Do NOT return Markdown.
10. Do NOT wrap the JSON inside ```json.

Return exactly:

{{
    "recommended_action": "हिंदी में छोटा और स्पष्ट मुख्य सुझाव",

    "why_dangerous": "हिंदी में 2-3 वाक्यों में बताएं कि यह खतरा क्यों है और उपयोगकर्ता को क्या नुकसान हो सकता है।",

    "immediate_steps": [
        "अभी क्या करना है - हिंदी में",
        "दूसरा तत्काल कदम - हिंदी में",
        "तीसरा तत्काल कदम - हिंदी में",
        "चौथा तत्काल कदम - हिंदी में"
    ],

    "recovery_steps": [
        "अगर उपयोगकर्ता पहले ही जानकारी दे चुका है तो क्या करे - हिंदी में",
        "दूसरा recovery कदम - हिंदी में",
        "तीसरा recovery कदम - हिंदी में"
    ],

    "helplines": [
        "संबंधित आधिकारिक हेल्पलाइन या पोर्टल"
    ]
}}
"""

    # ---------------------------------------------------------
    # Call AI safely
    # ---------------------------------------------------------

    try:
        data = call_openrouter(prompt)

    except Exception:
        # AI error -> DEFAULT
        return {
            **DEFAULT_SAFE_NEXT,
            "safe_next": DEFAULT_SAFE_NEXT["immediate_steps"]
        }

    # ---------------------------------------------------------
    # Validate AI response
    # ---------------------------------------------------------

    if not isinstance(data, dict):
        return {
            **DEFAULT_SAFE_NEXT,
            "safe_next": DEFAULT_SAFE_NEXT["immediate_steps"]
        }

    # ---------------------------------------------------------
    # Get AI fields with safe fallbacks
    # ---------------------------------------------------------

    recommended_action = (
        data.get("recommended_action")
        or DEFAULT_SAFE_NEXT["recommended_action"]
    )

    why_dangerous = (
        data.get("why_dangerous")
        or DEFAULT_SAFE_NEXT["why_dangerous"]
    )

    immediate = data.get("immediate_steps")

    if not isinstance(immediate, list) or not immediate:
        immediate = DEFAULT_SAFE_NEXT["immediate_steps"]

    recovery = data.get("recovery_steps")

    if not isinstance(recovery, list) or not recovery:
        recovery = DEFAULT_SAFE_NEXT["recovery_steps"]

    helplines = data.get("helplines")

    if not isinstance(helplines, list) or not helplines:
        helplines = DEFAULT_SAFE_NEXT["helplines"]

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
        "safe_next": immediate
    }