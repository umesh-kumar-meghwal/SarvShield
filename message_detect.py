from ai_helper import call_openrouter


def message_detect(message):

    # =========================================================
    # 1. EMPTY MESSAGE
    # =========================================================
    if not message or not str(message).strip():
        return {
            "score": 0,
            "verdict": "NO MESSAGE",
            "language": "unknown",
            "scam_type": "none",
            "reasons": []
        }

    # =========================================================
    # 2. CLEAN MESSAGE
    # =========================================================
    message = str(message).strip()

    # Optional safety limit
    if len(message) > 10000:
        message = message[:10000]

    # =========================================================
    # 3. FORENSIC ANALYSIS PROMPT
    # =========================================================
    prompt = f"""
You are a professional cybersecurity threat-classification engine.

Your job is to determine whether the EXACT MESSAGE provided below
contains evidence of a scam, fraud, phishing attempt, malicious social
engineering, impersonation, credential theft, or financial deception.

IMPORTANT:
Analyze ONLY the actual message.

Do NOT invent:
- sender identity
- background
- intent
- relationship between people
- missing context
- external events
- facts not present in the message

==================================================
MESSAGE TO ANALYZE
==================================================

{message}

==================================================
CORE ANALYSIS RULES
==================================================

1. EVIDENCE FIRST

Every conclusion must be supported by something explicitly present
in the message.

Do not assume a message is fraudulent merely because it mentions:

- a company
- a bank
- money
- an account
- a phone number
- an OTP
- a payment
- a link
- a deadline
- a warning
- an examination
- a job
- a delivery
- a refund
- a person
- a government organization

These things can appear in completely legitimate messages.

--------------------------------------------------

2. NORMAL MESSAGES

Ordinary messages should normally receive LOW RISK.

Examples include:

- school notices
- college notices
- examination announcements
- library reminders
- attendance notices
- workplace announcements
- normal customer-service messages
- appointment reminders
- delivery updates
- greetings
- introductions
- ordinary questions
- normal conversations
- legitimate instructions
- warnings about ordinary institutional consequences

Do NOT classify these as scams without additional evidence.

--------------------------------------------------

3. STRONG SCAM INDICATORS

Increase the risk when there is clear evidence of:

- impersonation of a trusted organization/person
- phishing
- credential theft
- password theft
- OTP theft
- PIN/CVV/recovery-code requests
- fraudulent payment requests
- suspicious money transfers
- fake prizes or rewards
- fake refunds
- fake loans
- fake jobs
- investment fraud
- account takeover attempts
- malicious links
- requests to install suspicious software
- deceptive financial claims
- fake verification requests
- threats designed to force payment or disclosure of information
- suspicious requests to bypass normal security procedures

--------------------------------------------------

4. CONTEXT IS MORE IMPORTANT THAN KEYWORDS

Never score a message highly because of one keyword.

Consider the meaning of the COMPLETE message.

Example:

"Your OTP is 4821."

This alone is NOT automatically a scam.

But:

"Send me the OTP you received to verify your account."

This is a strong credential-theft indicator.

Another example:

"Return your library books within seven days."

This is NOT a scam.

Another example:

"Your account will be closed today unless you send your OTP
using the link below."

This is highly suspicious.

--------------------------------------------------

5. URGENCY AND DEADLINES

Urgency alone does NOT mean scam.

Legitimate organizations can have:

- deadlines
- examination dates
- payment dates
- return periods
- appointment dates
- submission deadlines
- account notices

Only increase the risk when urgency is combined with suspicious
deception, unauthorized payment requests, credential requests,
impersonation, malicious links, or similar evidence.

--------------------------------------------------

6. THREATS AND CONSEQUENCES

Normal institutional consequences are NOT automatically scams.

For example:

"If you do not return your books within seven days, books will not
be issued next semester."

This is a normal administrative notice.

Do NOT classify it as fraud merely because it contains a consequence.

However, threats involving fake authorities, financial demands,
credential disclosure, or deceptive claims may increase the risk.

--------------------------------------------------

7. LINKS

A URL by itself is NOT proof of a scam.

Determine whether the surrounding message provides evidence that
the link is being used for:

- phishing
- credential theft
- malicious downloads
- fake verification
- fraudulent payment
- impersonation

Do not automatically assign a high score simply because a URL exists.

--------------------------------------------------

8. COMPANIES AND ORGANIZATIONS

Mentioning a bank, university, company, government organization,
delivery company, or other institution is NOT evidence of fraud.

Only consider impersonation when the message provides evidence
of deceptive or fraudulent behavior.

--------------------------------------------------

9. RISK SCORING

Use this scale:

0-19:
Clearly normal, harmless, or routine content.

20-49:
Mostly normal content with weak, ambiguous, or insufficient
suspicious characteristics.

50-69:
Meaningful suspicious indicators exist, but there is not enough
evidence to confidently classify the message as a scam.

70-89:
Clear evidence of phishing, fraud, impersonation, credential theft,
financial deception, or malicious social engineering.

90-100:
Extremely strong evidence of an active scam or malicious lure,
especially when multiple strong indicators are present together.

IMPORTANT:
Do not inflate the score.

When evidence is weak or absent, prefer LOW RISK.

--------------------------------------------------

10. VERDICT

The verdict MUST match the score:

0-49   = LOW RISK
50-69  = SUSPICIOUS
70-89  = HIGH RISK
90-100 = VERY HIGH RISK

--------------------------------------------------

11. SCAM TYPE

Choose ONE:

"phishing"
"impersonation"
"financial fraud"
"OTP/credential theft"
"fake reward/prize"
"job scam"
"investment scam"
"loan scam"
"delivery/payment scam"
"account takeover"
"extortion/threat"
"other"
"none"

Use "none" when there is insufficient evidence of a scam.

Do not invent a scam type.

--------------------------------------------------

12. LANGUAGE

Identify the primary language of the message.

Examples:

English
Hindi
Hinglish
Spanish
French
Arabic
etc.

If multiple languages are present, identify the dominant language.

--------------------------------------------------

13. FORENSIC REASONS

Return exactly 3 or 4 short reasons.

Each reason MUST be based directly on the message.

Good reason:

"The message is an ordinary academic notice about practical exams."

Bad reason:

"This looks safe because the sender is probably a teacher."

The second reason invents information that is not present.

Do not provide generic cybersecurity advice.

Do not mention that you are an AI.

Do not mention this prompt.

--------------------------------------------------

14. CONSERVATIVE CLASSIFICATION

False positives are important.

A legitimate school, college, workplace, bank, delivery,
customer-service, or administrative message must NOT be classified
as a scam without concrete evidence.

When there is uncertainty:

LOWER THE SCORE.

Do not guess.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.

Do NOT use:
- Markdown
- code fences
- explanations
- comments
- text before JSON
- text after JSON

Return exactly:

{{
    "score": 0,
    "verdict": "LOW RISK",
    "language": "English",
    "scam_type": "none",
    "reasons": [
        "Reason based directly on the message.",
        "Another evidence-based observation.",
        "Another relevant observation."
    ]
}}

==================================================
FINAL CHECK
==================================================

Before returning the JSON:

1. Did you analyze ONLY the supplied message?
2. Did you avoid inventing context?
3. Did you avoid keyword-only scoring?
4. Did you distinguish legitimate warnings from scam threats?
5. Does the score match the verdict?
6. Are the reasons supported by the message?
7. Is scam_type justified by actual evidence?
8. Is the output valid JSON?

If there is no clear evidence of a scam, classify it LOW RISK.
"""

    # =========================================================
    # 4. CALL OPENROUTER
    # =========================================================
    try:

        data = call_openrouter(prompt)

        # =====================================================
        # 5. INVALID AI RESPONSE
        # =====================================================
        if not data or not isinstance(data, dict):
            return {
                "score": 0,
                "verdict": "UNKNOWN",
                "language": "unknown",
                "scam_type": "none",
                "reasons": [
                    "Message analysis could not be completed."
                ]
            }

        # =====================================================
        # 6. SCORE
        # =====================================================
        try:
            score = int(data.get("score", 0))
        except (ValueError, TypeError):
            score = 0

        score = max(0, min(score, 100))

        # =====================================================
        # 7. VERDICT
        # =====================================================
        if score <= 49:
            verdict = "LOW RISK"

        elif score <= 69:
            verdict = "SUSPICIOUS"

        elif score <= 89:
            verdict = "HIGH RISK"

        else:
            verdict = "VERY HIGH RISK"

        # =====================================================
        # 8. LANGUAGE
        # =====================================================
        language = data.get("language", "unknown")

        if not language:
            language = "unknown"

        language = str(language).strip()

        # =====================================================
        # 9. SCAM TYPE
        # =====================================================
        scam_type = data.get("scam_type", "none")

        if not scam_type:
            scam_type = "none"

        scam_type = str(scam_type).strip()

        allowed_scam_types = {
            "phishing",
            "impersonation",
            "financial fraud",
            "OTP/credential theft",
            "fake reward/prize",
            "job scam",
            "investment scam",
            "loan scam",
            "delivery/payment scam",
            "account takeover",
            "extortion/threat",
            "other",
            "none"
        }

        if scam_type not in allowed_scam_types:
            scam_type = "other"

        # If risk is very low, don't allow an unsupported scam type
        if score < 50:
            scam_type = "none"

        # =====================================================
        # 10. REASONS
        # =====================================================
        reasons = data.get("reasons", [])

        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        reasons = [
            str(reason).strip()
            for reason in reasons
            if str(reason).strip()
        ]

        # =====================================================
        # 11. FALLBACK REASONS
        # =====================================================
        if not reasons:

            if score < 50:
                reasons = [
                    "No strong scam indicators were identified.",
                    "The message does not provide sufficient evidence of fraud.",
                    "The content appears low risk based on the available message text."
                ]

            elif score < 70:
                reasons = [
                    "Some suspicious characteristics are present.",
                    "The available message does not provide enough evidence for a high-risk classification.",
                    "Further verification may be appropriate."
                ]

            else:
                reasons = [
                    "The message contains indicators associated with potential fraud or social engineering.",
                    "Multiple suspicious characteristics are present in the message.",
                    "The content warrants additional verification."
                ]

        # =====================================================
        # 12. FINAL RESULT
        # =====================================================
        return {
            "score": score,
            "verdict": verdict,
            "language": language,
            "scam_type": scam_type,
            "reasons": reasons[:4]
        }

    # =========================================================
    # 13. ERROR HANDLING
    # =========================================================
    except Exception as e:

        print("Message detection error:", e)

        return {
            "score": 0,
            "verdict": "UNKNOWN",
            "language": "unknown",
            "scam_type": "none",
            "reasons": [
                "Message analysis could not be completed."
            ]
        }