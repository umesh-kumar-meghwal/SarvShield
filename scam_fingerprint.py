import json
from ai_helper import call_openrouter


# =========================================================
# DEFAULT FALLBACK
# =========================================================

DEFAULT_FINGERPRINT = {
    "scam_fingerprint": [
        "सुरक्षा संकेत"
    ],

    "attack_chain": [
        "चरण 1: दिए गए incident data का विश्लेषण किया गया।",
        "चरण 2: उपलब्ध संदिग्ध संकेतों की पहचान की गई।",
        "चरण 3: पहचाने गए संकेतों के आधार पर संभावित खतरे का मूल्यांकन किया गया।"
    ],

    "evidence": [
        "उपलब्ध incident data में सुरक्षा संबंधी संकेत पाए गए।"
    ],

    "why": (
        "उपलब्ध जानकारी में कुछ सुरक्षा संकेत पाए गए हैं। "
        "इन संकेतों के आधार पर incident का खतरा मूल्यांकित किया गया है।"
    ),

    "risk_score": 0,
    "risk_level": "कम जोखिम"
}


# =========================================================
# SAFE INTEGER
# =========================================================

def safe_int(value, default=0):

    try:
        value = int(float(value))

        if value < 0:
            return 0

        if value > 100:
            return 100

        return value

    except (TypeError, ValueError):
        return default


# =========================================================
# RISK LEVEL
# =========================================================

def get_risk_level(score):

    score = safe_int(score)

    if score >= 80:
        return "बहुत अधिक जोखिम"

    elif score >= 60:
        return "उच्च जोखिम"

    elif score >= 30:
        return "मध्यम जोखिम"

    else:
        return "कम जोखिम"


# =========================================================
# BUILD SCAM FINGERPRINT
# =========================================================

