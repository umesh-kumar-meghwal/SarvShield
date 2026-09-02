$(document).ready(function () {

    /* =========================================
       SIDEBAR
       ========================================= */

    const $sidebar = $("#sidebar");
    const $menuBtn = $("#menuBtn");


    /* =========================================
       TOGGLE SIDEBAR
       ========================================= */

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


    /* =========================================
       CLOSE MOBILE SIDEBAR
       WHEN CLICKING OUTSIDE
       ========================================= */

    $(document).on("click", function (event) {

        if (
            window.innerWidth <= 800 &&
            $sidebar.hasClass("open") &&
            !$(event.target).closest("#sidebar, #menuBtn").length
        ) {

            $sidebar.removeClass("open");

        }

    });


    /* =========================================
       MOBILE NAVIGATION
       ========================================= */

    $(".nav-item, .logout-link").on("click", function () {

        if (window.innerWidth <= 800) {

            $sidebar.removeClass("open");

        }

    });


    /* =========================================
       RESPONSIVE RESET
       ========================================= */

    $(window).on("resize", function () {

        if (window.innerWidth <= 800) {

            $sidebar.removeClass("collapsed");

        } else {

            $sidebar.removeClass("open");

        }

    });


    /* =========================================
       HISTORY CARD ANIMATION
       ========================================= */

    const $historyCards = $(".history-card");


    $historyCards.css({
        opacity: 0,
        transform: "translateY(20px)"
    });


    function revealHistoryCards() {

        const windowBottom =
            $(window).scrollTop() +
            $(window).height();


        $historyCards.each(function () {

            const $card = $(this);

            const cardTop =
                $card.offset().top;


            if (windowBottom > cardTop + 40) {

                $card.css({
                    opacity: 1,
                    transform: "translateY(0)",
                    transition:
                        "opacity 0.6s ease, transform 0.6s ease"
                });

            }

        });

    }


    /* =========================================
       SCROLL REVEAL
       ========================================= */

    $(window).on("scroll", revealHistoryCards);

    revealHistoryCards();


    /* =========================================
       HISTORY CARD CLICK FEEDBACK
       ========================================= */

    $(".history-card").on("click", function () {

        $(this).addClass("card-opening");

    });


    /* =========================================
       ESCAPE KEY
       CLOSE MOBILE SIDEBAR
       ========================================= */

    $(document).on("keydown", function (event) {

        if (
            event.key === "Escape" &&
            window.innerWidth <= 800
        ) {

            $sidebar.removeClass("open");

        }

    });

});