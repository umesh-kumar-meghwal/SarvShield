/* =========================================================
   SCAMSHIELD — SCAN HISTORY JAVASCRIPT
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