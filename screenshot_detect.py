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
Analyze this screenshot for phishing, fake payment slips (like UPI/Paytm), fake lottery, or credential theft.

CRITICAL MULTILINGUAL INSTRUCTION:
- The user requested output in: "{target_lang}".
- ALL descriptive forensic points in the "reasons" array MUST BE WRITTEN FULLY IN "{target_lang}" using its native writing script.
- "detected_text" must contain the original text transcribed from the image.
- "category" and "verdict" remain standard English.

Return valid JSON:
{{
  "score": 0,
  "verdict": "LOW RISK",
  "reasons": [
    "Specific visual evidence strictly in {target_lang}",
    "Second reason strictly in {target_lang}"
  ],
  "detected_text": "Transcribed text from image",
  "category": "Phishing / Fake UPI / Fake Bill / Safe / Unknown"
}}
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