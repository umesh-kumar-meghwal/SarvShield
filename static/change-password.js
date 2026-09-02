document.addEventListener("DOMContentLoaded", function () {

    const form =
        document.getElementById("passwordForm");

    const currentPassword =
        document.getElementById("currentPassword");

    const newPassword =
        document.getElementById("newPassword");

    const confirmPassword =
        document.getElementById("confirmPassword");


    const currentError =
        document.getElementById("currentError");

    const newError =
        document.getElementById("newError");

    const confirmError =
        document.getElementById("confirmError");


    const strengthFill =
        document.getElementById("strengthFill");

    const strengthText =
        document.getElementById("strengthText");


    /* =====================================
       SHOW / HIDE PASSWORD
    ===================================== */

    document
        .querySelectorAll(".eye-btn")
        .forEach(function (button) {

            button.addEventListener("click", function () {

                const input =
                    document.getElementById(
                        button.dataset.target
                    );


                if (input.type === "password") {

                    input.type = "text";

                    button.setAttribute(
                        "aria-label",
                        "Hide password"
                    );

                } else {

                    input.type = "password";

                    button.setAttribute(
                        "aria-label",
                        "Show password"
                    );

                }

            });

        });


    /* =====================================
       ERROR FUNCTIONS
    ===================================== */

    function showError(input, error, message) {

        input.classList.add("invalid");

        error.textContent = message;

        error.style.display = "block";
    }


    function clearError(input, error) {

        input.classList.remove("invalid");

        error.textContent = "";

        error.style.display = "none";
    }


    /* =====================================
       PASSWORD RULES
    ===================================== */

    function getRules(password) {

        return {

            length:
                password.length >= 8,

            upper:
                /[A-Z]/.test(password),

            lower:
                /[a-z]/.test(password),

            number:
                /[0-9]/.test(password),

            special:
                /[^A-Za-z0-9\s]/.test(password),

            noSpace:
                !/\s/.test(password)

        };

    }


    /* =====================================
       UPDATE REQUIREMENTS
    ===================================== */

    function updateRules() {

        const rules =
            getRules(newPassword.value);


        document
            .getElementById("lengthRule")
            .classList.toggle(
                "valid",
                rules.length
            );


        document
            .getElementById("upperRule")
            .classList.toggle(
                "valid",
                rules.upper
            );


        document
            .getElementById("lowerRule")
            .classList.toggle(
                "valid",
                rules.lower
            );


        document
            .getElementById("numberRule")
            .classList.toggle(
                "valid",
                rules.number
            );


        document
            .getElementById("specialRule")
            .classList.toggle(
                "valid",
                rules.special
            );


        document
            .getElementById("spaceRule")
            .classList.toggle(
                "valid",
                rules.noSpace
            );

    }


    /* =====================================
       STRENGTH
    ===================================== */

    function updateStrength() {

        const password =
            newPassword.value;

        const rules =
            getRules(password);


        let score = 0;


        if (rules.length) score++;

        if (rules.upper) score++;

        if (rules.lower) score++;

        if (rules.number) score++;

        if (rules.special) score++;

        if (rules.noSpace) score++;


        if (!password) {

            strengthFill.style.width = "0%";

            strengthText.textContent = "—";

            return;
        }


        const percentage =
            (score / 6) * 100;


        strengthFill.style.width =
            percentage + "%";


        if (score <= 2) {

            strengthText.textContent =
                "Weak";

            strengthFill.style.background =
                "#ff4d5e";

        } else if (score <= 4) {

            strengthText.textContent =
                "Medium";

            strengthFill.style.background =
                "#ffb020";

        } else if (score === 5) {

            strengthText.textContent =
                "Good";

            strengthFill.style.background =
                "#7c9cff";

        } else {

            strengthText.textContent =
                "Strong";

            strengthFill.style.background =
                "#2ed180";

        }

    }


    newPassword.addEventListener(
        "input",
        function () {

            updateRules();
            updateStrength();

            clearError(
                newPassword,
                newError
            );

        }
    );


    /* =====================================
       CONFIRM PASSWORD LIVE CHECK
    ===================================== */

    confirmPassword.addEventListener(
        "input",
        function () {

            clearError(
                confirmPassword,
                confirmError
            );


            if (
                confirmPassword.value &&
                confirmPassword.value !==
                newPassword.value
            ) {

                showError(
                    confirmPassword,
                    confirmError,
                    "Passwords do not match."
                );

            }

        }
    );


    currentPassword.addEventListener(
        "input",
        function () {

            clearError(
                currentPassword,
                currentError
            );

        }
    );


    /* =====================================
       FINAL VALIDATION
    ===================================== */

    form.addEventListener(
        "submit",
        function (event) {

            let valid = true;


            clearError(
                currentPassword,
                currentError
            );

            clearError(
                newPassword,
                newError
            );

            clearError(
                confirmPassword,
                confirmError
            );


            const current =
                currentPassword.value;

            const password =
                newPassword.value;

            const confirm =
                confirmPassword.value;


            /* CURRENT PASSWORD */

            if (!current) {

                showError(
                    currentPassword,
                    currentError,
                    "Current password is required."
                );

                valid = false;

            }


            /* NEW PASSWORD */

            if (!password) {

                showError(
                    newPassword,
                    newError,
                    "New password is required."
                );

                valid = false;

            } else {

                const rules =
                    getRules(password);


                if (password.length < 8) {

                    showError(
                        newPassword,
                        newError,
                        "Use at least 8 characters."
                    );

                    valid = false;

                } else if (!rules.upper) {

                    showError(
                        newPassword,
                        newError,
                        "Include at least one uppercase letter."
                    );

                    valid = false;

                } else if (!rules.lower) {

                    showError(
                        newPassword,
                        newError,
                        "Include at least one lowercase letter."
                    );

                    valid = false;

                } else if (!rules.number) {

                    showError(
                        newPassword,
                        newError,
                        "Include at least one number."
                    );

                    valid = false;

                } else if (!rules.special) {

                    showError(
                        newPassword,
                        newError,
                        "Include at least one special character."
                    );

                    valid = false;

                } else if (!rules.noSpace) {

                    showError(
                        newPassword,
                        newError,
                        "Password cannot contain spaces."
                    );

                    valid = false;

                } else if (password === current) {

                    showError(
                        newPassword,
                        newError,
                        "New password must be different from your current password."
                    );

                    valid = false;

                }

            }


            /* CONFIRM PASSWORD */

            if (!confirm) {

                showError(
                    confirmPassword,
                    confirmError,
                    "Please confirm your new password."
                );

                valid = false;

            } else if (confirm !== password) {

                showError(
                    confirmPassword,
                    confirmError,
                    "Passwords do not match."
                );

                valid = false;

            }


            /* STOP SUBMISSION */

            if (!valid) {

                event.preventDefault();

                return;

            }


            document
                .getElementById("changeBtn")
                .disabled = true;

        }
    );


    updateRules();
    updateStrength();

});