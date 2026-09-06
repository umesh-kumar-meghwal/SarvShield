# message_detect.py
from ai_helper import call_openrouter


def message_detect(message: str) -> dict:
    if not message or not str(message).strip():
        return {
            "score": 0,
            "verdict": "NO MESSAGE",
            "language": "unknown",
            "scam_type": "none",
            "reasons": ["No message content was provided for analysis."]
        }

    message = str(message).strip()
    if len(message) > 10000:
        message = message[:10000]

    prompt = f"""
You are a professional cybersecurity threat-classification engine.
Analyze the EXACT message provided below for scams, phishing, social engineering, impersonation, credential theft, or fraud.

MESSAGE TO ANALYZE:
{message}

ANALYSIS RULES:
1. Always output all text and reasons strictly in ENGLISH.
2. Evidence-based scoring: 
   - 0-19: Safe/Routine institutional or personal message.
   - 20-49: Low Risk.
   - 50-69: Suspicious / Unverified signals.
   - 70-89: High Risk / Phishing / Deception.
   - 90-100: Very High Risk / Critical credential harvesting or financial fraud.
3. Verdict MUST match the score:
   - 0-49: "LOW RISK"
   - 50-69: "SUSPICIOUS"
   - 70-89: "HIGH RISK"
   - 90-100: "VERY HIGH RISK"
4. scam_type MUST be one of:
   "phishing", "impersonation", "financial fraud", "OTP/credential theft", "fake reward/prize",
   "job scam", "investment scam", "loan scam", "delivery/payment scam", "account takeover",
   "extortion/threat", "other", "none".

Return ONLY valid JSON matching this schema:
{{
    "score": 0,
    "verdict": "LOW RISK",
    "language": "English",
    "scam_type": "none",
    "reasons": [
        "First evidence-based reason in English.",
        "Second reason in English."
    ]
}}
"""

    try:
        data = call_openrouter(prompt)
        if not data or not isinstance(data, dict):
            return {
                "score": 0,
                "verdict": "UNKNOWN",
                "language": "English",
                "scam_type": "none",
                "reasons": ["Message analysis could not be completed."]
            }

        score = max(0, min(int(data.get("score", 0) or 0), 100))

        if score <= 49:
            verdict = "LOW RISK"
        elif score <= 69:
            verdict = "SUSPICIOUS"
        elif score <= 89:
            verdict = "HIGH RISK"
        else:
            verdict = "VERY HIGH RISK"

        scam_type = str(data.get("scam_type") or "none").strip()
        if score < 50:
            scam_type = "none"

        reasons = data.get("reasons", [])
        if not isinstance(reasons, list) or not reasons:
            reasons = ["No critical threat indicators detected in the message text."]

        return {
            "score": score,
            "verdict": verdict,
            "language": str(data.get("language") or "English"),
            "scam_type": scam_type,
            "reasons": [str(r) for r in reasons[:4]]
        }

    except Exception as e:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "language": "English",
            "scam_type": "none",
            "reasons": [f"Message analysis error: {str(e)}"]
        }