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
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "1000"))
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5000").strip()
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "SarvShield").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT = 25

# Verified Active Free Models on OpenRouter (Updated)
FREE_TEXT_MODELS = [
    "openrouter/free",
    "minimax/minimax-m3:free"
]

FREE_VISION_MODELS = [
    "openrouter/free",
    "minimax/minimax-m3:free"
]


def empty_ai_result() -> Dict[str, Any]:
    return {
        "score": 0,
        "verdict": "LOW RISK",
        "scam_explanation": "AI analysis completed.",
        "reasons": [],
        "exact_scam_lines": [],
        "data_harvested": [],
        "detected_signals": [],
        "keywords": [],
        "immediate_steps": [],
        "recovery_steps": [],
        "helplines": [],
        "language": "English",
        "scam_type": "none",
        "detected_text": "",
        "category": "Unknown",
        "attack_chain": [],
        "scam_fingerprint": [],
        "evidence": [],
        "why": "",
        "recommended_action": "Verify through official sources.",
        "why_dangerous": "",
    }


def _safe_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _safe_score(value: Any) -> int:
    try:
        if isinstance(value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", value)
            if match:
                value = float(match.group(0))
        score = int(float(value))
    except Exception:
        score = 0
    return max(0, min(score, 100))


def normalize_ai_result(data: Any) -> Dict[str, Any]:
    result = empty_ai_result()
    if not isinstance(data, dict):
        return result

    result["score"] = _safe_score(data.get("score", 0))
    result["verdict"] = _safe_string(data.get("verdict"), "LOW RISK").upper()
    result["scam_explanation"] = _safe_string(
        data.get("scam_explanation") or data.get("explanation") or data.get("why"),
        "Analysis completed."
    )
    result["language"] = _safe_string(data.get("language"), "English")
    result["scam_type"] = _safe_string(data.get("scam_type"), "none")

    list_fields = [
        "reasons", "exact_scam_lines", "data_harvested", "detected_signals",
        "keywords", "immediate_steps", "recovery_steps", "helplines",
        "attack_chain", "scam_fingerprint", "evidence",
    ]
    for field in list_fields:
        vals = data.get(field)
        if isinstance(vals, list):
            result[field] = [_safe_string(item) for item in vals if _safe_string(item)]
        elif isinstance(vals, str) and vals.strip():
            result[field] = [vals.strip()]
        else:
            result[field] = []

    result["detected_text"] = _safe_string(data.get("detected_text"), "")
    result["category"] = _safe_string(data.get("category"), "Unknown")
    result["why"] = _safe_string(data.get("why"), "")
    result["recommended_action"] = _safe_string(data.get("recommended_action"), "Do not interact.")
    result["why_dangerous"] = _safe_string(data.get("why_dangerous"), "")
    return result


def _clean_ai_output(text: str) -> str:
    if not text:
        return ""
    # Strip <think> tags from reasoning models
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip markdown fences
    text = re.sub(r"^```(?:json|JSON)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def parse_ai_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Robust JSON parser that handles code blocks, dirty characters, and trailing commas."""
    if not raw_text:
        return None

    cleaned = _clean_ai_output(raw_text)

    # 1. Direct parse attempt
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # 2. Extract outermost JSON block {...}
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # 3. Clean trailing commas e.g. ", ]" or ", }"
        try:
            sanitized = re.sub(r",\s*([\]}])", r"\1", candidate)
            parsed = json.loads(sanitized)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 4. Fallback: Extract key values using regex if model returns malformed JSON
    try:
        fallback = {}
        score_m = re.search(r'"score"\s*:\s*(\d+)', cleaned)
        if score_m:
            fallback["score"] = int(score_m.group(1))

        verdict_m = re.search(r'"verdict"\s*:\s*"([^"]+)"', cleaned)
        if verdict_m:
            fallback["verdict"] = verdict_m.group(1)

        # Extract reasons list
        reasons_m = re.search(r'"reasons"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
        if reasons_m:
            items = re.findall(r'"([^"]+)"', reasons_m.group(1))
            if items:
                fallback["reasons"] = items

        if fallback:
            return fallback
    except Exception:
        pass

    return None


def _compress_and_encode_image(image_bytes: bytes) -> Optional[str]:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        max_dim = 1024
        if max(image.size) > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80, optimize=True)
        compressed_bytes = buffer.getvalue()
        b64_str = base64.b64encode(compressed_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"[AI IMAGE ERROR] Compression failed: {e}")
        return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"


def _image_to_data_url(image_data: Any) -> Optional[str]:
    if image_data is None:
        return None
    try:
        if isinstance(image_data, str):
            if image_data.startswith("data:image/"):
                return image_data
            if os.path.isfile(image_data):
                with open(image_data, "rb") as f:
                    return _compress_and_encode_image(f.read())
            try:
                raw = base64.b64decode(image_data)
                return _compress_and_encode_image(raw)
            except Exception:
                return None
        if isinstance(image_data, (bytes, bytearray)):
            return _compress_and_encode_image(bytes(image_data))
        if hasattr(image_data, "read"):
            return _compress_and_encode_image(image_data.read())
    except Exception as e:
        print(f"[AI IMAGE FORMAT ERROR] {e}")
    return None


def _extract_response_text(response_json: Dict[str, Any]) -> str:
    try:
        choices = response_json.get("choices", [])
        if not choices:
            return ""
        choice = choices[0] or {}
        message = choice.get("message", {}) or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = [str(b.get("text")) for b in content if isinstance(b, dict) and b.get("text")]
            if parts:
                return "\n".join(parts).strip()
        if "text" in choice:
            return _safe_string(choice.get("text"))
    except Exception as e:
        print(f"[AI PARSE ERROR] {e}")
    return ""


def call_openrouter(prompt: str, image_data: Any = None, system_prompt: Optional[str] = None,
                    max_tokens: Optional[int] = None) -> Dict[str, Any]:
    result = empty_ai_result()

    if not OPENROUTER_API_KEY:
        print("[AI ERROR] OPENROUTER_API_KEY is missing in your .env file!")
        return result

    prompt = _safe_string(prompt)
    if not prompt:
        return result

    token_limit = int(max_tokens if max_tokens is not None else OPENROUTER_MAX_TOKENS)
    token_limit = max(100, min(token_limit, 4000))

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
    }

    has_image = image_data is not None

    if has_image:
        image_url = _image_to_data_url(image_data)
        if not image_url:
            return result

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt + "\n\nCRITICAL: Return ONLY valid JSON format without markdown fences."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        models_to_try = FREE_VISION_MODELS
    else:
        sys_msg = system_prompt or "You are an AI cyber threat detector. Always return valid JSON only."
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]
        models_to_try = list(dict.fromkeys(FREE_TEXT_MODELS))

    payload = {
        "messages": messages,
        "max_tokens": token_limit,
        "temperature": 0.2
    }

    for target_model in models_to_try:
        payload["model"] = target_model
        print(f"[AI] Attempting call to: {target_model}")

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
        except requests.exceptions.Timeout:
            print(f"[AI TIMEOUT] {target_model} timed out. Trying next fallback...")
            continue
        except Exception as req_err:
            print(f"[AI CONNECTION ERROR] {target_model}: {req_err}")
            continue

        if response.status_code != 200:
            try:
                err_json = response.json()
                err_msg = err_json.get("error", {}).get("message", response.text[:200])
                print(f"[AI HTTP {response.status_code}] ({target_model}) Error: {err_msg}")
            except Exception:
                print(f"[AI HTTP {response.status_code}] ({target_model}) Raw: {response.text[:200]}")
            continue

        try:
            response_json = response.json()
        except Exception as json_err:
            print(f"[AI RESPONSE PARSE ERROR] {json_err}")
            continue

        raw_text = _extract_response_text(response_json)
        if not raw_text:
            continue

        parsed = parse_ai_json(raw_text)
        if parsed is not None:
            final_result = normalize_ai_result(parsed)
            actual_model = response_json.get("model", target_model)
            print(f"[AI SUCCESS] Successfully analyzed using: {actual_model}")
            return final_result
        else:
            print(f"[AI PARSE NOTICE] Failed to parse JSON from {target_model}, attempting regex fallback or next model...")

    print("[AI FAILED] All fallback models exhausted. Returning safe fallback.")
    return result


def ai_analyze(prompt: str, image_data: Any = None) -> Dict[str, Any]:
    return call_openrouter(prompt, image_data=image_data)


def openrouter_configured() -> bool:
    return bool(OPENROUTER_API_KEY)