/* =========================================
   SCAMSHIELD — MY FEEDBACK
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    const ratingBars =
        document.querySelectorAll(".rating-fill");


    ratingBars.forEach(function (bar) {

        const rating =
            Number(bar.dataset.rating);


        if (
            !Number.isNaN(rating) &&
            rating >= 1 &&
            rating <= 5
        ) {

            const percentage =
                (rating / 5) * 100;


            setTimeout(function () {

                bar.style.width =
                    percentage + "%";

            }, 150);

        }

    });

});