/* =========================================================
   SCAMSHIELD — SCAM RESULT JS
========================================================= */


/* =========================================================
   SIDEBAR
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
   SCORE BAR ANIMATION
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const scoreBars = document.querySelectorAll(".score-fill");

    scoreBars.forEach(function (bar) {

        const score = Number(bar.dataset.score || 0);

        setTimeout(function () {

            bar.style.width = Math.min(Math.max(score, 0), 100) + "%";

        }, 150);

    });

});


/* =========================================================
   CLOSE MOBILE SIDEBAR AFTER NAVIGATION
========================================================= */

const navItems = document.querySelectorAll(".nav-item");

navItems.forEach(function (item) {

    item.addEventListener("click", function () {

        if (window.innerWidth <= 800 && sidebar) {
            sidebar.classList.remove("open");
        }

    });

});


/* =========================================================
   ESC KEY CLOSES MOBILE SIDEBAR
========================================================= */

document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {

        if (sidebar && window.innerWidth <= 800) {
            sidebar.classList.remove("open");
        }

    }

});