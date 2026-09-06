# message_detect.py
from ai_helper import call_openrouter


def message_detect(message: str, language: str = "English") -> dict:
    target_lang = str(language or "English").strip()

    if not message or not str(message).strip():
        return {
            "score": 0,
            "verdict": "NO MESSAGE",
            "language": target_lang,
            "scam_type": "none",
            "reasons": ["No message provided."]
        }

    message = str(message).strip()[:10000]

    prompt = f"""
You are a global cybersecurity threat detection engine.
Analyze the message below for scam, phishing, impersonation, credential harvesting, or financial fraud:

MESSAGE:
{message}

CRITICAL MULTILINGUAL INSTRUCTION:
- The user requested output in: "{target_lang}".
- Write ALL human-readable reasons in the "reasons" array STRICTLY in "{target_lang}" using its native alphabet/script (e.g., if Bengali, use Bengali script; if Arabic, use Arabic script; if Russian, Cyrillic; if Tamil, Tamil script, etc.).
- The JSON keys and verdict ("LOW RISK", "SUSPICIOUS", "HIGH RISK", "VERY HIGH RISK") must stay in English.

Return ONLY valid JSON matching this schema:
{{
    "score": 0,
    "verdict": "LOW RISK",
    "language": "{target_lang}",
    "scam_type": "none",
    "reasons": [
        "First evidence-based reason strictly in {target_lang}.",
        "Second reason strictly in {target_lang}."
    ]
}}
"""

    try:
        data = call_openrouter(prompt)
        if not data or not isinstance(data, dict):
            return {
                "score": 0,
                "verdict": "UNKNOWN",
                "language": target_lang,
                "scam_type": "none",
                "reasons": ["Analysis completed."]
            }

        score = max(0, min(int(data.get("score", 0) or 0), 100))
        verdict = str(data.get("verdict") or (
            "VERY HIGH RISK" if score >= 80 else
            "HIGH RISK" if score >= 60 else
            "SUSPICIOUS" if score >= 30 else
            "LOW RISK"
        )).upper()

        reasons = data.get("reasons", [])
        if not isinstance(reasons, list) or not reasons:
            reasons = ["Analysis completed."]

        return {
            "score": score,
            "verdict": verdict,
            "language": target_lang,
            "scam_type": str(data.get("scam_type") or "none"),
            "reasons": [str(r) for r in reasons[:4]]
        }

    except Exception as e:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "language": target_lang,
            "scam_type": "none",
            "reasons": [f"Error: {str(e)}"]
        }