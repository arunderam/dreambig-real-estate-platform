// KYC Verification JavaScript Module
class KYCManager {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        this.setupFileUploads();
    }

    // Setup file upload handlers
    setupFileUploads() {
        const fileInputs = ['govId', 'addressProof'];
        
        fileInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            const uploadArea = input.parentElement;
            
            if (input && uploadArea) {
                // File input change handler
                input.addEventListener('change', (e) => {
                    this.handleFileSelect(e.target.files[0], inputId);
                });

                // Drag and drop handlers
                uploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    uploadArea.classList.add('dragover');
                });

                uploadArea.addEventListener('dragleave', () => {
                    uploadArea.classList.remove('dragover');
                });

                uploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    uploadArea.classList.remove('dragover');
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        this.handleFileSelect(files[0], inputId);
                        input.files = files;
                    }
                });
            }
        });
    }

    // Handle file selection
    handleFileSelect(file, inputId) {
        const preview = document.getElementById(`${inputId}Preview`);
        const nameSpan = document.getElementById(`${inputId}Name`);
        const errorSpan = document.getElementById(`${inputId}Error`);

        // Clear previous errors
        errorSpan.textContent = '';

        if (!file) return;

        // Validate file size
        if (file.size > this.maxFileSize) {
            errorSpan.textContent = 'File size must be less than 5MB';
            return;
        }

        // Validate file type
        if (!this.allowedTypes.includes(file.type)) {
            errorSpan.textContent = 'Only JPG, PNG, and PDF files are allowed';
            return;
        }

        // Show preview
        if (preview && nameSpan) {
            nameSpan.textContent = file.name;
            preview.classList.add('show');
        }
    }

    // Validate KYC form
    validateKYCForm(formData) {
        let isValid = true;
        const errors = {};

        // Validate required fields
        const requiredFields = [
            'fullName', 'dateOfBirth', 'nationality', 'occupation',
            'address', 'city', 'state', 'pincode'
        ];

        requiredFields.forEach(field => {
            const value = formData.get(field);
            if (!value || value.trim() === '') {
                errors[field] = 'This field is required';
                isValid = false;
            }
        });

        // Validate PIN code
        const pincode = formData.get('pincode');
        if (pincode && !/^\d{6}$/.test(pincode)) {
            errors.pincode = 'PIN code must be 6 digits';
            isValid = false;
        }

        // Validate date of birth (must be at least 18 years old)
        const dob = new Date(formData.get('dateOfBirth'));
        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();
        if (age < 18) {
            errors.dateOfBirth = 'You must be at least 18 years old';
            isValid = false;
        }

        // Validate file uploads
        const govId = formData.get('govId');
        const addressProof = formData.get('addressProof');

        if (!govId || govId.size === 0) {
            errors.govId = 'Government ID is required';
            isValid = false;
        }

        if (!addressProof || addressProof.size === 0) {
            errors.addressProof = 'Address proof is required';
            isValid = false;
        }

        // Display errors
        Object.keys(errors).forEach(field => {
            const errorElement = document.getElementById(`${field}Error`);
            if (errorElement) {
                errorElement.textContent = errors[field];
            }
        });

        return isValid;
    }

    // Clear form errors
    clearFormErrors() {
        const errorElements = document.querySelectorAll('.error-message');
        errorElements.forEach(element => {
            element.textContent = '';
        });
    }

    // Submit KYC form
    async submitKYC(formData) {
        try {
            // Get authentication token
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            // Prepare KYC data (convert FormData to object for JSON)
            const kycData = {
                personal_info: {
                    full_name: formData.get('fullName'),
                    date_of_birth: formData.get('dateOfBirth'),
                    nationality: formData.get('nationality'),
                    occupation: formData.get('occupation')
                },
                address_info: {
                    address: formData.get('address'),
                    city: formData.get('city'),
                    state: formData.get('state'),
                    pincode: formData.get('pincode')
                },
                documents: {
                    gov_id_uploaded: formData.get('govId').name,
                    address_proof_uploaded: formData.get('addressProof').name
                },
                submission_timestamp: new Date().toISOString()
            };

            // Submit to backend
            const response = await fetch(`${this.apiBaseUrl}/auth/kyc`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(kycData)
            });

            const data = await response.json();

            if (response.ok) {
                this.showVerificationStatus('success', 'KYC submitted successfully');
                this.displayFraudScore(data.fraud_analysis);
                authManager.showMessage('KYC verification submitted successfully!', 'success');
                
                // Update user info in localStorage
                const user = JSON.parse(localStorage.getItem('user') || '{}');
                user.kyc_verified = true;
                localStorage.setItem('user', JSON.stringify(user));
                
                return { success: true, data };
            } else {
                throw new Error(data.detail || 'KYC submission failed');
            }
        } catch (error) {
            console.error('KYC submission error:', error);
            this.showVerificationStatus('error', error.message);
            authManager.showMessage(error.message || 'KYC submission failed', 'error');
            return { success: false, error: error.message };
        }
    }

    // Show verification status
    showVerificationStatus(type, message) {
        const statusContainer = document.getElementById('verificationStatus');
        const statusItems = document.getElementById('statusItems');
        
        if (statusContainer && statusItems) {
            const statusItem = document.createElement('div');
            statusItem.className = `status-item ${type}`;
            
            let icon = '';
            switch (type) {
                case 'success':
                    icon = 'fas fa-check-circle';
                    break;
                case 'error':
                    icon = 'fas fa-exclamation-circle';
                    break;
                case 'pending':
                    icon = 'fas fa-clock';
                    break;
                default:
                    icon = 'fas fa-info-circle';
            }
            
            statusItem.innerHTML = `
                <i class="${icon}"></i>
                <div>
                    <strong>${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                    <p>${message}</p>
                </div>
            `;
            
            statusItems.appendChild(statusItem);
            statusContainer.classList.add('show');
        }
    }

    // Display fraud score analysis
    displayFraudScore(fraudAnalysis) {
        const fraudScoreContainer = document.getElementById('fraudScore');
        const scoreCircle = document.getElementById('scoreCircle');
        const scoreValue = document.getElementById('scoreValue');
        const scoreDescription = document.getElementById('scoreDescription');
        const scoreDetails = document.getElementById('scoreDetails');

        if (!fraudAnalysis || !fraudScoreContainer) return;

        // Calculate overall risk score (0-100)
        const riskScore = Math.round((fraudAnalysis.risk_score || 0) * 100);
        
        // Determine risk level
        let riskLevel = 'low';
        let riskText = 'Low Risk';
        if (riskScore > 70) {
            riskLevel = 'high';
            riskText = 'High Risk';
        } else if (riskScore > 40) {
            riskLevel = 'medium';
            riskText = 'Medium Risk';
        }

        // Update score display
        scoreValue.textContent = `${riskScore}%`;
        scoreCircle.className = `score-circle ${riskLevel}`;
        scoreDescription.textContent = `${riskText} - ${fraudAnalysis.message || 'Analysis complete'}`;

        // Display detailed analysis
        const details = [
            {
                title: 'Document Verification',
                value: fraudAnalysis.document_score ? `${Math.round(fraudAnalysis.document_score * 100)}%` : 'Pending',
                description: 'Document authenticity check'
            },
            {
                title: 'Identity Verification',
                value: fraudAnalysis.identity_score ? `${Math.round(fraudAnalysis.identity_score * 100)}%` : 'Pending',
                description: 'Identity matching analysis'
            },
            {
                title: 'Address Verification',
                value: fraudAnalysis.address_score ? `${Math.round(fraudAnalysis.address_score * 100)}%` : 'Pending',
                description: 'Address validation check'
            },
            {
                title: 'Overall Confidence',
                value: fraudAnalysis.confidence ? `${Math.round(fraudAnalysis.confidence * 100)}%` : 'Calculating',
                description: 'AI confidence level'
            }
        ];

        scoreDetails.innerHTML = details.map(detail => `
            <div class="score-detail">
                <h4>${detail.value}</h4>
                <p><strong>${detail.title}</strong></p>
                <p>${detail.description}</p>
            </div>
        `).join('');

        fraudScoreContainer.classList.add('show');
    }

    // Check current KYC status
    async checkKYCStatus() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                if (userData.kyc_verified) {
                    this.showVerificationStatus('success', 'Your KYC is already verified');
                    
                    // Hide form if already verified
                    const form = document.querySelector('.kyc-form');
                    if (form) {
                        form.style.display = 'none';
                    }
                } else {
                    this.showVerificationStatus('pending', 'KYC verification is required to access all features');
                }
            }
        } catch (error) {
            console.error('Error checking KYC status:', error);
        }
    }
}

// Initialize KYC functionality
function initializeKYC() {
    const kycManager = new KYCManager();
    const kycForm = document.getElementById('kycForm');
    const submitButton = document.getElementById('kycSubmitButton');

    // Check current KYC status
    kycManager.checkKYCStatus();

    if (kycForm) {
        kycForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(kycForm);
            
            // Clear previous errors
            kycManager.clearFormErrors();
            
            // Validate form
            if (!kycManager.validateKYCForm(formData)) {
                return;
            }
            
            // Show loading state
            submitButton.classList.add('loading');
            submitButton.disabled = true;
            
            // Submit KYC
            const result = await kycManager.submitKYC(formData);
            
            // Reset loading state
            submitButton.classList.remove('loading');
            submitButton.disabled = false;
            
            if (result.success) {
                // Optionally redirect after successful submission
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 3000);
            }
        });
    }
}

// Export for use in other files
window.kycManager = new KYCManager();
window.initializeKYC = initializeKYC;
