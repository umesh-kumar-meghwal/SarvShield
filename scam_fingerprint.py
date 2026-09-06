# scam_fingerprint.py
import json
from ai_helper import call_openrouter

DEFAULT_FINGERPRINT = {
    "scam_fingerprint": [
        "Suspicious Pattern Detection",
        "Unverified Communication"
    ],
    "attack_chain": [
        "Stage 1: Delivery of unsolicited communication via message or link.",
        "Stage 2: Social engineering pressure to trigger immediate victim compliance.",
        "Stage 3: Attempted credential harvesting or unauthorized transaction."
    ],
    "evidence": [
        "Unverified external source attempting to solicit sensitive user interaction."
    ],
    "why": "Security anomalies and high-risk signals were identified across the provided vectors.",
    "risk_score": 0,
    "risk_level": "Low Risk"
}


def safe_int(value, default=0):
    try:
        val = int(float(value))
        return max(0, min(100, val))
    except (TypeError, ValueError):
        return default


def get_risk_level(score: int) -> str:
    if score >= 80:
        return "Very High Risk"
    elif score >= 60:
        return "High Risk"
    elif score >= 30:
        return "Medium Risk"
    return "Low Risk"


def build_scam_fingerprint(
    message="",
    phone_result=None,
    link_result=None,
    screenshot_result=None,
    language="english"
) -> dict:
    phone_result = phone_result or {}
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}

    domain = link_result.get("final_domain") or link_result.get("domain") or "N/A"
    link_reasons = link_result.get("reasons", [])
    exact_scam_lines = link_result.get("exact_scam_lines", [])
    screenshot_text = screenshot_result.get("detected_text", "")
    screenshot_category = screenshot_result.get("category", "N/A")
    phone_reputation = phone_result.get("reputation", "UNKNOWN")

    incident_data = f"""
INCIDENT INPUTS:
Message: {message}
Domain: {domain}
Link Scam Summary: {link_result.get("scam_explanation", "")}
Link Reasons: {json.dumps(link_reasons)}
Exact Scam Lines: {json.dumps(exact_scam_lines)}
Screenshot Transcribed Text: {json.dumps(screenshot_text)}
Screenshot Category: {screenshot_category}
Phone Reputation: {phone_reputation}
"""

    prompt = f"""
You are a Cyber Threat Intelligence and Scam Pattern Analyst.
Analyze this incident data and reconstruct the attack profile.

{incident_data}

CRITICAL RULES:
- All output MUST be 100% in ENGLISH.
- Identify 3 to 5 realistic attack fingerprint vectors (e.g. "Credential Harvesting", "Brand Impersonation", "Urgency Manipulation").
- Structure a chronological 3-stage Attack Chain: "Stage 1: ...", "Stage 2: ...", "Stage 3: ...".
- List 2 to 4 key forensic evidence lines in English.
- Provide a clear 2-sentence 'why' summary.
- Compute a risk_score (0-100) and corresponding risk_level ("Low Risk", "Medium Risk", "High Risk", "Very High Risk").

Return ONLY valid JSON matching this structure:
{{
    "scam_fingerprint": ["Vector 1", "Vector 2"],
    "attack_chain": ["Stage 1: ...", "Stage 2: ...", "Stage 3: ..."],
    "evidence": ["Forensic evidence 1", "Forensic evidence 2"],
    "why": "Two English sentences explaining why this threat was classified as suspicious.",
    "risk_score": 75,
    "risk_level": "High Risk"
}}
"""

    try:
        data = call_openrouter(prompt)
    except Exception:
        return DEFAULT_FINGERPRINT

    if not isinstance(data, dict):
        return DEFAULT_FINGERPRINT

    fingerprint = [str(x).strip() for x in data.get("scam_fingerprint", []) if str(x).strip()]
    attack_chain = [str(x).strip() for x in data.get("attack_chain", []) if str(x).strip()]
    evidence = [str(x).strip() for x in data.get("evidence", []) if str(x).strip()]
    why = str(data.get("why") or DEFAULT_FINGERPRINT["why"]).strip()
    risk_score = safe_int(data.get("risk_score"), 0)
    risk_level = str(data.get("risk_level") or get_risk_level(risk_score)).strip()

    return {
        "scam_fingerprint": fingerprint or DEFAULT_FINGERPRINT["scam_fingerprint"],
        "attack_chain": attack_chain or DEFAULT_FINGERPRINT["attack_chain"],
        "evidence": evidence or DEFAULT_FINGERPRINT["evidence"],
        "why": why,
        "risk_score": risk_score,
        "risk_level": risk_level
    }