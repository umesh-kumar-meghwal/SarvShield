# scam_fingerprint.py
import json
from ai_helper import call_openrouter


def build_scam_fingerprint(
    message="",
    phone_result=None,
    link_result=None,
    screenshot_result=None,
    language="English"
) -> dict:
    target_lang = str(language or "English").strip()
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}
    phone_result = phone_result or {}

    domain = link_result.get("final_domain") or link_result.get("domain") or "N/A"

    prompt = f"""
You are a Cyber Threat Intelligence Analyst. Reconstruct the attack profile:
Message: {message}
Domain: {domain}
Phone Reputation: {phone_result.get("reputation", "UNKNOWN")}

CRITICAL MULTILINGUAL INSTRUCTION:
- The user requested output in: "{target_lang}".
- "scam_fingerprint", "attack_chain", "evidence", and "why" MUST BE FULLY GENERATED IN "{target_lang}" using its native script (e.g., Bengali, Urdu, Spanish, Russian, Marathi, Tamil, Japanese, etc.).
- "risk_score": integer (0-100).
- "risk_level": string in "{target_lang}".

Return valid JSON:
{{
    "scam_fingerprint": ["Vector 1 in {target_lang}", "Vector 2 in {target_lang}"],
    "attack_chain": ["Stage 1 in {target_lang}", "Stage 2 in {target_lang}"],
    "evidence": ["Evidence 1 in {target_lang}"],
    "why": "2 sentences explaining why this is suspicious in {target_lang}",
    "risk_score": 75,
    "risk_level": "Risk level in {target_lang}"
}}
"""

    try:
        data = call_openrouter(prompt)
        if isinstance(data, dict):
            return {
                "scam_fingerprint": [str(x) for x in data.get("scam_fingerprint", []) if str(x)],
                "attack_chain": [str(x) for x in data.get("attack_chain", []) if str(x)],
                "evidence": [str(x) for x in data.get("evidence", []) if str(x)],
                "why": str(data.get("why") or "Security analysis completed."),
                "risk_score": int(data.get("risk_score", 0) or 0),
                "risk_level": str(data.get("risk_level") or "Suspicious")
            }
    except Exception:
        pass

    return {
        "scam_fingerprint": ["Suspicious Activity"],
        "attack_chain": ["Stage 1: Delivery of unsolicited lure."],
        "evidence": ["Identified risk indicators."],
        "why": "Analysis identified suspicious patterns.",
        "risk_score": 50,
        "risk_level": "Medium"
    }