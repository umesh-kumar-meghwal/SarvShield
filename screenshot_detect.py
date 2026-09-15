import io
import json
import re
from urllib.parse import urlparse, urljoin, parse_qs
import cv2
import numpy as np
from PIL import Image
import requests
from bs4 import BeautifulSoup
import urllib3
from ai_helper import call_openrouter

# Free hosting / untrusted SSL warnings disable karta hai
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def auto_crop_qr_bounding_box(img):
    """Screen photo me se white QR box ko crop karta hai taaki glare aur background bezels hat jayein."""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        _, thresh = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = gray.shape[:2]
        min_area = (w * h) * 0.08

        best_crop = None
        max_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area and area > max_area:
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = float(cw) / ch if ch > 0 else 0
                if 0.75 <= aspect_ratio <= 1.35:
                    max_area = area
                    pad = int(min(cw, ch) * 0.08)
                    x1 = max(0, x - pad)
                    y1 = max(0, y - pad)
                    x2 = min(w, x + cw + pad)
                    y2 = min(h, y + ch + pad)
                    best_crop = img[y1:y2, x1:x2]

        return best_crop if best_crop is not None else img
    except Exception:
        return img


def decode_with_all_engines(cv_img, detected_list):
    """ZXing-CPP, OpenCV, aur PyzBar se QR code scan karta hai."""
    try:
        import zxingcpp
        results = zxingcpp.read_barcodes(cv_img)
        for r in results:
            text = (r.text or "").strip()
            if text and text not in detected_list:
                detected_list.append(text)
    except Exception:
        pass

    if detected_list:
        return

    try:
        detector = cv2.QRCodeDetector()
        retval, decoded_info, _, _ = detector.detectAndDecodeMulti(cv_img)
        if retval and decoded_info:
            for text in decoded_info:
                text = (text or "").strip()
                if text and text not in detected_list:
                    detected_list.append(text)

        if not detected_list:
            text, _, _ = detector.detectAndDecode(cv_img)
            text = (text or "").strip()
            if text and text not in detected_list:
                detected_list.append(text)
    except Exception:
        pass

    if detected_list:
        return

    try:
        from pyzbar.pyzbar import decode
        pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        for obj in decode(pil_img):
            text = obj.data.decode("utf-8", errors="ignore").strip()
            if text and text not in detected_list:
                detected_list.append(text)
    except Exception:
        pass


def extract_qr_code_payload(image_bytes) -> list:
    """Multi-pass pipeline: Anti-glare aur contrast filters lagakar QR decode karta hai."""
    detected_payloads = []
    if not image_bytes:
        return detected_payloads

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return detected_payloads

        # 1. Raw scan
        decode_with_all_engines(img, detected_payloads)
        if detected_payloads:
            return detected_payloads

        # 2. Auto-crop
        cropped_img = auto_crop_qr_bounding_box(img)
        decode_with_all_engines(cropped_img, detected_payloads)
        if detected_payloads:
            return detected_payloads

        # 3. CLAHE Anti-Glare
        gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_bgr = cv2.cvtColor(clahe.apply(gray), cv2.COLOR_GRAY2BGR)
        decode_with_all_engines(enhanced_bgr, detected_payloads)
        if detected_payloads:
            return detected_payloads

        # 4. Adaptive Thresholding
        thresh = cv2.adaptiveThreshold(
            cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY),
            255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )
        decode_with_all_engines(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR), detected_payloads)
        if detected_payloads:
            return detected_payloads

        # 5. Sharpening Filter
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        decode_with_all_engines(cv2.filter2D(cropped_img, -1, kernel), detected_payloads)

    except Exception as e:
        print("[QR DECODE NOTICE]:", repr(e))

    return detected_payloads


