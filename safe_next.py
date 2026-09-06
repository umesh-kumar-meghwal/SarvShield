# safe_next.py
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
    language="English"
) -> dict:
    target_lang = str(language or "English").strip()
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}
    phone_result = phone_result or {}
    fingerprint = fingerprint or {}
    attack_chain = attack_chain or {}

    prompt = f"""
You are SafeNext AI, an incident response cybersecurity coach.
Analyze this incident and generate guidance:

Threat Score: {final_score}/100 ({verdict})
Message: {message}
Domain: {link_result.get("final_domain") or link_result.get("domain") or "N/A"}
Phone Reputation: {phone_result.get("reputation", "UNKNOWN")}

CRITICAL MULTILINGUAL INSTRUCTION:
- The user requested response in: "{target_lang}".
- "recommended_action", "why_dangerous", "immediate_steps", and "recovery_steps" MUST BE FULLY GENERATED IN "{target_lang}" using its native script (Tamil, Russian, Spanish, Bengali, Urdu, Hindi, German, etc.).
- Helplines should reference 1930 and cybercrime.gov.in.

Return ONLY valid JSON:
{{
    "recommended_action": "Clear single recommendation strictly in {target_lang}",
    "why_dangerous": "2-3 sentences explaining why it is dangerous strictly in {target_lang}",
    "immediate_steps": [
        "First step strictly in {target_lang}",
        "Second step strictly in {target_lang}",
        "Third step strictly in {target_lang}"
    ],
    "recovery_steps": [
        "Recovery step 1 strictly in {target_lang}",
        "Recovery step 2 strictly in {target_lang}"
    ],
    "helplines": [
        "National Cyber Crime Helpline: 1930",
        "National Cyber Crime Reporting Portal: cybercrime.gov.in"
    ]
}}
"""

    try:
        data = call_openrouter(prompt)
        if isinstance(data, dict):
            immediate = [str(x) for x in data.get("immediate_steps", []) if str(x).strip()]
            recovery = [str(x) for x in data.get("recovery_steps", []) if str(x).strip()]
            return {
                "recommended_action": str(data.get("recommended_action") or "Do not interact with the suspicious sender."),
                "why_dangerous": str(data.get("why_dangerous") or "Potential cybersecurity deception risk."),
                "immediate_steps": immediate or ["Do not share OTPs, PINs, or credentials."],
                "recovery_steps": recovery or ["Report incident to cybercrime.gov.in or 1930."],
                "helplines": [
                    "National Cyber Crime Helpline: 1930",
                    "National Cyber Crime Reporting Portal: cybercrime.gov.in"
                ],
                "safe_next": immediate,
                "language": target_lang
            }
    except Exception:
        pass

    return {
        "recommended_action": "Do not interact with suspicious sender or link.",
        "why_dangerous": "Risk of credential theft or unauthorized transactions.",
        "immediate_steps": ["Do not share OTPs or click unknown links."],
        "recovery_steps": ["Contact authorities or call 1930 immediately."],
        "helplines": ["National Cyber Crime Helpline: 1930", "Portal: cybercrime.gov.in"],
        "safe_next": ["Do not share OTPs or click unknown links."],
        "language": target_lang
    }