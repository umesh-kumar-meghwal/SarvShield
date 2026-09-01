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
    attack_chain=None
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

CRITICAL RULES:
1. Provide highly specific steps tailored strictly to this exact scam (e.g., if Instagram follower scam -> Instagram password/2FA steps; if fake ID -> Aadhaar biometric lock; if banking/KYC -> bank freezing & 1930).
2. Separate into:
   - 'immediate_steps': What the user should do right now to avoid getting trapped.
   - 'recovery_steps': Exact steps to take if the user ALREADY clicked, submitted credentials, uploaded data, or paid money.
   - 'why_dangerous': 2-sentence explanation of legal/financial/privacy consequences.
   - 'helplines': Relevant official contact portals.

Return ONLY valid JSON matching this exact structure:
{{
    "recommended_action": "Short powerful headline (e.g. NEVER PROVIDE CREDENTIALS FOR FOLLOWERS / DO NOT USE FAKE ID GENERATOR)",
    "why_dangerous": "Detailed risk and consequence explanation.",
    "immediate_steps": [
        "Immediate preventive step 1 tailored to this threat",
        "Immediate preventive step 2",
        "Immediate preventive step 3",
        "Immediate preventive step 4"
    ],
    "recovery_steps": [
        "Specific recovery step if user already entered data / clicked / sent money",
        "Emergency recovery step 2",
        "Emergency recovery step 3"
    ],
    "helplines": [
        "National Cyber Crime Helpline: Dial 1930 (https://cybercrime.gov.in)",
        "Relevant specific authority or portal for this case"
    ]
}}
"""
    data = call_openrouter(prompt)

    if data:
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