$(document).ready(function () {

    /*
    ==========================================
    SIDEBAR
    ==========================================
    */

    const $sidebar = $("#sidebar");
    const $menuBtn = $("#menuBtn");


    /*
    Toggle Sidebar
    */

    $menuBtn.on("click", function (event) {

        event.stopPropagation();

        if (window.innerWidth > 800) {

            // Desktop: collapse / expand
            $sidebar.toggleClass("collapsed");

        } else {

            // Mobile: open / close
            $sidebar.toggleClass("open");

        }

    });


    /*
    Close mobile sidebar when clicking outside
    */

    $(document).on("click", function (event) {

        if (
            window.innerWidth <= 800 &&
            $sidebar.hasClass("open") &&
            !$(event.target).closest("#sidebar, #menuBtn").length
        ) {

            $sidebar.removeClass("open");

        }

    });


    /*
    ==========================================
    MOBILE NAVIGATION
    ==========================================
    */

    $(".nav-item, .logout-link").on("click", function () {

        if (window.innerWidth <= 800) {

            $sidebar.removeClass("open");

        }

    });


    /*
    ==========================================
    RESPONSIVE RESET
    ==========================================
    */

    $(window).on("resize", function () {

        if (window.innerWidth <= 800) {

            $sidebar.removeClass("collapsed");

        } else {

            $sidebar.removeClass("open");

        }

    });


    /*
    ==========================================
    WELCOME POPUP
    ==========================================
    */

    const $welcomeOverlay = $("#welcomeOverlay");
    const $closeWelcome = $("#closeWelcome");
    const $startExploring = $("#startExploring");


    function showWelcomePopup() {

        $welcomeOverlay.addClass("show");
        $welcomeOverlay.attr("aria-hidden", "false");

    }


    function closeWelcomePopup() {

        $welcomeOverlay.removeClass("show");
        $welcomeOverlay.attr("aria-hidden", "true");

    }


    /*
    Show popup when Home loads
    */

    setTimeout(function () {

        showWelcomePopup();

    }, 500);


    /*
    Close button
    */

    $closeWelcome.on("click", function () {

        closeWelcomePopup();

    });


    /*
    Start Exploring
    */

    $startExploring.on("click", function () {

        closeWelcomePopup();

    });


    /*
    Click outside modal
    */

    $welcomeOverlay.on("click", function (event) {

        if (event.target === this) {

            closeWelcomePopup();

        }

    });


    /*
    Escape key
    */

    $(document).on("keydown", function (event) {

        if (event.key === "Escape") {

            closeWelcomePopup();

        }

    });


    /*
    ==========================================
    SCROLL REVEAL
    ==========================================
    */

    const revealElements = $(
        ".quick-card, " +
        ".process-card, " +
        ".community-section, " +
        ".learn-section, " +
        ".final-cta"
    );


    revealElements.css({
        opacity: 0,
        transform: "translateY(18px)"
    });


    function revealOnScroll() {

        const windowBottom =
            $(window).scrollTop() +
            $(window).height();


        revealElements.each(function () {

            const $element = $(this);

            const elementTop =
                $element.offset().top;


            if (windowBottom > elementTop + 50) {

                $element.css({
                    opacity: 1,
                    transform: "translateY(0)",
                    transition:
                        "opacity 0.6s ease, transform 0.6s ease"
                });

            }

        });

    }


    $(window).on("scroll", revealOnScroll);

    revealOnScroll();

});