def build_scam_fingerprint(
    message="",
    phone_result=None,
    link_result=None,
    screenshot_result=None,
    language="hindi"
):

    phone_result = phone_result or {}
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}

    # ---------------------------------------------------------
    # INPUT DATA
    # ---------------------------------------------------------

    domain = (
        link_result.get("final_domain")
        or link_result.get("domain")
        or "N/A"
    )

    link_reasons = link_result.get("reasons", [])
    exact_scam_lines = link_result.get("exact_scam_lines", [])

    screenshot_text = screenshot_result.get(
        "detected_text",
        ""
    )

    screenshot_category = screenshot_result.get(
        "category",
        "N/A"
    )

    phone_reputation = phone_result.get(
        "reputation",
        "UNKNOWN"
    )

    phone_score = safe_int(
        phone_result.get("score", 0)
    )

    link_score = safe_int(
        link_result.get("score", 0)
        or link_result.get("risk_score", 0)
        or link_result.get("final_score", 0)
    )

    screenshot_score = safe_int(
        screenshot_result.get("score", 0)
        or screenshot_result.get("risk_score", 0)
        or screenshot_result.get("final_score", 0)
    )

    # ---------------------------------------------------------
    # INCIDENT DATA
    # ---------------------------------------------------------

    incident_data = f"""
INCIDENT INPUTS

MESSAGE:
{message}

LINK / DOMAIN:
{domain}

LINK SCAM ANALYSIS:
{link_result.get("scam_explanation", "")}

LINK THREAT REASONS:
{json.dumps(link_reasons, ensure_ascii=False)}

EXACT SCAM LINES:
{json.dumps(exact_scam_lines, ensure_ascii=False)}

SCREENSHOT TEXT:
{json.dumps(screenshot_text, ensure_ascii=False)}

SCREENSHOT CATEGORY:
{screenshot_category}

PHONE REPUTATION:
{phone_reputation}

PHONE SCORE:
{phone_score}

LINK SCORE:
{link_score}

SCREENSHOT SCORE:
{screenshot_score}
"""

    # ---------------------------------------------------------
    # AI PROMPT
    # ---------------------------------------------------------

    prompt = f"""
तुम एक Cyber Threat और Scam Pattern Analyst हो।

तुम्हें नीचे दिए गए वास्तविक incident data का विश्लेषण करना है।

{incident_data}


==================================================
मुख्य उद्देश्य
==================================================

इस incident के आधार पर:

1. Scam Fingerprint बनाओ।
2. Attack Chain बनाओ।
3. महत्वपूर्ण Evidence निकालो।
4. बताओ कि incident को suspicious क्यों माना गया।
5. उपलब्ध signals के आधार पर 0-100 Risk Score दो।


==================================================
भाषा नियम
==================================================

सभी AI-generated explanations हिंदी में होने चाहिए।

इन fields में English explanation नहीं होनी चाहिए:

- scam_fingerprint
- attack_chain
- evidence
- why
- risk_level

Technical terms इस्तेमाल कर सकते हो:

OTP
UPI
KYC
URL
PIN
2FA
password
phishing
malware
domain
browser

लेकिन explanation हिंदी में होनी चाहिए।

उदाहरण:

गलत:
"Urgency Trigger Detected"

सही:
"तुरंत कार्रवाई करने का दबाव पाया गया।"

गलत:
"Impersonation Detected"

सही:
"किसी विश्वसनीय व्यक्ति या संस्था की पहचान की नकल करने का संकेत पाया गया।"


==================================================
SCAM FINGERPRINT
==================================================

3 से 6 अलग-अलग threat tactics generate करो।

केवल उन्हीं tactics को शामिल करो जिनका evidence incident data में मौजूद है।

संभावित उदाहरण:

- फ़िशिंग
- संदिग्ध वेबसाइट
- पहचान की नकल
- OTP प्राप्त करने का प्रयास
- KYC धोखाधड़ी
- भुगतान का दबाव
- डेटा चोरी
- संदिग्ध लिंक
- अकाउंट takeover का प्रयास

लेकिन बिना evidence के कोई tactic मत बनाना।


==================================================
ATTACK CHAIN
==================================================

इस specific incident के आधार पर 3 से 5 chronological stages बनाओ।

Format:

"चरण 1: ..."
"चरण 2: ..."
"चरण 3: ..."

सिर्फ उपलब्ध evidence के आधार पर attack sequence बताओ।

अगर कोई stage evidence से साबित नहीं है तो उसे fact की तरह मत लिखो।

ऐसे शब्द इस्तेमाल करो:

"संभावित रूप से"
"उपलब्ध संकेतों के आधार पर"

जहां certainty नहीं है।


==================================================
EVIDENCE
==================================================

2 से 5 महत्वपूर्ण evidence points निकालो।

हर evidence हिंदी में होना चाहिए।

Evidence केवल provided data से होना चाहिए।

कुछ भी invent मत करो।


==================================================
WHY
==================================================

ठीक 2 हिंदी sentences लिखो।

इनमें बताओ कि उपलब्ध signals के आधार पर incident suspicious क्यों है।

==================================================
RISK SCORE
==================================================

0 से 100 के बीच integer score दो।

Score incident के उपलब्ध signals की गंभीरता के आधार पर होना चाहिए।

Scoring guidance:

0-19:
बहुत कम संकेत

20-39:
कुछ सावधानी वाले संकेत

40-59:
मध्यम स्तर के संदिग्ध संकेत

60-79:
कई मजबूत संदिग्ध संकेत

80-100:
बहुत मजबूत fraud/scam संकेत

महत्वपूर्ण:

यदि evidence कम है तो score artificially high मत करो।

यदि कोई strong signal नहीं है तो score कम रखो।

==================================================
RISK LEVEL
==================================================

Score के अनुसार:

0-29:
"कम जोखिम"

30-59:
"मध्यम जोखिम"

60-79:
"उच्च जोखिम"

80-100:
"बहुत अधिक जोखिम"


==================================================
IMPORTANT EVIDENCE RULE
==================================================

exact_scam_lines original evidence हैं।

अगर exact_scam_lines उपलब्ध हैं:

- उन्हें translate मत करो।
- उन्हें modify मत करो।
- उन्हें rewrite मत करो।
- quote invent मत करो।

उन्हें केवल evidence के रूप में exactly इस्तेमाल कर सकते हो।


==================================================
STRICT RULES
==================================================

1. केवल provided incident data इस्तेमाल करो।
2. कोई information invent मत करो।
3. कोई fake quote मत बनाओ।
4. सभी explanations हिंदी में हों।
5. scam_fingerprint हिंदी में हो।
6. attack_chain हिंदी में हो।
7. evidence हिंदी में हो।
8. why हिंदी में हो।
9. risk_score integer होना चाहिए।
10. risk_score 0-100 के बीच होना चाहिए।
11. risk_level हिंदी में होना चाहिए।
12. JSON keys English में exactly वही रहें।
13. Markdown मत दो।
14. ```json मत दो।
15. JSON के बाहर कोई text मत दो।
16. केवल valid JSON return करो।


==================================================
RETURN FORMAT
==================================================

{{
    "scam_fingerprint": [
        "फ़िशिंग",
        "संदिग्ध वेबसाइट",
        "डेटा चोरी"
    ],

    "attack_chain": [
        "चरण 1: उपयोगकर्ता को संदिग्ध संदेश या लिंक के माध्यम से संपर्क किया गया।",
        "चरण 2: उपयोगकर्ता को संदिग्ध वेबसाइट पर जाने के लिए प्रेरित किया गया।",
        "चरण 3: वेबसाइट के माध्यम से संवेदनशील जानकारी प्राप्त करने का प्रयास किया गया।"
    ],

    "evidence": [
        "संदेश में संदिग्ध गतिविधि के संकेत पाए गए।",
        "वेबसाइट का व्यवहार जोखिमपूर्ण दिखाई देता है।"
    ],

    "why": "इस incident में कई संदिग्ध सुरक्षा संकेत पाए गए हैं। उपलब्ध evidence के आधार पर इसमें साइबर धोखाधड़ी का संभावित जोखिम दिखाई देता है।",

    "risk_score": 75,

    "risk_level": "उच्च जोखिम"
}}
"""

    # ---------------------------------------------------------
    # AI CALL
    # ---------------------------------------------------------

    try:

        data = call_openrouter(prompt)

    except Exception:

        return {
            **DEFAULT_FINGERPRINT
        }

    # ---------------------------------------------------------
    # INVALID RESPONSE
    # ---------------------------------------------------------

    if not isinstance(data, dict):

        return {
            **DEFAULT_FINGERPRINT
        }

    # ---------------------------------------------------------
    # FINGERPRINT
    # ---------------------------------------------------------

    fingerprint = data.get(
        "scam_fingerprint",
        []
    )

    if not isinstance(fingerprint, list):
        fingerprint = []

    fingerprint = list(
        dict.fromkeys(
            [
                str(item).strip()
                for item in fingerprint
                if item
            ]
        )
    )

    # ---------------------------------------------------------
    # ATTACK CHAIN
    # ---------------------------------------------------------

    attack_chain = data.get(
        "attack_chain",
        []
    )

    if not isinstance(attack_chain, list):
        attack_chain = []

    attack_chain = list(
        dict.fromkeys(
            [
                str(item).strip()
                for item in attack_chain
                if item
            ]
        )
    )

    # ---------------------------------------------------------
    # EVIDENCE
    # ---------------------------------------------------------

    evidence = data.get(
        "evidence",
        []
    )

    if not isinstance(evidence, list):
        evidence = []

    evidence = list(
        dict.fromkeys(
            [
                str(item).strip()
                for item in evidence
                if item
            ]
        )
    )

    # ---------------------------------------------------------
    # WHY
    # ---------------------------------------------------------

    why = data.get("why")

    if not isinstance(why, str) or not why.strip():

        why = DEFAULT_FINGERPRINT["why"]

    else:

        why = why.strip()

    # ---------------------------------------------------------
    # RISK SCORE
    # ---------------------------------------------------------

    risk_score = safe_int(
        data.get("risk_score"),
        0
    )

    # ---------------------------------------------------------
    # RISK LEVEL
    # ---------------------------------------------------------

    risk_level = data.get("risk_level")

    if not isinstance(risk_level, str) or not risk_level.strip():

        risk_level = get_risk_level(risk_score)

    else:

        risk_level = risk_level.strip()

    # ---------------------------------------------------------
    # FALLBACK INDIVIDUAL FIELDS
    # ---------------------------------------------------------

    if not fingerprint:

        fingerprint = DEFAULT_FINGERPRINT[
            "scam_fingerprint"
        ]

    if not attack_chain:

        attack_chain = DEFAULT_FINGERPRINT[
            "attack_chain"
        ]

    if not evidence:

        # Real evidence available हो तो उसे इस्तेमाल करो
        fallback_evidence = (
            link_reasons
            + screenshot_result.get("reasons", [])
        )

        evidence = list(
            dict.fromkeys(
                [
                    str(item).strip()
                    for item in fallback_evidence
                    if item
                ]
            )
        )

        if not evidence:

            evidence = DEFAULT_FINGERPRINT[
                "evidence"
            ]

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    return {

        "scam_fingerprint": fingerprint,

        "attack_chain": attack_chain,

        "evidence": evidence,

        "why": why,

        "risk_score": risk_score,

        "risk_level": risk_level
    }