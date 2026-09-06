# safe_next.py
import json
from ai_helper import call_openrouter

DEFAULT_SAFE_NEXT = {
    "recommended_action": "Do not interact with the suspicious sender, message, or link.",
    "why_dangerous": (
        "This activity shows strong signs of phishing or deceptive social engineering designed "
        "to harvest sensitive credentials, compromise banking details, or inflict financial loss."
    ),
    "immediate_steps": [
        "Do not click on links or download unexpected attachments.",
        "Never share OTPs, UPI PINs, passwords, or personal banking credentials.",
        "Verify communications independently using the entity's verified official portal or app.",
        "Block the sender and report the contact immediately."
    ],
    "recovery_steps": [
        "If credentials were entered, change passwords immediately and enforce 2-Factor Authentication (2FA).",
        "If financial details were exposed, notify your bank immediately to freeze affected cards or accounts.",
        "File an incident complaint with the National Cyber Crime Reporting Portal at cybercrime.gov.in."
    ],
    "helplines": [
        "National Cyber Crime Helpline: 1930",
        "National Cyber Crime Reporting Portal: cybercrime.gov.in"
    ]
}


def clean_list(value, fallback):
    if not isinstance(value, list):
        return fallback
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    return cleaned if cleaned else fallback


def generate_safe_next(
    final_score=0,
    verdict="UNKNOWN",
    message="",
    link_result=None,
    screenshot_result=None,
    phone_result=None,
    fingerprint=None,
    attack_chain=None
) -> dict:
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}
    phone_result = phone_result or {}
    fingerprint = fingerprint or {}
    attack_chain = attack_chain or {}

    incident_report = f"""
INCIDENT CONTEXT:
Overall Threat Score: {final_score}/100 ({verdict})
User Message: {message}
Target Link / Domain: {link_result.get("final_domain") or link_result.get("domain") or "N/A"}
Website Scam Analysis: {link_result.get("scam_explanation", "")}
Webpage Threat Findings: {json.dumps(link_result.get("reasons", []))}
Screenshot OCR Transcribed: {screenshot_result.get("detected_text", "")}
Phone Reputation: {phone_result.get("reputation", "UNKNOWN")}
Scam Fingerprint: {json.dumps(fingerprint)}
Attack Chain: {json.dumps(attack_chain)}
"""

    prompt = f"""
You are SafeNext AI, an incident response cybersecurity expert.
Analyze the following security incident and generate structured, actionable, and defensive recovery steps.

{incident_report}

CRITICAL RULES:
- Output MUST be 100% in professional ENGLISH.
- Tailor advice to the specific attack vectors identified (phishing, fake UPI, banking, KYC, or impersonation).
- Return ONLY valid JSON matching this schema:
{{
    "recommended_action": "Clear, direct single recommendation in English.",
    "why_dangerous": "2-3 sentences explaining why this specific lure is dangerous.",
    "immediate_steps": [
        "First immediate defensive step in English",
        "Second step",
        "Third step",
        "Fourth step"
    ],
    "recovery_steps": [
        "First post-incident recovery step in English",
        "Second step",
        "Third step"
    ],
    "helplines": [
        "National Cyber Crime Helpline: 1930",
        "National Cyber Crime Reporting Portal: cybercrime.gov.in"
    ]
}}
"""

    try:
        data = call_openrouter(prompt)
    except Exception:
        return {
            **DEFAULT_SAFE_NEXT,
            "safe_next": DEFAULT_SAFE_NEXT["immediate_steps"],
            "language": "en"
        }

    if not isinstance(data, dict):
        return {
            **DEFAULT_SAFE_NEXT,
            "safe_next": DEFAULT_SAFE_NEXT["immediate_steps"],
            "language": "en"
        }

    recommended_action = str(data.get("recommended_action") or DEFAULT_SAFE_NEXT["recommended_action"]).strip()
    why_dangerous = str(data.get("why_dangerous") or DEFAULT_SAFE_NEXT["why_dangerous"]).strip()
    immediate = clean_list(data.get("immediate_steps"), DEFAULT_SAFE_NEXT["immediate_steps"])
    recovery = clean_list(data.get("recovery_steps"), DEFAULT_SAFE_NEXT["recovery_steps"])
    helplines = clean_list(data.get("helplines"), DEFAULT_SAFE_NEXT["helplines"])

    return {
        "recommended_action": recommended_action,
        "why_dangerous": why_dangerous,
        "immediate_steps": immediate,
        "recovery_steps": recovery,
        "helplines": helplines,
        "safe_next": immediate,
        "language": "en"
    }