import json

from ai_helper import call_openrouter


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

    incident_data = f"""
INCIDENT INPUTS:

- Message Text:
"{message}"

- Link / Domain:
"{link_result.get('final_domain') or link_result.get('domain') or 'N/A'}"

- Link Scam Analysis:
"{link_result.get('scam_explanation', '')}"

- Link Threat Reasons:
{json.dumps(link_result.get('reasons', []), ensure_ascii=False)}

- Link Quoted Lines:
{json.dumps(link_result.get('exact_scam_lines', []), ensure_ascii=False)}

- Screenshot Text / Category:
"{screenshot_result.get('detected_text', '')}" /
"{screenshot_result.get('category', 'N/A')}"

- Phone Reputation:
"{phone_result.get('reputation', 'UNKNOWN')}"
"""

    prompt = f"""
You are an expert Cyber Threat & Attack Pattern Analyst.

Review the incident data and generate a dynamic Scam Fingerprint
and Attack Vector Sequence.

{incident_data}

==================================================
OUTPUT LANGUAGE
==================================================

Selected language: {language}

The selected language is HINDI.

IMPORTANT:
ALL AI-GENERATED HUMAN-READABLE CONTENT MUST BE IN HINDI.

This includes:

1. scam_fingerprint
2. attack_chain
3. evidence
4. why

Use natural and easy-to-understand Hindi.

You may use commonly understood cybersecurity terms such as:
- फ़िशिंग
- मालवेयर
- OTP
- KYC
- पासवर्ड
- बैंक
- लिंक
- डोमेन
- डेटा
- अकाउंट

But the explanation around these terms must be Hindi.

==================================================
IMPORTANT EVIDENCE RULE
==================================================

exact_scam_lines are original evidence.

If exact webpage/message lines are provided:

- DO NOT translate them.
- DO NOT modify them.
- DO NOT rewrite them.
- Keep them exactly as provided.

Do not invent any quote.

==================================================
TASKS
==================================================

1. scam_fingerprint

Generate 3-6 distinct threat tactic badges based ONLY
on the provided incident data.

Examples:

[
    "फ़िशिंग",
    "नकली वेबसाइट",
    "डेटा चोरी",
    "OTP चोरी",
    "भुगतान का दबाव"
]

Do not generate a badge if there is no evidence for it.

--------------------------------------------------

2. attack_chain

Generate 3-5 chronological stages explaining how
this specific attack works.

Use this format:

"चरण 1: ..."
"चरण 2: ..."
"चरण 3: ..."

Only describe steps supported by the provided evidence.

--------------------------------------------------

3. evidence

Extract 2-5 important threat evidence points.

All evidence descriptions must be in Hindi.

Do not invent evidence.

--------------------------------------------------

4. why

Provide exactly 2 concise Hindi sentences explaining
why the incident was flagged.

==================================================
STRICT RULES
==================================================

1. Score is NOT required in this function.

2. Do not invent information.

3. Do not invent webpage quotes.

4. Use ONLY the provided incident data.

5. All generated explanations must be in Hindi.

6. scam_fingerprint must be in Hindi.

7. attack_chain must be in Hindi.

8. evidence must be in Hindi.

9. why must be in Hindi.

10. Original quoted lines must NOT be translated.

11. JSON keys MUST remain exactly as specified.

12. Return ONLY valid JSON.

13. Do not return Markdown.

14. Do not return ```json.

15. Do not add any text outside JSON.

==================================================
RETURN FORMAT
==================================================

{{
    "scam_fingerprint": [
        "फ़िशिंग",
        "संदिग्ध वेबसाइट",
        "डेटा संग्रह"
    ],

    "attack_chain": [
        "चरण 1: उपयोगकर्ता को संदिग्ध संदेश या लिंक भेजा जाता है।",
        "चरण 2: उपयोगकर्ता को संदिग्ध वेबसाइट पर जाने के लिए प्रेरित किया जाता है।",
        "चरण 3: वेबसाइट संवेदनशील जानकारी प्राप्त करने का प्रयास करती है।"
    ],

    "evidence": [
        "वेबसाइट संवेदनशील जानकारी मांगती है।",
        "लिंक में संदिग्ध गतिविधि के संकेत पाए गए हैं।"
    ],

    "why": "इस घटना में कई संदिग्ध सुरक्षा संकेत पाए गए हैं। उपलब्ध जानकारी के आधार पर इसे संभावित साइबर धोखाधड़ी के रूप में चिह्नित किया गया है।"
}}
"""

    data = call_openrouter(prompt)

    if data:
        return {
            "scam_fingerprint": list(
                dict.fromkeys(
                    [
                        str(item)
                        for item in data.get("scam_fingerprint", [])
                        if item
                    ]
                )
            ),

            "attack_chain": list(
                dict.fromkeys(
                    [
                        str(item)
                        for item in data.get("attack_chain", [])
                        if item
                    ]
                )
            ),

            "evidence": list(
                dict.fromkeys(
                    [
                        str(item)
                        for item in data.get("evidence", [])
                        if item
                    ]
                )
            ),

            "why": str(
                data.get(
                    "why",
                    "AI द्वारा खतरे का विश्लेषण पूरा किया गया।"
                )
            )
        }

    # AI failure fallback
    fallback_evidence = (
        link_result.get("reasons", [])
        + screenshot_result.get("reasons", [])
    )

    return {
        "scam_fingerprint": [
            "AI खतरा विश्लेषण"
        ],

        "attack_chain": [
            "चरण 1: दिए गए इनपुट का विश्लेषण किया गया।",
            "चरण 2: उपलब्ध खतरे के संकेतों की पहचान की गई।",
            "चरण 3: संभावित जोखिम का मूल्यांकन किया गया।"
        ],

        "evidence": [
            str(item)
            for item in fallback_evidence
            if item
        ],

        "why": (
            "दिए गए इनपुट में मौजूद सुरक्षा संकेतों का "
            "विश्लेषण किया गया। उपलब्ध जानकारी के आधार पर "
            "खतरे का मूल्यांकन तैयार किया गया है।"
        )
    }
