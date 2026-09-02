document.addEventListener("DOMContentLoaded", function () {

    const menuBtn = document.getElementById("menuBtn");
    const sidebar = document.getElementById("sidebar");

    if (!menuBtn || !sidebar) {
        return;
    }


    menuBtn.addEventListener("click", function () {

        if (window.innerWidth <= 800) {

            sidebar.classList.toggle("open");

        } else {

            sidebar.classList.toggle("collapsed");

        }

    });


    /*
     * Mobile par sidebar ke bahar click karne par
     * sidebar close ho jayega.
     */

    document.addEventListener("click", function (event) {

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

    });


    /*
     * Screen resize hone par classes reset
     */

    window.addEventListener("resize", function () {

        if (window.innerWidth > 800) {

            sidebar.classList.remove("open");

        }

    });

});