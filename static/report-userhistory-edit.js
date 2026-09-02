/* =========================================================
   SCAMSHIELD — EDIT REPORT JAVASCRIPT
   ========================================================= */


/* =========================================================
   SIDEBAR TOGGLE
   ========================================================= */

const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");

if (menuBtn && sidebar) {

    menuBtn.addEventListener("click", function () {

        if (window.innerWidth <= 800) {

            sidebar.classList.toggle("open");

        } else {

            sidebar.classList.toggle("collapsed");

        }

    });

}


/* =========================================================
   EDIT REPORT FORM
   ========================================================= */

const editReportForm =
    document.getElementById("editReportForm");

const updateBtn =
    document.getElementById("updateBtn");

const updateResponse =
    document.getElementById("updateResponse");


if (editReportForm) {

    editReportForm.addEventListener("submit", async function (event) {

        event.preventDefault();


        const phone =
            document.getElementById("phone").value.trim();

        const link =
            document.getElementById("link").value.trim();

        const reason =
            document.getElementById("reason").value.trim();


        /* At least phone OR link */

        if (!phone && !link) {

            updateResponse.textContent =
                "Please enter at least a Phone Number or a Link.";

            return;

        }


        /* Reason required */

        if (!reason) {

            updateResponse.textContent =
                "Please enter a reason for reporting.";

            return;

        }


        updateBtn.disabled = true;

        updateBtn.textContent = "Updating...";

        updateResponse.textContent =
            "Updating your report...";


        try {

            const formData = new FormData();

            formData.append("phone", phone);

            formData.append("link", link);

            formData.append("reason", reason);


            const response = await fetch(
                window.location.pathname,
                {
                    method: "POST",
                    body: formData
                }
            );


            const data = await response.json();


            updateResponse.textContent =
                data.message ||
                "Report updated successfully.";


            if (data.success) {

                setTimeout(function () {

                    window.location.href =
                        "/report-history";

                }, 1000);

            }


        } catch (error) {

            updateResponse.textContent =
                "Something went wrong. Please try again.";

        } finally {

            updateBtn.disabled = false;

            updateBtn.textContent =
                "Update Report";

        }

    });

}


/* =========================================================
   BACK TO HISTORY
   ========================================================= */

const backBtn =
    document.getElementById("backBtn");

if (backBtn) {

    backBtn.addEventListener("click", function () {

        window.location.href =
            "/report-history";

    });

}