/* =========================================
   SCAMSHIELD - USER REGISTER JS
========================================= */

$(document).ready(function () {

    let emailVerified = false;


    /* =========================================
       HELPERS
    ========================================= */

    function showEmailError(message) {

        $("#emailError").text(message);

        $("#email").addClass("input-error");
    }


    function clearEmailError() {

        $("#emailError").text("");

        $("#email").removeClass("input-error");
    }


    function showOtpError(message) {

        $("#otpError").text(message);

        $("#otp").addClass("input-error");
    }


    function clearOtpError() {

        $("#otpError").text("");

        $("#otp").removeClass("input-error");
    }


    function isValidEmail(email) {

        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }


    function enableRegistration() {

        $("#name").prop("disabled", false);

        $("#password").prop("disabled", false);

        $("#confirmPassword").prop("disabled", false);

        $("#phone").prop("disabled", false);

        $("#address").prop("disabled", false);

        $("#togglePassword").prop("disabled", false);

        $("#toggleConfirmPassword").prop("disabled", false);

        $("#registerBtn").prop("disabled", false);
    }


    /* =========================================
       EMAIL INPUT
    ========================================= */

    $("#email").on("input", function () {

        clearEmailError();

        emailVerified = false;

        $("#registerBtn").prop("disabled", true);

        $("#otpSection").hide();

        $("#otp").val("");

        $("#otpResponse").html("");

        $("#name").prop("disabled", true);
        $("#password").prop("disabled", true);
        $("#confirmPassword").prop("disabled", true);
        $("#phone").prop("disabled", true);
        $("#address").prop("disabled", true);

        $("#togglePassword").prop("disabled", true);
        $("#toggleConfirmPassword").prop("disabled", true);
    });


    /* =========================================
       SEND OTP
    ========================================= */

    $("#sendOtpBtn").on("click", function () {

        const email = $("#email").val().trim();

        clearEmailError();

        clearOtpError();

        $("#otpResponse").html("");


        /* Email required */

        if (email === "") {

            showEmailError("Email is required.");

            $("#email").focus();

            return;
        }


        /* Email validation */

        if (!isValidEmail(email)) {

            showEmailError("Please enter a valid email address.");

            $("#email").focus();

            return;
        }


        const button = $("#sendOtpBtn");

        button.prop("disabled", true);

        button.text("Sending...");


        $.ajax({

            url: "/send-otp",

            type: "POST",

            data: {
                email: email
            },


            success: function (response) {

                /*
                 * Backend should return:
                 *
                 * {
                 *   success: true,
                 *   message: "OTP sent successfully"
                 * }
                 */

                if (response.success) {

                    $("#otpSection").slideDown(250);

                    $("#otpResponse").html(
                        "<div class='success-message'>" +
                        (response.message || "OTP sent successfully. Check your email.") +
                        "</div>"
                    );

                    $("#otp").focus();

                    button.text("Resend OTP");

                } else {

                    $("#otpResponse").html(
                        "<div class='error-message'>" +
                        (response.message || "Unable to send OTP.") +
                        "</div>"
                    );

                    button.text("Send OTP");
                }
            },


            error: function (xhr) {

                let message = "Unable to send OTP.";

                if (xhr.responseJSON) {

                    message =
                        xhr.responseJSON.message ||
                        message;
                }

                $("#otpResponse").html(
                    "<div class='error-message'>" +
                    message +
                    "</div>"
                );

                button.text("Send OTP");
            },


            complete: function () {

                button.prop("disabled", false);
            }

        });

    });


    /* =========================================
       VERIFY OTP
    ========================================= */

    $("#verifyOtpBtn").on("click", function () {

        const email = $("#email").val().trim();

        const otp = $("#otp").val().trim();

        clearOtpError();


        if (email === "") {

            showEmailError("Email is required.");

            return;
        }


        if (otp === "") {

            showOtpError("OTP is required.");

            $("#otp").focus();

            return;
        }


        if (!/^\d{6}$/.test(otp)) {

            showOtpError("Please enter a valid 6-digit OTP.");

            $("#otp").focus();

            return;
        }


        const button = $("#verifyOtpBtn");

        button.prop("disabled", true);

        button.text("Verifying...");


        $.ajax({

            url: "/verify-otp",

            type: "POST",

            data: {
                email: email,
                otp: otp
            },


            success: function (response) {

                if (response.success) {

                    emailVerified = true;


                    $("#email")
                        .prop("disabled", true)
                        .removeClass("input-error")
                        .addClass("input-valid");


                    $("#sendOtpBtn")
                        .prop("disabled", true)
                        .text("Verified ✓");


                    $("#otp")
                        .prop("disabled", true)
                        .removeClass("input-error")
                        .addClass("input-valid");


                    button
                        .prop("disabled", true)
                        .text("Verified ✓");


                    $("#otpResponse").html(
                        "<div class='success-message'>" +
                        (response.message || "Email verified successfully.") +
                        "</div>"
                    );


                    enableRegistration();

                } else {

                    showOtpError(
                        response.message ||
                        "Invalid OTP."
                    );

                    button
                        .prop("disabled", false)
                        .text("Verify");
                }
            },


            error: function (xhr) {

                let message = "OTP verification failed.";

                if (xhr.responseJSON) {

                    message =
                        xhr.responseJSON.message ||
                        message;
                }

                showOtpError(message);

                button
                    .prop("disabled", false)
                    .text("Verify");
            }

        });

    });


    /* =========================================
       ONLY NUMBERS IN OTP
    ========================================= */

    $("#otp").on("input", function () {

        this.value = this.value
            .replace(/\D/g, "")
            .slice(0, 6);

        clearOtpError();
    });


    /* =========================================
       PASSWORD SHOW / HIDE
    ========================================= */

    $("#togglePassword").on("click", function () {

        const input = $("#password");

        if (input.attr("type") === "password") {

            input.attr("type", "text");

            $(this).text("Hide");

        } else {

            input.attr("type", "password");

            $(this).text("Show");
        }
    });


    $("#toggleConfirmPassword").on("click", function () {

        const input = $("#confirmPassword");

        if (input.attr("type") === "password") {

            input.attr("type", "text");

            $(this).text("Hide");

        } else {

            input.attr("type", "password");

            $(this).text("Show");
        }
    });


    /* =========================================
       PHONE ONLY NUMBERS
    ========================================= */

    $("#phone").on("input", function () {

        this.value = this.value
            .replace(/\D/g, "")
            .slice(0, 10);
    });


    /* =========================================
       REGISTER
    ========================================= */

    $("#userRegisterForm").on("submit", function (e) {

        e.preventDefault();


        if (!emailVerified) {

            $("#registerResponse").html(
                "<div class='error-message'>" +
                "Please verify your email first." +
                "</div>"
            );

            return;
        }


        const name = $("#name").val().trim();

        const email = $("#email").val().trim();

        const password = $("#password").val();

        const confirmPassword =
            $("#confirmPassword").val();

        const phone = $("#phone").val().trim();

        const address = $("#address").val().trim();


        let valid = true;


        /* Name */

        if (name === "") {

            $("#nameError").text("Full name is required.");

            valid = false;

        } else {

            $("#nameError").text("");
        }


        /* Password */

        if (password === "") {

            $("#passwordError").text(
                "Password is required."
            );

            valid = false;

        } else if (password.length < 6) {

            $("#passwordError").text(
                "Password must be at least 6 characters."
            );

            valid = false;

        } else {

            $("#passwordError").text("");
        }


        /* Confirm Password */

        if (confirmPassword === "") {

            $("#confirmPasswordError").text(
                "Please confirm your password."
            );

            valid = false;

        } else if (password !== confirmPassword) {

            $("#confirmPasswordError").text(
                "Passwords do not match."
            );

            valid = false;

        } else {

            $("#confirmPasswordError").text("");
        }


        /* Phone */

        if (phone === "") {

            $("#phoneError").text(
                "Phone number is required."
            );

            valid = false;

        } else if (!/^\d{10}$/.test(phone)) {

            $("#phoneError").text(
                "Enter a valid 10-digit phone number."
            );

            valid = false;

        } else {

            $("#phoneError").text("");
        }


        if (!valid) {
            return;
        }


        /* =====================================
           SUBMIT
        ===================================== */

        const registerBtn = $("#registerBtn");

        registerBtn.prop("disabled", true);

        $("#registerBtnText").text("Creating account...");

        $("#registerSpinner").prop("hidden", false);

        $("#registerResponse").html("");


        $.ajax({

            url: "/user-register",

            type: "POST",

            data: {
                name: name,
                email: email,
                password: password,
                phone: phone,
                address: address
            },


            success: function (response) {

                if (response.success) {

                    $("#registerResponse").html(
                        "<div class='success-message'>" +
                        (response.message ||
                        "Account created successfully.") +
                        "</div>"
                    );


                    setTimeout(function () {

                        if (response.redirect) {

                            window.location.href =
                                response.redirect;

                        } else {

                            window.location.href =
                                "/login";
                        }

                    }, 1000);

                } else {

                    $("#registerResponse").html(
                        "<div class='error-message'>" +
                        (response.message ||
                        "Registration failed.") +
                        "</div>"
                    );

                    registerBtn.prop("disabled", false);

                    $("#registerBtnText")
                        .text("Create Account");

                    $("#registerSpinner")
                        .prop("hidden", true);
                }
            },


            error: function (xhr) {

                let message =
                    "Unable to create account.";

                if (xhr.responseJSON) {

                    message =
                        xhr.responseJSON.message ||
                        message;
                }

                $("#registerResponse").html(
                    "<div class='error-message'>" +
                    message +
                    "</div>"
                );

                registerBtn.prop("disabled", false);

                $("#registerBtnText")
                    .text("Create Account");

                $("#registerSpinner")
                    .prop("hidden", true);
            }

        });

    });

});