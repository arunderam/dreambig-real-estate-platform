// Profile Management JavaScript Module
class ProfileManager {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.currentUser = null;
        this.setupRangeInputs();
    }

    // Setup range input handlers
    setupRangeInputs() {
        const budgetMin = document.getElementById('budgetMin');
        const budgetMax = document.getElementById('budgetMax');
        const budgetMinValue = document.getElementById('budgetMinValue');
        const budgetMaxValue = document.getElementById('budgetMaxValue');

        if (budgetMin && budgetMinValue) {
            budgetMin.addEventListener('input', (e) => {
                budgetMinValue.textContent = this.formatCurrency(e.target.value);
            });
        }

        if (budgetMax && budgetMaxValue) {
            budgetMax.addEventListener('input', (e) => {
                budgetMaxValue.textContent = this.formatCurrency(e.target.value);
            });
        }
    }

    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN').format(amount);
    }

    // Load user profile data
    async loadUserProfile() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.apiBaseUrl}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.currentUser = await response.json();
                this.populateProfileData();
                return this.currentUser;
            } else {
                throw new Error('Failed to load profile');
            }
        } catch (error) {
            console.error('Error loading profile:', error);
            authManager.showMessage('Failed to load profile data', 'error');
        }
    }

    // Populate profile data in forms
    populateProfileData() {
        if (!this.currentUser) return;

        // Update header
        const headerName = document.getElementById('profileHeaderName');
        const headerEmail = document.getElementById('profileHeaderEmail');
        const kycBadge = document.getElementById('kycBadge');

        if (headerName) headerName.textContent = this.currentUser.name || 'User';
        if (headerEmail) headerEmail.textContent = this.currentUser.email || '';
        
        if (kycBadge) {
            if (this.currentUser.kyc_verified) {
                kycBadge.textContent = '✓ KYC Verified';
                kycBadge.style.background = '#28a745';
                kycBadge.style.color = 'white';
                kycBadge.style.padding = '5px 15px';
                kycBadge.style.borderRadius = '20px';
                kycBadge.style.fontSize = '0.9rem';
            } else {
                kycBadge.innerHTML = '⚠ <a href="/kyc-verification" style="color: #ffc107;">Complete KYC</a>';
                kycBadge.style.background = '#ffc107';
                kycBadge.style.color = '#212529';
                kycBadge.style.padding = '5px 15px';
                kycBadge.style.borderRadius = '20px';
                kycBadge.style.fontSize = '0.9rem';
            }
        }

        // Populate personal info form
        const nameInput = document.getElementById('name');
        const phoneInput = document.getElementById('phone');
        const emailInput = document.getElementById('email');
        const roleSelect = document.getElementById('role');

        if (nameInput) nameInput.value = this.currentUser.name || '';
        if (phoneInput) phoneInput.value = this.currentUser.phone || '';
        if (emailInput) emailInput.value = this.currentUser.email || '';
        if (roleSelect) roleSelect.value = this.currentUser.role || 'tenant';
    }

    // Update personal information
    async updatePersonalInfo(formData) {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const updateData = {
                name: formData.get('name'),
                phone: formData.get('phone')
            };

            const response = await fetch(`${this.apiBaseUrl}/users/me`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(updateData)
            });

            const data = await response.json();

            if (response.ok) {
                this.currentUser = data;
                this.populateProfileData();
                authManager.showMessage('Profile updated successfully!', 'success');
                return { success: true, data };
            } else {
                throw new Error(data.detail || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            authManager.showMessage(error.message || 'Failed to update profile', 'error');
            return { success: false, error: error.message };
        }
    }

    // Update user preferences
    async updatePreferences(preferencesData) {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.apiBaseUrl}/users/preferences`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(preferencesData)
            });

            const data = await response.json();

            if (response.ok) {
                authManager.showMessage('Preferences updated successfully!', 'success');
                return { success: true, data };
            } else {
                throw new Error(data.detail || 'Failed to update preferences');
            }
        } catch (error) {
            console.error('Error updating preferences:', error);
            authManager.showMessage(error.message || 'Failed to update preferences', 'error');
            return { success: false, error: error.message };
        }
    }

    // Load notifications
    async loadNotifications() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/users/notifications`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const notifications = await response.json();
                this.displayNotifications(notifications);
            } else {
                throw new Error('Failed to load notifications');
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            const notificationsList = document.getElementById('notificationsList');
            if (notificationsList) {
                notificationsList.innerHTML = '<div class="error-message">Failed to load notifications</div>';
            }
        }
    }

    // Display notifications
    displayNotifications(notifications) {
        const notificationsList = document.getElementById('notificationsList');
        if (!notificationsList) return;

        if (!notifications || notifications.length === 0) {
            notificationsList.innerHTML = '<div class="empty-message">No notifications yet</div>';
            return;
        }

        const notificationsHTML = notifications.map(notification => {
            const iconClass = this.getNotificationIcon(notification.notification_type);
            const timeAgo = this.getTimeAgo(new Date(notification.created_at));
            
            return `
                <div class="notification-item ${notification.is_read ? '' : 'unread'}">
                    <div class="notification-icon ${notification.notification_type}">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">${notification.title}</div>
                        <div class="notification-message">${notification.message}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                    ${!notification.is_read ? `
                        <button class="mark-read-btn" onclick="markNotificationAsRead(${notification.id})">
                            Mark as Read
                        </button>
                    ` : ''}
                </div>
            `;
        }).join('');

        notificationsList.innerHTML = notificationsHTML;
    }

    // Get notification icon
    getNotificationIcon(type) {
        const icons = {
            'welcome': 'fas fa-hand-wave',
            'property_created': 'fas fa-home',
            'kyc_success': 'fas fa-shield-check',
            'preferences_updated': 'fas fa-cog',
            'default': 'fas fa-bell'
        };
        return icons[type] || icons.default;
    }

    // Get time ago string
    getTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        return `${Math.floor(diffInSeconds / 86400)} days ago`;
    }

    // Mark notification as read
    async markNotificationAsRead(notificationId) {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/users/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                // Reload notifications to update UI
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    // Load analytics
    async loadAnalytics() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/users/analytics`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const analytics = await response.json();
                this.displayAnalytics(analytics);
            } else {
                throw new Error('Failed to load analytics');
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    // Display analytics
    displayAnalytics(analytics) {
        const totalFavorites = document.getElementById('totalFavorites');
        const totalViewed = document.getElementById('totalViewed');
        const activityScore = document.getElementById('activityScore');
        const userType = document.getElementById('userType');

        if (totalFavorites) totalFavorites.textContent = analytics.total_favorites || 0;
        if (totalViewed) totalViewed.textContent = analytics.total_viewed || 0;
        if (activityScore) activityScore.textContent = analytics.activity_score || 0;
        if (userType) userType.textContent = analytics.user_type || 'New';
    }
}

// Initialize profile functionality
function initializeProfile() {
    const profileManager = new ProfileManager();

    // Load initial profile data
    profileManager.loadUserProfile();

    // Setup personal info form
    const personalInfoForm = document.getElementById('personalInfoForm');
    const updatePersonalButton = document.getElementById('updatePersonalButton');

    if (personalInfoForm) {
        personalInfoForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(personalInfoForm);

            // Show loading state
            updatePersonalButton.classList.add('loading');
            updatePersonalButton.disabled = true;

            // Update profile
            await profileManager.updatePersonalInfo(formData);

            // Reset loading state
            updatePersonalButton.classList.remove('loading');
            updatePersonalButton.disabled = false;
        });
    }

    // Setup preferences form
    const preferencesForm = document.getElementById('preferencesForm');
    const updatePreferencesButton = document.getElementById('updatePreferencesButton');

    if (preferencesForm) {
        preferencesForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(preferencesForm);

            // Collect preferences data
            const preferencesData = {
                property_types: Array.from(formData.getAll('property_types')),
                budget_min: parseFloat(formData.get('budget_min')) || 0,
                budget_max: parseFloat(formData.get('budget_max')) || 10000000,
                bhk_preference: Array.from(formData.getAll('bhk_preference')).map(Number)
            };

            // Show loading state
            updatePreferencesButton.classList.add('loading');
            updatePreferencesButton.disabled = true;

            // Update preferences
            await profileManager.updatePreferences(preferencesData);

            // Reset loading state
            updatePreferencesButton.classList.remove('loading');
            updatePreferencesButton.disabled = false;
        });
    }

    // Export functions for global use
    window.profileManager = profileManager;
    window.loadNotifications = () => profileManager.loadNotifications();
    window.loadAnalytics = () => profileManager.loadAnalytics();
    window.markNotificationAsRead = (id) => profileManager.markNotificationAsRead(id);
}

// Export for use in other files
window.initializeProfile = initializeProfile;
