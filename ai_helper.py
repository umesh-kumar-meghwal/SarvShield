# ai_helper.py
import os
import re
import json
import base64
import io
import requests
from typing import Any, Dict, Optional
from PIL import Image

# ============================================================
# CONFIGURATION
# ============================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash:free").strip()
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "1000"))
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5000").strip()
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "ScamShield").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT = 30

# ONLY PURE VISION MODELS (No Text-Only Garbage)
FREE_VISION_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "minimax/minimax-m3:free",
    "openrouter/free"
]


print(f"[AI CONFIG] DEFAULT MODEL: {OPENROUTER_MODEL}")
print(f"[AI CONFIG] MAX TOKENS: {OPENROUTER_MAX_TOKENS}")


def empty_ai_result() -> Dict[str, Any]:
    return {
        "score": 0, "verdict": "UNKNOWN", "scam_explanation": "AI analysis completed.",
        "reasons": [], "exact_scam_lines": [], "data_harvested": [], "detected_signals": [],
        "keywords": [], "immediate_steps": [], "recovery_steps": [], "helplines": [],
        "language": "unknown", "scam_type": "unknown", "detected_text": "", "category": "Unknown",
        "attack_chain": [], "scam_fingerprint": [], "evidence": [], "why": "",
        "recommended_action": "Verify through official sources", "why_dangerous": "",
    }


def _safe_list(value: Any) -> list:
    if value is None: return []
    if isinstance(value, list): return value
    if isinstance(value, tuple): return list(value)
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return [str(value)]


def _safe_string(value: Any, default: str = "") -> str:
    if value is None: return default
    if isinstance(value, str): return value.strip()
    return str(value).strip()


def _safe_score(value: Any) -> int:
    try:
        if isinstance(value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", value)
            if match: value = float(match.group(0))
        score = int(float(value))
    except Exception:
        score = 0
    return max(0, min(score, 100))


def normalize_ai_result(data: Any) -> Dict[str, Any]:
    result = empty_ai_result()
    if not isinstance(data, dict): return result
    result["score"] = _safe_score(data.get("score", 0))
    result["verdict"] = _safe_string(data.get("verdict"), "UNKNOWN")
    result["scam_explanation"] = _safe_string(
        data.get("scam_explanation") or data.get("explanation") or data.get("why"),
        "AI analysis completed."
    )
    result["language"] = _safe_string(data.get("language"), "unknown")
    result["scam_type"] = _safe_string(data.get("scam_type"), "unknown")

    list_fields = [
        "reasons", "exact_scam_lines", "data_harvested", "detected_signals",
        "keywords", "immediate_steps", "recovery_steps", "helplines",
        "attack_chain", "scam_fingerprint", "evidence",
    ]
    for field in list_fields:
        values = _safe_list(data.get(field))
        result[field] = [_safe_string(item) for item in values if _safe_string(item)]

    result["detected_text"] = _safe_string(data.get("detected_text"), "")
    result["category"] = _safe_string(data.get("category"), "Unknown")
    result["why"] = _safe_string(data.get("why"), "")
    result["recommended_action"] = _safe_string(data.get("recommended_action"), "")
    result["why_dangerous"] = _safe_string(data.get("why_dangerous"), "")
    return result


def _clean_ai_output(text: str) -> str:
    if not text: return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"^```(?:json|JSON)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def parse_ai_json(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text: return None
    cleaned = _clean_ai_output(raw_text)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict): return parsed
    except Exception:
        pass

    # Extract {...} JSON block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict): return parsed
        except Exception:
            pass

    return None


def _compress_and_encode_image(image_bytes: bytes) -> Optional[str]:
    """Compresses image to max 1024px and JPEG 80% to fix OpenRouter 400 errors."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Resize to max dimension 1024px maintaining aspect ratio
        max_dim = 1024
        if max(image.size) > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80, optimize=True)
        compressed_bytes = buffer.getvalue()

        b64_str = base64.b64encode(compressed_bytes).decode("utf-8")
        print(f"[AI] Image compressed successfully: {len(image_bytes) // 1024}KB -> {len(compressed_bytes) // 1024}KB")
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"[AI IMAGE COMPRESSION ERROR] {e}")
        # Fallback to direct raw base64
        return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"


def _image_to_data_url(image_data: Any) -> Optional[str]:
    if image_data is None: return None
    try:
        if isinstance(image_data, str):
            if image_data.startswith("data:image/"): return image_data
            if os.path.isfile(image_data):
                with open(image_data, "rb") as f: raw = f.read()
                return _compress_and_encode_image(raw)
            try:
                raw = base64.b64decode(image_data)
                return _compress_and_encode_image(raw)
            except Exception:
                return None
        if isinstance(image_data, (bytes, bytearray)):
            return _compress_and_encode_image(bytes(image_data))
        if hasattr(image_data, "read"):
            raw = image_data.read()
            return _compress_and_encode_image(raw)
    except Exception as e:
        print(f"[AI IMAGE ERROR] {e}")
    return None


def _extract_response_text(response_json: Dict[str, Any]) -> str:
    try:
        choices = response_json.get("choices", [])
        if not choices: return ""
        choice = choices[0] or {}
        message = choice.get("message", {}) or {}
        content = message.get("content")
        if isinstance(content, str): return content.strip()
        if isinstance(content, list):
            parts = [str(b.get("text")) for b in content if isinstance(b, dict) and b.get("text")]
            if parts: return "\n".join(parts).strip()
        if "text" in choice: return _safe_string(choice.get("text"))
    except Exception as e:
        print(f"[AI PARSE ERROR] {e}")
    return ""


def call_openrouter(prompt: str, image_data: Any = None, system_prompt: Optional[str] = None,
                    max_tokens: Optional[int] = None) -> Dict[str, Any]:
    result = empty_ai_result()
    if not OPENROUTER_API_KEY:
        print("[AI ERROR] OPENROUTER_API_KEY is missing.")
        return result

    prompt = _safe_string(prompt)
    if not prompt: return result

    token_limit = int(max_tokens if max_tokens is not None else OPENROUTER_MAX_TOKENS)
    token_limit = max(100, min(token_limit, 8000))

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
    }

    has_image = image_data is not None

    if has_image:
        image_url = _image_to_data_url(image_data)
        if not image_url: return result

        combined_instruction = f"""You are ScamShield Cybersecurity Threat Analyzer.
{prompt}

