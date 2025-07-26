// Accessibility Manager for DreamBig Real Estate Platform
class AccessibilityManager {
    constructor() {
        this.focusTrap = null;
        this.announcements = [];
        this.keyboardNavigation = true;
        this.reducedMotion = false;
        this.highContrast = false;
        
        this.init();
    }
    
    init() {
        this.detectUserPreferences();
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupAnnouncementRegion();
        this.setupFormValidation();
        this.setupModalAccessibility();
        this.setupSkipLinks();
        this.addAriaLabels();
    }
    
    // Detect user accessibility preferences
    detectUserPreferences() {
        // Check for reduced motion preference
        if (window.matchMedia) {
            const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
            this.reducedMotion = reducedMotionQuery.matches;
            
            reducedMotionQuery.addEventListener('change', (e) => {
                this.reducedMotion = e.matches;
                this.handleReducedMotion();
            });
            
            // Check for high contrast preference
            const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
            this.highContrast = highContrastQuery.matches;
            
            highContrastQuery.addEventListener('change', (e) => {
                this.highContrast = e.matches;
                this.handleHighContrast();
            });
        }
        
        console.log('Accessibility preferences:', {
            reducedMotion: this.reducedMotion,
            highContrast: this.highContrast
        });
    }
    
    // Setup keyboard navigation
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
        
