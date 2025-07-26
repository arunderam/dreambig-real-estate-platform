// Add Property JavaScript Module
class AddPropertyManager {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.maxFiles = 10;
        this.selectedImages = [];
        this.setupImageUpload();
    }

    // Setup image upload functionality
    setupImageUpload() {
        const imageInput = document.getElementById('propertyImages');
        const uploadArea = imageInput?.parentElement;

        if (imageInput && uploadArea) {
            // File input change handler
            imageInput.addEventListener('change', (e) => {
                this.handleImageSelect(e.target.files);
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
                this.handleImageSelect(files);
            });
        }
    }

    // Handle image selection
    handleImageSelect(files) {
        const errorSpan = document.getElementById('imagesError');
        errorSpan.textContent = '';

        // Validate file count
        if (this.selectedImages.length + files.length > this.maxFiles) {
            errorSpan.textContent = `Maximum ${this.maxFiles} images allowed`;
            return;
        }

        // Validate and add files
        Array.from(files).forEach(file => {
            if (this.validateImage(file)) {
                this.selectedImages.push(file);
            }
        });

        this.displayImagePreviews();
    }

    // Validate image file
    validateImage(file) {
        const errorSpan = document.getElementById('imagesError');

        // Check file type
        if (!file.type.startsWith('image/')) {
            errorSpan.textContent = 'Only image files are allowed';
            return false;
        }

        // Check file size
        if (file.size > this.maxFileSize) {
            errorSpan.textContent = 'Image size must be less than 5MB';
            return false;
        }

        return true;
    }

    // Display image previews
    displayImagePreviews() {
        const preview = document.getElementById('imagePreview');
        if (!preview) return;

        if (this.selectedImages.length === 0) {
            preview.classList.remove('show');
            return;
        }

        const previewHTML = this.selectedImages.map((file, index) => {
            const url = URL.createObjectURL(file);
            return `
                <div class="preview-item">
                    <img src="${url}" alt="Preview" class="preview-image">
                    <button type="button" class="remove-image" onclick="removeImage(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');

        preview.innerHTML = previewHTML;
        preview.classList.add('show');
    }

    // Remove image
    removeImage(index) {
        this.selectedImages.splice(index, 1);
        this.displayImagePreviews();
    }

    // Check KYC status
    async checkKYCStatus() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return false;

            const response = await fetch(`${this.apiBaseUrl}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                return userData.kyc_verified;
            }
        } catch (error) {
            console.error('Error checking KYC status:', error);
        }
        return false;
    }

    // Validate property form
    validatePropertyForm(formData) {
        let isValid = true;
        const errors = {};

        // Required fields validation
        const requiredFields = [
            'title', 'property_type', 'bhk', 'area', 'price', 
            'furnishing', 'description', 'address', 'city', 'state', 'pincode'
        ];

        requiredFields.forEach(field => {
            const value = formData.get(field);
            if (!value || value.trim() === '') {
                errors[field] = 'This field is required';
                isValid = false;
            }
        });

        // Specific validations
        const area = parseFloat(formData.get('area'));
        if (area && area <= 0) {
            errors.area = 'Area must be greater than 0';
            isValid = false;
        }

        const price = parseFloat(formData.get('price'));
        if (price && price <= 0) {
            errors.price = 'Price must be greater than 0';
            isValid = false;
        }

        const pincode = formData.get('pincode');
        if (pincode && !/^\d{6}$/.test(pincode)) {
            errors.pincode = 'PIN code must be 6 digits';
            isValid = false;
        }

        // Images validation
        if (this.selectedImages.length === 0) {
            errors.images = 'At least one image is required';
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

    // Submit property
    async submitProperty(formData) {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            // Prepare property data
            const propertyData = {
                title: formData.get('title'),
                property_type: formData.get('property_type'),
                bhk: parseInt(formData.get('bhk')),
                area: parseFloat(formData.get('area')),
                price: parseFloat(formData.get('price')),
                furnishing: formData.get('furnishing'),
                description: formData.get('description'),
                address: formData.get('address'),
                city: formData.get('city'),
                state: formData.get('state'),
                pincode: formData.get('pincode'),
                images_count: this.selectedImages.length
            };

            // Submit to backend
            const response = await fetch(`${this.apiBaseUrl}/properties/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(propertyData)
            });

            const data = await response.json();

            if (response.ok) {
                // Display AI analysis if available
                if (data.ai_analysis) {
                    this.displayAIAnalysis(data.ai_analysis);
                }

                authManager.showMessage('Property listed successfully!', 'success');
                
                // Redirect to property details after delay
                setTimeout(() => {
                    window.location.href = `/properties/${data.property.id}`;
                }, 3000);
                
                return { success: true, data };
            } else {
                throw new Error(data.detail || 'Failed to create property');
            }
        } catch (error) {
            console.error('Error submitting property:', error);
            authManager.showMessage(error.message || 'Failed to create property', 'error');
            return { success: false, error: error.message };
        }
    }

    // Display AI analysis
    displayAIAnalysis(analysis) {
        const aiAnalysis = document.getElementById('aiAnalysis');
        const analysisResults = document.getElementById('analysisResults');

        if (!aiAnalysis || !analysisResults) return;

        const results = [
            {
                label: 'Price Analysis',
                score: analysis.price_score || 0,
                description: 'Market price comparison'
            },
            {
                label: 'Location Score',
                score: analysis.location_score || 0,
                description: 'Area desirability rating'
            },
            {
                label: 'Property Quality',
                score: analysis.quality_score || 0,
                description: 'Overall property assessment'
            },
            {
                label: 'Market Demand',
                score: analysis.demand_score || 0,
                description: 'Expected interest level'
            }
        ];

        const resultsHTML = results.map(result => {
            const scorePercent = Math.round(result.score * 100);
            let scoreClass = 'good';
            if (scorePercent < 50) scoreClass = 'error';
            else if (scorePercent < 75) scoreClass = 'warning';

            return `
                <div class="analysis-item">
                    <div class="analysis-score ${scoreClass}">${scorePercent}%</div>
                    <div class="analysis-label">${result.label}</div>
                    <p style="font-size: 0.8rem; color: #666; margin-top: 5px;">${result.description}</p>
                </div>
            `;
        }).join('');

        analysisResults.innerHTML = resultsHTML;
        aiAnalysis.classList.add('show');
    }
}

// Global functions
function initializeAddProperty() {
    window.addPropertyManager = new AddPropertyManager();
    
    // Check KYC status
    checkKYCRequirement();

    // Setup form submission
    const propertyForm = document.getElementById('propertyForm');
    const submitButton = document.getElementById('submitButton');

    if (propertyForm) {
        propertyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(propertyForm);
            
            // Clear previous errors
            addPropertyManager.clearFormErrors();
            
            // Validate form
            if (!addPropertyManager.validatePropertyForm(formData)) {
                return;
            }
            
            // Show loading state
            submitButton.classList.add('loading');
            submitButton.disabled = true;
            
            // Submit property
            const result = await addPropertyManager.submitProperty(formData);
            
            // Reset loading state
            submitButton.classList.remove('loading');
            submitButton.disabled = false;
        });
    }
}

async function checkKYCRequirement() {
    const kycWarning = document.getElementById('kycWarning');
    const propertyForm = document.querySelector('.property-form');
    
    if (window.addPropertyManager) {
        const isKYCVerified = await addPropertyManager.checkKYCStatus();
        
        if (!isKYCVerified) {
            kycWarning.classList.add('show');
            propertyForm.style.display = 'none';
        }
    }
}

function removeImage(index) {
    if (window.addPropertyManager) {
        window.addPropertyManager.removeImage(index);
    }
}

// Export for use in other files
window.initializeAddProperty = initializeAddProperty;
