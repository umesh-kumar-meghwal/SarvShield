/* =========================================================
   SCAMSHIELD AI — SCAM CHECK
   FINAL JAVASCRIPT
   Works with Flask /scamcheck API
   Matches final ScamShield CSS
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       ELEMENTS
       ===================================================== */

    const sidebar = document.getElementById("sidebar");
    const menuBtn = document.getElementById("menuBtn");

    const form = document.getElementById("scamCheckForm");
    const checkBtn = document.getElementById("checkBtn");

    const senderInput = document.getElementById("sender");
    const urlInput = document.getElementById("url");
    const messageInput = document.getElementById("message");
    const fileInput = document.getElementById("screenshot");

    const loadingSection =
        document.getElementById("analysisLoading");

    let analysisResult =
        document.getElementById("analysisResult");


    /* =====================================================
       SIDEBAR
       ===================================================== */

    if (menuBtn && sidebar) {

        menuBtn.addEventListener("click", () => {

            if (window.innerWidth <= 800) {
                sidebar.classList.toggle("open");
            } else {
                sidebar.classList.toggle("collapsed");
            }

        });

    }


    document.addEventListener("click", (event) => {

        if (!sidebar || !menuBtn) return;

        if (window.innerWidth > 800) return;

        if (
            sidebar.classList.contains("open") &&
            !sidebar.contains(event.target) &&
            !menuBtn.contains(event.target)
        ) {
            sidebar.classList.remove("open");
        }

    });


    /* =====================================================
       FILE UPLOAD
       ===================================================== */

    if (fileInput) {

        fileInput.addEventListener("change", () => {

            const file = fileInput.files[0];

            const title =
                document.querySelector(".file-upload-title");

            const subtitle =
                document.querySelector(".file-upload-subtitle");

            if (!file) {

                if (title) {
                    title.textContent =
                        "Upload a screenshot";
                }

                if (subtitle) {
                    subtitle.textContent =
                        "PNG, JPG or WEBP";
                }

                return;
            }

            if (title) {
                title.textContent = file.name;
            }

            if (subtitle) {

                const size =
                    (file.size / (1024 * 1024)).toFixed(2);

                subtitle.textContent =
                    `${size} MB • Ready for analysis`;

            }

        });

    }


    /* =====================================================
       FORM SUBMIT
       ===================================================== */

    if (form) {

        form.addEventListener("submit", async (event) => {

            event.preventDefault();

            if (!validateInput()) return;

            await runAnalysis();

        });

    }


    /* =====================================================
       VALIDATION
       ===================================================== */

    function validateInput() {

        const sender =
            senderInput
                ? senderInput.value.trim()
                : "";

        const url =
            urlInput
                ? urlInput.value.trim()
                : "";

        const message =
            messageInput
                ? messageInput.value.trim()
                : "";

        const hasFile =
            fileInput &&
            fileInput.files &&
            fileInput.files.length > 0;

        if (
            !sender &&
            !url &&
            !message &&
            !hasFile
        ) {

            showError(
                "Please enter a message, phone number, suspicious link, or upload a screenshot."
            );

            return false;
        }

        return true;

    }


    /* =====================================================
       MESSAGES
       ===================================================== */

    function showError(message) {

        removeMessages();

        const error =
            document.createElement("div");

        error.className = "error-banner";

        error.innerHTML = `
            <span>!</span>
            <span>${escapeHTML(message)}</span>
        `;

        insertMessage(error);

        setTimeout(() => {

            error.style.opacity = "0";

            setTimeout(() => {
                if (error.parentNode) {
                    error.remove();
                }
            }, 300);

        }, 4000);

    }


    function showSuccess(message) {

        removeMessages();

        const success =
            document.createElement("div");

        success.className = "success-banner";

        success.innerHTML = `
            <span>✓</span>
            <span>${escapeHTML(message)}</span>
        `;

        insertMessage(success);

    }


    function insertMessage(element) {

        const inputCard =
            document.querySelector(".scam-input-card");

        if (
            inputCard &&
            inputCard.parentNode
        ) {

            inputCard.parentNode.insertBefore(
                element,
                inputCard
            );

        }

    }


    function removeMessages() {

        document
            .querySelectorAll(
                ".success-banner, .error-banner"
            )
            .forEach(element => element.remove());

    }


    /* =====================================================
       RUN ANALYSIS
       ===================================================== */

    async function runAnalysis() {

        setButtonLoading(true);

        removeMessages();
        hideResult();
        showLoading();

        try {

            const formData = new FormData();


            /* Sender / Phone */

            if (senderInput) {

                const sender =
                    senderInput.value.trim();

                formData.append(
                    "sender",
                    sender
                );

                formData.append(
                    "phone",
                    sender
                );

            }


            /* URL */

            if (urlInput) {

                formData.append(
                    "url",
                    urlInput.value.trim()
                );

            }


            /* Message */

            if (messageInput) {

                formData.append(
                    "message",
                    messageInput.value.trim()
                );

            }


            /* Screenshot */

            if (
                fileInput &&
                fileInput.files &&
                fileInput.files.length > 0
            ) {

                formData.append(
                    "screenshot",
                    fileInput.files[0]
                );

            }


            /* Flask API */

            const response =
                await fetch("/scamcheck", {
                    method: "POST",
                    body: formData
                });


            if (!response.ok) {

                throw new Error(
                    `Server returned ${response.status}`
                );

            }


            const data =
                await response.json();

            console.log(
                "ScamShield API Response:",
                data
            );


            hideLoading();

            displayResult(data);

        }
        catch (error) {

            console.error(
                "ScamShield analysis error:",
                error
            );

            hideLoading();

            showError(
                "Unable to complete the analysis. Please make sure the Flask server is running."
            );

        }
        finally {

            setButtonLoading(false);

        }

    }


    /* =====================================================
       LOADING
       ===================================================== */

    function showLoading() {

        if (!loadingSection) return;

        loadingSection.hidden = false;
        loadingSection.style.display = "block";

        loadingSection.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

    }


    function hideLoading() {

        if (!loadingSection) return;

        loadingSection.hidden = true;
        loadingSection.style.display = "none";

    }


    /* =====================================================
       CREATE RESULT SECTION
       ===================================================== */

    function createResultSection() {

        if (analysisResult) {
            return analysisResult;
        }

        analysisResult =
            document.createElement("section");

        analysisResult.id =
            "analysisResult";

        analysisResult.className =
            "analysis-result";

        analysisResult.style.display =
            "none";

        if (
            loadingSection &&
            loadingSection.parentNode
        ) {

            loadingSection.parentNode.insertBefore(
                analysisResult,
                loadingSection.nextSibling
            );

        }
        else {

            const inputCard =
                document.querySelector(
                    ".scam-input-card"
                );

            if (
                inputCard &&
                inputCard.parentNode
            ) {

                inputCard.parentNode.appendChild(
                    analysisResult
                );

            }

        }

        return analysisResult;

    }


    /* =====================================================
       DISPLAY RESULT
       ===================================================== */

    function displayResult(data) {

        const section =
            createResultSection();

        if (!section) return;


        const score =
            clamp(
                data.final_score ??
                data.risk_score ??
                data.score ??
                0
            );


        const verdict =
            data.verdict ??
            "ANALYSIS COMPLETE";


        const messageScore =
            clamp(data.message_score ?? 0);

        const phoneScore =
            clamp(data.phone_score ?? 0);

        const linkScore =
            clamp(data.link_score ?? 0);

        const screenshotScore =
            clamp(data.screenshot_score ?? 0);


        const fingerprints =
            Array.isArray(data.scam_fingerprint)
                ? data.scam_fingerprint
                : [];


        const attackChain =
            Array.isArray(data.attack_chain)
                ? data.attack_chain
                : [];


        const evidence =
            Array.isArray(data.evidence)
                ? data.evidence
                : [];


        const safeNext =
            Array.isArray(data.safe_next)
                ? data.safe_next
                : [];


        const signalContribution =
            data.signal_contribution ?? {};


        const urgency =
            data.urgency ?? {};


        const whatIf =
            data.what_if ?? {};


        section.innerHTML = `

            <!-- RISK HERO -->

            <div class="risk-hero reveal visible">

                <div class="risk-gauge-wrapper">

                    <div
                        class="risk-gauge animated"
                        data-score="${score}"
                    >

                        <svg viewBox="0 0 200 200">

                            <circle
                                class="gauge-track"
                                cx="100"
                                cy="100"
                                r="90"
                            />

                            <circle
                                id="gaugeProgress"
                                class="gauge-progress"
                                cx="100"
                                cy="100"
                                r="90"
                            />

                        </svg>

                        <div class="gauge-center">

                            <div class="gauge-score">

                                <span id="riskScore">
                                    0
                                </span>

                                <span>/100</span>

                            </div>

                            <div class="gauge-label">
                                Risk Score
                            </div>

                        </div>

                    </div>

                </div>


                <div class="risk-details">

                    <div class="risk-eyebrow">
                        Analysis Complete
                    </div>

                    <h2>
                        ${escapeHTML(verdict)}
                    </h2>

                    <div class="risk-verdict">
                        ${escapeHTML(
                            data.message_verdict ??
                            data.phone_reputation ??
                            "Risk assessment completed"
                        )}
                    </div>

                    <p class="risk-description">
                        ${escapeHTML(
                            data.why ??
                            "ScamShield analyzed multiple signals to determine the potential risk of this content."
                        )}
                    </p>

                </div>

            </div>


            <!-- DETECTOR GRID -->

            <div class="detector-grid reveal visible">

                ${createDetectorCard(
                    "T",
                    "Text Analysis",
                    messageScore
                )}

                ${createDetectorCard(
                    "U",
                    "URL Analysis",
                    linkScore
                )}

                ${createDetectorCard(
                    "S",
                    "Sender Analysis",
                    phoneScore
                )}

                ${createDetectorCard(
                    "I",
                    "Image Analysis",
                    screenshotScore
                )}

            </div>


            <!-- FINGERPRINT -->

            <section class="analysis-card fingerprint-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            Scam Fingerprint
                        </div>

                        <div class="analysis-card-description">
                            Detected patterns associated with known scam behavior.
                        </div>

                    </div>

                </div>

                <div class="fingerprint-grid">

                    ${
                        fingerprints.length
                            ? fingerprints.map(item => `
                                <span class="fingerprint-badge">
                                    ✓ ${escapeHTML(item)}
                                </span>
                            `).join("")
                            : `
                                <span class="fingerprint-badge">
                                    No specific fingerprint detected
                                </span>
                            `
                    }

                </div>

            </section>


            <!-- ATTACK CHAIN -->

            <section class="analysis-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            Attack Chain
                        </div>

                        <div class="analysis-card-description">
                            How the suspicious interaction may attempt to manipulate the target.
                        </div>

                    </div>

                </div>

                <div class="attack-chain">

                    ${
                        attackChain.length
                            ? attackChain.map((step, index) => `
                                <div class="attack-step">

                                    <div class="attack-number">
                                        ${index + 1}
                                    </div>

                                    <div class="attack-text">
                                        ${escapeHTML(step)}
                                    </div>

                                </div>
                            `).join("")
                            : `
                                <div class="attack-step">

                                    <div class="attack-number">
                                        1
                                    </div>

                                    <div class="attack-text">
                                        No attack chain information available.
                                    </div>

                                </div>
                            `
                    }

                </div>

            </section>


            <!-- URGENCY -->

            <section class="analysis-card urgency-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            Urgency &amp; Pressure Analysis
                        </div>

                        <div class="analysis-card-description">
                            Identifies language designed to make you act quickly.
                        </div>

                    </div>

                </div>

                <div class="urgency-level">
                    ${escapeHTML(
                        urgency.level ?? "LOW"
                    )}
                </div>

                <div class="urgency-text">
                    ${escapeHTML(
                        urgency.detected ??
                        "No additional urgency analysis is available."
                    )}
                </div>

            </section>


            <!-- EVIDENCE -->

            <section class="analysis-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            Evidence
                        </div>

                        <div class="analysis-card-description">
                            Signals that contributed to this assessment.
                        </div>

                    </div>

                </div>

                <ul class="evidence-list">

                    ${
                        evidence.length
                            ? evidence.map(item => `
                                <li class="evidence-item">
                                    ${escapeHTML(item)}
                                </li>
                            `).join("")
                            : `
                                <li class="evidence-item">
                                    No additional evidence available.
                                </li>
                            `
                    }

                </ul>

            </section>


            <!-- WHY FLAGGED -->

            <section class="analysis-card why-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            Why ScamShield Flagged This
                        </div>

                        <div class="analysis-card-description">
                            A simplified explanation of the risk assessment.
                        </div>

                    </div>

                </div>

                <div class="why-content">

                    ${escapeHTML(
                        data.why ??
                        "Multiple risk indicators were detected."
                    )}

                </div>

            </section>


            <!-- SIGNAL CONTRIBUTION -->

            <section class="analysis-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            Signal Contribution
                        </div>

                        <div class="analysis-card-description">
                            Relative contribution of detected risk signals.
                        </div>

                    </div>

                </div>

                <div class="signal-list">

                    ${
                        Object.entries(signalContribution)
                            .map(([name, value]) => {

                                const safeValue =
                                    clamp(value);

                                return `

                                    <div class="signal-row">

                                        <div class="signal-name">
                                            ${escapeHTML(name)}
                                        </div>

                                        <div class="signal-track">

                                            <div
                                                class="signal-fill"
                                                data-score="${safeValue}"
                                                style="width: 0%"
                                            ></div>

                                        </div>

                                        <div class="signal-value">
                                            ${Math.round(safeValue)}%
                                        </div>

                                    </div>

                                `;

                            })
                            .join("")
                    }

                </div>

            </section>


            <!-- SAFE NEXT -->

            <section class="analysis-card safenext-card reveal visible">

                <div class="safenext-header">

                    <div class="safenext-icon">
                        ✓
                    </div>

                    <div>

                        <div class="safenext-title">
                            Safe Next
                        </div>

                        <div class="safenext-subtitle">
                            Recommended actions to stay protected.
                        </div>

                    </div>

                </div>


                <div class="recommended-action">

                    ${escapeHTML(
                        data.recommended_action ??
                        "Do not interact with the suspicious content."
                    )}

                </div>


                <ul class="safe-list">

                    ${
                        safeNext.length
                            ? safeNext.map(step => `
                                <li>
                                    ${escapeHTML(step)}
                                </li>
                            `).join("")
                            : `
                                <li>
                                    Do not click suspicious links.
                                </li>

                                <li>
                                    Never share OTPs or passwords.
                                </li>
                            `
                    }

                </ul>


                <div class="recovery-section">

                    <div class="recovery-title">
                        If you already interacted with the message
                    </div>

                    <div class="helpline-list">

                        <div class="helpline-item">
                            Contact your bank immediately if money was transferred.
                        </div>

                        <div class="helpline-item">
                            Secure affected accounts and change compromised passwords.
                        </div>

                    </div>

                </div>

            </section>


            <!-- WHAT IF -->

            <section class="analysis-card what-if-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            What-If Simulator
                        </div>

                        <div class="analysis-card-description">
                            See how different signals may affect the overall risk.
                        </div>

                    </div>

                </div>


                <div class="what-if-grid">

                    ${createWhatIf(
                        "Current Risk",
                        whatIf.current ?? score
                    )}

                    ${createWhatIf(
                        "Without URL Signal",
                        whatIf.without_link
                    )}

                    ${createWhatIf(
                        "Without Text Signal",
                        whatIf.without_message
                    )}

                    ${createWhatIf(
                        "Without Sender Signal",
                        whatIf.without_phone
                    )}

                </div>

            </section>


            <!-- DETECTION DETAILS -->

            <section class="analysis-card reveal visible">

                <div class="analysis-card-header">

                    <div>

                        <div class="analysis-card-title">
                            Detection Details
                        </div>

                        <div class="analysis-card-description">
                            Additional signals detected during analysis.
                        </div>

                    </div>

                </div>

                <ul class="evidence-list">

                    <li class="evidence-item">
                        Message verdict:
                        ${escapeHTML(
                            data.message_verdict ?? "N/A"
                        )}
                    </li>

                    <li class="evidence-item">
                        Phone reputation:
                        ${escapeHTML(
                            data.phone_reputation ?? "N/A"
                        )}
                    </li>

                    <li class="evidence-item">
                        Phone reports:
                        ${escapeHTML(
                            data.phone_report_count ?? "0"
                        )}
                    </li>

                    <li class="evidence-item">
                        Link verdict:
                        ${escapeHTML(
                            data.link_verdict ?? "N/A"
                        )}
                    </li>

                    <li class="evidence-item">
                        Link domain:
                        ${escapeHTML(
                            data.link_domain ?? "N/A"
                        )}
                    </li>

                    <li class="evidence-item">
                        Screenshot verdict:
                        ${escapeHTML(
                            data.screenshot_verdict ?? "N/A"
                        )}
                    </li>

                </ul>

            </section>


            <!-- REPORT -->

            <div class="report-actions reveal visible">

                <a
                    href="/report-phone"
                    class="secondary-btn"
                >
                    ⚑ Report This Scam
                </a>

            </div>

        `;


        section.style.display = "block";
        section.hidden = false;


        animateGauge(score);
        animateBars(section);


        requestAnimationFrame(() => {

            section.style.opacity = "0";
            section.style.transform =
                "translateY(25px)";

            requestAnimationFrame(() => {

                section.style.transition =
                    "opacity 0.7s ease, transform 0.7s ease";

                section.style.opacity = "1";
                section.style.transform =
                    "translateY(0)";

            });

        });


        setTimeout(() => {

            section.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }, 200);

    }


    /* =====================================================
       DETECTOR CARD
       ===================================================== */

    function createDetectorCard(
        icon,
        name,
        score
    ) {

        const safeScore =
            clamp(score);

        return `

            <div class="detector-card">

                <div class="detector-header">

                    <div class="detector-name">

                        <div class="detector-icon">
                            ${escapeHTML(icon)}
                        </div>

                        ${escapeHTML(name)}

                    </div>

                    <div class="detector-score">

                        ${Math.round(safeScore)}

                        <span>%</span>

                    </div>

                </div>


                <div class="detector-meta">

                    <span>
                        Threat probability
                    </span>

                    <span>
                        ${Math.round(safeScore)}%
                    </span>

                </div>


                <div class="detector-bar">

                    <div
                        class="detector-bar-fill"
                        data-score="${safeScore}"
                        style="width: 0%"
                    ></div>

                </div>

            </div>

        `;

    }


    /* =====================================================
       WHAT-IF CARD
       ===================================================== */

    function createWhatIf(label, value) {

        const exists =
            value !== undefined &&
            value !== null &&
            value !== "" &&
            !Number.isNaN(Number(value));

        return `

            <div class="what-if-item">

                <div class="what-if-label">
                    ${escapeHTML(label)}
                </div>

                <div class="what-if-score">

                    ${
                        exists
                            ? Math.round(
                                clamp(Number(value))
                            )
                            : "--"
                    }

                    ${
                        exists
                            ? "<span>/100</span>"
                            : ""
                    }

                </div>

            </div>

        `;

    }


    /* =====================================================
       GAUGE ANIMATION
       ===================================================== */

    function animateGauge(score) {

        const progress =
            document.getElementById(
                "gaugeProgress"
            );

        const scoreElement =
            document.getElementById(
                "riskScore"
            );

        if (!progress) return;


        const circumference =
            2 * Math.PI * 90;


        progress.style.strokeDasharray =
            circumference;

        progress.style.strokeDashoffset =
            circumference;


        const finalScore =
            clamp(score);

        const duration = 1200;

        const start =
            performance.now();


        function animate(time) {

            const elapsed =
                time - start;

            const progressTime =
                Math.min(
                    elapsed / duration,
                    1
                );


            const eased =
                1 -
                Math.pow(
                    1 - progressTime,
                    3
                );


            const current =
                finalScore * eased;


            progress.style.strokeDashoffset =
                circumference -
                (current / 100) *
                circumference;


            if (scoreElement) {

                scoreElement.textContent =
                    Math.round(current);

            }


            if (progressTime < 1) {

                requestAnimationFrame(
                    animate
                );

            }

        }


        if (scoreElement) {
            scoreElement.textContent = "0";
        }

        requestAnimationFrame(animate);

    }


    /* =====================================================
       BAR ANIMATION
       ===================================================== */

    function animateBars(section) {

        if (!section) return;

        const bars =
            section.querySelectorAll(
                "[data-score]"
            );


        bars.forEach((bar, index) => {

            const score =
                clamp(
                    Number(
                        bar.dataset.score ?? 0
                    )
                );


            setTimeout(() => {

                requestAnimationFrame(() => {

                    bar.style.width =
                        `${score}%`;

                });

            }, 100 + index * 80);

        });

    }


    /* =====================================================
       HIDE RESULT
       ===================================================== */

    function hideResult() {

        if (!analysisResult) return;

        analysisResult.style.display =
            "none";

        analysisResult.hidden =
            true;

    }


    /* =====================================================
       BUTTON LOADING
       ===================================================== */

    function setButtonLoading(isLoading) {

        if (!checkBtn) return;


        if (isLoading) {

            if (
                !checkBtn.dataset.originalHTML
            ) {

                checkBtn.dataset.originalHTML =
                    checkBtn.innerHTML;

            }

            checkBtn.disabled = true;

            checkBtn.innerHTML = `

                <span class="check-btn-icon">
                    ⟳
                </span>

                <span class="check-btn-text">
                    Analyzing...
                </span>

            `;

        }
        else {

            checkBtn.disabled = false;

            if (
                checkBtn.dataset.originalHTML
            ) {

                checkBtn.innerHTML =
                    checkBtn.dataset.originalHTML;

            }

        }

    }


    /* =====================================================
       SCROLL REVEAL
       ===================================================== */

    function setupReveal() {

        const elements =
            document.querySelectorAll(
                ".reveal"
            );


        if (
            "IntersectionObserver" in window
        ) {

            const observer =
                new IntersectionObserver(
                    entries => {

                        entries.forEach(entry => {

                            if (
                                entry.isIntersecting
                            ) {

                                entry.target
                                    .classList
                                    .add("visible");

                                observer.unobserve(
                                    entry.target
                                );

                            }

                        });

                    },
                    {
                        threshold: 0.12
                    }
                );


            elements.forEach(element => {
                observer.observe(element);
            });

        }
        else {

            elements.forEach(element => {
                element.classList.add("visible");
            });

        }

    }


    /* =====================================================
       UTILITY
       ===================================================== */

    function clamp(value) {

        const number =
            Number(value);

        if (
            Number.isNaN(number) ||
            !Number.isFinite(number)
        ) {
            return 0;
        }

        return Math.max(
            0,
            Math.min(
                100,
                number
            )
        );

    }


    function escapeHTML(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    /* =====================================================
       RESPONSIVE SIDEBAR
       ===================================================== */

    window.addEventListener(
        "resize",
        () => {

            if (!sidebar) return;

            if (window.innerWidth > 800) {

                sidebar.classList.remove("open");

            }

        }
    );


    /* =====================================================
       INITIAL STATE
       ===================================================== */

    hideLoading();

    setupReveal();

});