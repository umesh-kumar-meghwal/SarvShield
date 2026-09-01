from ai_helper import call_openrouter


def screenshot_detect(image_data):
    if not image_data:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "reasons": ["No screenshot was provided."],
            "detected_text": "",
            "category": "Unknown"
        }

    prompt = """
You are an expert screenshot scam detector.

Analyze the uploaded screenshot carefully.

Look for:
- phishing/login pages
- fake banking or payment interfaces
- fake UPI/payment requests
- fake government/KYC services
- fake Aadhaar/document generators
- fake social-media login pages
- fake lottery/prize/cashback claims
- suspicious advertisements
- credential harvesting
- impersonation of trusted brands
- suspicious URLs/domains
- requests for OTP, PIN, password or financial information

Read visible text from the screenshot when possible.

Return ONLY valid JSON.
Do not use markdown fences.
Do not add explanations outside JSON.

Exact structure:

{
  "score": 0,
  "verdict": "UNKNOWN",
  "reasons": [],
  "detected_text": "",
  "category": "Unknown"
}

Score:
0-19 = LOW RISK
20-39 = SUSPICIOUS
40-59 = MEDIUM RISK
60-79 = HIGH RISK
80-100 = VERY HIGH RISK

If the screenshot contains no useful evidence, return score 0 and verdict UNKNOWN.
"""

    try:
        data = call_openrouter(
            prompt,
            image_data=image_data
        )

        if not isinstance(data, dict):
            return {
                "score": 0,
                "verdict": "UNKNOWN",
                "reasons": ["AI returned an invalid screenshot result."],
                "detected_text": "",
                "category": "Unknown"
            }

        score = max(
            0,
            min(
                int(data.get("score", 0) or 0),
                100
            )
        )

        reasons = data.get("reasons", [])

        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        verdict = str(
            data.get("verdict") or
            ("VERY HIGH RISK" if score >= 80 else
             "HIGH RISK" if score >= 60 else
             "MEDIUM RISK" if score >= 40 else
             "SUSPICIOUS" if score >= 20 else
             "LOW RISK")
        )

        return {
            "score": score,
            "verdict": verdict,
            "reasons": [str(x) for x in reasons],
            "detected_text": str(data.get("detected_text", "") or ""),
            "category": str(data.get("category", "Unknown") or "Unknown")
        }

    except Exception as e:
        print("[SCREENSHOT ERROR]", repr(e))

        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "reasons": ["Screenshot AI analysis was unavailable."],
            "detected_text": "",
            "category": "Unknown"
        }