        // Add keyboard navigation indicators
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }
    
    // Handle keyboard navigation
    handleKeyboardNavigation(e) {
        switch (e.key) {
            case 'Escape':
                this.handleEscapeKey(e);
                break;
            case 'Enter':
            case ' ':
                this.handleActivationKeys(e);
                break;
            case 'ArrowUp':
            case 'ArrowDown':
            case 'ArrowLeft':
            case 'ArrowRight':
                this.handleArrowKeys(e);
                break;
        }
    }
    
    // Handle escape key
    handleEscapeKey(e) {
        // Close modals
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            this.closeModal(openModal);
            e.preventDefault();
            return;
        }
        
        // Close dropdowns
        const openDropdown = document.querySelector('.dropdown.show');
        if (openDropdown) {
            openDropdown.classList.remove('show');
            e.preventDefault();
            return;
        }
        
        // Clear search if focused
        const searchInput = document.querySelector('input[type="search"]:focus');
        if (searchInput && searchInput.value) {
            searchInput.value = '';
            e.preventDefault();
            return;
        }
    }
    
    // Handle activation keys (Enter/Space)
    handleActivationKeys(e) {
        const target = e.target;
        
        // Handle clickable elements that aren't buttons or links
        if (target.hasAttribute('role') && 
            ['button', 'tab', 'menuitem'].includes(target.getAttribute('role'))) {
            target.click();
            e.preventDefault();
        }
        
        // Handle card clicks
        if (target.classList.contains('property-card') || 
            target.classList.contains('investment-card') ||
            target.classList.contains('service-card')) {
            target.click();
            e.preventDefault();
        }
    }
    
    // Handle arrow keys for navigation
    handleArrowKeys(e) {
        const target = e.target;
        const parent = target.parentElement;
        
        // Handle tab navigation
        if (target.getAttribute('role') === 'tab') {
            this.handleTabNavigation(e, target);
            return;
        }
        
        // Handle menu navigation
        if (parent && parent.getAttribute('role') === 'menu') {
            this.handleMenuNavigation(e, target);
            return;
        }
        
        // Handle grid navigation
        if (parent && parent.classList.contains('property-grid')) {
            this.handleGridNavigation(e, target);
            return;
        }
    }
    
    // Setup focus management
    setupFocusManagement() {
        // Track focus for better UX
        let lastFocusedElement = null;
        
        document.addEventListener('focusin', (e) => {
            lastFocusedElement = e.target;
        });
        
        // Store last focused element for modal restoration
        this.lastFocusedElement = lastFocusedElement;
        
        // Ensure focus is visible
        document.addEventListener('focusin', (e) => {
            this.ensureFocusVisible(e.target);
        });
    }
    
    // Ensure focused element is visible
    ensureFocusVisible(element) {
        if (!element) return;
        
        const rect = element.getBoundingClientRect();
        const isVisible = rect.top >= 0 && 
                         rect.left >= 0 && 
                         rect.bottom <= window.innerHeight && 
                         rect.right <= window.innerWidth;
        
        if (!isVisible) {
            element.scrollIntoView({
                behavior: this.reducedMotion ? 'auto' : 'smooth',
                block: 'center'
            });
        }
    }
    
    // Setup announcement region for screen readers
    setupAnnouncementRegion() {
        let announcer = document.getElementById('announcer');
        
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'announcer';
            announcer.className = 'announcement';
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            document.body.appendChild(announcer);
        }
        
        this.announcer = announcer;
    }
    
    // Announce message to screen readers
    announce(message, priority = 'polite') {
        if (!this.announcer) return;
        
        this.announcer.setAttribute('aria-live', priority);
        this.announcer.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            this.announcer.textContent = '';
        }, 1000);
        
        console.log('Announced:', message);
    }
    
    // Setup form validation accessibility
    setupFormValidation() {
        document.addEventListener('invalid', (e) => {
            this.handleFormValidation(e);
        }, true);
        
        document.addEventListener('input', (e) => {
            this.clearFormErrors(e.target);
        });
    }
    
    // Handle form validation
    handleFormValidation(e) {
        const field = e.target;
        const fieldName = field.getAttribute('name') || field.id || 'field';
        
        // Set aria-invalid
        field.setAttribute('aria-invalid', 'true');
        
        // Create or update error message
        let errorId = field.id + '-error';
        let errorElement = document.getElementById(errorId);
        
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = errorId;
            errorElement.className = 'form-error';
            errorElement.setAttribute('role', 'alert');
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = field.validationMessage;
        field.setAttribute('aria-describedby', errorId);
        
        // Announce error
        this.announce(`Error in ${fieldName}: ${field.validationMessage}`, 'assertive');
    }
    
    // Clear form errors
    clearFormErrors(field) {
        if (field.validity.valid) {
            field.removeAttribute('aria-invalid');
            
            const errorId = field.id + '-error';
            const errorElement = document.getElementById(errorId);
            
            if (errorElement) {
                errorElement.remove();
                field.removeAttribute('aria-describedby');
            }
        }
    }
    
    // Setup modal accessibility
    setupModalAccessibility() {
        document.addEventListener('click', (e) => {
            if (e.target.hasAttribute('data-modal-target')) {
                const modalId = e.target.getAttribute('data-modal-target');
                this.openModal(modalId);
            }
            
            if (e.target.classList.contains('modal-close')) {
                const modal = e.target.closest('.modal');
                this.closeModal(modal);
            }
        });
    }
    
    // Open modal with accessibility
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        // Store last focused element
        this.lastFocusedElement = document.activeElement;
        
        // Show modal
        modal.classList.add('show');
        modal.setAttribute('aria-hidden', 'false');
        
        // Focus first focusable element
        const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        // Setup focus trap
        this.setupFocusTrap(modal);
        
        // Announce modal opening
        const modalTitle = modal.querySelector('.modal-title');
        if (modalTitle) {
            this.announce(`Dialog opened: ${modalTitle.textContent}`);
        }
    }
    
    // Close modal
    closeModal(modal) {
        if (!modal) return;
        
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
        
        // Restore focus
        if (this.lastFocusedElement) {
            this.lastFocusedElement.focus();
        }
        
        // Remove focus trap
        this.removeFocusTrap();
        
        // Announce modal closing
        this.announce('Dialog closed');
    }
    
    // Setup focus trap for modals
    setupFocusTrap(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        this.focusTrap = (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        lastElement.focus();
                        e.preventDefault();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        firstElement.focus();
                        e.preventDefault();
                    }
                }
            }
        };
        
        modal.addEventListener('keydown', this.focusTrap);
    }
    
    // Remove focus trap
    removeFocusTrap() {
        if (this.focusTrap) {
            document.removeEventListener('keydown', this.focusTrap);
            this.focusTrap = null;
        }
    }
    
    // Setup skip links
    setupSkipLinks() {
        // Add skip to main content link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link';
        skipLink.textContent = 'Skip to main content';
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Ensure main content has ID
        let mainContent = document.getElementById('main-content');
        if (!mainContent) {
            mainContent = document.querySelector('main') || 
                         document.querySelector('.main-content') ||
                         document.querySelector('.container');
            
            if (mainContent) {
                mainContent.id = 'main-content';
                mainContent.setAttribute('tabindex', '-1');
            }
        }
    }
    
    // Add ARIA labels to elements
    addAriaLabels() {
        // Add labels to form controls without labels
        const unlabeledInputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
        unlabeledInputs.forEach(input => {
            const placeholder = input.getAttribute('placeholder');
            const name = input.getAttribute('name');
            
            if (placeholder) {
                input.setAttribute('aria-label', placeholder);
            } else if (name) {
                input.setAttribute('aria-label', name.replace(/([A-Z])/g, ' $1').trim());
            }
        });
        
        // Add labels to buttons without text
        const unlabeledButtons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        unlabeledButtons.forEach(button => {
            const icon = button.querySelector('i');
            const title = button.getAttribute('title');
            
            if (title) {
                button.setAttribute('aria-label', title);
            } else if (icon && icon.className.includes('fa-')) {
                const iconName = icon.className.match(/fa-([a-z-]+)/);
                if (iconName) {
                    button.setAttribute('aria-label', iconName[1].replace(/-/g, ' '));
                }
            }
        });
        
        // Add role and labels to clickable cards
        const cards = document.querySelectorAll('.property-card, .investment-card, .service-card');
        cards.forEach(card => {
            if (!card.getAttribute('role')) {
                card.setAttribute('role', 'button');
                card.setAttribute('tabindex', '0');
                
                const title = card.querySelector('h3, .card-title, .title');
                if (title) {
                    card.setAttribute('aria-label', `View details for ${title.textContent}`);
                }
            }
        });
    }
    
    // Handle reduced motion
    handleReducedMotion() {
        if (this.reducedMotion) {
            document.body.classList.add('reduce-motion');
        } else {
            document.body.classList.remove('reduce-motion');
        }
    }
    
    // Handle high contrast
    handleHighContrast() {
        if (this.highContrast) {
            document.body.classList.add('high-contrast');
        } else {
            document.body.classList.remove('high-contrast');
        }
    }
}

// Initialize accessibility manager
let accessibilityManager;

document.addEventListener('DOMContentLoaded', () => {
    accessibilityManager = new AccessibilityManager();
    
    // Make it globally available
    window.accessibilityManager = accessibilityManager;
    
    console.log('Accessibility Manager initialized');
});
