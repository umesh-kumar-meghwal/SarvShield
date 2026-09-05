import json
from ai_helper import call_openrouter


def generate_safe_next(
    final_score=0,
    verdict="UNKNOWN",
    message="",
    link_result=None,
    screenshot_result=None,
    phone_result=None,
    fingerprint=None,
    attack_chain=None,
    language="english"
):
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}
    phone_result = phone_result or {}

    incident_report = f"""
INCIDENT CONTEXT:
- Overall Threat: {final_score}/100 ({verdict})
- User Message: "{message}"
- Target Link / Domain: "{link_result.get('final_domain') or link_result.get('domain') or 'N/A'}"
- Scam Analysis on Site: "{link_result.get('scam_explanation', '')}"
- Webpage Threat Findings: {json.dumps(link_result.get('reasons', []))}
- Screenshot OCR: "{screenshot_result.get('detected_text', '')}"
- Phone Status: "{phone_result.get('reputation', 'UNKNOWN')}"
"""

    prompt = f"""
You are SafeNext AI, an expert Cyber Defense and Fraud Incident Recovery Coach.
Analyze the specific scam incident above and generate tailored, actionable guidance.

{incident_report}

CRITICAL REQUIREMENT - LANGUAGE:
You MUST generate the entire output in the following language: {language.upper()}.
- If language is 'hindi', write everything in Hindi (Devanagari script).
- If language is 'hinglish', write in a casual mix of Hindi and English (Hinglish).
- If language is 'english', write in professional English.

Return ONLY valid JSON matching this exact structure:
{{
    "recommended_action": "Short powerful headline in {language}",
    "why_dangerous": "Detailed risk and consequence explanation in {language}.",
    "immediate_steps": [
        "Immediate preventive step 1 in {language}",
        "Immediate preventive step 2 in {language}",
        "Immediate preventive step 3 in {language}"
    ],
    "recovery_steps": [
        "Specific recovery step in {language}",
        "Emergency recovery step 2 in {language}"
    ],
    "helplines": [
        "National Cyber Crime Helpline: Dial 1930 (https://cybercrime.gov.in)"
    ]
}}
"""
    data = call_openrouter(prompt)

    if data and isinstance(data, dict):
        immediate = data.get("immediate_steps") or [
            "Do not open suspicious links or download unverified files.",
            "Never share passwords, OTPs, or government identity documents.",
            "Independently verify sender authenticity through official channels."
        ]
        recovery = data.get("recovery_steps") or [
            "If you entered credentials, change your passwords immediately and enable 2-Factor Authentication (2FA).",
            "If financial loss or data leak occurred, immediately report to the National Cyber Crime Helpline at 1930."
        ]
        return {
            "recommended_action": data.get("recommended_action", "DO NOT INTERACT"),
            "why_dangerous": data.get("why_dangerous", "Interacting with this threat poses severe security, privacy, and financial risks."),
            "immediate_steps": immediate,
            "recovery_steps": recovery,
            "helplines": data.get("helplines", ["National Cyber Crime Helpline: Dial 1930 (https://cybercrime.gov.in)"]),
            "safe_next": immediate
        }

    return {
        "recommended_action": "DO NOT INTERACT",
        "why_dangerous": "Interacting with unverified sources can lead to account compromise, identity theft, or financial loss.",
        "immediate_steps": [
            "Do not open suspicious links or download unverified files.",
            "Never share passwords, OTPs, or government identity numbers.",
            "Verify any official request directly through verified customer support."
        ],
        "recovery_steps": [
            "If you entered credentials, change passwords immediately and enable 2FA.",
            "If money was deducted, immediately call 1930 (National Cyber Crime Helpline) or report to cybercrime.gov.in."
        ],
        "helplines": ["National Cyber Crime Helpline: Dial 1930 (https://cybercrime.gov.in)"],
        "safe_next": ["Do not open suspicious links.", "Never share OTPs or KYC details."]
    }