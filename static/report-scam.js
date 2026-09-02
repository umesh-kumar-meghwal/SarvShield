$(document).ready(function () {

    /* =====================================================
       SIDEBAR
    ====================================================== */

    const $sidebar = $("#sidebar");
    const $menuBtn = $("#menuBtn");


    $menuBtn.on("click", function (event) {

        event.stopPropagation();

        if (window.innerWidth > 800) {

            $sidebar.toggleClass("collapsed");

        } else {

            $sidebar.toggleClass("open");

        }

    });


    $(document).on("click", function (event) {

        if (
            window.innerWidth <= 800 &&
            $sidebar.hasClass("open") &&
            !$(event.target).closest("#sidebar, #menuBtn").length
        ) {

            $sidebar.removeClass("open");

        }

    });


    $(".nav-item, .logout-link").on("click", function () {

        if (window.innerWidth <= 800) {

            $sidebar.removeClass("open");

        }

    });


    $(window).on("resize", function () {

        if (window.innerWidth <= 800) {

            $sidebar.removeClass("collapsed");

        } else {

            $sidebar.removeClass("open");

        }

    });


    /* =====================================================
       FORM ELEMENTS
    ====================================================== */

    const $form = $("#scamReportForm");
    const $phone = $("#phone");
    const $link = $("#link");
    const $reason = $("#reason");

    const $phoneError = $("#phoneError");
    const $linkError = $("#linkError");
    const $reasonError = $("#reasonError");

    const $reportBtn = $("#reportBtn");
    const $reportResponse = $("#reportResponse");

    const $characterCount = $("#characterCount");


    /* =====================================================
       CHARACTER COUNTER
    ====================================================== */

    function updateCharacterCount() {

        const length = $reason.val().length;

        $characterCount.text(
            length + " / 1000"
        );

    }


    $reason.on("input", function () {

        updateCharacterCount();

        clearFieldError($reason, $reasonError);

    });


    updateCharacterCount();


    /* =====================================================
       VALIDATION HELPERS
    ====================================================== */

    function clearFieldError($field, $errorElement) {

        $field.closest(".form-group")
            .removeClass("invalid");

        $errorElement.text("");

    }


    function setFieldError(
        $field,
        $errorElement,
        message
    ) {

        $field.closest(".form-group")
            .addClass("invalid");

        $errorElement.text(message);

    }


    function normalizePhone(value) {

        return value.replace(
            /[\s\-().]/g,
            ""
        );

    }


    function isValidPhone(value) {

        const phone = normalizePhone(value);

        return /^[+]?[0-9]{7,15}$/.test(phone);

    }


    function isValidUrl(value) {

        try {

            const url = new URL(value);

            return (
                url.protocol === "http:" ||
                url.protocol === "https:"
            );

        } catch (error) {

            return false;

        }

    }


    /* =====================================================
       LIVE VALIDATION
    ====================================================== */

    $phone.on("input", function () {

        const value = $phone.val().trim();

        clearFieldError(
            $phone,
            $phoneError
        );

        if (value && !isValidPhone(value)) {

            setFieldError(
                $phone,
                $phoneError,
                "Enter a valid phone number."
            );

        }

    });


    $link.on("input", function () {

        const value = $link.val().trim();

        clearFieldError(
            $link,
            $linkError
        );

        if (value && !isValidUrl(value)) {

            setFieldError(
                $link,
                $linkError,
                "Enter a valid website URL."
            );

        }

    });


    $reason.on("blur", function () {

        const value = $reason.val().trim();

        clearFieldError(
            $reason,
            $reasonError
        );

        if (!value) {

            setFieldError(
                $reason,
                $reasonError,
                "Please describe the scam activity."
            );

        }

    });


    /* =====================================================
       RESPONSE
    ====================================================== */

    function showResponse(
        type,
        message
    ) {

        $reportResponse
            .removeClass("success error")
            .addClass(type)
            .text(message)
            .addClass("show");

    }


    function clearResponse() {

        $reportResponse
            .removeClass("success error show")
            .text("");

    }


    /* =====================================================
       FORM SUBMISSION
    ====================================================== */

    $form.on("submit", function (event) {

        event.preventDefault();

        clearResponse();

        const phone = $phone.val().trim();
        const link = $link.val().trim();
        const reason = $reason.val().trim();


        let isValid = true;


        /* ---------------------------------------------
           PHONE OR LINK REQUIRED
        --------------------------------------------- */

        if (!phone && !link) {

            setFieldError(
                $phone,
                $phoneError,
                "Enter a phone number or website link."
            );

            setFieldError(
                $link,
                $linkError,
                "Enter a phone number or website link."
            );

            isValid = false;

        } else {

            clearFieldError(
                $phone,
                $phoneError
            );

            clearFieldError(
                $link,
                $linkError
            );

        }


        /* ---------------------------------------------
           PHONE VALIDATION
        --------------------------------------------- */

        if (phone && !isValidPhone(phone)) {

            setFieldError(
                $phone,
                $phoneError,
                "Enter a valid phone number."
            );

            isValid = false;

        }


        /* ---------------------------------------------
           URL VALIDATION
        --------------------------------------------- */

        if (link && !isValidUrl(link)) {

            setFieldError(
                $link,
                $linkError,
                "Enter a valid website URL."
            );

            isValid = false;

        }


        /* ---------------------------------------------
           REASON VALIDATION
        --------------------------------------------- */

        if (!reason) {

            setFieldError(
                $reason,
                $reasonError,
                "Please describe the scam activity."
            );

            isValid = false;

        } else {

            clearFieldError(
                $reason,
                $reasonError
            );

        }


        if (!isValid) {

            const $firstInvalid =
                $(".form-group.invalid").first();

            if ($firstInvalid.length) {

                $("html, body").animate(
                    {
                        scrollTop:
                            $firstInvalid.offset().top - 110
                    },
                    350
                );

            }

            return;

        }


        /* =================================================
           SUBMIT
        ================================================== */

        $reportBtn
            .prop("disabled", true)
            .addClass("loading");

        $reportBtn
            .find(".submit-text")
            .text("Submitting Report");


        showResponse(
            "success",
            "Submitting your report..."
        );


        $.ajax({

            url: "/report-scam",

            type: "POST",

            data: {

                phone_number: phone,
                link: link,
                reason: reason

            },

            success: function (response) {

                const message =
                    response &&
                    response.message
                        ? response.message
                        : "Scam report submitted successfully.";

                showResponse(
                    "success",
                    message
                );

                $form[0].reset();

                updateCharacterCount();

                clearFieldError(
                    $phone,
                    $phoneError
                );

                clearFieldError(
                    $link,
                    $linkError
                );

                clearFieldError(
                    $reason,
                    $reasonError
                );

            },


            error: function (xhr) {

                let message =
                    "Unable to submit the scam report.";

                if (
                    xhr.responseJSON &&
                    xhr.responseJSON.message
                ) {

                    message =
                        xhr.responseJSON.message;

                }

                showResponse(
                    "error",
                    message
                );

            },


            complete: function () {

                $reportBtn
                    .prop("disabled", false)
                    .removeClass("loading");

                $reportBtn
                    .find(".submit-text")
                    .text("Submit Scam Report");

            }

        });

    });


    /* =====================================================
       ESCAPE FORM RESPONSE
    ====================================================== */

    $phone.on("focus", clearResponse);
    $link.on("focus", clearResponse);
    $reason.on("focus", clearResponse);

});