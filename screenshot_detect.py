# screenshot_detect.py
from ai_helper import call_openrouter


def screenshot_detect(image_data) -> dict:
    if not image_data:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "reasons": ["No screenshot image provided."],
            "detected_text": "",
            "category": "Unknown"
        }

    prompt = """
You are an expert cybersecurity visual forensic examiner.
Analyze this uploaded screenshot carefully for scams, phishing, fake UPI/banking screenshots, fake payment confirmations, fraudulent login portals, fake lottery notifications, or impersonation.

INSTRUCTIONS:
1. Transcribe any visible key text into 'detected_text'.
2. Identify threat signals and explain them in clear ENGLISH.
3. Compute an accurate threat score between 0 and 100.
4. Output MUST be valid JSON matching this exact structure:
{
  "score": 0,
  "verdict": "LOW RISK",
  "reasons": [
    "Specific visual/textual evidence found in screenshot in English",
    "Second reason in English"
  ],
  "detected_text": "Transcribed text from image",
  "category": "Phishing / Fake UPI / Fake Bill / Safe / Unknown"
}

Scoring Scale:
0-19: LOW RISK
20-39: SUSPICIOUS
40-59: MEDIUM RISK
60-79: HIGH RISK
80-100: VERY HIGH RISK
"""

    try:
        data = call_openrouter(prompt, image_data=image_data)
        if not isinstance(data, dict):
            return {
                "score": 0,
                "verdict": "UNKNOWN",
                "reasons": ["AI visual analysis returned an invalid response."],
                "detected_text": "",
                "category": "Unknown"
            }

        score = max(0, min(int(data.get("score", 0) or 0), 100))
        reasons = data.get("reasons", [])
        if not isinstance(reasons, list) or not reasons:
            reasons = ["Visual scan completed with no obvious threat signatures detected."]

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
            "reasons": [f"Screenshot AI analysis could not be completed: {str(e)}"],
            "detected_text": "",
            "category": "Unknown"
        }