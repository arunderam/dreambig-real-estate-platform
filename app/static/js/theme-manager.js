// Theme Management System for DreamBig Real Estate Platform
class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.systemPreference = 'light';
        this.userPreference = null;
        this.mediaQuery = null;
        
        this.init();
    }
    
    init() {
        this.detectSystemPreference();
        this.loadUserPreference();
        this.createThemeToggle();
        this.applyTheme();
        this.setupMediaQueryListener();
        this.setupKeyboardShortcuts();
    }
    
    // Detect system color scheme preference
    detectSystemPreference() {
        if (window.matchMedia) {
            this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            this.systemPreference = this.mediaQuery.matches ? 'dark' : 'light';
            
            console.log('System preference detected:', this.systemPreference);
        }
    }
    
    // Load user's saved theme preference
    loadUserPreference() {
        const saved = localStorage.getItem('dreambig-theme');
        
        if (saved && ['light', 'dark', 'auto'].includes(saved)) {
            this.userPreference = saved;
            console.log('User preference loaded:', this.userPreference);
        } else {
            this.userPreference = 'auto'; // Default to auto
        }
        
        this.updateCurrentTheme();
    }
    
    // Update current theme based on user preference and system settings
    updateCurrentTheme() {
        if (this.userPreference === 'auto') {
            this.currentTheme = this.systemPreference;
        } else {
            this.currentTheme = this.userPreference;
        }
        
        console.log('Current theme updated to:', this.currentTheme);
    }
    
    // Apply theme to the document
    applyTheme() {
        const html = document.documentElement;
        const body = document.body;
        
        // Remove existing theme classes
        html.removeAttribute('data-theme');
        body.classList.remove('theme-light', 'theme-dark');
        
        // Apply new theme
        html.setAttribute('data-theme', this.currentTheme);
        body.classList.add(`theme-${this.currentTheme}`);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor();
        
        // Update theme toggle button
        this.updateThemeToggle();
        
        // Dispatch theme change event
        this.dispatchThemeChangeEvent();
        
        console.log('Theme applied:', this.currentTheme);
    }
    
    // Update meta theme-color for mobile browsers
    updateMetaThemeColor() {
        let themeColorMeta = document.querySelector('meta[name="theme-color"]');
        
        if (!themeColorMeta) {
            themeColorMeta = document.createElement('meta');
            themeColorMeta.name = 'theme-color';
            document.head.appendChild(themeColorMeta);
        }
        
        const themeColors = {
            light: '#667eea',
            dark: '#1a1a1a'
        };
        
        themeColorMeta.content = themeColors[this.currentTheme];
    }
    
    // Create theme toggle button
    createThemeToggle() {
        // Check if toggle already exists
        if (document.getElementById('theme-toggle')) {
            return;
        }
        
        const toggle = document.createElement('button');
        toggle.id = 'theme-toggle';
        toggle.className = 'theme-toggle';
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.setAttribute('title', 'Toggle between light and dark theme');
        
        // Add icon
        const icon = document.createElement('i');
        icon.className = 'fas fa-moon';
        toggle.appendChild(icon);
        
        // Add click handler
        toggle.addEventListener('click', () => this.toggleTheme());
        
        // Add to page
        document.body.appendChild(toggle);
        
        console.log('Theme toggle created');
    }
    
    // Update theme toggle button appearance
    updateThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        if (!toggle) return;
        
        const icon = toggle.querySelector('i');
        if (!icon) return;
        
        // Update icon based on current theme
        icon.className = this.currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        
        // Update tooltip
        const tooltipText = this.currentTheme === 'dark' 
            ? 'Switch to light theme' 
            : 'Switch to dark theme';
        toggle.setAttribute('title', tooltipText);
        toggle.setAttribute('aria-label', tooltipText);
    }
    
    // Toggle between themes
    toggleTheme() {
        if (this.userPreference === 'auto') {
            // If auto, switch to opposite of system preference
            this.userPreference = this.systemPreference === 'dark' ? 'light' : 'dark';
        } else {
            // Toggle between light and dark
            this.userPreference = this.currentTheme === 'dark' ? 'light' : 'dark';
        }
        
        this.saveUserPreference();
        this.updateCurrentTheme();
        this.applyTheme();
        
        // Add visual feedback
        this.showThemeChangeNotification();
    }
    
    // Set specific theme
    setTheme(theme) {
        if (!['light', 'dark', 'auto'].includes(theme)) {
            console.error('Invalid theme:', theme);
            return;
        }
        
        this.userPreference = theme;
        this.saveUserPreference();
        this.updateCurrentTheme();
        this.applyTheme();
    }
    
    // Save user preference to localStorage
    saveUserPreference() {
        localStorage.setItem('dreambig-theme', this.userPreference);
        console.log('Theme preference saved:', this.userPreference);
    }
    
    // Setup media query listener for system preference changes
    setupMediaQueryListener() {
        if (this.mediaQuery) {
            this.mediaQuery.addEventListener('change', (e) => {
                this.systemPreference = e.matches ? 'dark' : 'light';
                console.log('System preference changed to:', this.systemPreference);
                
                // Update theme if user preference is auto
                if (this.userPreference === 'auto') {
                    this.updateCurrentTheme();
                    this.applyTheme();
                }
            });
        }
    }
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + T to toggle theme
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }
    
    // Show theme change notification
    showThemeChangeNotification() {
        // Remove existing notification
        const existing = document.getElementById('theme-notification');
        if (existing) {
            existing.remove();
        }
        
        const notification = document.createElement('div');
        notification.id = 'theme-notification';
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: var(--card-bg);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: var(--card-shadow);
            z-index: 1001;
            font-size: 14px;
            animation: slideInRight 0.3s ease;
            transition: all 0.3s ease;
        `;
        
        const themeName = this.currentTheme === 'dark' ? 'Dark' : 'Light';
        notification.innerHTML = `
            <i class="fas fa-${this.currentTheme === 'dark' ? 'moon' : 'sun'}"></i>
            ${themeName} theme activated
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 2 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => notification.remove(), 300);
            }
        }, 2000);
    }
    
    // Dispatch theme change event
    dispatchThemeChangeEvent() {
        const event = new CustomEvent('themechange', {
            detail: {
                theme: this.currentTheme,
                userPreference: this.userPreference,
                systemPreference: this.systemPreference
            }
        });
        
        document.dispatchEvent(event);
    }
    
    // Get current theme info
    getThemeInfo() {
        return {
            current: this.currentTheme,
            userPreference: this.userPreference,
            systemPreference: this.systemPreference,
            isAuto: this.userPreference === 'auto'
        };
    }
    
    // Initialize theme for specific components
    initializeComponentTheme(component) {
        if (typeof component.onThemeChange === 'function') {
            // Call component's theme change handler
            component.onThemeChange(this.currentTheme);
            
            // Listen for future theme changes
            document.addEventListener('themechange', (e) => {
                component.onThemeChange(e.detail.theme);
            });
        }
    }
    
    // Add CSS animation styles
    addAnimationStyles() {
        if (document.getElementById('theme-animations')) {
            return;
        }
        
        const styles = document.createElement('style');
        styles.id = 'theme-animations';
        styles.textContent = `
            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(100%);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            .theme-transition {
                transition: all 0.3s ease !important;
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    // Preload theme assets
    preloadThemeAssets() {
        // Preload dark mode images if they exist
        const darkModeImages = [
            '/static/images/logo-dark.png',
            '/static/images/hero-dark.jpg'
        ];
        
        darkModeImages.forEach(src => {
            const img = new Image();
            img.src = src;
        });
    }
}

// Initialize theme manager
let themeManager;

document.addEventListener('DOMContentLoaded', () => {
    themeManager = new ThemeManager();
    
    // Make it globally available
    window.themeManager = themeManager;
    
    console.log('Theme Manager initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}
