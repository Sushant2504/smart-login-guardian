/**
 * Additional 3D Animations and Visual Effects
 * Enhances the dashboard with animated UI elements
 */

// Animated Number Counter
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Particle Background Effect
class ParticleBackground {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '0';

        this.container.style.position = 'relative';
        this.container.appendChild(this.canvas);

        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 50;

        this.resize();
        this.createParticles();
        this.animate();

        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        this.canvas.width = this.container.offsetWidth;
        this.canvas.height = this.container.offsetHeight;
    }

    createParticles() {
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.particles.forEach(particle => {
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;

            // Wrap around edges
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;

            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity})`;
            this.ctx.fill();

            // Draw connections
            this.particles.forEach(other => {
                const dx = particle.x - other.x;
                const dy = particle.y - other.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 100) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(other.x, other.y);
                    this.ctx.strokeStyle = `rgba(0, 212, 255, ${0.2 * (1 - distance / 100)})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.stroke();
                }
            });
        });

        requestAnimationFrame(() => this.animate());
    }
}

// Glowing Card Effect
function addGlowEffect(selector) {
    const cards = document.querySelectorAll(selector);

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });
}

// Animated Progress Ring
class ProgressRing {
    constructor(element, progress, color = '#00d4ff') {
        this.element = element;
        this.progress = 0;
        this.targetProgress = progress;
        this.color = color;
        this.radius = 40;
        this.strokeWidth = 6;

        this.create();
        this.animate();
    }

    create() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', (this.radius + this.strokeWidth) * 2);
        svg.setAttribute('height', (this.radius + this.strokeWidth) * 2);

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        const circumference = 2 * Math.PI * this.radius;

        circle.setAttribute('cx', this.radius + this.strokeWidth);
        circle.setAttribute('cy', this.radius + this.strokeWidth);
        circle.setAttribute('r', this.radius);
        circle.setAttribute('fill', 'none');
        circle.setAttribute('stroke', this.color);
        circle.setAttribute('stroke-width', this.strokeWidth);
        circle.setAttribute('stroke-dasharray', circumference);
        circle.setAttribute('stroke-dashoffset', circumference);
        circle.setAttribute('transform', `rotate(-90 ${this.radius + this.strokeWidth} ${this.radius + this.strokeWidth})`);

        svg.appendChild(circle);
        this.element.appendChild(svg);
        this.circle = circle;
        this.circumference = circumference;
    }

    animate() {
        const step = () => {
            if (this.progress < this.targetProgress) {
                this.progress += 1;
                const offset = this.circumference - (this.progress / 100) * this.circumference;
                this.circle.setAttribute('stroke-dashoffset', offset);
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }
}

// 3D Tilt Effect on Hover
function add3DTilt(selector) {
    const elements = document.querySelectorAll(selector);

    elements.forEach(element => {
        element.addEventListener('mousemove', (e) => {
            const rect = element.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;

            element.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
        });

        element.addEventListener('mouseleave', () => {
            element.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
        });
    });
}

// Ripple Effect on Click
function addRippleEffect(selector) {
    const elements = document.querySelectorAll(selector);

    elements.forEach(element => {
        element.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');

            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });
}

// Floating Animation
function addFloatingAnimation(selector, duration = 3000) {
    const elements = document.querySelectorAll(selector);

    elements.forEach((element, index) => {
        element.style.animation = `float ${duration}ms ease-in-out infinite`;
        element.style.animationDelay = `${index * 200}ms`;
    });
}

// Data Flow Animation
class DataFlowAnimation {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.style.position = 'absolute';
        this.svg.style.top = '0';
        this.svg.style.left = '0';
        this.svg.style.width = '100%';
        this.svg.style.height = '100%';
        this.svg.style.pointerEvents = 'none';
        this.svg.style.zIndex = '1';

        this.container.style.position = 'relative';
        this.container.appendChild(this.svg);

        this.createPaths();
    }

    createPaths() {
        const width = this.container.offsetWidth;
        const height = this.container.offsetHeight;

        for (let i = 0; i < 5; i++) {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const startX = 0;
            const startY = height * (i / 5);
            const endX = width;
            const endY = height * ((i + 1) / 5);

            const d = `M ${startX} ${startY} Q ${width / 2} ${(startY + endY) / 2} ${endX} ${endY}`;

            path.setAttribute('d', d);
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', 'rgba(0, 212, 255, 0.3)');
            path.setAttribute('stroke-width', '1');

            // Animated stroke
            const length = path.getTotalLength();
            path.style.strokeDasharray = length;
            path.style.strokeDashoffset = length;
            path.style.animation = `drawPath 3s ease-in-out infinite`;
            path.style.animationDelay = `${i * 0.3}s`;

            this.svg.appendChild(path);

            // Animated dots
            for (let j = 0; j < 3; j++) {
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('r', '3');
                circle.setAttribute('fill', '#00d4ff');
                circle.style.opacity = '0.8';

                const animateMotion = document.createElementNS('http://www.w3.org/2000/svg', 'animateMotion');
                animateMotion.setAttribute('dur', '3s');
                animateMotion.setAttribute('repeatCount', 'indefinite');
                animateMotion.setAttribute('begin', `${(i * 0.3) + (j * 1)}s`);

                const mpath = document.createElementNS('http://www.w3.org/2000/svg', 'mpath');
                mpath.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', `#path${i}`);

                path.id = `path${i}`;
                animateMotion.appendChild(mpath);
                circle.appendChild(animateMotion);
                this.svg.appendChild(circle);
            }
        }
    }
}

// Add keyframe animations via CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    @keyframes drawPath {
        to { stroke-dashoffset: 0; }
    }

    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(0, 212, 255, 0.5);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }

    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }

    .stat-card {
        transition: transform 0.3s ease;
    }

    .panel {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
`;
document.head.appendChild(style);

// Initialize animations on page load
document.addEventListener('DOMContentLoaded', () => {
    // Add particle background to main dashboard
    new ParticleBackground('globeContainer');

    // Add 3D tilt effect to stat cards
    add3DTilt('.stat-card');

    // Add ripple effect to buttons
    addRippleEffect('.btn-simulate');
    addRippleEffect('.btn-control');

    // Add floating animation to icons
    addFloatingAnimation('.stat-icon');

    // Animate numbers when they come into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const value = parseInt(element.textContent) || 0;
                animateValue(element, 0, value, 1000);
                observer.unobserve(element);
            }
        });
    });

    document.querySelectorAll('.stat-value').forEach(el => observer.observe(el));
});

// Export for use in dashboard.js
window.AnimationHelpers = {
    animateValue,
    ParticleBackground,
    ProgressRing,
    add3DTilt,
    addRippleEffect,
    addFloatingAnimation,
    DataFlowAnimation,
    addGlowEffect
};
