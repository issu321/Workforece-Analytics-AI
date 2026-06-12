/* ============================================
   WorkforceAI - Main JavaScript
   GitHub: https://github.com/issu321
   Repo: https://github.com/issu321/Workforece-Analytics-AI
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initMobileNav();
    initDropdowns();
    initScrollAnimations();
    initParticles();
    initFlashMessages();
    initSmoothScroll();
    initAnimatedCounters();
    initBackToTop();
    initNavHighlight();
});

function initTheme() {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;
    const savedTheme = localStorage.getItem('workforce-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('workforce-theme', next);
        updateThemeIcon(next);
    });
}

function updateThemeIcon(theme) {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;
    const icon = toggle.querySelector('i');
    if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function initMobileNav() {
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    if (!toggle || !links) return;
    toggle.addEventListener('click', () => {
        links.classList.toggle('open');
        const icon = toggle.querySelector('i');
        if (icon) {
            icon.className = links.classList.contains('open') ? 'fas fa-times' : 'fas fa-bars';
        }
    });
    links.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            links.classList.remove('open');
            const icon = toggle.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        });
    });
    document.addEventListener('click', (e) => {
        if (!toggle.contains(e.target) && !links.contains(e.target)) {
            links.classList.remove('open');
            const icon = toggle.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        }
    });
}

function initDropdowns() {
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        if (!toggle) return;
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.dropdown').forEach(d => {
                if (d !== dropdown) d.classList.remove('active');
            });
            dropdown.classList.toggle('active');
        });
    });
    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
    });
}

function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });

    document.querySelectorAll('.glass:not(.visible)').forEach((el, i) => {
        if (!el.closest('.navbar') && !el.classList.contains('animate-on-scroll')) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            const cardObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            el.style.opacity = '1';
                            el.style.transform = 'translateY(0)';
                        }, i * 50);
                        cardObserver.unobserve(el);
                    }
                });
            }, { threshold: 0.1 });
            cardObserver.observe(el);
        }
    });
}

function initParticles() {
    const canvas = document.getElementById('heroCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    let animationId;
    let isActive = true;

    function resize() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    const colors = ['#ff6b35', '#00d4ff', '#c084fc', '#ffd700'];

    class Particle {
        constructor() { this.reset(); }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 3 + 1;
            this.speedX = (Math.random() - 0.5) * 0.5;
            this.speedY = (Math.random() - 0.5) * 0.5;
            this.color = colors[Math.floor(Math.random() * colors.length)];
            this.opacity = Math.random() * 0.5 + 0.2;
            this.life = Math.random() * 100 + 100;
            this.maxLife = this.life;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.life--;
            if (this.life <= 0 || this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                this.reset();
            }
        }
        draw() {
            const lifeRatio = this.life / this.maxLife;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.globalAlpha = this.opacity * lifeRatio;
            ctx.fill();
            ctx.globalAlpha = 1;
        }
    }

    for (let i = 0; i < 60; i++) {
        particles.push(new Particle());
    }

    function animate() {
        if (!isActive) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = 'rgba(255, 107, 53, 0.08)';
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
        particles.forEach(p => { p.update(); p.draw(); });
        animationId = requestAnimationFrame(animate);
    }

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            isActive = false;
            cancelAnimationFrame(animationId);
        } else {
            isActive = true;
            animate();
        }
    });
    animate();
}

function initFlashMessages() {
    document.querySelectorAll('.flash').forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(120%)';
            setTimeout(() => flash.remove(), 400);
        }, 5000);
    });
}

function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

function initAnimatedCounters() {
    const counters = document.querySelectorAll('.metric-value[data-count]');
    if (!counters.length) return;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.getAttribute('data-count'));
                const duration = 1500;
                const start = performance.now();
                function update(now) {
                    const elapsed = now - start;
                    const progress = Math.min(elapsed / duration, 1);
                    const ease = 1 - Math.pow(1 - progress, 3);
                    el.textContent = Math.floor(ease * target).toLocaleString();
                    if (progress < 1) requestAnimationFrame(update);
                }
                requestAnimationFrame(update);
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });
    counters.forEach(counter => observer.observe(counter));
}

function initBackToTop() {
    const btn = document.createElement('button');
    btn.id = 'backToTop';
    btn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    btn.style.cssText = `
        position: fixed;
        bottom: 30px; right: 30px;
        width: 48px; height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ff6b35, #00d4ff);
        color: #fff; border: none; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
        opacity: 0; visibility: hidden;
        transform: translateY(20px);
        transition: all 0.3s ease;
        z-index: 999;
    `;
    document.body.appendChild(btn);
    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            btn.style.opacity = '1';
            btn.style.visibility = 'visible';
            btn.style.transform = 'translateY(0)';
        } else {
            btn.style.opacity = '0';
            btn.style.visibility = 'hidden';
            btn.style.transform = 'translateY(20px)';
        }
    });
}

function initNavHighlight() {
    const sections = document.querySelectorAll('section[id]');
    if (!sections.length) return;
    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (scrollY >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.flash-container') || (() => {
        const c = document.createElement('div');
        c.className = 'flash-container';
        document.body.appendChild(c);
        return c;
    })();
    const toast = document.createElement('div');
    toast.className = `flash flash-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(120%)';
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function getChartTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        bg: isDark ? '#0c0a1a' : '#f0f4f8',
        paper: isDark ? 'rgba(12, 12, 35, 0.72)' : 'rgba(255,255,255,0.82)',
        text: isDark ? '#f1f5f9' : '#0f172a',
        grid: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
        primary: '#ff6b35',
        secondary: '#00d4ff',
        accent: '#c084fc'
    };
}
