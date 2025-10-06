        // BARRE DE PROGRESSION - N'AFFICHER QU'APRÈS AVOIR SCROLLÉ
window.addEventListener('scroll', () => {
    const progressContainer = document.querySelector('.progress-container');
    const progressBar = document.querySelector('.progress-bar');
    const headerHeight = document.querySelector('header').offsetHeight;

  // Affichage de la barre de progression
    if (window.pageYOffset > headerHeight - 100) {
        progressContainer.classList.add('visible');
    } else {
        progressContainer.classList.remove('visible');
    }

  // Progression
    const scrolled = (window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
    progressBar.style.width = scrolled + '%';

  // Navigation active
    let current = '';
    document.querySelectorAll('section').forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= sectionTop - 100) {
            current = section.getAttribute('id');
        }
    });
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === `#${current}`);
    });

  // Bouton retour haut
    const backToTop = document.querySelector('.back-to-top');
    backToTop.classList.toggle('visible', window.pageYOffset > 300);
});


        // SMOOTH SCROLLING AMÉLIORÉ
        document.querySelectorAll('nav a').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            });
        });

        // BACK TO TOP
        document.querySelector('.back-to-top').addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // ANIMATIONS AU SCROLL
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);

        // Observer les éléments à animer
        document.querySelectorAll('.section, .skill-category, .project-card, .experience-card, .education-card, .feature-item').forEach(el => {
            observer.observe(el);
        });

        // TOOLTIPS POUR LES TECHNOLOGIES
        document.querySelectorAll('.tech-tag').forEach(tag => {
            tag.addEventListener('mouseenter', function() {
                this.style.zIndex = '1000';
            });
            
            tag.addEventListener('mouseleave', function() {
                this.style.zIndex = '';
            });
        });

// PROJETS DEPLIABLE AU CLIC 
         document.querySelectorAll('.project-card').forEach(card => {
            card.classList.add('collapsed');
            card.addEventListener('click', function() {
                const wasCollapsed = this.classList.contains('collapsed');
                document.querySelectorAll('.project-card').forEach(c => c.classList.add('collapsed'));
                if (wasCollapsed) this.classList.remove('collapsed');


            card.setAttribute('tabindex', '0');
            card.addEventListener('keypress', e => {
                if (e.key === 'Enter') card.click();
            });
            });
        

    
        // Animation au chargement
        setTimeout(() => {
            card.classList.add('collapsed');
        }, 1000);
    });

