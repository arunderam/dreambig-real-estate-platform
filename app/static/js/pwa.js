// PWA Management and Installation
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isStandalone = false;
        this.serviceWorkerRegistration = null;
        
        this.init();
    }
    
    async init() {
        this.checkInstallationStatus();
        this.registerServiceWorker();
        this.setupInstallPrompt();
        this.setupUpdateNotification();
        this.setupOfflineDetection();
        this.createInstallButton();
    }
    
    // Check if app is installed or running in standalone mode
    checkInstallationStatus() {
        // Check if running in standalone mode
        this.isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                           window.navigator.standalone ||
                           document.referrer.includes('android-app://');
        
        // Check if app is installed
        this.isInstalled = this.isStandalone || 
                          localStorage.getItem('pwa-installed') === 'true';
        
        console.log('PWA Status:', {
            isStandalone: this.isStandalone,
            isInstalled: this.isInstalled
        });
        
        if (this.isStandalone) {
            document.body.classList.add('pwa-standalone');
            this.hideInstallPrompts();
        }
    }
    
    // Register Service Worker
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                this.serviceWorkerRegistration = await navigator.serviceWorker.register('/static/sw.js', {
                    scope: '/'
                });
                
                console.log('Service Worker registered successfully:', this.serviceWorkerRegistration);
                
                // Listen for updates
                this.serviceWorkerRegistration.addEventListener('updatefound', () => {
                    this.handleServiceWorkerUpdate();
                });
                
                // Check for existing service worker
                if (this.serviceWorkerRegistration.active) {
                    console.log('Service Worker is active');
                }
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        } else {
            console.log('Service Worker not supported');
        }
    }
    
    // Handle Service Worker updates
    handleServiceWorkerUpdate() {
        const newWorker = this.serviceWorkerRegistration.installing;
        
        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New version available
                this.showUpdateNotification();
            }
        });
    }
    
    // Setup install prompt handling
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('Install prompt available');
            
            // Prevent the mini-infobar from appearing on mobile
            e.preventDefault();
            
            // Save the event for later use
            this.deferredPrompt = e;
            
            // Show custom install button
            this.showInstallButton();
        });
        
        // Listen for app installation
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.deferredPrompt = null;
            this.isInstalled = true;
            localStorage.setItem('pwa-installed', 'true');
            this.hideInstallButton();
            this.showInstallSuccessMessage();
        });
    }
    
    // Create install button
    createInstallButton() {
        // Check if button already exists
        if (document.getElementById('pwa-install-btn')) {
            return;
        }
        
        const installButton = document.createElement('button');
        installButton.id = 'pwa-install-btn';
        installButton.className = 'pwa-install-button';
        installButton.innerHTML = `
            <i class="fas fa-download"></i>
            <span>Install App</span>
        `;
        installButton.style.display = 'none';
        installButton.addEventListener('click', () => this.installApp());
        
        // Add to page
        document.body.appendChild(installButton);
        
        // Add CSS styles
        this.addInstallButtonStyles();
    }
    
    // Add CSS styles for install button
    addInstallButtonStyles() {
        if (document.getElementById('pwa-install-styles')) {
            return;
        }
        
        const styles = document.createElement('style');
        styles.id = 'pwa-install-styles';
        styles.textContent = `
            .pwa-install-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 50px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s ease;
                animation: pulse 2s infinite;
            }
            
            .pwa-install-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
            }
            
            .pwa-install-button i {
                font-size: 16px;
            }
            
            @keyframes pulse {
                0% { box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); }
                50% { box-shadow: 0 4px 20px rgba(102, 126, 234, 0.8); }
                100% { box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); }
            }
            
            .pwa-update-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                z-index: 1001;
                max-width: 300px;
                animation: slideInRight 0.3s ease;
            }
            
            .pwa-update-notification button {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 8px 16px;
                margin-top: 10px;
                cursor: pointer;
                font-size: 12px;
            }
            
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            .pwa-offline-indicator {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #dc3545;
                color: white;
                text-align: center;
                padding: 10px;
                z-index: 1002;
                font-size: 14px;
                transform: translateY(-100%);
                transition: transform 0.3s ease;
            }
            
            .pwa-offline-indicator.show {
                transform: translateY(0);
            }
            
            .pwa-standalone .navbar {
                padding-top: env(safe-area-inset-top);
            }
            
            @media (max-width: 768px) {
                .pwa-install-button {
                    bottom: 80px;
                    right: 15px;
                    padding: 10px 16px;
                    font-size: 13px;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    // Show install button
    showInstallButton() {
        const button = document.getElementById('pwa-install-btn');
        if (button && !this.isInstalled) {
            button.style.display = 'flex';
        }
    }
    
    // Hide install button
    hideInstallButton() {
        const button = document.getElementById('pwa-install-btn');
        if (button) {
            button.style.display = 'none';
        }
    }
    
    // Hide all install prompts
    hideInstallPrompts() {
        this.hideInstallButton();
        // Hide any other install prompts in the UI
        const installPrompts = document.querySelectorAll('.install-prompt');
        installPrompts.forEach(prompt => {
            prompt.style.display = 'none';
        });
    }
    
    // Install the app
    async installApp() {
        if (!this.deferredPrompt) {
            console.log('No install prompt available');
            return;
        }
        
        try {
            // Show the install prompt
            this.deferredPrompt.prompt();
            
            // Wait for the user's response
            const { outcome } = await this.deferredPrompt.userChoice;
            
            console.log('Install prompt outcome:', outcome);
            
            if (outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            
            // Clear the deferred prompt
            this.deferredPrompt = null;
            this.hideInstallButton();
            
        } catch (error) {
            console.error('Error during app installation:', error);
        }
    }
    
    // Show update notification
    showUpdateNotification() {
        // Remove existing notification
        const existing = document.getElementById('pwa-update-notification');
        if (existing) {
            existing.remove();
        }
        
        const notification = document.createElement('div');
        notification.id = 'pwa-update-notification';
        notification.className = 'pwa-update-notification';
        notification.innerHTML = `
            <div>
                <strong>Update Available!</strong><br>
                A new version of DreamBig is ready.
            </div>
            <button onclick="pwaManager.applyUpdate()">Update Now</button>
            <button onclick="this.parentElement.remove()" style="margin-left: 10px;">Later</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }
    
    // Apply service worker update
    applyUpdate() {
        if (this.serviceWorkerRegistration && this.serviceWorkerRegistration.waiting) {
            this.serviceWorkerRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
            window.location.reload();
        }
    }
    
    // Setup offline detection
    setupOfflineDetection() {
        const offlineIndicator = document.createElement('div');
        offlineIndicator.id = 'pwa-offline-indicator';
        offlineIndicator.className = 'pwa-offline-indicator';
        offlineIndicator.innerHTML = `
            <i class="fas fa-wifi"></i>
            You're currently offline. Some features may be limited.
        `;
        
        document.body.appendChild(offlineIndicator);
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            offlineIndicator.classList.remove('show');
            console.log('App is online');
        });
        
        window.addEventListener('offline', () => {
            offlineIndicator.classList.add('show');
            console.log('App is offline');
        });
        
        // Check initial state
        if (!navigator.onLine) {
            offlineIndicator.classList.add('show');
        }
    }
    
    // Show install success message
    showInstallSuccessMessage() {
        const message = document.createElement('div');
        message.className = 'pwa-update-notification';
        message.style.background = '#28a745';
        message.innerHTML = `
            <div>
                <strong>App Installed!</strong><br>
                DreamBig has been added to your home screen.
            </div>
        `;
        
        document.body.appendChild(message);
        
        setTimeout(() => {
            message.remove();
        }, 5000);
    }
    
    // Setup update notification on page load
    setupUpdateNotification() {
        // Check for updates when page loads
        if (this.serviceWorkerRegistration) {
            this.serviceWorkerRegistration.update();
        }
    }
    
    // Get app info
    getAppInfo() {
        return {
            isInstalled: this.isInstalled,
            isStandalone: this.isStandalone,
            isOnline: navigator.onLine,
            hasServiceWorker: !!this.serviceWorkerRegistration
        };
    }
}

// Initialize PWA Manager
let pwaManager;

document.addEventListener('DOMContentLoaded', () => {
    pwaManager = new PWAManager();
    
    // Make it globally available
    window.pwaManager = pwaManager;
    
    console.log('PWA Manager initialized');
});
