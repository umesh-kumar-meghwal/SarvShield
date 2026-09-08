# app.py
import os
import uuid
import re
import json
import random
import smtplib
import secrets
import traceback
from flask_cors import CORS
import requests
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# Internal Modules
from db import supabase
from message_detect import message_detect
from phone_detect import phone_detect
from link_detect import link_detect
from screenshot_detect import screenshot_detect
from risk_engine import calculate_risk, what_if_analysis
from scam_fingerprint import build_scam_fingerprint
from safe_next import generate_safe_next

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "scamcheck-prod-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB Max Upload

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

# =========================================================
# OTP / EMAIL UTILITY
# =========================================================
def send_otp_email(to_email: str, otp: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("[EMAIL WARNING] SMTP credentials missing. OTP is:", otp)
        return

    msg = EmailMessage()
    msg["Subject"] = "SarvShield Security Verification Code"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(f"Your SarvShield verification code is: {otp}\nValid for 10 minutes.")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_EMAIL.strip(), SMTP_PASSWORD.strip())
        server.send_message(msg)


# =========================================================
# AUTHENTICATION ROUTES
# =========================================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/send-otp", methods=["POST"])
def send_otp():
    try:
        email = request.form.get("email", "").strip().lower()
        if not email or "@" not in email:
            return jsonify({"success": False, "message": "A valid email address is required."}), 400

        existing = supabase.table("login").select("email").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "message": "Email is already registered."}), 409

        last_sent = session.get("otp_sent_at")
        if last_sent:
            current_time = datetime.now(timezone.utc).timestamp()
            if current_time - last_sent < 60:
                remaining = int(60 - (current_time - last_sent))
                return jsonify({"success": False, "message": f"Please wait {remaining} seconds before requesting a new OTP."}), 429

        otp = str(secrets.randbelow(900000) + 100000)
        session["otp"] = otp
        session["otp_email"] = email
        session["otp_expires"] = (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()
        session["otp_sent_at"] = datetime.now(timezone.utc).timestamp()
        session.pop("email_verified", None)

        send_otp_email(email, otp)
        return jsonify({"success": True, "message": "OTP sent successfully to your email."}), 200

    except Exception as e:
        print("SEND OTP ERROR:", e)
        return jsonify({"success": False, "message": "Unable to send OTP at this time."}), 500


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        entered_otp = request.form.get("otp", "").strip()
        saved_otp = session.get("otp")
        otp_email = session.get("otp_email")
        expires_at = session.get("otp_expires")

        if not saved_otp or not otp_email:
            return jsonify({"success": False, "message": "Please request an OTP first."}), 400

        if not entered_otp.isdigit() or len(entered_otp) != 6:
            return jsonify({"success": False, "message": "Enter a valid 6-digit OTP."}), 400

        current_time = datetime.now(timezone.utc).timestamp()
        if not expires_at or current_time > expires_at:
            session.pop("otp", None)
            return jsonify({"success": False, "message": "OTP has expired. Please request a new one."}), 400

        if entered_otp != saved_otp:
            return jsonify({"success": False, "message": "Invalid OTP entered."}), 400

        session["email_verified"] = True
        session["verified_email"] = otp_email
        session.pop("otp", None)
        session.pop("otp_expires", None)

        return jsonify({"success": True, "message": "Email verified successfully!"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "email" in session:
            return redirect("/admin-dashboard" if session.get("usertype") == "admin" else "/home")
        return render_template("login.html")

    try:
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required."}), 400

        result = supabase.table("login").select("email, password, usertype").eq("email", email).execute()
        if not result.data:
            return jsonify({"success": False, "message": "Invalid email or password."}), 401

        user = result.data[0]
        stored_password = user.get("password", "")

        is_valid = (
            check_password_hash(stored_password, password)
            if stored_password.startswith(("pbkdf2:", "scrypt:", "bcrypt:"))
            else (stored_password == password)
        )

        if not is_valid:
            return jsonify({"success": False, "message": "Invalid email or password."}), 401

        session["email"] = user["email"]
        session["usertype"] = user["usertype"]
        redirect_url = "/admin-dashboard" if user["usertype"] == "admin" else "/home"

        return jsonify({"success": True, "message": "Login successful!", "redirect": redirect_url}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/user-register", methods=["GET", "POST"])
def user_register():
    if request.method == "GET":
        if "email" in session and session.get("usertype") == "user":
            return redirect("/user-dashboard")
        return render_template("user-register.html")

    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "").strip()

        if not all([name, email, phone, address, password]):
            return jsonify({"success": False, "message": "All fields are required."}), 400

        if not session.get("email_verified") or session.get("verified_email") != email:
            return jsonify({"success": False, "message": "Please verify your email address first."}), 403

        existing = supabase.table("login").select("email").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "message": "Email already registered."}), 409

        password_hash = generate_password_hash(password)
        supabase.table("user").insert({"name": name, "email": email, "phone": phone, "address": address}).execute()
        supabase.table("login").insert({"email": email, "password": password_hash, "usertype": "user"}).execute()

        session.pop("email_verified", None)
        session.pop("verified_email", None)
        session["email"] = email
        session["usertype"] = "user"

        return jsonify({"success": True, "redirect": "/user-dashboard", "message": "Registration successful!"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500


# =========================================================
# CORE SCAMCHECK DETECTION ROUTE
# =========================================================
@app.route("/scamcheck", methods=["GET", "POST"])
def scamcheck_check():
    if request.method == "GET":
        user_email = session.get("email")
        user_data = {}
        if user_email:
            try:
                res = supabase.table("user").select("name, profile_picture").eq("email", user_email).limit(1).execute()
                if res.data:
                    user_data = res.data[0]
            except Exception:
                pass
        return render_template("user-dashboard.html", data=user_data)

    try:
        # 1. Extract inputs
        message = request.form.get("message", "").strip()
        phone = request.form.get("phone", "").strip()
        link = request.form.get("link", "").strip()
        screenshot_file = request.files.get("screenshot")

        # 2. Extract selected language dynamically (POST form or GET query param)
        selected_language = (
            request.form.get("language") or 
            request.args.get("lang") or 
            "Marathi"
        ).strip()

        has_message = bool(message)
        has_phone = bool(phone)
        has_link = bool(link)
        has_screenshot = bool(screenshot_file and screenshot_file.filename)

        if not (has_message or has_phone or has_link or has_screenshot):
            return jsonify({
                "success": False, 
                "message": "Provide at least one input (Message, Phone, Link, or Screenshot)."
            }), 400

        screenshot_bytes = None
        screenshot_db_record = None

        # 3. Process Screenshot
        if has_screenshot:
            try:
                suffix = os.path.splitext(screenshot_file.filename)[1].lower() or ".png"
                filename = f"{uuid.uuid4().hex}{suffix}"
                storage_path = f"screenshots/{filename}"
                screenshot_db_record = storage_path
                screenshot_bytes = screenshot_file.read()

                try:
                    supabase.storage.from_("scam-screenshots").upload(
                        storage_path,
                        screenshot_bytes,
                        {"content-type": screenshot_file.content_type or "image/png"}
                    )
                except Exception as st_err:
                    print("SUPABASE STORAGE NOTICE:", repr(st_err))
            except Exception as ss_err:
                print("SCREENSHOT EXTRACTION ERROR:", repr(ss_err))

        # Default results
        message_result = {"score": 0, "verdict": "UNKNOWN", "language": selected_language, "reasons": []}
        phone_result = {"found": False, "score": None, "reputation": "UNKNOWN", "report_count": 0, "reasons": []}
        link_result = {"score": 0, "domain": "", "final_domain": "", "verdict": "UNKNOWN", "reasons": []}
        screenshot_result = {"score": 0, "verdict": "UNKNOWN", "category": "Unknown", "detected_text": "", "reasons": []}

        # 4. Multi-Threaded Parallel Execution with Safe Exception Handling
        with ThreadPoolExecutor(max_workers=4) as executor:
            fut_msg = executor.submit(message_detect, message, selected_language) if has_message else None
            fut_phone = executor.submit(phone_detect, supabase, phone, selected_language) if has_phone else None
            fut_link = executor.submit(link_detect, link, selected_language) if has_link else None
            fut_ss = executor.submit(screenshot_detect, screenshot_bytes, selected_language) if (has_screenshot and screenshot_bytes) else None

            if fut_msg:
                try:
                    message_result = fut_msg.result()
                except Exception as e:
                    message_result = {"score": 0, "verdict": "UNKNOWN", "reasons": [str(e)]}

            if fut_phone:
                try:
                    phone_result = fut_phone.result()
                except Exception as e:
                    phone_result = {"found": False, "score": None, "reputation": "UNKNOWN", "report_count": 0, "reasons": [str(e)]}

            if fut_link:
                try:
                    link_result = fut_link.result()
                except Exception as e:
                    link_result = {"score": 0, "domain": "", "verdict": "UNKNOWN", "reasons": [str(e)]}

            if fut_ss:
                try:
                    screenshot_result = fut_ss.result()
                except Exception as e:
                    screenshot_result = {"score": 0, "verdict": "UNKNOWN", "category": "Unknown", "reasons": [str(e)]}

        message_score = int(message_result.get("score", 0) or 0)
        screenshot_score = int(screenshot_result.get("score", 0) or 0)
        link_score = int(link_result.get("score", 0) or 0)
        phone_score = phone_result.get("score")

        scores = {
            "message": message_score if has_message else 0,
            "phone": int(phone_score or 0) if (has_phone and phone_score is not None) else 0,
            "link": link_score if has_link else 0,
            "screenshot": screenshot_score if has_screenshot else 0
        }

        # 5. Risk Calculation Engine
        risk_res = calculate_risk(scores)
        final_score = risk_res.get("final_score", 0)
        final_verdict = risk_res.get("verdict", "UNKNOWN")
        contribution_data = risk_res.get("contribution", {})

        # 6. Attack Chain & Scam Fingerprint
        fingerprint_data = build_scam_fingerprint(
            message=message,
            phone_result=phone_result,
            link_result=link_result,
            screenshot_result=screenshot_result,
            language=selected_language
        )

        fingerprint = fingerprint_data.get("scam_fingerprint", [])
        attack_chain = fingerprint_data.get("attack_chain", [])
        why_text = fingerprint_data.get("why", "Security analysis completed based on submitted attributes.")

        evidence = list(dict.fromkeys([
            str(r) for r in (
                message_result.get("reasons", []) +
                link_result.get("reasons", []) +
                screenshot_result.get("reasons", []) +
                phone_result.get("reasons", [])
            ) if r
        ]))

        # 7. SafeNext AI Defensive Advice
        coach_advice = generate_safe_next(
            final_score=final_score,
            verdict=final_verdict,
            message=message,
            link_result=link_result,
            screenshot_result=screenshot_result,
            phone_result=phone_result,
            fingerprint=fingerprint,
            attack_chain=attack_chain,
            language=selected_language
        )

        wi = what_if_analysis(
            message_score=scores["message"],
            phone_score=scores["phone"],
            link_score=scores["link"],
            screenshot_score=scores["screenshot"]
        )

        urgency_detected = [
            w for w in ["immediately", "verify", "suspended", "urgent", "24 hours", "blocked", "warning", "kyc"] 
            if w in (message + " " + link).lower()
        ]

        # 8. Save Record to Supabase DB
        try:
            current_user = session.get("email", "anonymous_user")
            supabase.table("scam_checks").insert({
                "user_email": current_user,
                "message": message if has_message else None,
                "phone": phone if has_phone else None,
                "link": link if has_link else None,
                "screenshot": screenshot_db_record if has_screenshot else None,
                "final_score": final_score,
                "verdict": final_verdict,
                "message_score": message_score if has_message else None,
                "link_score": link_score if has_link else None,
                "screenshot_score": screenshot_score if has_screenshot else None,
                "scam_fingerprint": fingerprint,
                "attack_chain": attack_chain,
                "evidence": evidence,
                "recommended_action": coach_advice.get("recommended_action", "DO NOT INTERACT"),
                "safe_next": coach_advice.get("safe_next", []),
                "why_summary": why_text
            }).execute()
        except Exception as db_err:
            print("DB SCAM CHECK LOG NOTICE:", repr(db_err))

        # 9. Return JSON Response with Dynamic Language Output
        return jsonify({
            "success": True,
            "final_score": final_score,
            "verdict": final_verdict,
            "inputs": {
                "message": has_message,
                "phone": has_phone,
                "link": has_link,
                "screenshot": has_screenshot
            },
            "selected_language": selected_language,
            "message_score": message_score,
            "message_verdict": message_result.get("verdict", "UNKNOWN"),
            "message_language": message_result.get("language", selected_language),
            "message_reasons": [str(r) for r in message_result.get("reasons", [])],
            "phone_score": phone_score,
            "phone_reputation": phone_result.get("reputation", "UNKNOWN"),
            "phone_report_count": phone_result.get("report_count", 0),
            "phone_reasons": [str(r) for r in phone_result.get("reasons", [])],
            "phone_carrier": phone_result.get("carrier", "Unknown"),
            "phone_line_type": phone_result.get("line_type", "Unknown"),
            "phone_valid": phone_result.get("valid"),
            "phone_country": phone_result.get("country", "India"),
            "link_score": link_score,
            "link_verdict": link_result.get("verdict", "UNKNOWN"),
            "link_domain": link_result.get("domain", ""),
            "link_reasons": [str(r) for r in link_result.get("reasons", [])],
            "screenshot_score": screenshot_score,
            "screenshot_verdict": screenshot_result.get("verdict", "UNKNOWN"),
            "screenshot_category": screenshot_result.get("category", "Unknown"),
            "detected_text": screenshot_result.get("detected_text", ""),
            "screenshot_reasons": [str(r) for r in screenshot_result.get("reasons", [])],
            "scam_fingerprint": fingerprint,
            "attack_chain": attack_chain,
            "evidence": evidence,
            "why": why_text,
            "urgency_level": "HIGH" if len(urgency_detected) >= 2 else "MEDIUM" if len(urgency_detected) == 1 else "LOW",
            "urgency_detected": ", ".join(urgency_detected) if urgency_detected else "none detected",
            "signal_contribution": contribution_data,
            "signal_impact": wi.get("impact", {}),
            "recommended_action": coach_advice.get("recommended_action", "DO NOT INTERACT"),
            "why_dangerous": coach_advice.get("why_dangerous", ""),
            "immediate_steps": coach_advice.get("immediate_steps", []),
            "recovery_steps": coach_advice.get("recovery_steps", []),
            "helplines": coach_advice.get("helplines", []),
            "safe_next": coach_advice.get("safe_next", []),
            "what_if": wi
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500
    
    
    
    
@app.route('/history')
def history():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")
    user_email = session.get("email")
    response = (supabase.table("user").select("profile_picture").eq("email", user_email).single().execute())
    data = response.data
    if not data:
        return redirect("/error")
    return render_template('history.html',data=data)
    
    
@app.route("/scam-report", methods=["GET", "POST"])
def scam_report():
    # Login & User Type Check
    if "email" not in session or session.get("usertype") != "user":
        if request.method == "GET":
            return redirect("/login")
        return jsonify({"success": False, "message": "Please login as user to report a scam"}), 401

    user_email = session.get("email")

    if request.method == "GET":
        response = (supabase.table("user").select("profile_picture").eq("email", user_email).single().execute())
        data = response.data
        if not data:
            return redirect("/error")
        return render_template("report-scam.html",data=data)

    try:
        phone_number = request.form.get("phone_number", "").strip()
        link = request.form.get("link", "").strip()
        reason = request.form.get("reason", "").strip()

        # 1. Validation: Phone ya Link dono me se kam se kam ek hona chahiye
        if not phone_number and not link:
            return jsonify({
                "success": False,
                "message": "Please provide at least a Phone Number OR a Link to report."
            }), 400

        # 2. Reason required
        if not reason:
            return jsonify({
                "success": False,
                "message": "Reason is required."
            }), 400

        # =========================================================
        # 3. DUPLICATE CHECK: Kya is user ne pehle report kiya hai?
        # =========================================================
        if phone_number:
            check_phone = (
                supabase
                .table("scam_reports")
                .select("id")
                .eq("user_email", user_email)
                .eq("phone", phone_number)
                .execute()
            )
            if check_phone.data and len(check_phone.data) > 0:
                return jsonify({
                    "success": False,
                    "message": "You have already reported this phone number previously."
                }), 409

        if link:
            check_link = (
                supabase
                .table("scam_reports")
                .select("id")
                .eq("user_email", user_email)
                .eq("link", link)
                .execute()
            )
            if check_link.data and len(check_link.data) > 0:
                return jsonify({
                    "success": False,
                    "message": "You have already reported this link previously."
                }), 409

        # =========================================================
        # 4. INSERT INTO scam_reports (User Audit Log)
        # =========================================================
        supabase.table("scam_reports").insert({
            "user_email": user_email,
            "phone": phone_number if phone_number else None,
            "link": link if link else None,
            "reason": reason
        }).execute()

        # =========================================================
        # 5. SYNC WITH spam_numbers TABLE (Auto-Increment / Create)
        # =========================================================
        if phone_number:
            exist_num = (
                supabase
                .table("spam_numbers")
                .select("id, report_count")
                .eq("phone", phone_number)
                .execute()
            )
            if exist_num.data and len(exist_num.data) > 0:
                current_count = exist_num.data[0].get("report_count") or 0
                new_count = current_count + 1
                supabase.table("spam_numbers").update({
                    "report_count": new_count
                }).eq("phone", phone_number).execute()
                print(f"✓ Phone '{phone_number}' report_count updated to {new_count}")
            else:
                supabase.table("spam_numbers").insert({
                    "phone": phone_number,
                    "report_count": 1,
                    "reputation": "SPAM",
                    "score": 90
                }).execute()
                print(f"✓ New Phone '{phone_number}' added with report_count = 1")

        # =========================================================
        # 6. SYNC WITH spam_links TABLE (Auto-Increment / Create)
        # =========================================================
        if link:
            exist_lnk = (
                supabase
                .table("spam_links")
                .select("id, report_count")
                .eq("link", link)
                .execute()
            )
            if exist_lnk.data and len(exist_lnk.data) > 0:
                current_count = exist_lnk.data[0].get("report_count") or 0
                new_count = current_count + 1
                supabase.table("spam_links").update({
                    "report_count": new_count
                }).eq("link", link).execute()
                print(f"✓ Link '{link}' report_count updated to {new_count}")
            else:
                supabase.table("spam_links").insert({
                    "link": link,
                    "report_count": 1,
                    "reputation": "SPAM",
                    "score": 90
                }).execute()
                print(f"✓ New Link '{link}' added with report_count = 1")

        return jsonify({
            "success": True,
            "message": "Scam reported successfully and spam database updated!"
        }), 200

    except Exception as e:
        print("SCAM REPORT ERROR:", repr(e))
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/user-show", methods=["GET"])
def user_show():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")
    try:
        result = supabase.table("user").select("name, email, phone, address, profile_picture").execute()
        return render_template("user-show.html", users=result.data or [])
    except Exception as e:
        return f"Error: {str(e)}", 500
    
    
    
    
@app.route("/user-edit/<email>", methods=["GET", "POST"])
def user_edit(email):

    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    try:

        # =========================================
        # GET USER
        # =========================================

        if request.method == "GET":

            result = (
                supabase
                .table("user")
                .select(
                    "name, email, phone, address, profile_picture"
                )
                .eq("email", email)
                .execute()
            )

            if not result.data:
                return "User not found", 404

            return render_template(
                "user-edit.html",
                user=result.data[0]
            )


        # =========================================
        # POST / UPDATE USER
        # =========================================

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        update_data = {
            "name": name,
            "phone": phone,
            "address": address
        }


        # =========================================
        # PROFILE PICTURE
        # =========================================

        profile_picture = request.files.get("profile_picture")

        if profile_picture and profile_picture.filename:

            filename = secure_filename(profile_picture.filename)

            allowed_extensions = {
                "jpg",
                "jpeg",
                "png",
                "webp"
            }

            extension = filename.rsplit(".", 1)[-1].lower()

            if extension not in allowed_extensions:

                return jsonify({
                    "success": False,
                    "message": "Only JPG, JPEG, PNG and WEBP images are allowed."
                }), 400


            # =====================================
            # DELETE OLD PROFILE PICTURES
            # =====================================

            bucket = supabase.storage.from_("profile-pictures")

            old_files = bucket.list(email)

            print("Old files:", old_files)


            if old_files:

                old_file_paths = []

                for old_file in old_files:

                    old_file_name = old_file.get("name")

                    if old_file_name:

                        old_file_paths.append(
                            f"{email}/{old_file_name}"
                        )


                if old_file_paths:

                    print(
                        "Deleting old files:",
                        old_file_paths
                    )

                    bucket.remove(old_file_paths)


            # =====================================
            # UPLOAD NEW PROFILE PICTURE
            # =====================================

            file_path = f"{email}/profile.{extension}"

            file_bytes = profile_picture.read()


            bucket.upload(
                file_path,
                file_bytes,
                file_options={
                    "content-type": profile_picture.content_type,
                    "upsert": "true"
                }
            )


            # =====================================
            # GET PUBLIC URL
            # =====================================

            public_url = bucket.get_public_url(file_path)


            update_data["profile_picture"] = public_url


        # =========================================
        # UPDATE USER TABLE
        # =========================================

        result = (
            supabase
            .table("user")
            .update(update_data)
            .eq("email", email)
            .execute()
        )


        print("User Updated:", result)


        return jsonify({
            "success": True,
            "message": "User updated successfully!"
        }), 200


    except Exception as e:

        print("User Edit Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

from urllib.parse import unquote

@app.route("/scamcheck-userhistory/<path:email>", methods=["GET"])
def scamcheck_userhistory(email):

    if "email" not in session or session.get("usertype") != "admin":
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    try:
        # Decode email if it is URL encoded
        email = unquote(email).strip().lower()

        print("HISTORY EMAIL:", repr(email))

        result = (
            supabase
            .table("scam_checks")
            .select("*")
            .eq("user_email", email)
            .order("created_at", desc=True)
            .execute()
        )

        history = result.data or []

        print("HISTORY COUNT:", len(history))

        return render_template(
            "scamcheck-userhistory",
            history=history,
            email=email
        )

    except Exception as e:
        print("Scam Check History Error:", repr(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route("/admin-show", methods=["GET"])
def admin_show():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")
    try:
        result = supabase.table("admin").select("name, email, phone, address").execute()
        return render_template("admin-show.html", admins=result.data or [])
    except Exception as e:
        return f"Error: {str(e)}", 500
    
@app.route("/admin-register", methods=["GET", "POST"])
def admin_register():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    if request.method == "GET":

        return render_template("admin-register.html")

    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not email or not password or not address:
            return jsonify({"success": False, "message": "All fields are required"}), 400

        existing = supabase.table("login").select("email").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "message": "Admin email already registered"}), 409

        supabase.table("admin").insert({"name": name, "email": email, "phone": phone, "address": address}).execute()
        supabase.table("login").insert({"email": email, "password": generate_password_hash(password), "usertype": "admin"}).execute()

        return jsonify({"success": True, "message": "Admin registered successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/feedbacks")
def feedbacks():
    try:
        response = supabase.table("feedback").select("email, message, rating, created_at").order("created_at", desc=True).execute()

        feedback_data = response.data or []

        return render_template(
            "feedbacks.html",
            feedbacks=feedback_data
        )

    except Exception as e:
        print("Feedback Error:", e)
        return "Unable to fetch feedbacks", 500    

@app.route("/my-profile", methods=["GET", "POST"])
def my_profile():

    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    user_email = session.get("email")

    try:

        # =========================
        # SAVE PROFILE
        # =========================
        if request.method == "POST":

            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()

            profile_picture = request.files.get("profile_picture")

            update_data = {
                "name": name,
                "phone": phone,
                "address": address
            }

            # =========================
            # PROFILE PICTURE
            # =========================
            if profile_picture and profile_picture.filename:

                filename = secure_filename(profile_picture.filename)

                allowed_extensions = {
                    "jpg",
                    "jpeg",
                    "png",
                    "webp"
                }

                extension = filename.rsplit(".", 1)[-1].lower()

                if extension not in allowed_extensions:
                    return redirect("/my-profile")

                file_path = f"{user_email}/profile.{extension}"

                file_bytes = profile_picture.read()

                # Supabase Storage upload
                supabase.storage \
                    .from_("profile-pictures") \
                    .upload(
                        file_path,
                        file_bytes,
                        {
                            "content-type": profile_picture.content_type,
                            "upsert": "true"
                        }
                    )

                # Public URL
                public_url = (
                    supabase.storage
                    .from_("profile-pictures")
                    .get_public_url(file_path)
                )

                update_data["profile_picture"] = public_url

            # =========================
            # UPDATE USER
            # =========================
            supabase \
                .table("user") \
                .update(update_data) \
                .eq("email", user_email) \
                .execute()

            return redirect("/my-profile")


        # =========================
        # GET PROFILE
        # =========================

        response = (
            supabase
            .table("user")
            .select(
                "email, name, phone, address, profile_picture"
            )
            .eq("email", user_email)
            .single()
            .execute()
        )

        data = response.data

        if not data:
            return redirect("/error")

        return render_template(
            "my-profile.html",
            data=data
        )

    except Exception as e:

        print("My Profile Error:", e)

        return redirect("/error")





@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    user_email = session.get("email")

    try:
        # User profile picture aur name fetch karein (table: 'user')
        user_data = {}
        try:
            user_profile = (
                supabase.table("user")  # <-- Yahan 'user' table aayega
                .select("name, profile_picture")
                .eq("email", user_email)
                .limit(1)
                .execute()
            )
            if user_profile.data:
                user_data = user_profile.data[0]
        except Exception:
            user_data = {}

        # 1. Check if user has used ScamCheck at least once
        scam_result = (
            supabase.table("scam_checks")
            .select("id")
            .eq("user_email", user_email)
            .limit(1)
            .execute()
        )

        if not scam_result.data:
            return render_template(
                "feedback.html",
                can_feedback=False,
                already_submitted=False,
                data=user_data
            )

        # 2. Check if user has ALREADY submitted feedback
        existing_feedback = (
            supabase.table("feedback")
            .select("*")
            .eq("email", user_email)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )

        user_feedback = existing_feedback.data[0] if existing_feedback.data else None

        # =========================================
        # GET REQUEST
        # =========================================
        if request.method == "GET":
            return render_template(
                "feedback.html",
                can_feedback=True,
                already_submitted=(user_feedback is not None),
                user_feedback=user_feedback,
                data=user_data
            )

        # =========================================
        # POST REQUEST (SUBMISSION)
        # =========================================
        if user_feedback:
            return jsonify({
                "success": False,
                "message": "You have already submitted your feedback."
            }), 400

        rating = request.form.get("rating", "").strip()
        message = request.form.get("message", "").strip()

        if not rating:
            return jsonify({
                "success": False,
                "message": "Please select a rating."
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "message": "Please enter your feedback message."
            }), 400

        # Save Feedback in Supabase
        supabase.table("feedback").insert({
            "email": user_email,
            "rating": int(rating),
            "message": message
        }).execute()

        return jsonify({
            "success": True,
            "message": "Thank you! Your feedback has been submitted successfully."
        }), 200

    except Exception as e:
        print("Feedback Error:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500




@app.route('/alerts')
def alerts():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")
    user_email = session.get("email")
    response = (supabase.table("user").select("profile_picture").eq("email", user_email).single().execute())
    data = response.data
    if not data:
        return redirect("/error")
    return render_template('alerts.html',data=data)

@app.route('/learn-more')
def learn_more():
    if "email" not in session or session.get("usertype") != "user":
            return redirect("/error")
    user_email = session.get("email")
    response = (supabase.table("user").select("profile_picture").eq("email", user_email).single().execute())
    data = response.data
    if not data:
        return redirect("/error")
    return render_template('learn-more.html',data=data)





@app.route("/checkscam-history")
def checkscam_history():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")
    try:
        user_email = session.get("email")
        print(user_email)

        # Fetch scan records for this logged-in user
        result = (
            supabase
            .table("scam_checks")
            .select("*")
            .eq("user_email", user_email)
            .execute()
        )

        scans = result.data or []

        # Generate Public Image URL from 'scam-screenshots' bucket
        for scan in scans:
            if scan.get("screenshot"):
                scan["screenshot_url"] = supabase.storage \
                    .from_("scam-screenshots") \
                    .get_public_url(scan["screenshot"])
            else:
                scan["screenshot_url"] = None
        response = (supabase.table("user").select("profile_picture").eq("email", user_email).single().execute())
        data = response.data
        if not data:
            return redirect("/error")

        return render_template("checkscam-history.html", scans=scans,data=data)

    except Exception as e:
        print("HISTORY FETCH ERROR:", repr(e))
        return f"Error loading scan history: {str(e)}", 500
    
    
@app.route("/report-history")
def report_history():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")
    try:
        # Fetch all reported scams (Phone/Link) from Supabase
        user_email = session.get("email")

        result = (
            supabase
            .table("scam_reports")
            .select("*")
            .eq("user_email", user_email)
            .execute()
        )
        reports = result.data or []
        response = (supabase.table("user").select("profile_picture").eq("email", user_email).single().execute())
        data = response.data
        if not data:
            return redirect("/error")
        return render_template("report-history.html", reports=reports,data=data)
    except Exception as e:
        print("REPORT HISTORY ERROR:", repr(e))
        return f"Error loading report history: {str(e)}", 500
       

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    # User login check
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    user_email = session.get("email")

    if request.method == "POST":

        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Check empty fields
        if not current_password or not new_password or not confirm_password:
            return render_template(
                "change-password.html",
                error="All fields are required."
            )

        # Check new password confirmation
        if new_password != confirm_password:
            return render_template(
                "change-password.html",
                error="New password and confirm password do not match."
            )

        try:

            # Get current user password
            response = (
                supabase
                .table("login")
                .select("password")
                .eq("email", user_email)
                .single()
                .execute()
            )

            user_data = response.data

            if not user_data:
                return render_template(
                    "change-password.html",
                    error="User not found."
                )

            # Check old password
            if current_password != user_data["password"]:
                return render_template(
                    "change-password.html",
                    error="Current password is incorrect."
                )

            # Update password
            supabase.table("login").update({
                "password": new_password
            }).eq("email", user_email).execute()

            return render_template(
                "change-password.html",
                success="Password changed successfully."
            )

        except Exception as e:

            print("Change Password Error:", e)

            return render_template(
                "change-password.html",
                error="Something went wrong."
            )

    return render_template("change-password.html")





@app.route("/user-view/<email>")
def user_view(email):

    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    try:

        result = (
            supabase
            .table("user")
            .select(
                "name, email, phone, address, profile_picture"
            )
            .eq("email", email)
            .execute()
        )

        if not result.data:
            return "User not found", 404

        return render_template(
            "user-view.html",
            user=result.data[0]
        )

    except Exception as e:

        print("User View Error:", e)

        return "Something went wrong", 500

@app.route("/report-userhistory-delete/<id>", methods=["POST"])
def report_userhistory_delete(id):

    if "email" not in session or session.get("usertype") != "admin":
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    try:

        result = (
            supabase
            .table("scam_reports")
            .delete()
            .eq("id", id)
            .execute()
        )

        return jsonify({
            "success": True,
            "message": "Report deleted successfully!"
        }), 200

    except Exception as e:

        print("Delete Report Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
@app.route("/scamcheck-userhistory-view/<id>", methods=["GET"])
def scamcheck_userhistory_view(id):

    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    try:

        result = (
            supabase
            .table("scam_checks")
            .select("*")
            .eq("id", id)
            .single()
            .execute()
        )

        if not result.data:
            return "Scam check history not found", 404

        scan = result.data

        return render_template(
            "scamcheck-userhistory-view.html",
            scan=scan
        )

    except Exception as e:

        print("Scam Check User History View Error:", e)

        return "Something went wrong", 500
@app.route("/report-userhistory-edit/<id>", methods=["GET", "POST"])
def report_userhistory_edit(id):

    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    try:

        # ==============================
        # GET
        # ==============================

        if request.method == "GET":

            result = (
                supabase
                .table("scam_reports")
                .select("*")
                .eq("id", id)
                .single()
                .execute()
            )

            if not result.data:
                return "Report not found", 404

            return render_template(
                "report-userhistory-edit.html",
                report=result.data
            )


        # ==============================
        # POST
        # ==============================

        phone = request.form.get("phone", "").strip()
        link = request.form.get("link", "").strip()
        reason = request.form.get("reason", "").strip()


        supabase \
            .table("scam_reports") \
            .update({
                "phone": phone,
                "link": link,
                "reason": reason
            }) \
            .eq("id", id) \
            .execute()


        return jsonify({
            "success": True,
            "message": "Report updated successfully!"
        }), 200


    except Exception as e:

        print("Edit Report Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/report-userhistory/<path:email>", methods=["GET"])
def report_userhistory(email):

    if "email" not in session or session.get("usertype") != "admin":
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    try:
        # Decode URL-encoded email
        email = unquote(email).strip().lower()

        print("REPORT HISTORY EMAIL:", repr(email))

        result = (
            supabase
            .table("scam_reports")
            .select("*")
            .eq("user_email", email)
            .order("created_at", desc=True)
            .execute()
        )

        reports = result.data or []

        print("REPORT HISTORY COUNT:", len(reports))

        return render_template(
            "report-userhistory",
            reports=reports,
            email=email
        )

    except Exception as e:
        print("Report History Error:", repr(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/scam-result/<int:scan_id>")
def scam_result_detail(scan_id):
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    try:
        user_email = session.get("email")

        # Fetch single scan by ID and logged-in user email
        result = (
            supabase
            .table("scam_checks")
            .select("*")
            .eq("id", scan_id)
            .eq("user_email", user_email)
            .execute()
        )

        if not result.data or len(result.data) == 0:
            return redirect("/error")

        scan = result.data[0]

        # Generate Public Image URL for this single scan (No loop needed)
        if scan.get("screenshot"):
            scan["screenshot_url"] = supabase.storage \
                .from_("scam-screenshots") \
                .get_public_url(scan["screenshot"])
        else:
            scan["screenshot_url"] = None
        response = (supabase.table("user").select("profile_picture").eq("email", user_email).single().execute())
        data = response.data
        if not data:
            return redirect("/error")

        return render_template("scam-result.html", scan=scan,data=data)

    except Exception as e:
        print("FETCH SCAM RESULT ERROR:", repr(e))
        return f"Error loading scan result: {str(e)}", 500    
    
    
# =========================================================
# USER TRUST & STATS API
# =========================================================
@app.route("/api/user-trust", methods=["GET"])
def user_trust():
    try:
        if "email" not in session:
            return jsonify({"success": False, "message": "Please login again."}), 401

        user_email = str(session.get("email", "")).strip().lower()
        scam_result = supabase.table("scam_checks").select("id, final_score, verdict, created_at").eq("user_email", user_email).order("created_at", desc=False).execute()
        scam_checks = scam_result.data or []

        report_result = supabase.table("scam_reports").select("id, phone, link, reason, created_at").eq("user_email", user_email).order("created_at", desc=False).execute()
        reports = report_result.data or []

        if scam_checks:
            trust_values = [100 - max(0, min(100, float(row.get("final_score") or 0))) for row in scam_checks]
            trust_score = round(sum(trust_values) / len(trust_values))
        else:
            trust_score = 100

        label = "TRUSTED" if trust_score >= 80 else "CAUTION" if trust_score >= 50 else "HIGH RISK"

        activities = []
        for row in scam_checks:
            risk = float(row.get("final_score") or 0)
            activities.append({
                "date": row.get("created_at"),
                "type": "Scam Check",
                "verdict": str(row.get("verdict") or "UNKNOWN").upper(),
                "risk_score": round(risk),
                "trust_score": round(100 - risk)
            })

        for row in reports:
            activities.append({
                "date": row.get("created_at"),
                "type": "Spam Report",
                "verdict": "REPORTED",
                "risk_score": None,
                "trust_score": None
            })

        activities.sort(key=lambda x: x.get("date") or "")
        trend = [{"date": a["date"], "score": a["trust_score"]} for a in activities if a["type"] == "Scam Check"]

        return jsonify({
            "success": True,
            "trust_score": trust_score,
            "trust_label": label,
            "scam_checks_count": len(scam_checks),
            "reports_count": len(reports),
            "activities": activities,
            "trend": trend
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500











# =========================================================
# OTHER DASHBOARD & PROFILE ROUTES
# =========================================================
@app.route('/home')
def home_page():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")
    user_email = session.get("email")
    response = supabase.table("user").select("profile_picture").eq("email", user_email).single().execute()
    return render_template('home.html', data=response.data or {})


@app.route("/admin-dashboard")
def admin_dashboard():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")
    try:
        user_email = session.get("email")
        admin_res = supabase.table("admin").select("*").eq("email", user_email).limit(1).execute()
        data = admin_res.data[0] if admin_res.data else None
        stats = {
            "users": supabase.table("user").select("*", count="exact").execute().count or 0,
            "admins": supabase.table("admin").select("*", count="exact").execute().count or 0,
            "scam_checks": supabase.table("scam_checks").select("*", count="exact").execute().count or 0,
            "scam_reports": supabase.table("scam_reports").select("*", count="exact").execute().count or 0,
            "spam_numbers": supabase.table("spam_numbers").select("*", count="exact").execute().count or 0,
            "spam_links": supabase.table("spam_links").select("*", count="exact").execute().count or 0,
            "feedback": supabase.table("feedback").select("*", count="exact").execute().count or 0
        }
        recent_checks = supabase.table("scam_checks").select("*").order("created_at", desc=True).limit(10).execute().data or []
        recent_reports = supabase.table("scam_reports").select("*").order("created_at", desc=True).limit(10).execute().data or []
        recent_feedback = supabase.table("feedback").select("*").order("created_at", desc=True).limit(10).execute().data or []

        return render_template("admin-dashboard.html", data=data, stats=stats, recent_checks=recent_checks, recent_reports=recent_reports, recent_feedback=recent_feedback)
    except Exception as e:
        return redirect("/error")


@app.route("/error")
def error():
    return render_template("error.html")


if __name__ == '__main__':
    app.run(debug=True)