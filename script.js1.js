document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const menuOverlay = document.getElementById('menuOverlay');
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuToggle.addEventListener('click', function() {
        menuToggle.classList.toggle('active');
        menuOverlay.classList.toggle('active');
        document.body.style.overflow = menuOverlay.classList.contains('active') ? 'hidden' : '';
    });

    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                menuToggle.classList.remove('active');
                menuOverlay.classList.remove('active');
                document.body.style.overflow = '';
                
                setTimeout(() => {
                    targetSection.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 300);
            }
        });
    });

    menuOverlay.addEventListener('click', function(e) {
        if (e.target === menuOverlay) {
            menuToggle.classList.remove('active');
            menuOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    });

    const observerOptions = {
        threshold: 0.3,
        rootMargin: '0px 0px -20% 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll('.success-card, .mission-text, .mission-image');
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(50px)';
        element.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(element);
    });

    const timelineObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const milestone = entry.target;
                const analyticsItems = milestone.querySelectorAll('.analytics-item');
                
                analyticsItems.forEach((item, index) => {
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }, index * 200);
                });
                
                const dot = milestone.querySelector('.milestone-dot');
                if (dot) {
                    setTimeout(() => {
                        dot.style.transform = 'scale(1.2)';
                        setTimeout(() => {
                            dot.style.transform = 'scale(1)';
                        }, 300);
                    }, 100);
                }
            }
        });
    }, {
        threshold: 0.3,
        rootMargin: '0px 0px -10% 0px'
    });

    const milestones = document.querySelectorAll('.milestone');
    milestones.forEach(milestone => {
        timelineObserver.observe(milestone);
    });

    let ticking = false;
    function updateScrollProgress() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        
        const missionSection = document.querySelector('.mission-section');
        if (missionSection) {
            missionSection.style.transform = `translateY(${rate * 0.3}px)`;
        }
        
        ticking = false;
    }

    function requestScrollUpdate() {
        if (!ticking) {
            requestAnimationFrame(updateScrollProgress);
            ticking = true;
        }
    }

    window.addEventListener('scroll', requestScrollUpdate);

    const successCards = document.querySelectorAll('.success-card');
    successCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.15}s`;
    });
});