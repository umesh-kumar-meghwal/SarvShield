# link_detect.py
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ai_helper import call_openrouter


def link_detect(url: str, language: str = "English") -> dict:
    target_lang = str(language or "English").strip()
    result = {
        "score": 0,
        "domain": "",
        "final_domain": "",
        "verdict": "UNKNOWN",
        "scam_explanation": "",
        "reasons": [],
        "exact_scam_lines": [],
        "data_harvested": [],
        "content_preview": "",
        "content_analyzed": False
    }

    if not url or not str(url).strip():
        return result

    url = str(url).strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().split(":")[0]
        url_path = parsed.path or "/"
        result["domain"] = domain
    except Exception:
        result["reasons"] = ["Invalid URL format."]
        return result

    if not domain:
        result["reasons"] = ["Could not determine website domain."]
        return result

    website_text = ""
    page_title = ""

    try:
        response = requests.get(
            url,
            timeout=6,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
            }
        )
        try:
            result["final_domain"] = urlparse(response.url).netloc.lower().split(":")[0]
        except Exception:
            result["final_domain"] = domain

        soup = BeautifulSoup(response.text[:60000], "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "template"]):
            tag.decompose()

        if soup.title:
            page_title = soup.title.get_text(" ", strip=True)

        extracted = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:10000]
        if len(extracted) > 30:
            website_text = extracted
            result["content_analyzed"] = True
            result["content_preview"] = website_text[:1200]

    except Exception as e:
        result["reasons"].append(f"Connection notice: {str(e)}")

    prompt = f"""
You are a Senior Cyber Threat Analyst.
Analyze this website for malicious activity, phishing, or scams:

URL: {url}
Domain: {domain}
Path: {url_path}
Final Domain: {result.get('final_domain', '')}
Page Title: {page_title}
Webpage Content:
{website_text if website_text else "Page content unavailable. Analyze domain/path pattern only."}

CRITICAL MULTILINGUAL INSTRUCTION:
- The user requested output in: "{target_lang}".
- "scam_explanation", "reasons", and "data_harvested" MUST BE WRITTEN 100% IN "{target_lang}" using its native writing script.
- Keep exact quotes in "exact_scam_lines" unmodified as they appeared on the page.
- "verdict" must be one of: LOW RISK, SUSPICIOUS, HIGH RISK, VERY HIGH RISK.

Return ONLY valid JSON matching this schema:
{{
    "score": 0,
    "verdict": "LOW RISK",
    "scam_explanation": "Detailed explanation strictly in {target_lang}",
    "reasons": [
        "First reason strictly in {target_lang}",
        "Second reason strictly in {target_lang}"
    ],
    "exact_scam_lines": [],
    "data_harvested": []
}}
"""

    try:
        data = call_openrouter(prompt)
    except Exception:
        data = None

    if isinstance(data, dict):
        score = max(0, min(int(data.get("score", 0) or 0), 100))
        result["score"] = score
        verdict = str(data.get("verdict", "UNKNOWN")).strip().upper()
        result["verdict"] = verdict if verdict in {"LOW RISK", "SUSPICIOUS", "HIGH RISK", "VERY HIGH RISK"} else "UNKNOWN"
        result["scam_explanation"] = str(data.get("scam_explanation") or "Analysis completed.")
        
        ai_reasons = data.get("reasons", [])
        if isinstance(ai_reasons, list):
            result["reasons"].extend([str(r).strip() for r in ai_reasons if str(r).strip()])

        result["exact_scam_lines"] = [str(x).strip() for x in data.get("exact_scam_lines", []) if str(x).strip()]
        result["data_harvested"] = [str(x).strip() for x in data.get("data_harvested", []) if str(x).strip()]

    result["reasons"] = list(dict.fromkeys(result["reasons"]))
    return result