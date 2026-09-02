/* =========================================================
   SCAMSHIELD — REPORT HISTORY JAVASCRIPT
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
   EDIT REPORT
   ========================================================= */

function editReport(id) {

    window.location.href =
        "/report-userhistory-edit/" + id;

}

/* =========================================================
   DELETE REPORT
   ========================================================= */

let reportToDelete = null;

function deleteReport(id) {

    // Store the report ID
    reportToDelete = id;

    // Open custom delete modal
    const modal = document.getElementById("deleteModal");

    if (modal) {
        modal.classList.add("show");
    }
}


/* =========================================================
   CANCEL DELETE
   ========================================================= */

document
    .getElementById("cancelDeleteBtn")
    ?.addEventListener("click", function () {

        reportToDelete = null;

        const modal = document.getElementById("deleteModal");

        if (modal) {
            modal.classList.remove("show");
        }

    });


/* =========================================================
   CONFIRM DELETE
   ========================================================= */

document
    .getElementById("confirmDeleteBtn")
    ?.addEventListener("click", function () {

        if (!reportToDelete) {
            return;
        }

        const id = reportToDelete;

        const modal = document.getElementById("deleteModal");

        // Close modal immediately
        if (modal) {
            modal.classList.remove("show");
        }


        $.ajax({

            url: "/report-userhistory-delete/" + id,

            type: "POST",

            success: function (response) {

                if (response.success) {

                    $("#report-" + id).fadeOut(250, function () {

                        $(this).remove();

                    });


                    $("#reportResponse").html(
                        "<p>" +
                        (response.message ||
                        "Report deleted successfully.") +
                        "</p>"
                    );

                } else {

                    $("#reportResponse").html(
                        "<p>" +
                        (response.message ||
                        "Unable to delete the report.") +
                        "</p>"
                    );

                }

            },


            error: function (xhr) {

                let message =
                    "Something went wrong.";

                if (xhr.responseJSON) {

                    message =
                        xhr.responseJSON.message ||
                        message;

                }


                $("#reportResponse").html(
                    "<p>" +
                    message +
                    "</p>"
                );

            }

        });


        reportToDelete = null;

    });  
