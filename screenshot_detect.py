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

# Free hosting ya untrusted domain ke SSL warning ko disable karta hai
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
    """
    Kisi bhi destination website ko open karta hai aur uska actual data
    (Title, Headings, Text, Forms, Outbound Action Links) extract karta hai.
    """
    page_info = {
        "url": target_url,
        "final_url": target_url,
        "domain": "",
        "title": "",
        "headings": [],
        "text_content": "",
        "form_inputs": [],
        "action_links": [],
        "is_direct_download": False,
        "error": None
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8"
    }

    try:
        session = requests.Session()
        resp = session.get(target_url, timeout=8, allow_redirects=True, headers=headers, verify=False)
        page_info["final_url"] = resp.url
        page_info["domain"] = urlparse(resp.url).netloc.lower().split(":")[0]

        content_type = resp.headers.get("content-type", "").lower()
        if resp.url.lower().endswith((".apk", ".exe", ".zip")) or "application/vnd.android.package-archive" in content_type:
            page_info["is_direct_download"] = True

        html_text = resp.text[:75000]
        soup = BeautifulSoup(html_text, "html.parser")

        # 1. Page Title
        if soup.title and soup.title.string:
            page_info["title"] = re.sub(r"\s+", " ", soup.title.string).strip()

        # 2. Page Headings (H1, H2, H3)
        for h in soup.find_all(["h1", "h2", "h3"]):
            text = h.get_text(" ", strip=True)
            if text and len(text) > 2:
                page_info["headings"].append(text)

        # 3. Form Inputs (User se kya maang rahe hain)
        for inp in soup.find_all(["input", "textarea"]):
            name_val = inp.get("placeholder") or inp.get("name") or inp.get("type") or ""
            if name_val and name_val not in page_info["form_inputs"]:
                page_info["form_inputs"].append(name_val)

        # 4. Outbound Action Links & Buttons (Andar lage huye doosre links)
        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if raw_href and not raw_href.startswith(("#", "javascript:")):
                full_link = urljoin(resp.url, raw_href)
                btn_name = a_tag.get_text(" ", strip=True)
                desc = f"{btn_name} -> {full_link}" if btn_name else full_link
                if desc not in page_info["action_links"]:
                    page_info["action_links"].append(desc)

        # 5. Clean Visible Body Text
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        clean_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        page_info["text_content"] = clean_text[:3000]

    except Exception as e:
        page_info["error"] = str(e)

    return page_info


