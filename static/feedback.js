document.addEventListener("DOMContentLoaded", function () {

    const feedbackForm =
        document.getElementById("feedbackForm");

    if (!feedbackForm) {
        return;
    }


    const rating =
        document.getElementById("rating");

    const message =
        document.getElementById("message");

    const ratingError =
        document.getElementById("ratingError");

    const messageError =
        document.getElementById("messageError");

    const submitButton =
        document.getElementById("submitFeedback");

    const responseBox =
        document.getElementById("feedbackResponse");

    const characterCount =
        document.getElementById("characterCount");


    /* =========================
       ERROR HELPERS
    ========================= */

    function showError(element, text) {

        element.textContent = text;
        element.style.display = "block";

    }


    function clearError(element) {

        element.textContent = "";
        element.style.display = "none";

    }


    /* =========================
       RATING VALIDATION
    ========================= */

    function validateRating() {

        if (!rating.value) {

            showError(
                ratingError,
                "Please select a rating."
            );

            return false;
        }

        clearError(ratingError);

        return true;
    }


    /* =========================
       MESSAGE VALIDATION
    ========================= */

    function validateMessage() {

        const value =
            message.value.trim();


        if (!value) {

            showError(
                messageError,
                "Feedback is required."
            );

            return false;
        }


        if (value.length < 5) {

            showError(
                messageError,
                "Feedback must be at least 5 characters."
            );

            return false;
        }


        if (value.length > 500) {

            showError(
                messageError,
                "Feedback must be 500 characters or less."
            );

            return false;
        }


        clearError(messageError);

        return true;
    }


    /* =========================
       LIVE VALIDATION
    ========================= */

    rating.addEventListener(
        "change",
        validateRating
    );


    message.addEventListener(
        "input",
        function () {

            validateMessage();

            characterCount.textContent =
                message.value.length;

        }
    );


    /* =========================
       SUBMIT
    ========================= */

    feedbackForm.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();


            const ratingValid =
                validateRating();

            const messageValid =
                validateMessage();


            if (!ratingValid || !messageValid) {
                return;
            }


            submitButton
                .disabled = true;

            submitButton.textContent =
                "Submitting...";

            responseBox.textContent = "";
            responseBox.className =
                "feedback-response";


            $.ajax({

                url: "/feedback",

                type: "POST",

                data: $(feedbackForm).serialize(),


                success: function (response) {

                    responseBox.textContent =
                        response.message ||
                        "Feedback submitted successfully.";

                    responseBox.className =
                        "feedback-response success";


                    if (response.success) {

                        feedbackForm.reset();

                        characterCount.textContent =
                            "0";

                        clearError(ratingError);
                        clearError(messageError);

                    }

                },


                error: function (xhr) {

                    let errorMessage =
                        "Something went wrong. Please try again.";


                    if (xhr.responseJSON) {

                        errorMessage =
                            xhr.responseJSON.message ||
                            errorMessage;

                    }


                    responseBox.textContent =
                        errorMessage;

                    responseBox.className =
                        "feedback-response error";

                },


                complete: function () {

                    submitButton.disabled =
                        false;

                    submitButton.textContent =
                        "Submit Feedback";

                }

            });

        }
    );

});