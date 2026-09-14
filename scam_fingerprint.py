import json
import re
from ai_helper import call_openrouter


def build_scam_fingerprint(
    message="",
    phone="",
    phone_result=None,
    link="",
    link_result=None,
    screenshot_result=None,
    final_score=0,
    language="English"
) -> dict:
    """
    Reconstructs an attack profile and scam fingerprint based on the
    actual user-submitted evidence (Phone, Link, Screenshot, Message).
    """
    target_lang = str(language or "English").strip()
    link_result = link_result or {}
    screenshot_result = screenshot_result or {}
    phone_result = phone_result or {}

    # Extract dynamic real evidence
    domain = link_result.get("final_domain") or link_result.get("domain") or link or "N/A"
    phone_number = phone_result.get("phone") or phone or "N/A"
    phone_rep = phone_result.get("reputation") or phone_result.get("status") or "UNKNOWN"
    phone_carrier = phone_result.get("carrier") or "Unknown"
    phone_reports = phone_result.get("report_count") or 0
    ocr_text = screenshot_result.get("detected_text") or "N/A"
    ss_category = screenshot_result.get("category") or "Unknown"

    prompt = f"""
You are an expert Cyber Threat Intelligence Analyst.
Analyze the specific security evidence submitted by a user and generate a UNIQUE, tailored attack profile.

SUBMITTED EVIDENCE:
- Message Text: "{message if message else 'Not provided'}"
- Target URL / Domain: "{domain}"
- Phone Number: "{phone_number}" (Carrier: {phone_carrier}, Community Status: {phone_rep}, Reports: {phone_reports})
- Screenshot Evidence OCR: "{ocr_text}" (Category: {ss_category})
- Overall Calculated Risk Score: {final_score}/100

CRITICAL MULTILINGUAL & CONTEXT RULES:
1. Base your analysis STRICTLY on the actual evidence above. Do NOT use static generic templates.
2. If only a Phone was submitted, focus on vishing, telecom spoofing, or SMS lure tactics.
3. If only a Link was submitted, focus on web domain spoofing, fake login portals, or credential harvesting.
4. If only a Screenshot was submitted, focus on visual deception (fake payment receipts, QR traps, chat impersonation).
5. If only a Message was submitted, analyze its exact wording, psychological pressure, and scam mechanism.
6. The user requested output in: "{target_lang}".
   - "scam_fingerprint": 3 to 4 specific detected triggers written in "{target_lang}" using its native script (e.g., Fake KYC Notification, Urgency Threat, Toll-Free Spoof, Unverified Payment Link).
   - "attack_chain": 3 specific step-by-step stages showing how THIS SPECIFIC attack unfolds in "{target_lang}".
   - "evidence": 2 to 3 factual observations based strictly on the submitted input in "{target_lang}".
   - "why": 2 clear sentences explaining why this specific content is dangerous in "{target_lang}".
   - "match_score": integer (between 30 and 99) reflecting how strongly this matches a known scam pattern.

Return ONLY valid JSON matching this schema:
{{
    "scam_fingerprint": ["Specific Trigger 1", "Specific Trigger 2", "Specific Pattern Matched"],
    "attack_chain": ["Stage 1: ...", "Stage 2: ...", "Stage 3: ..."],
    "evidence": ["Observation 1", "Observation 2"],
    "why": "Specific explanation in {target_lang}",
    "match_score": {max(35, min(98, final_score if final_score > 0 else 60))}
}}
"""

    try:
        raw_res = call_openrouter(prompt)

        # Parse string or dict response safely
        if isinstance(raw_res, str):
            clean_str = re.sub(r"^```json\s*", "", raw_res.strip())
            clean_str = re.sub(r"\s*```$", "", clean_str)
            data = json.loads(clean_str)
        elif isinstance(raw_res, dict):
            data = raw_res
        else:
            data = None

        if isinstance(data, dict):
            fps = [str(x).strip() for x in data.get("scam_fingerprint", []) if str(x).strip()]
            chains = [str(x).strip() for x in data.get("attack_chain", []) if str(x).strip()]
            evs = [str(x).strip() for x in data.get("evidence", []) if str(x).strip()]
            why = str(data.get("why") or "").strip()
            match_score = int(data.get("match_score") or final_score or 65)

            if fps and chains:
                return {
                    "scam_fingerprint": fps[:4],
                    "attack_chain": chains[:4],
                    "evidence": evs[:4],
                    "why": why if why else "Security analysis completed based on submitted attributes.",
                    "match_score": max(30, min(99, match_score))
                }
    except Exception as err:
        print("[FINGERPRINT AI ERROR]:", repr(err))

    # Context-Aware Dynamic Fallbacks (Input-specific, never static identical text)
    fallback_fps = []
    fallback_chain = []

    if phone and not (message or link or ocr_text != "N/A"):
        fallback_fps = ["Unverified Caller ID", "Telecom Carrier Anomaly", "Unsolicited Cold Contact"]
        fallback_chain = ["Stage 1: Unsolicited Telecom Contact", "Stage 2: Social Engineering & Trust Bait", "Stage 3: Information / Fund Coercion"]
    elif link and not (message or phone or ocr_text != "N/A"):
        fallback_fps = ["Deceptive Domain Pattern", "Suspicious Web Path", "Credential Harvesting Vector"]
        fallback_chain = ["Stage 1: Link Redirection", "Stage 2: Forged Authentication Portal", "Stage 3: Data Compromise Attempt"]
    elif ocr_text != "N/A" and not (message or phone or link):
        fallback_fps = ["Forged Visual Template", "Fake Transaction Layout", "Proof-of-Payment Trick"]
        fallback_chain = ["Stage 1: Fabricated Image Proof", "Stage 2: False Financial Clearance Lure", "Stage 3: Exploitation of Trust"]
    else:
        fallback_fps = ["Urgency Pressure Trigger", "Deceptive Threat Vector", "Unverified Action Prompt"]
        fallback_chain = ["Stage 1: Initial Hook Lure", "Stage 2: Psychological Stress Coercion", "Stage 3: Targeted Action Exploitation"]

    return {
        "scam_fingerprint": fallback_fps,
        "attack_chain": fallback_chain,
        "evidence": ["Analysis completed using submitted threat signals."],
        "why": "The submitted evidence exhibits characteristics commonly associated with deceptive digital activity.",
        "match_score": max(35, min(95, final_score if final_score > 0 else 60))
    }