def deep_trace_any_link(initial_payload: str) -> dict:
    """
    100% Generic Multi-Hop Link Tracer:
    Yeh kisi bhi link (Link 1 -> Link 2 -> Link 3) ko deeply trace karke
    uska poora asli content nikalta hai. Koi bhi brand hardcode nahi hai.
    """
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

    # Check UPI
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

    # Check Web URL
    is_http = bool(re.match(r"^https?://", initial_payload, re.IGNORECASE))
    is_domain = bool(re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$", initial_payload))

    if not (is_http or is_domain):
        return report

    report["is_url"] = True
    url_1 = initial_payload if is_http else ("https://" + initial_payload)
    report["hops"].append(url_1)

    # 1. Fetch First Destination Page
    page_1 = fetch_webpage_content(url_1)
    report["pages"].append(page_1)

    if page_1["final_url"] != url_1:
        report["hops"].append(page_1["final_url"])
    report["deepest_url"] = page_1["final_url"]
    report["deepest_title"] = page_1["title"]

    # 2. Check if Page 1 has an Outbound/Nested Link to another external service
    next_external_target = None
    for link_str in page_1["action_links"]:
        actual_url = link_str.split(" -> ")[-1]
        p_target = urlparse(actual_url)
        # Agar link kisi doosre domain ya Telegram/download par le ja raha hai
        if p_target.netloc and p_target.netloc != page_1["domain"] and not p_target.netloc.endswith("google.com"):
            next_external_target = actual_url
            report["nested_links_found"].append(link_str)

    # 3. Agar andar doosra link mila, toh usko bhi fetch aur scrape karo!
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

    # 1. Hardware/Optical scan for QR Code
    qr_payloads = extract_qr_code_payload(image_data)
    has_qr = len(qr_payloads) > 0
    raw_qr_payload = qr_payloads[0] if has_qr else ""

    # 2. Deep Generic Link Trace & Web Scrape
    intel = deep_trace_any_link(raw_qr_payload) if has_qr else {}

    # 3. Format the actual scraped webpage content for AI (NO HARDCODING)
    scraped_report_text = "NO QR CODE PRESENT"

    if has_qr:
        if intel.get("is_url"):
            pages_summary = []
            for i, pg in enumerate(intel.get("pages", [])):
                headings_fmt = " | ".join(pg.get("headings", [])) if pg.get("headings") else "None"
                inputs_fmt = ", ".join(pg.get("form_inputs", [])) if pg.get("form_inputs") else "None"
                links_fmt = "\n    * ".join(pg.get("action_links", [])[:6]) if pg.get("action_links") else "None"
                text_preview = pg.get("text_content", "")[:1500]

                pages_summary.append(f"""
--- [WEBPAGE {i+1} SCRAPED DATA] ---
- Requested URL: {pg.get('requested_url')}
- Final Loaded URL: {pg.get('final_url')}
- Domain: {pg.get('domain')}
- Page Title: "{pg.get('title') or 'No Title'}"
- Headings on Page: "{headings_fmt}"
- Forms / Data Fields Requested from User: "{inputs_fmt}"
- Direct Download Flag: {"YES (.apk / binary download)" if pg.get('is_direct_download') else "NO"}
- Outbound Action Links / Buttons Discovered on this Page:
    * {links_fmt}
- ACTUAL VISIBLE TEXT WRITTEN ON THIS WEBPAGE:
\"\"\"{text_preview if text_preview else 'Page text is empty or dynamically hidden.'}\"\"\"
""")

            hops_chain = " -> ".join(intel.get("hops", [raw_qr_payload]))
            nested_str = "\n  * ".join(intel.get("nested_links_found", ["None"])) if intel.get("nested_links_found") else "None"

            scraped_report_text = f"""
============================================================
LIVE QR CODE & FULL WEBPAGE SCRAPED FORENSIC REPORT:
- Initial Scanned QR Link: "{raw_qr_payload}"
- Complete Redirection Chain (Hops): {hops_chain}
- Final Deepest Destination URL: "{intel.get('deepest_url')}"
- Final Destination Title: "{intel.get('deepest_title') or 'No Title'}"
- Secondary / Nested Action Links Found Inside Pages:
  * {nested_str}

{chr(10).join(pages_summary)}
============================================================
"""
        elif intel.get("is_upi"):
            upi = intel.get("upi_details") or {}
            scraped_report_text = f"""
- QR Code Decoded: UPI Payment Intent
- Payee VPA / ID: "{upi.get('payee_vpa')}"
- Payee Name: "{upi.get('payee_name')}"
- Amount: "{upi.get('amount') or 'Open / Dynamic Amount'}"
"""
        else:
            scraped_report_text = f"- Raw QR Decoded Text: {raw_qr_payload}"

    # 4. Pure Dynamic AI Analysis (AI reads the content and decides category & reasons)
    prompt = f"""
You are a Senior Cyber Threat Intelligence Investigator.
Analyze the submitted screenshot alongside the ACTUAL LIVE SCRAPED WEBPAGE CONTENT provided below.

{scraped_report_text}

CRITICAL RULES FOR DYNAMIC THREAT EVALUATION:
1. READ THE "ACTUAL VISIBLE TEXT WRITTEN ON THIS WEBPAGE" CAREFULLY.
2. DO NOT USE ANY STATIC OR HARDCODED ASSUMPTIONS.
   - Analyze whatever the webpage is actually about (e.g. Electricity Bill, Banking, Job Offer, Exam Results, Crypto, Courier Delivery, Lottery, Telegram Group, or completely legitimate content).
3. IN THE "reasons" ARRAY, YOU MUST PROVIDE 2 TO 4 DETAILED, EVIDENCE-BASED BULLET POINTS IN "{target_lang}":
   - Explicitly quote or describe what claims, services, or text are actually written on the destination webpage.
   - If the QR code redirects to an intermediate page which then links to another destination (like Telegram or an APK download), explain this exact multi-hop funnel.
   - Point out what data the page is trying to collect or why the domain/hosting looks unverified.
4. "category" MUST BE DECIDED DYNAMICALLY BY YOU based solely on the actual evidence (e.g. Phishing, Quishing, Fake Payment, Malware Distribution, Job Scam, Impersonation, Credential Theft, Safe, etc.).
5. "score": Integer 0-100 reflecting the genuine threat level.
6. "verdict": LOW RISK, SUSPICIOUS, HIGH RISK, or VERY HIGH RISK.

MULTILINGUAL INSTRUCTION:
- Target Language: "{target_lang}".
- ALL bullet points in the "reasons" array MUST be written fully in "{target_lang}" using its native script.

Return ONLY valid JSON matching this schema:
{{
  "score": 0,
  "verdict": "SAFE",
  "qr_detected": { "true" if has_qr else "false" },
  "qr_content": "{raw_qr_payload}",
  "reasons": [
    "Specific explanation in {target_lang} describing the exact content and claims found on the scraped webpage",
    "Second specific observation in {target_lang} explaining the link redirection or nested action buttons"
  ],
  "detected_text": "{intel.get('deepest_title') or raw_qr_payload}",
  "category": "Dynamically determined category"
}}
"""

    try:
        # Send pure text prompt so the AI can process full scraped HTML text without vision timeouts
        raw_res = call_openrouter(prompt)

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
            category = str(data.get("category") or "Quishing").strip()
            verdict = str(data.get("verdict") or (
                "VERY HIGH RISK" if score >= 80 else
                "HIGH RISK" if score >= 60 else
                "SUSPICIOUS" if score >= 30 else
                "LOW RISK"
            )).upper()

            if reasons:
                return {
                    "score": score,
                    "verdict": verdict,
                    "reasons": reasons,
                    "detected_text": str(data.get("detected_text") or intel.get("deepest_title") or raw_qr_payload),
                    "category": category,
                    "qr_detected": bool(has_qr),
                    "qr_content": str(raw_qr_payload),
                    "qr_destination": intel.get("deepest_url", raw_qr_payload)
                }
    except Exception as e:
        print("[AI DYNAMIC ANALYSIS ERROR]:", repr(e))

    # Dynamic Fallback based strictly on real scraped metadata (NO hardcoded brands!)
    target_l = target_lang.lower()
    is_hi = target_l in ["hindi", "hi", "hinglish"]

    dynamic_reasons = []
    deep_url = intel.get("deepest_url", raw_qr_payload)
    deep_title = intel.get("deepest_title", "")
    has_redirect = len(intel.get("hops", [])) > 1

    if has_redirect:
        if is_hi:
            dynamic_reasons.append(f"QR कोड रीडायरेक्शन: यह लिंक आगे '{deep_url}' पर रीडायरेक्ट हो रहा है।")
        else:
            dynamic_reasons.append(f"QR Redirection: The link redirects to '{deep_url}'.")

    if deep_title:
        if is_hi:
            dynamic_reasons.append(f"वेबसाइट कंटेंट: इस पेज का टाइटल '{deep_title}' है।")
        else:
            dynamic_reasons.append(f"Webpage Content: The page displays title '{deep_title}'.")

    if intel.get("nested_links_found"):
        top_nested = intel["nested_links_found"][0]
        if is_hi:
            dynamic_reasons.append(f"पेज के अंदर अगला लिंक मिला: {top_nested[:65]}...")
        else:
            dynamic_reasons.append(f"Nested Link Inside Page: Discovered secondary link: {top_nested[:65]}...")

    if not dynamic_reasons:
        dynamic_reasons = [f"QR Link analyzed: {raw_qr_payload}"]

    return {
        "score": 65 if has_redirect else (30 if has_qr else 0),
        "verdict": "HIGH RISK" if has_redirect else ("SUSPICIOUS" if has_qr else "LOW RISK"),
        "reasons": dynamic_reasons,
        "detected_text": deep_title or raw_qr_payload,
        "category": "QR Analysis",
        "qr_detected": bool(has_qr),
        "qr_content": str(raw_qr_payload),
        "qr_destination": deep_url
    }