def fetch_webpage_content(target_url: str) -> dict:
    """Destination website ko open karke uska content scrape karta hai."""
    page_info = {
        "url": target_url,
        "final_url": target_url,
        "domain": "",
        "title": "",
        "headings": [],
        "text_content": "",
        "action_links": [],
        "is_direct_download": False
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        session = requests.Session()
        resp = session.get(target_url, timeout=7, allow_redirects=True, headers=headers, verify=False)
        page_info["final_url"] = resp.url
        page_info["domain"] = urlparse(resp.url).netloc.lower().split(":")[0]

        content_type = resp.headers.get("content-type", "").lower()
        if resp.url.lower().endswith((".apk", ".exe", ".zip")) or "application/vnd.android.package-archive" in content_type:
            page_info["is_direct_download"] = True

        html_text = resp.text[:50000]
        soup = BeautifulSoup(html_text, "html.parser")

        if soup.title and soup.title.string:
            page_info["title"] = re.sub(r"\s+", " ", soup.title.string).strip()

        for h in soup.find_all(["h1", "h2", "h3"]):
            t = h.get_text(" ", strip=True)
            if t and len(t) > 2:
                page_info["headings"].append(t)

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if raw_href and not raw_href.startswith(("#", "javascript:")):
                full_link = urljoin(resp.url, raw_href)
                btn_name = a_tag.get_text(" ", strip=True)
                desc = f"{btn_name} -> {full_link}" if btn_name else full_link
                if desc not in page_info["action_links"]:
                    page_info["action_links"].append(desc)

        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        clean_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        page_info["text_content"] = clean_text[:1200]

    except Exception:
        pass

    return page_info


def deep_trace_any_link(initial_payload: str) -> dict:
    """Link 1 -> Link 2 -> Link 3 ko deeply trace karta hai."""
    report = {
        "initial_payload": initial_payload,
        "is_url": False,
        "is_upi": False,
        "hops": [],
        "pages": [],
        "deepest_url": initial_payload,
        "deepest_title": "",
        "nested_links_found": []
    }

    if not initial_payload:
        return report

    if initial_payload.lower().startswith("upi://pay"):
        report["is_upi"] = True
        try:
            parsed = urlparse(initial_payload)
            qs = parse_qs(parsed.query)
            report["upi_details"] = {
                "payee_vpa": qs.get("pa", [""])[0],
                "payee_name": qs.get("pn", [""])[0],
                "amount": qs.get("am", [""])[0],
                "note": qs.get("tn", [""])[0]
            }
        except Exception:
            pass
        return report

    is_http = bool(re.match(r"^https?://", initial_payload, re.IGNORECASE))
    is_domain = bool(re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$", initial_payload))

    if not (is_http or is_domain):
        return report

    report["is_url"] = True
    url_1 = initial_payload if is_http else ("https://" + initial_payload)
    report["hops"].append(url_1)

    page_1 = fetch_webpage_content(url_1)
    report["pages"].append(page_1)

    if page_1["final_url"] != url_1:
        report["hops"].append(page_1["final_url"])
    report["deepest_url"] = page_1["final_url"]
    report["deepest_title"] = page_1["title"]

    next_external_target = None
    for link_str in page_1["action_links"]:
        actual_url = link_str.split(" -> ")[-1]
        p_target = urlparse(actual_url)
        if p_target.netloc and p_target.netloc != page_1["domain"] and not p_target.netloc.endswith("google.com"):
            next_external_target = actual_url
            report["nested_links_found"].append(link_str)

    if next_external_target and next_external_target not in report["hops"]:
        report["hops"].append(next_external_target)
        if not ("t.me/" in next_external_target or next_external_target.lower().endswith(".apk")):
            page_2 = fetch_webpage_content(next_external_target)
            report["pages"].append(page_2)
            report["deepest_url"] = page_2["final_url"]
            if page_2["title"]:
                report["deepest_title"] = page_2["title"]

    return report


def screenshot_detect(image_data, language: str = "English") -> dict:
    target_lang = str(language or "English").strip()

    if not image_data:
        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "reasons": ["No screenshot image provided."],
            "detected_text": "",
            "category": "Unknown",
            "qr_detected": False,
            "qr_content": ""
        }

    # 1. Check if Image contains a QR code
    qr_payloads = extract_qr_code_payload(image_data)
    has_qr = len(qr_payloads) > 0
    raw_qr_payload = qr_payloads[0] if has_qr else ""

    # 2. If QR Code exists, trace the destination link / UPI
    intel = deep_trace_any_link(raw_qr_payload) if has_qr else {}

    # QR Context Report
    qr_info_block = "NO QR CODE DETECTED IN IMAGE."
    if has_qr:
        if intel.get("is_url"):
            hops_str = " -> ".join(intel.get("hops", [raw_qr_payload]))
            nested_str = ", ".join(intel.get("nested_links_found", ["None"])) if intel.get("nested_links_found") else "None"
            scraped_snippet = intel.get("pages", [{}])[0].get("text_content", "")[:600] if intel.get("pages") else ""

            qr_info_block = f"""
QR CODE FORENSIC TRACE:
- QR Code Decoded: YES
- Initial QR URL: "{raw_qr_payload}"
- Redirect Chain: {hops_str}
- Final Destination: "{intel.get('deepest_url')}"
- Target Page Title: "{intel.get('deepest_title')}"
- Nested Inner Links Found on Page: {nested_str}
- Scraped Webpage Text Preview: "{scraped_snippet}"
"""
        elif intel.get("is_upi"):
            upi = intel.get("upi_details") or {}
            qr_info_block = f"""
QR CODE UPI INTENT DETECTED:
- Payee VPA / ID: "{upi.get('payee_vpa')}"
- Payee Name: "{upi.get('payee_name')}"
- Requested Amount: "{upi.get('amount') or 'User Input'}"
"""
        else:
            qr_info_block = f"QR Code Decoded Text: {raw_qr_payload}"

    # 3. Comprehensive Vision Prompt (Reads Image Text + QR Code)
    prompt = f"""
You are a Senior Cybersecurity Visual Forensic Examiner.

Analyze the ATTACHED SCREENSHOT IMAGE thoroughly.

{qr_info_block}

CRITICAL FORENSIC INSTRUCTIONS:
1. READ AND EXTRACT ALL VISIBLE TEXT IN THE IMAGE:
   - Carefully read every text line visible in the image (e.g. bank names, account numbers, payment instructions, offer claims, WhatsApp messages, buttons).
   - Return this in "detected_text".
2. ANALYZE BOTH VISUAL EVIDENCE AND QR CODE:
   - If a QR code is present, compare the text written in the image with what the QR code actually does!
     (Example: If image text says "Scan to receive money / cashback" while it's a payment QR, that is an INSTANT HIGH RISK FRAUD [1, 2]).
   - If NO QR code is present, perform full visual threat analysis on the image text, logos, fake bills, fake receipts, urgency threats, or impersonation.
3. IN THE "reasons" ARRAY, YOU MUST PROVIDE 2 TO 4 SPECIFIC OBSERVATIONS IN "{target_lang}":
   - Specifically mention what text and details you read from the image.
   - If a QR code was scanned, mention what link/data was found inside it.
   - Explain why this is safe, suspicious, or a scam.
4. "category": Choose dynamically based on evidence (e.g. Fake Payment, Quishing, Phishing, Fake UPI, Fake Bill, Fake Receipt, Safe, etc.).
5. "score": Integer 0 to 100.
6. "verdict": LOW RISK, SUSPICIOUS, HIGH RISK, or VERY HIGH RISK.

MULTILINGUAL INSTRUCTION:
- Target Language: "{target_lang}".
- Write ALL "reasons" strictly in "{target_lang}" using its native script.

Return ONLY valid JSON matching this schema:
{{
  "score": 0,
  "verdict": "LOW RISK",
  "qr_detected": { "true" if has_qr else "false" },
  "qr_content": "{raw_qr_payload}",
  "reasons": [
    "Observation 1 in {target_lang} describing text/visuals seen in the image",
    "Observation 2 in {target_lang}"
  ],
  "detected_text": "Transcribe all visible text from the image here",
  "category": "..."
}}
"""

    try:
        # Pass image_data so Vision AI reads the image pixels directly!
        raw_res = call_openrouter(prompt, image_data=image_data)

        if isinstance(raw_res, str):
            clean_str = re.sub(r"^```json\s*", "", raw_res.strip())
            clean_str = re.sub(r"\s*```$", "", clean_str)
            data = json.loads(clean_str)
        elif isinstance(raw_res, dict):
            data = raw_res
        else:
            data = None

        if isinstance(data, dict):
            score = max(0, min(int(data.get("score", 0) or 0), 100))
            reasons = [str(x).strip() for x in data.get("reasons", []) if str(x).strip()]
            category = str(data.get("category") or ("Quishing" if has_qr else "Visual Scan")).strip()
            verdict = str(data.get("verdict") or (
                "VERY HIGH RISK" if score >= 80 else
                "HIGH RISK" if score >= 60 else
                "SUSPICIOUS" if score >= 30 else
                "LOW RISK"
            )).upper()

            detected_t = str(data.get("detected_text") or "").strip()
            if not detected_t and intel.get("deepest_title"):
                detected_t = intel.get("deepest_title")

            if reasons:
                return {
                    "score": score,
                    "verdict": verdict,
                    "reasons": reasons,
                    "detected_text": detected_t,
                    "category": category,
                    "qr_detected": bool(has_qr),
                    "qr_content": str(raw_qr_payload),
                    "qr_destination": intel.get("deepest_url", raw_qr_payload)
                }
    except Exception as e:
        print("[SCREENSHOT VISION ERROR]:", repr(e))

    # Safe Dynamic Fallback
    fallback_reasons = []
    if has_qr:
        fallback_reasons.append(f"QR Code Scanned: {raw_qr_payload}")
        if intel.get("deepest_title"):
            fallback_reasons.append(f"Target page title: {intel.get('deepest_title')}")
    else:
        fallback_reasons.append("Visual analysis completed based on image evidence.")

    return {
        "score": 40 if has_qr else 0,
        "verdict": "SUSPICIOUS" if has_qr else "LOW RISK",
        "reasons": fallback_reasons,
        "detected_text": intel.get("deepest_title", raw_qr_payload),
        "category": "Quishing" if has_qr else "Visual Analysis",
        "qr_detected": bool(has_qr),
        "qr_content": str(raw_qr_payload),
        "qr_destination": intel.get("deepest_url", raw_qr_payload)
    }