CRITICAL: Return ONLY a valid JSON object matching the requested schema. No conversational comments."""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": combined_instruction},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        models_to_try = FREE_VISION_MODELS
    else:
        sys_msg = system_prompt or "You are ScamShield threat analyzer. Output ONLY valid JSON."
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]
        models_to_try = [OPENROUTER_MODEL, "google/gemini-2.0-flash:free", "openrouter/free"]

    payload = {
        "messages": messages,
        "max_tokens": token_limit,
        "temperature": 0.1
    }

    # Only set response_format for text calls
    if not has_image:
        payload["response_format"] = {"type": "json_object"}

    # Loop through Vision models
    for target_model in models_to_try:
        payload["model"] = target_model
        print(f"[AI] Trying Target Model: {target_model}")

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            print(f"[AI TIMEOUT] {target_model} timed out. Trying next fallback...")
            continue
        except Exception as req_err:
            print(f"[AI REQUEST ERROR] {target_model}: {req_err}")
            continue

        print(f"[AI] OpenRouter HTTP Status: {response.status_code} ({target_model})")

        if response.status_code != 200:
            try:
                err_detail = response.json()
                print(f"[AI API ERROR] {err_detail.get('error', {}).get('message', response.text[:200])}")
            except Exception:
                print(f"[AI API ERROR] {response.text[:200]}")
            continue

        try:
            response_json = response.json()
        except Exception:
            continue

        raw_text = _extract_response_text(response_json)
        if not raw_text:
            continue

        parsed = parse_ai_json(raw_text)
        if parsed is not None:
            final_result = normalize_ai_result(parsed)
            print(f"[AI SUCCESS] Model used: {response_json.get('model', target_model)}")
            return final_result

    print("[AI FAILED] All fallback models exhausted.")
    return result


def ai_analyze(prompt: str, image_data: Any = None) -> Dict[str, Any]:
    return call_openrouter(prompt, image_data=image_data)


def openrouter_configured() -> bool:
    return bool(OPENROUTER_API_KEY)


def screenshot_detect(image_data):
    if not image_data:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "reasons": ["No screenshot was provided."],
            "detected_text": "",
            "category": "Unknown"
        }

    prompt = """Analyze this screenshot carefully for fraud/scams (e.g. fake UPI transaction, fake lottery, fake electricity bill suspension, phishing login, fake WhatsApp support).
1. Read and transcribe any visible text into 'detected_text'.
2. Calculate a threat score (0-100).
3. Return ONLY this exact JSON schema:
{
  "score": 0,
  "verdict": "LOW RISK",
  "reasons": ["Specific evidence 1 found in image", "Specific evidence 2"],
  "detected_text": "All transcribed text from screenshot",
  "category": "Phishing / Fake UPI / Fake Bill / Safe / Unknown"
}
Score scale: 0-19: LOW RISK, 20-39: SUSPICIOUS, 40-59: MEDIUM RISK, 60-79: HIGH RISK, 80-100: VERY HIGH RISK"""

    try:
        data = call_openrouter(prompt, image_data=image_data)
        score = max(0, min(int(data.get("score", 0) or 0), 100))
        reasons = data.get("reasons", [])
        if not isinstance(reasons, list):
            reasons = [str(reasons)] if reasons else []

        verdict = str(data.get("verdict") or (
            "VERY HIGH RISK" if score >= 80 else
            "HIGH RISK" if score >= 60 else
            "MEDIUM RISK" if score >= 40 else
            "SUSPICIOUS" if score >= 20 else
            "LOW RISK"
        ))

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
            "reasons": ["AI screenshot analysis could not be completed."],
            "detected_text": "",
            "category": "Unknown"
        }