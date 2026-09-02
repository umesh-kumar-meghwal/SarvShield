import os
import traceback
import uuid
import tempfile
import re
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect
)

load_dotenv()

# Internal Detection & AI Modules
from db import supabase
from message_detect import message_detect
from phone_detect import phone_detect
from link_detect import link_detect
from screenshot_detect import screenshot_detect
from risk_engine import calculate_risk, what_if_analysis
from scam_fingerprint import build_scam_fingerprint
from safe_next import generate_safe_next
import secrets
import smtplib

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "scamcheck-prod-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB Max Upload
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

# =========================================================
# AUTHENTICATION & USER MANAGEMENT
# =========================================================

def send_otp_email(to_email, otp):

    print("SMTP EMAIL:", SMTP_EMAIL)
    print("PASSWORD EXISTS:", bool(SMTP_PASSWORD))
    print("PASSWORD LENGTH:", len(SMTP_PASSWORD or ""))

    msg = EmailMessage()
    msg["Subject"] = "ScamShield OTP"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    msg.set_content(
        f"Your ScamShield OTP is: {otp}"
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            SMTP_EMAIL.strip(),
            SMTP_PASSWORD.strip()
        )

        server.send_message(msg)

@app.route("/send-otp", methods=["POST"])
def send_otp():

    try:

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        if not email:

            return jsonify({
                "success": False,
                "message": "Email is required"
            }), 400


        # -------------------------
        # CHECK EMAIL FORMAT
        # -------------------------

        if "@" not in email:

            return jsonify({
                "success": False,
                "message": "Enter a valid email"
            }), 400


        # -------------------------
        # CHECK EXISTING USER
        # -------------------------

        existing = (
            supabase
            .table("login")
            .select("email")
            .eq("email", email)
            .execute()
        )


        if existing.data:

            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409


        # -------------------------
        # SERVER SIDE 60 SEC CHECK
        # -------------------------

        last_sent = session.get(
            "otp_sent_at"
        )

        if last_sent:

            current_time = (
                datetime.now(timezone.utc)
                .timestamp()
            )

            if current_time - last_sent < 60:

                remaining = int(
                    60 -
                    (current_time - last_sent)
                )

                return jsonify({
                    "success": False,
                    "message":
                        f"Please wait {remaining} seconds before requesting another OTP."
                }), 429


        # -------------------------
        # GENERATE OTP
        # -------------------------

        otp = str(
            secrets.randbelow(900000) + 100000
        )


        # -------------------------
        # SAVE OTP IN SESSION
        # -------------------------

        session["otp"] = otp

        session["otp_email"] = email

        session["otp_expires"] = (
            datetime.now(timezone.utc)
            + timedelta(minutes=10)
        ).timestamp()

        session["otp_sent_at"] = (
            datetime.now(timezone.utc)
            .timestamp()
        )


        # Email is not verified yet

        session.pop(
            "email_verified",
            None
        )


        # -------------------------
        # SEND EMAIL
        # -------------------------

        send_otp_email(
            email,
            otp
        )


        return jsonify({

            "success": True,

            "message":
                "OTP sent successfully to your email."

        }), 200


    except Exception as e:

        print(
            "SEND OTP ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to send OTP."

        }), 500




@app.route("/verify-otp", methods=["POST"])
def verify_otp():

    try:

        entered_otp = request.form.get(
            "otp",
            ""
        ).strip()


        saved_otp = session.get(
            "otp"
        )

        otp_email = session.get(
            "otp_email"
        )

        expires_at = session.get(
            "otp_expires"
        )


        # -------------------------
        # OTP EXISTS?
        # -------------------------

        if not saved_otp or not otp_email:

            return jsonify({

                "success": False,

                "message":
                    "Please request an OTP first."

            }), 400


        # -------------------------
        # VALIDATE OTP FORMAT
        # -------------------------

        if not entered_otp.isdigit() or len(entered_otp) != 6:

            return jsonify({

                "success": False,

                "message":
                    "Enter a valid 6-digit OTP."

            }), 400


        # -------------------------
        # CHECK EXPIRY
        # -------------------------

        current_time = (
            datetime.now(timezone.utc)
            .timestamp()
        )


        if not expires_at or current_time > expires_at:

            session.pop("otp", None)
            session.pop("otp_email", None)
            session.pop("otp_expires", None)
            session.pop("otp_sent_at", None)


            return jsonify({

                "success": False,

                "message":
                    "OTP expired. Please request a new OTP."

            }), 400


        # -------------------------
        # CHECK OTP
        # -------------------------

        if entered_otp != saved_otp:

            return jsonify({

                "success": False,

                "message":
                    "Invalid OTP."

            }), 400


        # -------------------------
        # EMAIL VERIFIED
        # -------------------------

        session["email_verified"] = True

        session["verified_email"] = otp_email


        # OTP no longer needed

        session.pop("otp", None)
        session.pop("otp_expires", None)
        session.pop("otp_sent_at", None)


        return jsonify({

            "success": True,

            "message":
                "Email verified successfully!"

        }), 200


    except Exception as e:

        print(
            "VERIFY OTP ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Something went wrong."

        }), 500






