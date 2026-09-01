def calculate_risk(
    message_score=0,
    phone_score=0,
    link_score=0,
    screenshot_score=0,
    cross_signal_boost=0,
    **kwargs
):
    if isinstance(message_score, dict):
        d = message_score
        message_score = d.get("message", 0)
        phone_score = d.get("phone", 0)
        link_score = d.get("link", 0)
        screenshot_score = d.get("screenshot", 0)

    scores = {
        "message": max(0, min(int(message_score or 0), 100)),
        "phone": max(0, min(int(phone_score or 0), 100)),
        "link": max(0, min(int(link_score or 0), 100)),
        "screenshot": max(0, min(int(screenshot_score or 0), 100))
    }

    supplied = {k: v for k, v in scores.items() if v > 0}
    if not supplied:
        return {
            "final_score": 0,
            "verdict": "LOW RISK",
            "contribution": {}
        }

    strongest_name = max(supplied, key=supplied.get)
    strongest_score = supplied[strongest_name]

    supporting_bonus = sum(
        4 if s >= 80 else 3 if s >= 60 else 2 if s >= 40 else 1
        for name, s in supplied.items() if name != strongest_name
    )

    multi_bonus = max(0, len(supplied) - 1) * 2
    final_score = min(100, max(0, strongest_score + supporting_bonus + multi_bonus + int(cross_signal_boost or 0)))

    verdict = "VERY HIGH RISK" if final_score >= 80 else "HIGH RISK" if final_score >= 60 else "SUSPICIOUS" if final_score >= 30 else "LOW RISK"

    tot = sum(supplied.values())
    contribution = {k: round((v / tot) * 100, 1) for k, v in scores.items()} if tot > 0 else {}

    return {
        "final_score": final_score,
        "verdict": verdict,
        "contribution": contribution
    }


def what_if_analysis(message_score=0, phone_score=0, link_score=0, screenshot_score=0):
    m = int(message_score or 0)
    p = int(phone_score or 0)
    l = int(link_score or 0)
    s = int(screenshot_score or 0)

    current = calculate_risk(m, p, l, s)["final_score"]
    w_link = calculate_risk(m, p, 0, s)["final_score"]
    w_phone = calculate_risk(m, 0, l, s)["final_score"]
    w_ss = calculate_risk(m, p, l, 0)["final_score"]
    w_msg = calculate_risk(0, p, l, s)["final_score"]

    return {
        "current": current,
        "without_link": w_link,
        "without_phone": w_phone,
        "without_screenshot": w_ss,
        "without_message": w_msg,
        "message_only": calculate_risk(m, 0, 0, 0)["final_score"] if m > 0 else 0,
        "phone_only": calculate_risk(0, p, 0, 0)["final_score"] if p > 0 else "UNKNOWN",
        "link_only": calculate_risk(0, 0, l, 0)["final_score"] if l > 0 else 0,
        "screenshot_only": calculate_risk(0, 0, 0, s)["final_score"] if s > 0 else 0,
        "impact": {
            "message": max(0, current - w_msg) if m > 0 else 0,
            "screenshot": max(0, current - w_ss) if s > 0 else 0,
            "link": max(0, current - w_link) if l > 0 else 0,
            "phone": max(0, current - w_phone) if p > 0 else 0
        }
    }