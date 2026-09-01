def phone_detect(supabase, phone):
    # Clean phone number (Keep digits and +)
    clean_phone = "".join(filter(lambda c: c.isdigit() or c == "+", str(phone or "")))

    if not clean_phone:
        return {
            "found": False,
            "score": None,
            "reputation": "UNKNOWN",
            "report_count": 0,
            "reasons": ["Invalid or empty phone number provided."]
        }

    try:
        # Query the 'spam_numbers' table
        result = (
            supabase
            .table("spam_numbers")
            .select("phone, report_count, reputation, score")
            .eq("phone", clean_phone)
            .execute()
        )

        rows = result.data or []

        # Agar number spam_numbers table me milta hai
        if rows and len(rows) > 0:
            number_data = rows[0]
            count = int(number_data.get("report_count") or 0)

            # =========================================================
            # REPORT COUNT RULES & DYNAMIC SCORING
            # =========================================================

            # Rule 1: 5 ya usse zyada reports (5+) -> SPAM / SCAM (Score: 90)
            if count >= 5:
                score = 90
                reputation = "SPAM / SCAM"
                reasons = [
                    f"This phone number has {count} community complaints .",
                    "Flagged as a confirmed high-risk malicious SPAM/SCAM number."
                ]

            # Rule 2: 3 se 4 reports (3-4) -> SUSPICIOUS (Score: 60)
            elif count >= 3:
                score = 60
                reputation = "SUSPICIOUS"
                reasons = [
                    f"This phone number has {count} community reports in the database.",
                    "Multiple users have flagged this number as suspicious."
                ]

            # Rule 3: 1 se 2 reports (1-2) -> SAFE / UNVERIFIED (Score: 30)
            elif count >= 1:
                score = 30
                reputation = "SAFE / UNVERIFIED"
                reasons = [
                    f"This phone number has {count} initial report(s) in the database.",
                    "Marked as unverified with low threat frequency."
                ]

            # Rule 4: 0 reports
            else:
                score = 0
                reputation = "CLEAN / NO REPORTS"
                reasons = ["No active complaints recorded for this phone number."]

            return {
                "found": True,
                "score": score,
                "reputation": reputation,
                "report_count": count,
                "reasons": reasons
            }

        # Agar number table me nahi mila (0 Reports)
        return {
            "found": False,
            "score": 0,
            "reputation": "CLEAN / NO REPORTS",
            "report_count": 0,
            "reasons": ["No scam reports found in the community database for this number."]
        }

    except Exception as e:
        print("PHONE DETECT ERROR:", repr(e))
        return {
            "found": False,
            "score": None,
            "reputation": "UNKNOWN",
            "report_count": 0,
            "reasons": [f"Phone reputation lookup error: {str(e)}"]
        }