@app.route("/")
def index():
    return render_template("index.html")




@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/error")
def error():
    return render_template("error.html")

import os
from werkzeug.utils import secure_filename


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













@app.route("/login", methods=["GET", "POST"])
def login():

    # =========================================
    # GET
    # =========================================

    if request.method == "GET":

        if (
            "email" in session
            and session.get("usertype") == "user"
        ):
            return redirect("/user-dashboard")

        elif (
            "email" in session
            and session.get("usertype") == "admin"
        ):
            return redirect("/admin-dashboard")

        else:
            return render_template("login.html")


    # =========================================
    # POST
    # =========================================

    try:

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()


        # =========================================
        # VALIDATION
        # =========================================

        if not email or not password:

            return jsonify({
                "success": False,
                "message": "Email and password are required"
            }), 400


        # =========================================
        # GET LOGIN DATA
        # =========================================

        result = (
            supabase
            .table("login")
            .select("email, password, usertype")
            .eq("email", email)
            .execute()
        )


        if not result.data:

            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401


        user = result.data[0]

        stored_password = user.get("password", "")


        # =========================================
        # PASSWORD CHECK
        # =========================================

        if stored_password.startswith(
            ("pbkdf2:", "scrypt:", "bcrypt:")
        ):

            is_valid = check_password_hash(
                stored_password,
                password
            )

        else:

            is_valid = (
                stored_password == password
            )


        if not is_valid:

            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401


        # =========================================
        # CREATE SESSION
        # =========================================

        session["email"] = user["email"]
        session["usertype"] = user["usertype"]


        # =========================================
        # REDIRECT
        # =========================================

        if user["usertype"] == "admin":

            redirect_url = "/admin-dashboard"

        else:

            redirect_url = "/user-dashboard"


        return jsonify({
            "success": True,
            "message": "Login successful!",
            "redirect": redirect_url
        }), 200


    except Exception as e:

        print("LOGIN ERROR:", repr(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
@app.route("/admin-dashboard")
def admin_dashboard():

    # =========================
    # ADMIN LOGIN CHECK
    # =========================
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    user_email = session.get("email")

    try:
        # =========================
        # ADMIN PROFILE
        # =========================
        admin_response = (
            supabase
            .table("admin")
            .select("*")
            .eq("email", user_email)
            .limit(1)
            .execute()
        )

        data = admin_response.data[0] if admin_response.data else None

        if not data:
            return redirect("/error")


        # =========================
        # TOTAL USERS
        # =========================
        users_response = (
            supabase
            .table("user")
            .select("*", count="exact")
            .execute()
        )

        total_users = users_response.count or 0


        # =========================
        # TOTAL ADMINS
        # =========================
        admins_response = (
            supabase
            .table("admin")
            .select("*", count="exact")
            .execute()
        )

        total_admins = admins_response.count or 0


        # =========================
        # TOTAL SCAM CHECKS
        # =========================
        scam_checks_response = (
            supabase
            .table("scam_checks")
            .select("*", count="exact")
            .execute()
        )

        total_scam_checks = scam_checks_response.count or 0


        # =========================
        # TOTAL SCAM REPORTS
        # =========================
        scam_reports_response = (
            supabase
            .table("scam_reports")
            .select("*", count="exact")
            .execute()
        )

        total_scam_reports = scam_reports_response.count or 0


        # =========================
        # TOTAL SPAM NUMBERS
        # =========================
        spam_numbers_response = (
            supabase
            .table("spam_numbers")
            .select("*", count="exact")
            .execute()
        )

        total_spam_numbers = spam_numbers_response.count or 0


        # =========================
        # TOTAL SPAM LINKS
        # =========================
        spam_links_response = (
            supabase
            .table("spam_links")
            .select("*", count="exact")
            .execute()
        )

        total_spam_links = spam_links_response.count or 0


        # =========================
        # TOTAL FEEDBACK
        # =========================
        feedback_response = (
            supabase
            .table("feedback")
            .select("*", count="exact")
            .execute()
        )

        total_feedback = feedback_response.count or 0


        # =========================
        # STATS OBJECT
        # =========================
        stats = {
            "users": total_users,
            "admins": total_admins,
            "scam_checks": total_scam_checks,
            "scam_reports": total_scam_reports,
            "spam_numbers": total_spam_numbers,
            "spam_links": total_spam_links,
            "feedback": total_feedback
        }


        # =========================
        # RECENT SCAM CHECKS
        # =========================
        recent_checks_response = (
            supabase
            .table("scam_checks")
            .select("*")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        recent_checks = recent_checks_response.data or []


        # =========================
        # RECENT SCAM REPORTS
        # =========================
        recent_reports_response = (
            supabase
            .table("scam_reports")
            .select("*")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        recent_reports = recent_reports_response.data or []


        # =========================
        # RECENT FEEDBACK
        # =========================
        recent_feedback_response = (
            supabase
            .table("feedback")
            .select("*")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        recent_feedback = recent_feedback_response.data or []


        # =========================
        # SEND EVERYTHING TO HTML
        # =========================
        return render_template(
            "admin-dashboard.html",
            data=data,
            stats=stats,
            recent_checks=recent_checks,
            recent_reports=recent_reports,
            recent_feedback=recent_feedback
        )


    except Exception as e:

        print("ADMIN DASHBOARD ERROR:", e)

        return redirect("/error")
@app.route("/user-dashboard")
def user_dashboard():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")
    user_email = session.get("email")
    response = (
        supabase
        .table("user")
        .select(
            "profile_picture"
        )
        .eq("email", user_email)
        .single()
        .execute()
    )
    data = response.data

    if not data:
        return redirect("/error")


    return render_template("user-dashboard.html",data=data)


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


@app.route("/user-register", methods=["GET", "POST"])
def user_register():

    if request.method == "GET":

        if (
            "email" in session
            and session.get("usertype") == "user"
        ):
            return redirect("/user-dashboard")

        return render_template(
            "user-register.html"
        )


    try:

        # -------------------------
        # GET FORM DATA
        # -------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        # -------------------------
        # VALIDATION
        # -------------------------

        if (
            not name
            or not email
            or not phone
            or not address
            or not password
        ):

            return jsonify({

                "success": False,

                "message":
                    "All fields are required."

            }), 400


        # -------------------------
        # CHECK EMAIL VERIFIED
        # -------------------------

        if not session.get(
            "email_verified"
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please verify your email first."

            }), 403


        # -------------------------
        # CHECK SAME EMAIL
        # -------------------------

        verified_email = session.get(
            "verified_email"
        )


        if verified_email != email:

            return jsonify({

                "success": False,

                "message":
                    "Please use the verified email."

            }), 400


        # -------------------------
        # CHECK EXISTING EMAIL
        # -------------------------

        existing = (
            supabase
            .table("login")
            .select("email")
            .eq("email", email)
            .execute()
        )


        if existing.data:

            return jsonify({

                "success": False,

                "message":
                    "Email already registered."

            }), 409


        # -------------------------
        # PASSWORD HASH
        # -------------------------

        password_hash = (
            generate_password_hash(
                password
            )
        )


        # -------------------------
        # CREATE USER
        # -------------------------

        user_response = (
            supabase
            .table("user")
            .insert({

                "name": name,
                "email": email,
                "phone": phone,
                "address": address

            })
            .execute()
        )


        # -------------------------
        # CREATE LOGIN
        # -------------------------

        login_response = (
            supabase
            .table("login")
            .insert({

                "email": email,

                "password":
                    password_hash,

                "usertype":
                    "user"

            })
            .execute()
        )


        # -------------------------
        # LOGIN SESSION
        # -------------------------

        session.pop(
            "email_verified",
            None
        )

        session.pop(
            "verified_email",
            None
        )

        session["email"] = email

        session["usertype"] = "user"


        return jsonify({

            "success": True,

            "redirect":
                "/user-dashboard",

            "message":
                "User registered successfully!"

        }), 201


    except Exception as e:

        print(
            "USER REGISTER ERROR:",
            e
        )


        return jsonify({

            "success": False,

            "message":
                "Registration failed. Please try again."

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

@app.route("/my-feedback", methods=["GET", "POST"])
def my_feedback():

    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    user_email = session.get("email")

    try:

        # =========================================
        # POST - ADD FEEDBACK
        # =========================================

        if request.method == "POST":

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
                    "message": "Please enter your feedback."
                }), 400

            try:
                rating = int(rating)
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Invalid rating."
                }), 400

            if rating < 1 or rating > 5:
                return jsonify({
                    "success": False,
                    "message": "Rating must be between 1 and 5."
                }), 400

            supabase.table("feedback").insert({
                "email": user_email,
                "rating": rating,
                "message": message
            }).execute()

            return jsonify({
                "success": True,
                "message": "Feedback submitted successfully!"
            }), 200


        # =========================================
        # GET - FEEDBACK LIST
        # =========================================

        result = (
            supabase
            .table("feedback")
            .select("*")
            .eq("email", user_email)
            .order("created_at", desc=True)
            .execute()
        )

        return render_template(
            "my-feedback.html",
            feedbacks=result.data
        )


    except Exception as e:

        print("My Feedback Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500



@app.route("/feedback", methods=["GET", "POST"])
def feedback():

    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    user_email = session.get("email")

    try:

        # =========================================
        # CHECK SCAMCHECK USED OR NOT
        # =========================================

        scam_result = (
            supabase
            .table("scam_checks")
            .select("id")
            .eq("user_email", user_email)
            .limit(1)
            .execute()
        )

        # ScamCheck use nahi kiya
        if not scam_result.data:

            return render_template(
                "feedback.html",
                can_feedback=False
            )


        # =========================================
        # GET
        # =========================================

        if request.method == "GET":

            return render_template(
                "feedback.html",
                can_feedback=True
            )


        # =========================================
        # POST
        # =========================================

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
                "message": "Please enter your feedback."
            }), 400


        # =========================================
        # DOUBLE SECURITY CHECK
        # =========================================

        scam_check = (
            supabase
            .table("scam_checks")
            .select("id")
            .eq("user_email", user_email)
            .limit(1)
            .execute()
        )

        if not scam_check.data:

            return jsonify({
                "success": False,
                "message": "You must use ScamCheck before submitting feedback."
            }), 403


        # =========================================
        # SAVE FEEDBACK
        # =========================================

        supabase \
            .table("feedback") \
            .insert({
                "email": user_email,
                "rating": int(rating),
                "message": message
            }) \
            .execute()


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

@app.route("/api/user-trust", methods=["GET"])
def user_trust():

    try:

        if "email" not in session:
            return jsonify({
                "success": False,
                "message": "Please login again."
            }), 401

        user_email = str(
            session.get("email", "")
        ).strip().lower()

        print("TRUST USER EMAIL:", repr(user_email))
        print("TRUST USER TYPE:", repr(session.get("usertype")))

        # IMPORTANT:
        # Don't reject here based on exact "user" string
        # until we confirm your actual session value.

        # Scam checks
        scam_result = (
            supabase
            .table("scam_checks")
            .select(
                "id,user_email,final_score,verdict,created_at"
            )
            .eq("user_email", user_email)
            .order("created_at", desc=False)
            .execute()
        )

        scam_checks = scam_result.data or []

        # Reports
        report_result = (
            supabase
            .table("scam_reports")
            .select(
                "id,user_email,phone,link,reason,created_at"
            )
            .eq("user_email", user_email)
            .order("created_at", desc=False)
            .execute()
        )

        reports = report_result.data or []

        print("SCAM CHECKS:", len(scam_checks))
        print("REPORTS:", len(reports))

        # -----------------------------
        # TRUST SCORE
        # -----------------------------

        if scam_checks:

            trust_values = []

            for row in scam_checks:

                try:
                    risk = float(
                        row.get("final_score") or 0
                    )
                except:
                    risk = 0

                risk = max(0, min(100, risk))

                trust_values.append(
                    100 - risk
                )

            trust_score = round(
                sum(trust_values) /
                len(trust_values)
            )

        else:
            trust_score = 100

        # -----------------------------
        # LABEL
        # -----------------------------

        if trust_score >= 80:
            label = "TRUSTED"
        elif trust_score >= 50:
            label = "CAUTION"
        else:
            label = "HIGH RISK"

        # -----------------------------
        # ACTIVITIES
        # -----------------------------

        activities = []

        for row in scam_checks:

            try:
                risk = float(
                    row.get("final_score") or 0
                )
            except:
                risk = 0

            activities.append({
                "date": row.get("created_at"),
                "type": "Scam Check",
                "verdict": str(
                    row.get("verdict") or "UNKNOWN"
                ).upper(),
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

        activities.sort(
            key=lambda x: x.get("date") or ""
        )

        # -----------------------------
        # TREND
        # -----------------------------

        trend = []

        for activity in activities:

            if activity["type"] == "Scam Check":

                trend.append({
                    "date": activity["date"],
                    "score": activity["trust_score"]
                })

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

        print("TRUST API ERROR:", repr(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500   
    
    
    

    try:

        if "email" not in session:
            return jsonify({
                "success": False,
                "message": "Please login again."
            }), 401

        user_email = str(
            session.get("email", "")
        ).strip().lower()

        print("TRUST USER EMAIL:", repr(user_email))
        print("TRUST USER TYPE:", repr(session.get("usertype")))

        # IMPORTANT:
        # Don't reject here based on exact "user" string
        # until we confirm your actual session value.

        # Scam checks
        scam_result = (
            supabase
            .table("scam_checks")
            .select(
                "id,user_email,final_score,verdict,created_at"
            )
            .eq("user_email", user_email)
            .order("created_at", desc=False)
            .execute()
        )

        scam_checks = scam_result.data or []

        # Reports
        report_result = (
            supabase
            .table("scam_reports")
            .select(
                "id,user_email,phone,link,reason,created_at"
            )
            .eq("user_email", user_email)
            .order("created_at", desc=False)
            .execute()
        )

        reports = report_result.data or []

        print("SCAM CHECKS:", len(scam_checks))
        print("REPORTS:", len(reports))

        # -----------------------------
        # TRUST SCORE
        # -----------------------------

        if scam_checks:

            trust_values = []

            for row in scam_checks:

                try:
                    risk = float(
                        row.get("final_score") or 0
                    )
                except:
                    risk = 0

                risk = max(0, min(100, risk))

                trust_values.append(
                    100 - risk
                )

            trust_score = round(
                sum(trust_values) /
                len(trust_values)
            )

        else:
            trust_score = 100

        # -----------------------------
        # LABEL
        # -----------------------------

        if trust_score >= 80:
            label = "TRUSTED"
        elif trust_score >= 50:
            label = "CAUTION"
        else:
            label = "HIGH RISK"

        # -----------------------------
        # ACTIVITIES
        # -----------------------------

        activities = []

        for row in scam_checks:

            try:
                risk = float(
                    row.get("final_score") or 0
                )
            except:
                risk = 0

            activities.append({
                "date": row.get("created_at"),
                "type": "Scam Check",
                "verdict": str(
                    row.get("verdict") or "UNKNOWN"
                ).upper(),
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

        activities.sort(
            key=lambda x: x.get("date") or ""
        )

        # -----------------------------
        # TREND
        # -----------------------------

        trend = []

        for activity in activities:

            if activity["type"] == "Scam Check":

                trend.append({
                    "date": activity["date"],
                    "score": activity["trust_score"]
                })

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

        print("TRUST API ERROR:", repr(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    print("========== TRUST API ==========")
    print("SESSION:", dict(session))
    print("EMAIL:", session.get("email"))
    print("USERTYPE:", session.get("usertype"))

    if "email" not in session or session.get("usertype") != "user":
        print("TRUST API UNAUTHORIZED")

        return jsonify({
            "success": False,
            "message": "Unauthorized",
            "session_email": session.get("email"),
            "session_usertype": session.get("usertype")
        }), 403

    # baaki tumhara existing code...
@app.route("/user-delete/<path:email>", methods=["POST"])
def user_delete(email):
    email = unquote(email).strip().lower()
    if "email" not in session or session.get("usertype") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    try:
        supabase.table("user").delete().eq("email", email).execute()
        supabase.table("login").delete().eq("email", email).execute()
        return jsonify({"success": True, "message": "User deleted successfully!"}), 200
    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500



# =========================================================
# SINGLE SCAM RESULT DETAIL ROUTE (BY ID)
# =========================================================
# =========================================================
# SINGLE SCAM RESULT DETAIL ROUTE (CORRECTED)
# =========================================================

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

        return render_template("scam-result.html", scan=scan)

    except Exception as e:
        print("FETCH SCAM RESULT ERROR:", repr(e))
        return f"Error loading scan result: {str(e)}", 500


# =========================================================
# REPORTED SCAMS HISTORY ROUTE
# =========================================================

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
        return render_template("report-history.html", reports=reports)
    except Exception as e:
        print("REPORT HISTORY ERROR:", repr(e))
        return f"Error loading report history: {str(e)}", 500





# =========================================================
# SCAM HISTORY ROUTE
# =========================================================
# =========================================================
# SCAM HISTORY ROUTE (WITH PUBLIC SCREENSHOT URL)
# =========================================================

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

        return render_template("checkscam-history.html", scans=scans)

    except Exception as e:
        print("HISTORY FETCH ERROR:", repr(e))
        return f"Error loading scan history: {str(e)}", 500
# =========================================================
# REPORT SCAM (PHONE AND/OR LINK)
# =========================================================

# =========================================================
# REPORT SCAM (DUPLICATE REPORT RESTRICTION ADDED)
# =========================================================

# =========================================================
# REPORT SCAM (AUTO-INCREMENT IN spam_numbers & spam_links)
# =========================================================

@app.route("/scam-report", methods=["GET", "POST"])
def scam_report():
    # Login & User Type Check
    if "email" not in session or session.get("usertype") != "user":
        if request.method == "GET":
            return redirect("/login")
        return jsonify({"success": False, "message": "Please login as user to report a scam"}), 401

    user_email = session.get("email")

    if request.method == "GET":
        return render_template("report-scam.html")

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

# =========================================================
# CORE SCAMCHECK DETECTION ROUTE
# =========================================================




import traceback
import uuid


@app.route("/scamcheck", methods=["GET", "POST"])
def scamcheck_check():
    if request.method == "GET":
        return redirect("user-dashboard")

    try:
        message = request.form.get("message", "").strip()
        phone = request.form.get("phone", "").strip()
        link = request.form.get("link", "").strip()
        screenshot_file = request.files.get("screenshot")

        has_message = bool(message)
        has_phone = bool(phone)
        has_link = bool(link)
        has_screenshot = bool(screenshot_file and screenshot_file.filename)

        screenshot_bytes = None
        screenshot_db_record = None

        # 1. In-Memory Screenshot Handling (No Disk Lock Errors)
        if has_screenshot:
            try:
                suffix = os.path.splitext(screenshot_file.filename)[1].lower() or ".png"
                filename = f"{uuid.uuid4().hex}{suffix}"
                storage_path = f"screenshots/{filename}"
                screenshot_db_record = storage_path

                screenshot_bytes = screenshot_file.read()

                # Upload to Supabase Storage (Safe)
                try:
                    supabase.storage.from_("scam-screenshots").upload(
                        storage_path,
                        screenshot_bytes,
                        {"content-type": screenshot_file.content_type or "image/png"}
                    )
                except Exception as st_err:
                    print("STORAGE UPLOAD NOTICE:", repr(st_err))
            except Exception as ss_err:
                print("SCREENSHOT PROCESS ERROR:", repr(ss_err))

        message_result = {"score": 0, "verdict": "UNKNOWN", "language": "unknown", "reasons": []}
        phone_result = {"found": False, "score": None, "reputation": "UNKNOWN", "report_count": 0, "reasons": []}
        link_result = {"score": 0, "domain": "", "final_domain": "", "verdict": "UNKNOWN", "reasons": []}
        screenshot_result = {"score": 0, "verdict": "UNKNOWN", "category": "Unknown", "detected_text": "", "reasons": []}

        # 2. Parallel AI Execution (In-Memory)
        with ThreadPoolExecutor(max_workers=4) as executor:
            fut_msg = executor.submit(message_detect, message) if has_message else None
            fut_phone = executor.submit(phone_detect, supabase, phone) if has_phone else None
            fut_link = executor.submit(link_detect, link) if has_link else None
            fut_ss = executor.submit(screenshot_detect, screenshot_bytes) if (has_screenshot and screenshot_bytes) else None

            if fut_msg:
                try: message_result = fut_msg.result()
                except Exception as e: message_result = {"score": 0, "verdict": "UNKNOWN", "reasons": [str(e)]}

            if fut_phone:
                try: phone_result = fut_phone.result()
                except Exception as e: phone_result = {"found": False, "score": None, "reputation": "UNKNOWN", "report_count": 0, "reasons": [str(e)]}

            if fut_link:
                try: link_result = fut_link.result()
                except Exception as e: link_result = {"score": 0, "domain": "", "verdict": "UNKNOWN", "reasons": [str(e)]}

            if fut_ss:
                try: screenshot_result = fut_ss.result()
                except Exception as e: screenshot_result = {"score": 0, "verdict": "UNKNOWN", "category": "Unknown", "reasons": [str(e)]}

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

        # 3. Risk Engine
        try:
            risk_result = calculate_risk(scores)
        except Exception:
            risk_result = max(scores.values()) if any(scores.values()) else 0

        if isinstance(risk_result, dict):
            final_score = int(risk_result.get("final_score", risk_result.get("score", 0)) or 0)
            final_verdict = risk_result.get("verdict", "UNKNOWN")
            contribution_data = risk_result.get("contribution", {})
        else:
            final_score = int(risk_result or 0)
            final_verdict = "VERY HIGH RISK" if final_score >= 80 else "HIGH RISK" if final_score >= 60 else "SUSPICIOUS" if final_score >= 30 else "LOW RISK"
            contribution_data = {}

        # 4. Fingerprint & Evidence
        try:
            fingerprint_data = build_scam_fingerprint(
                message=message,
                phone_result=phone_result,
                link_result=link_result,
                screenshot_result=screenshot_result
            )
            if not isinstance(fingerprint_data, dict): fingerprint_data = {}
        except Exception:
            fingerprint_data = {}

        fingerprint = fingerprint_data.get("scam_fingerprint", [])
        attack_chain = fingerprint_data.get("attack_chain", [])
        why_text = fingerprint_data.get("why", "Analysis completed.")

        evidence = list(dict.fromkeys([
            str(r) for r in (
                message_result.get("reasons", []) +
                link_result.get("reasons", []) +
                screenshot_result.get("reasons", [])
            ) if r
        ]))

        # 5. SafeNext Coach
        try:
            coach_advice = generate_safe_next(
                final_score=final_score,
                verdict=final_verdict,
                message=message,
                link_result=link_result,
                screenshot_result=screenshot_result,
                phone_result=phone_result,
                fingerprint=fingerprint,
                attack_chain=attack_chain
            )
            if not isinstance(coach_advice, dict): coach_advice = {}
        except Exception:
            coach_advice = {}

        # 6. What-If
        try:
            wi = what_if_analysis(
                message_score=scores["message"],
                phone_score=scores["phone"],
                link_score=scores["link"],
                screenshot_score=scores["screenshot"]
            )
            if not isinstance(wi, dict): wi = {}
        except Exception:
            wi = {}

        signal_impact = wi.get("impact", {}) if isinstance(wi.get("impact"), dict) else {}
        urgency_detected = [w for w in ["immediately", "verify", "suspended", "urgent", "24 hours", "blocked", "warning"] if w in (message + " " + link).lower()]

        # 7. Safe Supabase Save
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
            print("DB NOTICE (Non-Fatal):", repr(db_err))

        # 8. Success JSON Return
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
            "message_score": message_score,
            "message_verdict": message_result.get("verdict", "UNKNOWN"),
            "message_language": message_result.get("language", "unknown"),
            "message_reasons": [str(r) for r in message_result.get("reasons", [])],
            "phone_score": phone_score,
            "phone_reputation": phone_result.get("reputation", "UNKNOWN"),
            "phone_report_count": phone_result.get("report_count", 0),
            "phone_reasons": [str(r) for r in phone_result.get("reasons", [])],
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
            "signal_impact": signal_impact,
            "recommended_action": coach_advice.get("recommended_action", "DO NOT INTERACT"),
            "why_dangerous": coach_advice.get("why_dangerous", ""),
            "immediate_steps": coach_advice.get("immediate_steps", []),
            "recovery_steps": coach_advice.get("recovery_steps", []),
            "helplines": coach_advice.get("helplines", []),
            "safe_next": coach_advice.get("safe_next", []),
            "what_if": wi
        })

    except Exception as e:
        print("\n❌ CRITICAL ROUTE CRASH ERROR:")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server Error: {str(e)}", "error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)