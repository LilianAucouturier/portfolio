        // MENU BURGER
const burger = document.getElementById('burger');
const navLinks = document.getElementById('nav-links');

if (burger) {
    burger.addEventListener('click', () => {
        burger.classList.toggle('active');
        navLinks.classList.toggle('active');
    });
}

// Fermer le menu au clic sur un lien interne (mobiles)
document.querySelectorAll('nav a:not(.lang-link)').forEach(link => {
    link.addEventListener('click', () => {
        if (burger) burger.classList.remove('active');
        if (navLinks) navLinks.classList.remove('active');
    });
});

// GESTION DU BOUTON 3D
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.view-3d-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); // Empêche de replier/déplier la carte
            const container = this.closest('.project-image');
            const isShowing3D = container.classList.toggle('show-3d');
            
            // Mise à jour du texte du bouton
            const span = this.querySelector('span');
            if (isShowing3D) {
                span.textContent = this.getAttribute('data-text-close') || 'Quitter la 3D';
                // Activer le premier model-config (multi-config) ou le model-viewer simple
                const configs = container.querySelectorAll('model-viewer.model-config');
                if (configs.length > 0) {
                    // Multi-config : activer la première option (ou celle sélectionnée dans le select)
                    const select = container.querySelector('.config-selector select');
                    const selectedValue = select ? select.value : null;
                    configs.forEach(mv => {
                        mv.classList.toggle('active-config', mv.dataset.config === selectedValue);
                    });
                }
            } else {
                span.textContent = this.getAttribute('data-text-open') || 'Voir en 3D';
            }
        });
    });

    // GESTION DU SÉLECTEUR DE CONFIGURATION (MULTI-CONFIG)
    document.querySelectorAll('.config-selector select').forEach(select => {
        select.addEventListener('click', e => e.stopPropagation());
        select.addEventListener('change', function(e) {
            e.stopPropagation();
            const container = this.closest('.project-image');
            const selectedConfig = this.value;
            container.querySelectorAll('model-viewer.model-config').forEach(mv => {
                mv.classList.toggle('active-config', mv.dataset.config === selectedConfig);
            });
        });
    });

    // Empêcher les clics dans le model-viewer et le sélecteur de fermer la carte
    document.querySelectorAll('model-viewer').forEach(mv => {
        mv.addEventListener('click', e => e.stopPropagation());
        mv.addEventListener('mousedown', e => e.stopPropagation());
        mv.addEventListener('mouseup', e => e.stopPropagation());
        mv.addEventListener('pointerdown', e => e.stopPropagation());
        mv.addEventListener('pointerup', e => e.stopPropagation());
    });

    document.querySelectorAll('.config-selector').forEach(el => {
        el.addEventListener('click', e => e.stopPropagation());
        el.addEventListener('mousedown', e => e.stopPropagation());
    });
});



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
    document.querySelectorAll('nav a:not(.lang-link)').forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === `#${current}`);
    });

  // Bouton retour haut
    const backToTop = document.querySelector('.back-to-top');
    backToTop.classList.toggle('visible', window.pageYOffset > 300);
});


        // SMOOTH SCROLLING AMÉLIORÉ - Uniquement pour les ancres internes (#)
        document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    e.preventDefault();
                    window.scrollTo({
                        top: targetElement.offsetTop - 80,
                        behavior: 'smooth'
                    });
                }
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
            card.addEventListener('click', function(e) {
                // Si le clic vient du visualiseur 3D ou du bouton 3D, on ne replie pas
                if (e.target.closest('model-viewer') || e.target.closest('.view-3d-btn')) return;
                // Si le mode 3D est actif dans cette carte, on ignore le clic
                if (this.querySelector('.project-image.show-3d')) return;

                const wasCollapsed = this.classList.contains('collapsed');
                document.querySelectorAll('.project-card').forEach(c => c.classList.add('collapsed'));
                if (wasCollapsed) this.classList.remove('collapsed');
            });

            card.setAttribute('tabindex', '0');
            card.addEventListener('keypress', e => {
                if (e.key === 'Enter') card.click();
            });
        

    
        // Animation au chargement
        setTimeout(() => {
            card.classList.add('collapsed');
        }, 1000);
    });

