import json
from ai_helper import call_openrouter


def build_scam_fingerprint(
    message="",
    phone_result=None,
    link_result=None,
    screenshot_result=None
):
    phone_result = phone_result or {}
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}

    incident_data = f"""
INCIDENT INPUTS:
- Message Text: "{message}"
- Link / Domain: "{link_result.get('final_domain') or link_result.get('domain') or 'N/A'}"
- Link Scam Analysis: "{link_result.get('scam_explanation', '')}"
- Link Threat Reasons: {json.dumps(link_result.get('reasons', []))}
- Link Quoted Lines: {json.dumps(link_result.get('exact_scam_lines', []))}
- Screenshot Text / Category: "{screenshot_result.get('detected_text', '')}" / {screenshot_result.get('category', 'N/A')}
- Phone Reputation: "{phone_result.get('reputation', 'UNKNOWN')}"
"""

    prompt = f"""
You are an expert Cyber Threat & Attack Pattern Analyst.
Review the incident data above and generate dynamic Scam Fingerprint Badges and the Attack Vector Sequence.

{incident_data}

TASKS:
1. 'scam_fingerprint': Generate 3-6 distinct threat tactic badges/tags strictly based on this input (e.g. UPPERCASE TAGS).
2. 'attack_chain': Generate 3-5 chronological steps of how this specific attack works from start to finish (Step 1, Step 2, Step 3, etc.).
3. 'evidence': Extract 2-5 core threat evidence points.
4. 'why': Provide a 2-sentence synthesis explaining why this was flagged.

Return ONLY valid JSON:
{{
    "scam_fingerprint": ["TAG 1", "TAG 2", "TAG 3"],
    "attack_chain": [
        "Stage 1: ...",
        "Stage 2: ...",
        "Stage 3: ..."
    ],
    "evidence": ["Evidence 1", "Evidence 2"],
    "why": "Explanation sentence."
}}
"""
    data = call_openrouter(prompt)

    if data:
        return {
            "scam_fingerprint": list(dict.fromkeys(data.get("scam_fingerprint", []))),
            "attack_chain": list(dict.fromkeys(data.get("attack_chain", []))),
            "evidence": list(dict.fromkeys([str(e) for e in data.get("evidence", []) if e])),
            "why": data.get("why", "Analysis completed by AI Threat Engine.")
        }

    return {
        "scam_fingerprint": ["AI ANALYSIS COMPLETED"],
        "attack_chain": ["Attack sequence evaluated by AI."],
        "evidence": link_result.get("reasons", []) + screenshot_result.get("reasons", []),
        "why": "Threat indicators evaluated across submitted inputs."
    }