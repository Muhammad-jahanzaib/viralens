
// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
});

// Custom cursor (desktop only)
if (window.innerWidth > 768) {
    const cursor = document.querySelector('.custom-cursor');
    const follower = document.querySelector('.cursor-follower');

    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
        follower.style.left = e.clientX + 'px';
        follower.style.top = e.clientY + 'px';
    });
}

// Particle animation (hero section)
const canvas = document.getElementById('particles-canvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const particleCount = 80;

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 3 + 1;
            this.speedX = Math.random() * 1 - 0.5;
            this.speedY = Math.random() * 1 - 0.5;
            this.opacity = Math.random() * 0.5 + 0.2;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;

            if (this.x > canvas.width) this.x = 0;
            if (this.x < 0) this.x = canvas.width;
            if (this.y > canvas.height) this.y = 0;
            if (this.y < 0) this.y = canvas.height;
        }

        draw() {
            ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }

    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        requestAnimationFrame(animateParticles);
    }
    animateParticles();

    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Counter animation
const counters = document.querySelectorAll('.counter-number');
const speed = 150; // Slower speed

const animateCounter = (counter) => {
    const target = +counter.getAttribute('data-target');
    const duration = 2500; // 2.5 seconds - SMOOTH & GENTLE
    const fps = 60;
    const totalFrames = (duration / 1000) * fps;
    let currentFrame = 0;

    // Smooth easing function (ease-out-cubic for gentle deceleration)
    const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

    const animate = () => {
        currentFrame++;
        const progress = currentFrame / totalFrames;
        const easedProgress = easeOutCubic(progress);
        const currentValue = Math.floor(target * easedProgress);

        counter.innerText = currentValue.toLocaleString();

        if (currentFrame < totalFrames) {
            requestAnimationFrame(animate);
        } else {
            counter.innerText = target.toLocaleString(); // Ensure final value
        }
    };

    requestAnimationFrame(animate);
};

const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounter(entry.target);
            counterObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

counters.forEach(counter => counterObserver.observe(counter));

// Scroll reveal animations
const reveals = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
        }
    });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

reveals.forEach(reveal => revealObserver.observe(reveal));

// FAQ accordion
document.querySelectorAll('.faq-question').forEach(question => {
    question.addEventListener('click', () => {
        const item = question.parentElement;
        const wasActive = item.classList.contains('active');

        document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));

        if (!wasActive) {
            item.classList.add('active');
        }
    });
});

// Pricing calculator
const slider = document.getElementById('videos-per-month');
const videosValue = document.getElementById('videos-value');
const savingsAmount = document.getElementById('savings-amount');

if (slider && videosValue && savingsAmount) {
    slider.addEventListener('input', () => {
        const videos = slider.value;
        videosValue.textContent = videos;

        const hoursPerVideo = 3.5;
        const hourlyRate = 40;
        const totalSaved = videos * hoursPerVideo * hourlyRate;
        const netSavings = totalSaved - 29;

        savingsAmount.textContent = '$' + netSavings.toLocaleString();
    });
}

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Floating notification (cycle through different users)
const notifications = [
    { name: 'Jake', initial: 'JD', location: 'Los Angeles, CA', country: '🇺🇸' },
    { name: 'Emma', initial: 'EW', location: 'London, UK', country: '🇬🇧' },
    { name: 'Carlos', initial: 'CM', location: 'Barcelona, ES', country: '🇪🇸' },
    { name: 'Yuki', initial: 'YT', location: 'Tokyo, JP', country: '🇯🇵' }
];

let notificationIndex = 0;

function showNotification() {
    const notification = document.getElementById('notification');
    if (!notification) return;

    const data = notifications[notificationIndex];

    notification.querySelector('.notification-avatar').textContent = data.initial;
    notification.querySelector('strong').textContent = `${data.name} just signed up!`;
    notification.querySelector('span').textContent = `${data.country} ${data.location} • ${Math.floor(Math.random() * 5) + 1} minutes ago`;

    // Removing animation class to re-trigger it
    notification.style.animation = 'none';
    notification.offsetHeight; /* trigger reflow */
    notification.style.animation = 'slideInLeft 0.5s ease, slideOutLeft 0.5s ease 4.5s forwards';

    notificationIndex = (notificationIndex + 1) % notifications.length;

    setTimeout(showNotification, 10000);
}

// Start notification loop after 3 seconds
setTimeout(showNotification, 3000);

// Mobile Menu Toggle
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navLinks = document.querySelector('.nav-links');

if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', () => {
        mobileMenuToggle.classList.toggle('active');
        navLinks.classList.toggle('active');
    });

    // Close menu when clicking on a link
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            mobileMenuToggle.classList.remove('active');
            navLinks.classList.remove('active');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!mobileMenuToggle.contains(e.target) && !navLinks.contains(e.target)) {
            mobileMenuToggle.classList.remove('active');
            navLinks.classList.remove('active');
        }
    });
}
