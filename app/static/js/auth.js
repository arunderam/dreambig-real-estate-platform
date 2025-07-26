// Authentication JavaScript Module
class AuthManager {
    constructor() {
        this.auth = window.firebaseAuth;
        this.apiBaseUrl = '/api/v1';
        this.currentUser = null;
        this.isLoggingOut = false;

        // Set Firebase persistence to LOCAL (survives browser restarts)
        this.auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL)
            .then(() => {
                this.setupAuthStateListener();
            })
            .catch((error) => {
                console.error('Error setting Firebase persistence:', error);
                this.setupAuthStateListener(); // Continue anyway
            });
    }

    // Setup Firebase Auth State Listener
    setupAuthStateListener() {
        this.auth.onAuthStateChanged((user) => {
            this.currentUser = user;
            this.updateUIForAuthState(user);
        });

        // Also check for existing authentication on page load
        this.restoreAuthState();
    }

    // Restore authentication state from localStorage
    restoreAuthState() {
        const storedUser = localStorage.getItem('user');
        const storedToken = localStorage.getItem('access_token');

        if (storedUser && storedToken) {
            try {
                const userData = JSON.parse(storedUser);
                console.log('Restored auth state for user:', userData.email);
                // Don't clear the auth state immediately
            } catch (error) {
                console.error('Error parsing stored user data:', error);
                localStorage.removeItem('user');
                localStorage.removeItem('access_token');
            }
        }
    }

    // Update UI based on authentication state
    updateUIForAuthState(user) {
        if (user) {
            // User is signed in
            console.log('User signed in:', user.email);
            // Store user info in localStorage
            localStorage.setItem('user', JSON.stringify({
                uid: user.uid,
                email: user.email,
                displayName: user.displayName
            }));
        } else {
            // User is signed out - but only clear storage if we're on login/register pages
            // or if this is an intentional logout
            console.log('User signed out');
            const currentPath = window.location.pathname;
            const publicPages = ['/login', '/register', '/', '/about'];

            // Only clear storage if we're on public pages or if explicitly logging out
            if (publicPages.includes(currentPath) || this.isLoggingOut) {
                localStorage.removeItem('user');
                localStorage.removeItem('access_token');
            }
        }
    }

    // Show message to user
    showMessage(message, type = 'info') {
        const messageContainer = document.getElementById('messageContainer');
        if (!messageContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;

        messageContainer.appendChild(messageDiv);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }

    // Validate email format
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Validate password strength
    validatePassword(password) {
        const minLength = password.length >= 6;
        const hasUpper = /[A-Z]/.test(password);
        const hasLower = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        const score = [minLength, hasUpper, hasLower, hasNumber, hasSpecial].filter(Boolean).length;
        
        return {
            isValid: minLength,
            strength: score <= 2 ? 'weak' : score <= 4 ? 'medium' : 'strong',
            score: score
        };
    }

    // Update password strength indicator
    updatePasswordStrength(password) {
        const strengthIndicator = document.getElementById('passwordStrength');
        if (!strengthIndicator) return;

        const validation = this.validatePassword(password);
        strengthIndicator.className = `password-strength ${validation.strength}`;
    }

    // Toggle password visibility
    togglePasswordVisibility(inputId) {
        const input = document.getElementById(inputId);
        const icon = document.getElementById(`${inputId}ToggleIcon`);
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            input.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    // Login with email and password
    async loginWithEmail(email, password) {
        try {
            const userCredential = await this.auth.signInWithEmailAndPassword(email, password);
            const user = userCredential.user;
            
            // Get Firebase ID token
            const idToken = await user.getIdToken();
            
            // Send token to backend
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id_token: idToken })
            });

            const data = await response.json();

            if (response.ok) {
                // Store access token
                localStorage.setItem('access_token', data.access_token);
                this.showMessage('Login successful! Redirecting...', 'success');
                
                // Redirect to dashboard after short delay
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
                
                return { success: true, data };
            } else {
                throw new Error(data.detail || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showMessage(error.message || 'Login failed. Please try again.', 'error');
            return { success: false, error: error.message };
        }
    }

    // Register with email and password
    async registerWithEmail(userData) {
        try {
            // First create user in Firebase
            const userCredential = await this.auth.createUserWithEmailAndPassword(
                userData.email, 
                userData.password
            );
            const user = userCredential.user;

            // Update user profile
            await user.updateProfile({
                displayName: userData.name
            });

            // Get Firebase ID token
            const idToken = await user.getIdToken();

            // Prepare registration data for backend
            const registrationData = {
                email: userData.email,
                name: userData.name,
                phone: userData.phone,
                password: userData.password,
                role: userData.role,
                preferences: userData.preferences || {},
                location: userData.location || null
            };

            // Send registration data to backend
            const response = await fetch(`${this.apiBaseUrl}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(registrationData)
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Registration successful! Please check your email for verification.', 'success');

                // Display AI features if available
                if (data.fraud_score) {
                    this.displayFraudScore(data.fraud_score);
                }

                if (data.recommendations && data.recommendations.length > 0) {
                    this.displayRecommendations(data.recommendations);
                }

                // Redirect to login page after longer delay to show AI features
                setTimeout(() => {
                    window.location.href = '/login';
                }, 5000);

                return { success: true, data };
            } else {
                // If backend registration fails, delete the Firebase user
                await user.delete();
                throw new Error(data.detail || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showMessage(error.message || 'Registration failed. Please try again.', 'error');
            return { success: false, error: error.message };
        }
    }

    // Sign in with Google
    async signInWithGoogle() {
        try {
            const provider = new firebase.auth.GoogleAuthProvider();
            provider.addScope('email');
            provider.addScope('profile');

            const result = await this.auth.signInWithPopup(provider);
            const user = result.user;
            
            // Get Firebase ID token
            const idToken = await user.getIdToken();
            
            // Send token to backend
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id_token: idToken })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('access_token', data.access_token);
                this.showMessage('Google sign-in successful! Redirecting...', 'success');
                
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
                
                return { success: true, data };
            } else {
                throw new Error(data.detail || 'Google sign-in failed');
            }
        } catch (error) {
            console.error('Google sign-in error:', error);
            if (error.code !== 'auth/popup-closed-by-user') {
                this.showMessage(error.message || 'Google sign-in failed. Please try again.', 'error');
            }
            return { success: false, error: error.message };
        }
    }

    // Logout
    async logout() {
        try {
            this.isLoggingOut = true; // Set flag to indicate intentional logout
            await this.auth.signOut();
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            this.showMessage('Logged out successfully', 'success');

            // Redirect to login page
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        } catch (error) {
            console.error('Logout error:', error);
            this.showMessage('Logout failed. Please try again.', 'error');
        } finally {
            this.isLoggingOut = false; // Reset flag
        }
    }

    // Check if user is authenticated
    isAuthenticated() {
        const hasToken = localStorage.getItem('access_token') !== null;
        const hasUser = localStorage.getItem('user') !== null;

        // Return true if we have both token and user data
        // Don't rely on this.currentUser as it might not be set during page load
        return hasToken && hasUser;
    }

    // Get current user token
    async getCurrentUserToken() {
        if (this.currentUser) {
            return await this.currentUser.getIdToken();
        }
        return null;
    }

    // Display fraud score analysis
    displayFraudScore(fraudScore) {
        const messageContainer = document.getElementById('messageContainer');
        if (!messageContainer || !fraudScore) return;

        const riskScore = Math.round((fraudScore.risk_score || 0) * 100);
        let riskLevel = 'low';
        let riskColor = '#28a745';

        if (riskScore > 70) {
            riskLevel = 'high';
            riskColor = '#dc3545';
        } else if (riskScore > 40) {
            riskLevel = 'medium';
            riskColor = '#ffc107';
        }

        const fraudDiv = document.createElement('div');
        fraudDiv.className = 'message info';
        fraudDiv.style.maxWidth = '400px';
        fraudDiv.innerHTML = `
            <div style="text-align: center;">
                <h4>🛡️ AI Security Analysis</h4>
                <div style="margin: 15px 0;">
                    <div style="width: 60px; height: 60px; border-radius: 50%; background: ${riskColor};
                                color: white; display: flex; align-items: center; justify-content: center;
                                margin: 0 auto; font-weight: bold; font-size: 1.2rem;">
                        ${riskScore}%
                    </div>
                    <p style="margin-top: 10px; color: #666;">
                        ${fraudScore.message || `${riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} risk profile detected`}
                    </p>
                </div>
            </div>
        `;

        messageContainer.appendChild(fraudDiv);

        // Auto remove after 8 seconds
        setTimeout(() => {
            if (fraudDiv.parentNode) {
                fraudDiv.parentNode.removeChild(fraudDiv);
            }
        }, 8000);
    }

    // Display AI recommendations
    displayRecommendations(recommendations) {
        const messageContainer = document.getElementById('messageContainer');
        if (!messageContainer || !recommendations || recommendations.length === 0) return;

        const recDiv = document.createElement('div');
        recDiv.className = 'message success';
        recDiv.style.maxWidth = '450px';

        const recHTML = recommendations.slice(0, 3).map(rec => `
            <div style="padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px;">
                <strong>${rec.title || 'Property Recommendation'}</strong>
                <p style="margin: 5px 0; font-size: 0.9rem; color: #666;">
                    ${rec.description || rec.location || 'Personalized recommendation based on your preferences'}
                </p>
                ${rec.price ? `<span style="color: #667eea; font-weight: 600;">₹${rec.price}</span>` : ''}
            </div>
        `).join('');

        recDiv.innerHTML = `
            <div>
                <h4>🎯 AI-Powered Recommendations</h4>
                <p style="margin-bottom: 15px; color: #666;">Based on your profile, here are some properties you might like:</p>
                ${recHTML}
                <p style="margin-top: 15px; font-size: 0.9rem; color: #666;">
                    More personalized recommendations available in your dashboard!
                </p>
            </div>
        `;

        messageContainer.appendChild(recDiv);

        // Auto remove after 10 seconds
        setTimeout(() => {
            if (recDiv.parentNode) {
                recDiv.parentNode.removeChild(recDiv);
            }
        }, 10000);
    }
}

// Initialize AuthManager
const authManager = new AuthManager();

// Global functions for template usage
function togglePassword(inputId = 'password') {
    authManager.togglePasswordVisibility(inputId);
}

// Login Page Initialization
function initializeLogin() {
    const loginForm = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');
    const googleSignInButton = document.getElementById('googleSignIn');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;

            // Clear previous errors
            clearFormErrors();

            // Validate form
            if (!validateLoginForm(email, password)) {
                return;
            }

            // Show loading state
            setButtonLoading(loginButton, true);

            // Attempt login
            const result = await authManager.loginWithEmail(email, password);

            // Reset loading state
            setButtonLoading(loginButton, false);
        });
    }

    if (googleSignInButton) {
        googleSignInButton.addEventListener('click', async () => {
            await authManager.signInWithGoogle();
        });
    }
}

// Register Page Initialization
function initializeRegister() {
    const registerForm = document.getElementById('registerForm');
    const registerButton = document.getElementById('registerButton');
    const googleSignUpButton = document.getElementById('googleSignUp');
    const passwordInput = document.getElementById('password');

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(registerForm);
            const userData = {
                name: formData.get('name').trim(),
                email: formData.get('email').trim(),
                phone: formData.get('phone').trim(),
                password: formData.get('password'),
                confirmPassword: formData.get('confirmPassword'),
                role: formData.get('role'),
                termsAccepted: formData.get('termsAccepted') === 'on'
            };

            // Clear previous errors
            clearFormErrors();

            // Validate form
            if (!validateRegisterForm(userData)) {
                return;
            }

            // Show loading state
            setButtonLoading(registerButton, true);

            // Attempt registration
            const result = await authManager.registerWithEmail(userData);

            // Reset loading state
            setButtonLoading(registerButton, false);
        });
    }

    if (passwordInput) {
        passwordInput.addEventListener('input', (e) => {
            authManager.updatePasswordStrength(e.target.value);
        });
    }

    if (googleSignUpButton) {
        googleSignUpButton.addEventListener('click', async () => {
            await authManager.signInWithGoogle();
        });
    }
}

// Form Validation Functions
function validateLoginForm(email, password) {
    let isValid = true;

    if (!email) {
        showFieldError('emailError', 'Email is required');
        isValid = false;
    } else if (!authManager.validateEmail(email)) {
        showFieldError('emailError', 'Please enter a valid email address');
        isValid = false;
    }

    if (!password) {
        showFieldError('passwordError', 'Password is required');
        isValid = false;
    }

    return isValid;
}

function validateRegisterForm(userData) {
    let isValid = true;

    // Name validation
    if (!userData.name || userData.name.length < 2) {
        showFieldError('nameError', 'Name must be at least 2 characters long');
        isValid = false;
    }

    // Email validation
    if (!userData.email) {
        showFieldError('emailError', 'Email is required');
        isValid = false;
    } else if (!authManager.validateEmail(userData.email)) {
        showFieldError('emailError', 'Please enter a valid email address');
        isValid = false;
    }

    // Phone validation (optional)
    if (userData.phone && userData.phone.trim() && userData.phone.trim().length < 10) {
        showFieldError('phoneError', 'Phone number must be at least 10 digits');
        isValid = false;
    }

    // Password validation
    const passwordValidation = authManager.validatePassword(userData.password);
    if (!passwordValidation.isValid) {
        showFieldError('passwordError', 'Password must be at least 6 characters long');
        isValid = false;
    }

    // Confirm password validation
    if (userData.password !== userData.confirmPassword) {
        showFieldError('confirmPasswordError', 'Passwords do not match');
        isValid = false;
    }

    // Role validation
    if (!userData.role) {
        showFieldError('roleError', 'Please select your role');
        isValid = false;
    }

    // Terms validation
    if (!userData.termsAccepted) {
        showFieldError('termsError', 'You must accept the terms and conditions');
        isValid = false;
    }

    return isValid;
}

// Utility Functions
function showFieldError(errorId, message) {
    const errorElement = document.getElementById(errorId);
    if (errorElement) {
        errorElement.textContent = message;
    }
}

function clearFormErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.textContent = '';
    });
}

function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// Check authentication status on protected pages
function checkAuthStatus() {
    const protectedPages = ['/dashboard', '/properties', '/investments', '/services', '/profile', '/kyc-verification'];
    const currentPath = window.location.pathname;

    if (protectedPages.includes(currentPath)) {
        // Give Firebase time to initialize and check auth state
        setTimeout(() => {
            if (!authManager.isAuthenticated()) {
                console.log('User not authenticated, redirecting to login');
                window.location.href = '/login';
            } else {
                console.log('User authenticated, staying on page');
            }
        }, 1000); // Wait 1 second for Firebase to initialize
    }
}

// Initialize auth check on page load
document.addEventListener('DOMContentLoaded', () => {
    // Wait for Firebase to initialize before checking auth
    setTimeout(() => {
        checkAuthStatus();
    }, 500);
});

// Export for use in other files
window.authManager = authManager;
window.initializeLogin = initializeLogin;
window.initializeRegister = initializeRegister;
