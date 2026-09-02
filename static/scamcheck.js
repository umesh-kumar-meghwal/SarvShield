document.addEventListener("DOMContentLoaded", function () {

    /* =========================================================
       ELEMENTS
    ========================================================= */

    const form = document.getElementById("scamCheckForm");

    if (!form) {
        console.warn("ScamCheck form not found.");
        return;
    }

    const submitBtn =
        form.querySelector("button[type='submit']") ||
        document.getElementById("checkBtn");

    const messageInput = document.getElementById("message");
    const phoneInput = document.getElementById("phone");
    const linkInput = document.getElementById("link");
    const screenshotInput = document.getElementById("screenshot");

    const resultContainer =
        document.getElementById("resultContainer") ||
        document.getElementById("results");

    const errorBox =
        document.getElementById("errorBox");

    /* =========================================================
       HELPERS
    ========================================================= */

    function showError(message) {
        if (errorBox) {
            errorBox.textContent = message;
            errorBox.style.display = "block";
        } else {
            alert(message);
        }
    }

    function hideError() {
        if (errorBox) {
            errorBox.textContent = "";
            errorBox.style.display = "none";
        }
    }

    function setLoading(loading) {

        if (!submitBtn) {
            return;
        }

        if (loading) {

            submitBtn.disabled = true;

            if (!submitBtn.dataset.originalText) {
                submitBtn.dataset.originalText =
                    submitBtn.textContent.trim();
            }

            submitBtn.textContent = "Checking...";

        } else {

            submitBtn.disabled = false;

            submitBtn.textContent =
                submitBtn.dataset.originalText || "Check Scam";
        }
    }

    function escapeHTML(value) {

        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function getValue(element) {

        if (!element) {
            return "";
        }

        return element.value.trim();
    }

    /* =========================================================
       URL EXTRACTION
    ========================================================= */

    function extractURL(text) {

        if (!text) {
            return "";
        }

        const urlRegex =
            /(https?:\/\/[^\s]+|www\.[^\s]+)/i;

        const match = text.match(urlRegex);

        if (!match) {
            return "";
        }

        let url = match[0].replace(/[.,!?;:]+$/, "");

        if (url.startsWith("www.")) {
            url = "https://" + url;
        }

        return url;
    }

    /* =========================================================
       VERDICT CLASS
    ========================================================= */

    function getVerdictClass(verdict) {

        const value =
            String(verdict || "").toLowerCase();

        if (
            value === "safe" ||
            value === "legitimate" ||
            value === "clean"
        ) {
            return "safe";
        }

        if (
            value === "scam" ||
            value === "dangerous" ||
            value === "malicious" ||
            value === "fraud"
        ) {
            return "danger";
        }

        return "warning";
    }

    /* =========================================================
       SCORE NORMALIZATION
    ========================================================= */

    function normalizeScore(score) {

        let number = Number(score);

        if (Number.isNaN(number)) {
            return 0;
        }

        number = Math.max(0, Math.min(100, number));

        return Math.round(number);
    }

    /* =========================================================
       RESULT HTML
    ========================================================= */

    function renderResult(data) {

        if (!resultContainer) {
            console.log("ScamShield Result:", data);
            return;
        }

        const finalScore =
            normalizeScore(
                data.final_score ??
                data.score ??
                data.finalScore ??
                0
            );

        const verdict =
            data.verdict ||
            data.final_verdict ||
            data.finalVerdict ||
            "UNKNOWN";

        const verdictClass =
            getVerdictClass(verdict);

        const messageScore =
            normalizeScore(
                data.message_score ??
                data.messageScore ??
                0
            );

        const phoneScore =
            normalizeScore(
                data.phone_score ??
                data.phoneScore ??
                0
            );

        const linkScore =
            normalizeScore(
                data.link_score ??
                data.linkScore ??
                0
            );

        const screenshotScore =
            normalizeScore(
                data.screenshot_score ??
                data.screenshotScore ??
                0
            );

        const explanation =
            data.scam_explanation ||
            data.explanation ||
            data.message_explanation ||
            data.reason ||
            "No additional explanation available.";

        resultContainer.innerHTML = `

            <div class="result-card">

                <div class="result-header">

                    <div>
                        <span class="section-label">
                            SCAMSHIELD ANALYSIS
                        </span>

                        <h2>Scan Result</h2>
                    </div>

                    <div class="final-score ${verdictClass}">
                        <strong>${finalScore}</strong>
                        <span>/100</span>
                    </div>

                </div>


                <div class="verdict-box ${verdictClass}">

                    <span class="verdict-label">
                        VERDICT
                    </span>

                    <strong>
                        ${escapeHTML(verdict)}
                    </strong>

                </div>


                <div class="analysis-grid">

                    <div class="analysis-item">

                        <span>Message</span>

                        <strong>
                            ${messageScore}/100
                        </strong>

                    </div>


                    <div class="analysis-item">

                        <span>Phone</span>

                        <strong>
                            ${phoneScore}/100
                        </strong>

                    </div>


                    <div class="analysis-item">

                        <span>Link</span>

                        <strong>
                            ${linkScore}/100
                        </strong>

                    </div>


                    <div class="analysis-item">

                        <span>Screenshot</span>

                        <strong>
                            ${screenshotScore}/100
                        </strong>

                    </div>

                </div>


                <div class="explanation-box">

                    <span class="section-label">
                        ANALYSIS
                    </span>

                    <p>
                        ${escapeHTML(explanation)}
                    </p>

                </div>

            </div>
        `;

        resultContainer.style.display = "block";

        resultContainer.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    /* =========================================================
       AJAX REQUEST
    ========================================================= */

    async function submitScan() {

        hideError();

        const message =
            getValue(messageInput);

        const phone =
            getValue(phoneInput);

        let link =
            getValue(linkInput);

        const screenshot =
            screenshotInput &&
            screenshotInput.files.length > 0
                ? screenshotInput.files[0]
                : null;


        /* -----------------------------------------------------
           AUTO EXTRACT LINK FROM MESSAGE
        ----------------------------------------------------- */

        if (!link && message) {
            link = extractURL(message);
        }


        /* -----------------------------------------------------
           VALIDATION
        ----------------------------------------------------- */

        if (
            !message &&
            !phone &&
            !link &&
            !screenshot
        ) {
            showError(
                "Please enter a message, phone number, link, or screenshot."
            );

            return;
        }


        /* -----------------------------------------------------
           FORM DATA
        ----------------------------------------------------- */

        const formData = new FormData();

        formData.append("message", message);
        formData.append("phone", phone);
        formData.append("link", link);

        if (screenshot) {
            formData.append(
                "screenshot",
                screenshot
            );
        }


        /* -----------------------------------------------------
           LOADING
        ----------------------------------------------------- */

        setLoading(true);


        try {

            const response =
                await fetch("/scamcheck", {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With":
                            "XMLHttpRequest"
                    }
                });


            let data;

            try {

                data = await response.json();

            } catch (jsonError) {

                throw new Error(
                    "Server returned an invalid response."
                );
            }


            /* -------------------------------------------------
               SERVER ERROR
            ------------------------------------------------- */

            if (!response.ok) {

                throw new Error(
                    data.error ||
                    data.message ||
                    "Scam check failed."
                );
            }


            if (
                data.success === false ||
                data.status === "error"
            ) {

                throw new Error(
                    data.error ||
                    data.message ||
                    "Unable to analyse this scan."
                );
            }


            /* -------------------------------------------------
               DISPLAY RESULT
            ------------------------------------------------- */

            renderResult(data);


        } catch (error) {

            console.error(
                "ScamShield error:",
                error
            );

            showError(
                error.message ||
                "Something went wrong. Please try again."
            );

        } finally {

            setLoading(false);
        }
    }


    /* =========================================================
       FORM SUBMIT
    ========================================================= */

    form.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();

            submitScan();
        }
    );


    /* =========================================================
       ENTER KEY
    ========================================================= */

    if (messageInput) {

        messageInput.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    if (!submitBtn || !submitBtn.disabled) {
                        submitScan();
                    }
                }
            }
        );
    }


    /* =========================================================
       SCREENSHOT PREVIEW
    ========================================================= */

    if (screenshotInput) {

        screenshotInput.addEventListener(
            "change",
            function () {

                const file =
                    screenshotInput.files[0];

                if (!file) {
                    return;
                }

                if (!file.type.startsWith("image/")) {

                    showError(
                        "Please select a valid image file."
                    );

                    screenshotInput.value = "";

                    return;
                }

                hideError();

                console.log(
                    "Screenshot selected:",
                    file.name
                );
            }
        );
    }


    /* =========================================================
       CLEAR ERROR WHEN USER TYPES
    ========================================================= */

    [
        messageInput,
        phoneInput,
        linkInput
    ].forEach(function (input) {

        if (!input) {
            return;
        }

        input.addEventListener(
            "input",
            function () {
                hideError();
            }
        );
    });


    /* =========================================================
       SIDEBAR
    ========================================================= */

    const menuBtn =
        document.getElementById("menuBtn");

    const sidebar =
        document.getElementById("sidebar");


    if (menuBtn && sidebar) {

        menuBtn.addEventListener(
            "click",
            function () {

                if (window.innerWidth <= 800) {

                    sidebar.classList.toggle("open");

                } else {

                    sidebar.classList.toggle("collapsed");
                }
            }
        );


        document.addEventListener(
            "click",
            function (event) {

                if (window.innerWidth > 800) {
                    return;
                }

                if (
                    sidebar.classList.contains("open") &&
                    !sidebar.contains(event.target) &&
                    !menuBtn.contains(event.target)
                ) {

                    sidebar.classList.remove("open");
                }
            }
        );


        window.addEventListener(
            "resize",
            function () {

                if (window.innerWidth > 800) {

                    sidebar.classList.remove("open");
                }
            }
        );
    }

});