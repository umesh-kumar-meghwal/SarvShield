/**
 * ScamShield AI - Landing Page Script
 * File: static/index.js
 *
 * Handles:
 * 1. Smooth scroll-reveal animations
 * 2. FAQ accordion
 * 3. Dynamic navbar on scroll
 * 4. Hero background parallax
 * 5. Smooth navigation scrolling
 * 6. Metric/progress animations
 * 7. Feature card reveal animations
 */

document.addEventListener('DOMContentLoaded', () => {
    initScrollReveals();
    initAccordion();
    initNavbarScroll();
    initHeroParallax();
    initSmoothScroll();
    initMetricBars();
});


/* =========================================================
   1. SCROLL REVEAL ANIMATIONS
   ========================================================= */

function initScrollReveals() {

    const revealElements = document.querySelectorAll('.reveal-on-scroll');

    if (!revealElements.length) return;

    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -80px 0px',
        threshold: 0.12
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {

        entries.forEach(entry => {

            if (entry.isIntersecting) {

                entry.target.classList.add('is-visible');

                // Run only once for better performance
                observer.unobserve(entry.target);
            }

        });

    }, observerOptions);


    revealElements.forEach(element => {
        revealObserver.observe(element);
    });
}


/* =========================================================
   2. FAQ ACCORDION
   ========================================================= */

function initAccordion() {

    const accordionHeaders =
        document.querySelectorAll('.accordion-header');

    if (!accordionHeaders.length) return;


    accordionHeaders.forEach(header => {

        header.addEventListener('click', () => {

            const currentItem = header.closest('.accordion-item');

            if (!currentItem) return;

            const isAlreadyOpen =
                currentItem.classList.contains('active');


            // Close every other FAQ item
            document.querySelectorAll('.accordion-item').forEach(item => {
                item.classList.remove('active');
            });


            // Open clicked item if it was previously closed
            if (!isAlreadyOpen) {
                currentItem.classList.add('active');
            }

        });

    });
}


/* =========================================================
   3. NAVBAR SCROLL EFFECT
   ========================================================= */

function initNavbarScroll() {

    const navbar = document.querySelector('.navbar');

    if (!navbar) return;


    function updateNavbar() {

        if (window.scrollY > 40) {

            navbar.classList.add('navbar-scrolled');

        } else {

            navbar.classList.remove('navbar-scrolled');

        }

    }


    window.addEventListener('scroll', updateNavbar, {
        passive: true
    });


    // Run once when page loads
    updateNavbar();
}


/* =========================================================
   4. HERO BACKGROUND PARALLAX
   ========================================================= */

function initHeroParallax() {

    const heroSection = document.getElementById('hero');

    const shape1 = document.querySelector('.shape-1');
    const shape2 = document.querySelector('.shape-2');


    if (!heroSection || !shape1 || !shape2) return;


    // Disable mouse parallax on touch/mobile devices
    if (window.matchMedia('(pointer: coarse)').matches) {
        return;
    }


    heroSection.addEventListener('mousemove', (event) => {

        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;


        const moveX = event.clientX - centerX;
        const moveY = event.clientY - centerY;


        const shape1X = moveX * 0.018;
        const shape1Y = moveY * 0.018;

        const shape2X = moveX * -0.012;
        const shape2Y = moveY * -0.012;


        shape1.style.transform =
            `translate3d(${shape1X}px, ${shape1Y}px, 0)`;

        shape2.style.transform =
            `translate3d(${shape2X}px, ${shape2Y}px, 0)`;

    });


    // Smoothly return shapes when mouse leaves hero
    heroSection.addEventListener('mouseleave', () => {

        shape1.style.transform = 'translate3d(0, 0, 0)';
        shape2.style.transform = 'translate3d(0, 0, 0)';

    });

}


/* =========================================================
   5. SMOOTH INTERNAL NAVIGATION
   ========================================================= */

function initSmoothScroll() {

    const navigationLinks =
        document.querySelectorAll('a[href^="#"]');

    if (!navigationLinks.length) return;


    navigationLinks.forEach(link => {

        link.addEventListener('click', (event) => {

            const targetId =
                link.getAttribute('href');


            // Ignore empty "#"
            if (!targetId || targetId === '#') {
                return;
            }


            const targetElement =
                document.querySelector(targetId);


            if (!targetElement) return;


            event.preventDefault();


            const navbar =
                document.querySelector('.navbar');

            const navbarHeight =
                navbar ? navbar.offsetHeight : 80;


            const targetPosition =
                targetElement.getBoundingClientRect().top +
                window.scrollY -
                navbarHeight;


            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });

        });

    });

}


/* =========================================================
   6. METRIC / PROGRESS BAR ANIMATION
   ========================================================= */

function initMetricBars() {

    const progressBars =
        document.querySelectorAll('.progress-fill');

    if (!progressBars.length) return;


    const progressObserver =
        new IntersectionObserver((entries, observer) => {

            entries.forEach(entry => {

                if (!entry.isIntersecting) return;


                const bar = entry.target;

                /*
                 * The width is already defined by CSS.
                 * We temporarily hide it and animate it
                 * when the element enters the viewport.
                 */

                const finalWidth =
                    getComputedStyle(bar).width;


                bar.style.width = '0';


                requestAnimationFrame(() => {

                    bar.style.transition =
                        'width 1.5s cubic-bezier(0.16, 1, 0.3, 1)';

                    bar.style.width = finalWidth;

                });


                observer.unobserve(bar);

            });

        }, {
            threshold: 0.3
        });


    progressBars.forEach(bar => {
        progressObserver.observe(bar);
    });

}


/* =========================================================
   7. ACCESSIBILITY: REDUCED MOTION
   ========================================================= */

function initReducedMotionSupport() {

    const prefersReducedMotion =
        window.matchMedia('(prefers-reduced-motion: reduce)');

    if (!prefersReducedMotion.matches) return;


    document.documentElement.classList.add('reduce-motion');

}


initReducedMotionSupport();