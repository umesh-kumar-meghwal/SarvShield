/**
 * SarvShield AI - Landing Page Script
 * File: static/index.js
 */

document.addEventListener('DOMContentLoaded', () => {
    initMobileNav();
    initScrollReveals();
    initAccordion();
    initNavbarScroll();
    initHeroParallax();
    initSmoothScroll();
});

/* =========================================================
   1. MOBILE NAVBAR TOGGLE
   ========================================================= */
function initMobileNav() {
    const navBtn = document.getElementById('navToggleBtn');
    const navMenu = document.getElementById('navLinksMenu');

    if (!navBtn || !navMenu) return;

    navBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navMenu.classList.toggle('active');
        const icon = navBtn.querySelector('i');
        if (icon) {
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-xmark');
        }
    });

    // Close when clicking any nav link
    navMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
            const icon = navBtn.querySelector('i');
            if (icon) {
                icon.classList.add('fa-bars');
                icon.classList.remove('fa-xmark');
            }
        });
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!navMenu.contains(e.target) && !navBtn.contains(e.target)) {
            navMenu.classList.remove('active');
            const icon = navBtn.querySelector('i');
            if (icon) {
                icon.classList.add('fa-bars');
                icon.classList.remove('fa-xmark');
            }
        }
    });
}

/* =========================================================
   2. SCROLL REVEAL ANIMATIONS (Mobile Safe)
   ========================================================= */
function initScrollReveals() {
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    if (!revealElements.length) return;

    // Direct fallback if browser doesn't support IntersectionObserver
    if (!('IntersectionObserver' in window)) {
        revealElements.forEach(el => el.classList.add('is-visible'));
        return;
    }

    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -40px 0px',
        threshold: 0.08
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    revealElements.forEach(element => {
        revealObserver.observe(element);
    });
}

/* =========================================================
   3. FAQ ACCORDION
   ========================================================= */
function initAccordion() {
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    if (!accordionHeaders.length) return;

    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const currentItem = header.closest('.accordion-item');
            if (!currentItem) return;

            const isAlreadyOpen = currentItem.classList.contains('active');

            // Close all items
            document.querySelectorAll('.accordion-item').forEach(item => {
                item.classList.remove('active');
            });

            // Open clicked if closed
            if (!isAlreadyOpen) {
                currentItem.classList.add('active');
            }
        });
    });
}

/* =========================================================
   4. NAVBAR SCROLL EFFECT
   ========================================================= */
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    function updateNavbar() {
        if (window.scrollY > 30) {
            navbar.style.background = 'rgba(8, 14, 26, 0.98)';
            navbar.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.4)';
        } else {
            navbar.style.background = 'rgba(8, 14, 26, 0.9)';
            navbar.style.boxShadow = 'none';
        }
    }

    window.addEventListener('scroll', updateNavbar, { passive: true });
    updateNavbar();
}

/* =========================================================
   5. HERO BACKGROUND PARALLAX
   ========================================================= */
function initHeroParallax() {
    const heroSection = document.getElementById('hero');
    const shape1 = document.querySelector('.shape-1');
    const shape2 = document.querySelector('.shape-2');

    if (!heroSection || !shape1 || !shape2) return;

    if (window.matchMedia('(pointer: coarse)').matches) {
        return; // Disable on touch devices to save battery & prevent lag
    }

    heroSection.addEventListener('mousemove', (event) => {
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;

        const moveX = event.clientX - centerX;
        const moveY = event.clientY - centerY;

        shape1.style.transform = `translate3d(${moveX * 0.018}px, ${moveY * 0.018}px, 0)`;
        shape2.style.transform = `translate3d(${moveX * -0.012}px, ${moveY * -0.012}px, 0)`;
    });

    heroSection.addEventListener('mouseleave', () => {
        shape1.style.transform = 'translate3d(0, 0, 0)';
        shape2.style.transform = 'translate3d(0, 0, 0)';
    });
}

/* =========================================================
   6. SMOOTH INTERNAL NAVIGATION
   ========================================================= */
function initSmoothScroll() {
    const navigationLinks = document.querySelectorAll('a[href^="#"]');
    if (!navigationLinks.length) return;

    navigationLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            const targetId = link.getAttribute('href');
            if (!targetId || targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (!targetElement) return;

            event.preventDefault();
            const navbar = document.querySelector('.navbar');
            const navbarHeight = navbar ? navbar.offsetHeight : 70;

            const targetPosition = targetElement.getBoundingClientRect().top + window.scrollY - navbarHeight;

            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        });
    });
}