// Navbar Scroll Effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }

    // Active Link Highlight
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-links a');

    let current = '';

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (pageYOffset >= (sectionTop - sectionHeight / 3)) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(current)) {
            link.classList.add('active');
        }
    });
});

// Scroll Reveal Animation (Intersection Observer)
const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px"
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.scroll-fade').forEach(el => {
    observer.observe(el);
});

// Directional Scroll Reveal Observer
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            revealObserver.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.15,
    rootMargin: "0px 0px -40px 0px"
});

document.querySelectorAll('.scroll-reveal').forEach(el => {
    revealObserver.observe(el);
});

// Auth Tabs Toggle
let activeRole = 'user';

function switchTab(role) {
    activeRole = role;
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.innerText.toLowerCase() === role) {
            tab.classList.add('active');
        }
    });

    // Optional: Could change form fields based on role here
    console.log(`Switched to ${role} login`);
}

// Handle Login Submission
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const btn = document.querySelector('#loginForm button[type="submit"]');
    const originalText = btn.innerHTML;

    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Authenticating...';
    btn.disabled = true;

    try {
        const user = await SkillXApi.post('/auth/login', {
            email: email,
            password: password
        });

        localStorage.setItem('SkillXUser', JSON.stringify(user));

        if (user.role === 'recruiter') {
            window.location.href = 'recruiter-dashboard.html';
        } else {
            window.location.href = 'user-dashboard.html';
        }
    } catch (error) {
        alert(error.message || 'Login failed. Please check your credentials.');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Smooth scroll to login when CTA is clicked
function scrollToLogin() {
    const welcomeSection = document.getElementById('welcome');
    if (welcomeSection) {
        welcomeSection.scrollIntoView({ behavior: 'smooth' });
        const emailInput = document.getElementById('email');
        if (emailInput) emailInput.focus();
    }
}

// ===============================
// Theme Toggle Logic
// ===============================
function setTheme(themeName) {
    localStorage.setItem('SkillXTheme', 'light-theme');
    document.body.className = 'light-theme';
}

function toggleTheme() {
    setTheme('light-theme');
}

// On load, force light theme
(function () {
    setTheme('light-theme');
})();

// ===============================
// Interactive Lamp Logic
// ===============================
function pullLamp() {
    const rope = document.getElementById('lamp-rope');
    const lamp = document.getElementById('lamp');
    const card = document.getElementById('login-container');

    if (!rope || !lamp || !card) return;

    // Visual rope pull effect
    rope.style.transform = 'translateY(15px)';

    setTimeout(() => {
        // Snap rope back
        rope.style.transform = 'translateY(0)';

        // Toggle the Lamp Light
        lamp.classList.toggle('on');

        // Toggle the Auth Container
        if (card.classList.contains('lamp-hidden')) {
            card.classList.remove('lamp-hidden');
            card.classList.add('lamp-visible');
        } else {
            card.classList.remove('lamp-visible');
            card.classList.add('lamp-hidden');
        }
    }, 250);
}

// Handle Registration Submission
async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const btn = document.querySelector('#registerForm button[type="submit"]');
    const originalText = btn.innerHTML;

    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Creating Account...';
    btn.disabled = true;

    try {
        const user = await SkillXApi.post('/auth/register', {
            name: name,
            email: email,
            password: password,
            role: activeRole
        });

        alert('Account created successfully! Please log in.');
        window.location.href = 'login.html';
    } catch (error) {
        alert(error.message || 'Registration failed.');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Login Card 3D Tilt Effect
const authCard = document.querySelector('.auth-card');
if (authCard) {
    authCard.addEventListener('mousemove', (e) => {
        const rect = authCard.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * -5;
        const rotateY = ((x - centerX) / centerX) * 5;

        authCard.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        authCard.style.transition = 'transform 0.1s ease-out';
    });

    authCard.addEventListener('mouseleave', () => {
        authCard.style.transform = `perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)`;
        authCard.style.transition = 'transform 0.5s ease-out';
    });
}

// ===============================
// API Helpers
// ===============================
const SKILLX_API_BASE =
    localStorage.getItem('SkillXApiBase') ||
    window.SKILLX_API_BASE ||
    'http://127.0.0.1:8000/api';

async function skillxPost(path, payload) {
    const response = await fetch(`${SKILLX_API_BASE}${path}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    let data = null;
    try {
        data = await response.json();
    } catch (error) {
        data = null;
    }

    if (!response.ok) {
        const detail = data?.detail || data?.message || `Request failed with status ${response.status}`;
        throw new Error(detail);
    }

    return data;
}

async function skillxGet(path) {
    const response = await fetch(`${SKILLX_API_BASE}${path}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    let data = null;
    try {
        data = await response.json();
    } catch (error) {
        data = null;
    }

    if (!response.ok) {
        const detail = data?.detail || data?.message || `Request failed with status ${response.status}`;
        throw new Error(detail);
    }

    return data;
}

window.SkillXApi = {
    baseUrl: SKILLX_API_BASE,
    post: skillxPost,
    get: skillxGet
};
