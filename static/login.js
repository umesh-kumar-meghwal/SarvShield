/* =========================================================
   SCAMSHIELD LOGIN
   ========================================================= */

$(document).ready(function () {

    const form = $("#loginForm");
    const email = $("#email");
    const password = $("#password");

    const emailError = $("#emailError");
    const passwordError = $("#passwordError");

    const loginBtn = $("#loginBtn");
    const loginBtnText = $("#loginBtnText");
    const loginSpinner = $("#loginSpinner");

    const loginResponse = $("#loginResponse");

    const togglePassword = $("#togglePassword");


    /* =====================================================
       EMAIL VALIDATION
       ===================================================== */

    function validateEmail() {

        const value = email.val().trim();

        email.removeClass("input-error");
        emailError.text("");

        if (value === "") {

            email.addClass("input-error");

            emailError.text(
                "Please enter your email address."
            );

            return false;
        }


        if (value.length > 254) {

            email.addClass("input-error");

            emailError.text(
                "Email address is too long."
            );

            return false;
        }


        const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


        if (!emailPattern.test(value)) {

            email.addClass("input-error");

            emailError.text(
                "Please enter a valid email address."
            );

            return false;
        }


        return true;
    }


    /* =====================================================
       PASSWORD VALIDATION
       ===================================================== */

    function validatePassword() {

        const value = password.val();

        password.removeClass("input-error");
        passwordError.text("");

        if (value === "") {

            password.addClass("input-error");

            passwordError.text(
                "Please enter your password."
            );

            return false;
        }


        if (value.length < 6) {

            password.addClass("input-error");

            passwordError.text(
                "Password must contain at least 6 characters."
            );

            return false;
        }


        if (value.length > 128) {

            password.addClass("input-error");

            passwordError.text(
                "Password is too long."
            );

            return false;
        }


        return true;
    }


    /* =====================================================
       LIVE VALIDATION
       ===================================================== */

    email.on("blur", function () {
        validateEmail();
    });


    password.on("blur", function () {
        validatePassword();
    });


    email.on("input", function () {

        if (email.hasClass("input-error")) {
            validateEmail();
        }

    });


    password.on("input", function () {

        if (password.hasClass("input-error")) {
            validatePassword();
        }

    });


    /* =====================================================
       SHOW / HIDE PASSWORD
       ===================================================== */

    togglePassword.on("click", function () {

        const isPassword =
            password.attr("type") === "password";


        if (isPassword) {

            password.attr("type", "text");

            togglePassword.attr(
                "aria-label",
                "Hide password"
            );

            togglePassword.attr(
                "title",
                "Hide password"
            );

        } else {

            password.attr("type", "password");

            togglePassword.attr(
                "aria-label",
                "Show password"
            );

            togglePassword.attr(
                "title",
                "Show password"
            );

        }

    });


    /* =====================================================
       LOGIN SUBMIT
       ===================================================== */

    form.on("submit", function (e) {

        e.preventDefault();


        loginResponse
            .removeClass("error")
            .text("");


        const validEmail = validateEmail();
        const validPassword = validatePassword();


        if (!validEmail || !validPassword) {

            return;
        }


        /* Disable button */

        loginBtn.prop("disabled", true);

        loginBtnText.text("Signing in...");

        loginSpinner.prop("hidden", false);


        /* =================================================
           BACKEND REQUEST
           ================================================= */

        $.ajax({

            url: "/login",

            type: "POST",

            data: {
                email: email.val().trim(),
                password: password.val()
            },


            success: function (response) {

                if (
                    response &&
                    response.redirect
                ) {

                    window.location.href =
                        response.redirect;

                } else {

                    loginResponse
                        .addClass("error")
                        .text(
                            "Login successful, but redirect information was not received."
                        );

                }

            },


            error: function (xhr) {

                let message =
                    "Invalid email or password.";


                if (
                    xhr.responseJSON &&
                    xhr.responseJSON.message
                ) {

                    message =
                        xhr.responseJSON.message;

                }


                loginResponse
                    .addClass("error")
                    .text(message);

            },


            complete: function () {

                loginBtn.prop("disabled", false);

                loginBtnText.text("Sign in");

                loginSpinner.prop("hidden", true);

            }

        });

    });

});