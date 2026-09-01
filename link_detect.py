import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ai_helper import call_openrouter


def link_detect(url):

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


    # =====================================================
    # EMPTY URL
    # =====================================================

    if not url or not str(url).strip():
        return result


    url = str(url).strip()


    # =====================================================
    # ADD HTTPS
    # =====================================================

    if not re.match(
        r"^https?://",
        url,
        re.IGNORECASE
    ):
        url = "https://" + url


    # =====================================================
    # PARSE URL
    # =====================================================

    try:

        parsed = urlparse(url)

        domain = (
            parsed.netloc
            .lower()
            .split(":")[0]
        )

        url_path = parsed.path or "/"

        result["domain"] = domain

    except Exception as e:

        result["reasons"] = [
            "Invalid URL format."
        ]

        return result


    # =====================================================
    # BASIC DOMAIN VALIDATION
    # =====================================================

    if not domain:

        result["reasons"] = [
            "Could not determine website domain."
        ]

        return result


    # =====================================================
    # FETCH WEBSITE
    # =====================================================

    website_text = ""

    page_title = ""

    try:

        response = requests.get(

            url,

            timeout=6,

            allow_redirects=True,

            headers={
                "User-Agent":
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            }

        )


        # ---------------------------------------------
        # FINAL DOMAIN AFTER REDIRECT
        # ---------------------------------------------

        try:

            result["final_domain"] = (
                urlparse(response.url)
                .netloc
                .lower()
                .split(":")[0]
            )

        except Exception:

            result["final_domain"] = domain


        # ---------------------------------------------
        # HTTP STATUS
        # ---------------------------------------------

        if response.status_code >= 400:

            result["reasons"].append(
                f"Website returned HTTP status {response.status_code}."
            )


        # ---------------------------------------------
        # PARSE HTML
        # ---------------------------------------------

        soup = BeautifulSoup(
            response.text[:60000],
            "html.parser"
        )


        # Remove unnecessary elements

        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "template"
        ]):

            tag.decompose()


        # ---------------------------------------------
        # PAGE TITLE
        # ---------------------------------------------

        if soup.title:

            page_title = soup.title.get_text(
                " ",
                strip=True
            )


        # ---------------------------------------------
        # EXTRACT TEXT
        # ---------------------------------------------

        extracted = re.sub(
            r"\s+",
            " ",
            soup.get_text(
                " ",
                strip=True
            )
        )


        extracted = extracted[:10000]


        # ---------------------------------------------
        # CLOUDFLARE CHECK
        # ---------------------------------------------

        if "just a moment" in extracted.lower():

            result["reasons"].append(
                "The page appears to be protected by a verification page."
            )

        elif len(extracted) > 30:

            website_text = extracted

            result["content_analyzed"] = True

            result["content_preview"] = (
                website_text[:1200]
            )

        else:

            result["reasons"].append(
                "Very little readable webpage content was available."
            )


    except requests.exceptions.Timeout:

        result["reasons"].append(
            "Website request timed out."
        )

    except requests.exceptions.ConnectionError:

        result["reasons"].append(
            "Could not connect to the website."
        )

    except requests.exceptions.RequestException as e:

        result["reasons"].append(
            "Website request failed."
        )

        print(
            "LINK REQUEST ERROR:",
            repr(e)
        )

    except Exception as e:

        result["reasons"].append(
            "Website content could not be analyzed."
        )

        print(
            "LINK FETCH ERROR:",
            repr(e)
        )


    # =====================================================
    # AI PROMPT
    # =====================================================

    prompt = f"""
You are a Senior Cyber Threat Analyst.

Analyze the following website URL and available webpage text.

Target URL:
{url}

Domain:
{domain}

Path:
{url_path}

Final Domain:
{result.get("final_domain", "")}

Page Title:
{page_title}

Webpage Content:
\"\"\"
{
    website_text
    if website_text
    else
    "Page text could not be fetched. Analyze the domain and URL path only."
}
\"\"\"

Return ONLY valid JSON.

Required JSON format:

{{
    "score": 0,
    "verdict": "LOW RISK",
    "scam_explanation": "Short explanation of the website risk.",
    "reasons": [
        "Reason 1",
        "Reason 2"
    ],
    "exact_scam_lines": [
        "Exact phrase from webpage if available"
    ],
    "data_harvested": [
        "Email",
        "Phone number"
    ]
}}

Rules:

1. Score must be between 0 and 100.

2. Verdict should be one of:
   LOW RISK
   SUSPICIOUS
   HIGH RISK
   VERY HIGH RISK
   UNKNOWN

3. Do not invent webpage quotes.

4. Only include exact_scam_lines when the text actually contains those phrases.

5. If webpage content is unavailable, exact_scam_lines should be an empty list.

6. data_harvested should contain only information that the webpage appears to request or collect.

7. reasons should contain concise security reasons.

8. Return valid JSON only.
"""


    # =====================================================
    # OPENROUTER AI
    # =====================================================

    try:

        data = call_openrouter(prompt)

    except Exception as e:

        print(
            "OPENROUTER LINK ERROR:",
            repr(e)
        )

        data = None


    # =====================================================
    # PROCESS AI RESULT
    # =====================================================

    if isinstance(data, dict):

        # ---------------------------------------------
        # SCORE
        # ---------------------------------------------

        try:

            score = int(
                data.get("score", 0)
            )

        except Exception:

            score = 0


        result["score"] = max(
            0,
            min(score, 100)
        )


        # ---------------------------------------------
        # VERDICT
        # ---------------------------------------------

        result["verdict"] = str(
            data.get(
                "verdict",
                "UNKNOWN"
            )
        )


        # ---------------------------------------------
        # EXPLANATION
        # ---------------------------------------------

        result["scam_explanation"] = str(
            data.get(
                "scam_explanation",
                ""
            )
        )


        # ---------------------------------------------
        # REASONS
        # ---------------------------------------------

        reasons = data.get(
            "reasons",
            []
        )

        if isinstance(reasons, list):

            result["reasons"].extend(
                [
                    str(x)
                    for x in reasons
                    if x
                ]
            )


        # ---------------------------------------------
        # EXACT SCAM LINES
        # ---------------------------------------------

        exact_lines = data.get(
            "exact_scam_lines",
            []
        )

        if isinstance(
            exact_lines,
            list
        ):

            result["exact_scam_lines"] = [

                str(line)

                for line in exact_lines

                if line
                and "just a moment"
                not in str(line).lower()

            ]


        # ---------------------------------------------
        # DATA HARVESTED
        # ---------------------------------------------

        harvested = data.get(
            "data_harvested",
            []
        )

        if isinstance(
            harvested,
            list
        ):

            result["data_harvested"] = [

                str(x)

                for x in harvested

                if x

            ]


    else:

        # =================================================
        # AI FAILED
        # =================================================

        result["reasons"].append(
            "AI website analysis was unavailable."
        )


    # =====================================================
    # REMOVE DUPLICATE REASONS
    # =====================================================

    result["reasons"] = list(
        dict.fromkeys(
            result["reasons"]
        )
    )


    return result