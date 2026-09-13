# screenshot_detect.py
from ai_helper import call_openrouter


def screenshot_detect(image_data, language: str = "English") -> dict:
    target_lang = str(language or "English").strip()

    if not image_data:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "reasons": ["No screenshot image provided."],
            "detected_text": "",
            "category": "Unknown"
        }

    prompt = f"""

You are an expert cybersecurity visual forensic examiner.

Analyze the ENTIRE IMAGE and determine whether the image itself contains
any visible scam, fraud, phishing, social-engineering, fake-payment,
credential-theft, fake-offer, or other suspicious content.

IMPORTANT:
Do not focus only on phishing or payment screenshots.

Inspect EVERYTHING visible in the image, including:
- Text
- Logos and branding
- URLs and links
- QR codes
- Phone numbers
- Email addresses
- Payment instructions
- UPI/payment details
- OTP/password/login requests
- Bank or card information
- Fake bills or receipts
- Lottery/prize/giveaway claims
- Investment/earning claims
- Urgency/threat messages
- Suspicious offers
- Social-media messages/posts/profiles
- Impersonation indicators
- Buttons and calls-to-action
- Any other visible content that could indicate a scam

The classification MUST be based only on evidence actually visible in the image.

Do NOT assume something is a scam simply because:
- It is a social-media profile
- It contains a verified badge
- It has many followers
- It contains a person's photograph
- It contains normal profile information
- It contains a normal website or social-media link

If there is no visible evidence of scam/fraud/phishing/suspicious activity,
classify the image as SAFE.

If there are some suspicious indicators but there is not enough evidence
to confidently call it a scam, classify it as SUSPICIOUS.

If the image contains clear visible evidence of scam/fraud/phishing,
classify it as SCAM.

CRITICAL:
Do NOT invent information that is not visible in the image.
Do NOT assume hidden context.
Do NOT claim a URL, payment request, OTP, phone number, or scam message
exists unless it is actually visible.

SCORING:
0-20   = LOW RISK
21-50  = SUSPICIOUS
51-100 = HIGH RISK

The score must reflect the strength of visible evidence.

MULTILINGUAL INSTRUCTION:

The user requested output in: "{target_lang}".

ALL descriptive explanations in the "reasons" array MUST be written fully
in "{target_lang}" using its native writing script.

"detected_text" must contain the ORIGINAL text visible in the image.

"category" and "verdict" MUST remain in standard English.

Return ONLY valid JSON:

{{
  "score": 0,
  "verdict": "SAFE",
  "reasons": [
    "Specific visual evidence from the image",
    "Second specific observation from the image"
  ],
  "detected_text": "All important text visible in the image",
  "category": "Safe / Phishing / Fake Payment / Fake UPI / Fake Bill / Fake Lottery / Credential Theft / Investment Scam / Social Engineering / Impersonation / Other Scam / Unknown"
}}

FINAL RULE:
First inspect the complete image.
Then identify visible evidence.
Then classify the image as SAFE, SUSPICIOUS, or SCAM.
Never classify based on assumptions outside the image.
"""

    try:
        data = call_openrouter(prompt, image_data=image_data)
        if not isinstance(data, dict):
            return {
                "score": 0,
                "verdict": "UNKNOWN",
                "reasons": ["Visual analysis returned invalid response."],
                "detected_text": "",
                "category": "Unknown"
            }

        score = max(0, min(int(data.get("score", 0) or 0), 100))
        reasons = data.get("reasons", [])
        if not isinstance(reasons, list) or not reasons:
            reasons = ["Visual scan completed."]

        verdict = str(data.get("verdict") or (
            "VERY HIGH RISK" if score >= 80 else
            "HIGH RISK" if score >= 60 else
            "MEDIUM RISK" if score >= 40 else
            "SUSPICIOUS" if score >= 20 else
            "LOW RISK"
        )).upper()

        return {
            "score": score,
            "verdict": verdict,
            "reasons": [str(x) for x in reasons],
            "detected_text": str(data.get("detected_text", "") or ""),
            "category": str(data.get("category", "Unknown") or "Unknown")
        }

    except Exception as e:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "reasons": [f"Error: {str(e)}"],
            "detected_text": "",
            "category": "Unknown"
        }