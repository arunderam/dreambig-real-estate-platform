// Property Details JavaScript Module
class PropertyDetailsManager {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.propertyId = null;
        this.property = null;
        this.isFavorite = false;
    }

    // Load property details
    async loadPropertyDetails(propertyId) {
        this.propertyId = propertyId;
        
        try {
            const token = await authManager.getCurrentUserToken();
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${this.apiBaseUrl}/properties/${propertyId}`, {
                headers: headers
            });

            if (response.ok) {
                const data = await response.json();
                this.property = data.property;
                this.displayPropertyDetails(data);
                
                // Load similar properties if available
                if (data.similar_properties && data.similar_properties.length > 0) {
                    this.displaySimilarProperties(data.similar_properties);
                }
                
                // Check if property is in favorites
                if (token) {
                    this.checkFavoriteStatus();
                }
            } else if (response.status === 404) {
                this.displayError('Property not found');
            } else {
                throw new Error('Failed to load property details');
            }
        } catch (error) {
            console.error('Error loading property details:', error);
            this.displayError('Failed to load property details. Please try again.');
        }
    }

    // Display property details
    displayPropertyDetails(data) {
        const property = data.property;
        
        // Update header
        this.updatePropertyHeader(property);
        
        // Update details grid
        this.updateDetailsGrid(property);
        
        // Update description
        document.getElementById('propertyDescription').textContent = property.description || 'No description available.';
        
        // Update owner info
        this.updateOwnerInfo(property);
        
        // Show content
        document.getElementById('propertyContent').style.display = 'grid';
    }

    // Update property header
    updatePropertyHeader(property) {
        const header = document.getElementById('propertyHeader');
        const formattedPrice = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(property.price);

        header.innerHTML = `
            <div class="property-title">${property.title}</div>
            <div class="property-location">
                <i class="fas fa-map-marker-alt"></i>
                ${property.address}, ${property.city}, ${property.state} - ${property.pincode}
            </div>
            <div class="property-price">${formattedPrice}</div>
            <div class="property-actions">
                <button class="action-btn btn-primary" onclick="contactOwner()">
                    <i class="fas fa-phone"></i>
                    Contact Owner
                </button>
                <button class="action-btn btn-secondary" onclick="scheduleVisit()">
                    <i class="fas fa-calendar"></i>
                    Schedule Visit
                </button>
                <button class="action-btn btn-favorite ${this.isFavorite ? 'active' : ''}" 
                        onclick="toggleFavorite()" id="favoriteBtn">
                    <i class="fas fa-heart"></i>
                    ${this.isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
                </button>
                <button class="action-btn btn-secondary" onclick="shareProperty()">
                    <i class="fas fa-share"></i>
                    Share
                </button>
            </div>
        `;
    }

    // Update details grid
    updateDetailsGrid(property) {
        const grid = document.getElementById('propertyDetailsGrid');
        
        const details = [
            {
                icon: 'fas fa-bed',
                label: 'Bedrooms',
                value: `${property.bhk} BHK`
            },
            {
                icon: 'fas fa-expand-arrows-alt',
                label: 'Area',
                value: `${property.area} sq ft`
            },
            {
                icon: 'fas fa-couch',
                label: 'Furnishing',
                value: property.furnishing
            },
            {
                icon: 'fas fa-home',
                label: 'Property Type',
                value: property.property_type
            },
            {
                icon: 'fas fa-check-circle',
                label: 'Status',
                value: property.status
            },
            {
                icon: 'fas fa-shield-alt',
                label: 'Verified',
                value: property.is_verified ? 'Yes' : 'No'
            }
        ];

        grid.innerHTML = details.map(detail => `
            <div class="detail-item">
                <div class="detail-icon">
                    <i class="${detail.icon}"></i>
                </div>
                <div class="detail-label">${detail.label}</div>
                <div class="detail-value">${detail.value}</div>
            </div>
        `).join('');
    }

    // Update owner info
    updateOwnerInfo(property) {
        const ownerInfo = document.getElementById('ownerInfo');
        
        // For now, we'll show placeholder owner info since the API doesn't return owner details
        ownerInfo.innerHTML = `
            <div class="owner-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="owner-details">
                <h4>Property Owner</h4>
                <p>Verified Owner</p>
                <p><i class="fas fa-star"></i> 4.8 Rating</p>
            </div>
        `;
    }

    // Check favorite status
    async checkFavoriteStatus() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/users/favorites`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const favorites = await response.json();
                this.isFavorite = favorites.includes(this.propertyId);
                this.updateFavoriteButton();
            }
        } catch (error) {
            console.error('Error checking favorite status:', error);
        }
    }

    // Update favorite button
    updateFavoriteButton() {
        const btn = document.getElementById('favoriteBtn');
        if (btn) {
            btn.className = `action-btn btn-favorite ${this.isFavorite ? 'active' : ''}`;
            btn.innerHTML = `
                <i class="fas fa-heart"></i>
                ${this.isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
            `;
        }
    }

    // Toggle favorite
    async toggleFavorite() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                authManager.showMessage('Please log in to add favorites', 'error');
                return;
            }

            const method = this.isFavorite ? 'DELETE' : 'POST';
            const endpoint = `${this.apiBaseUrl}/users/favorites/${this.propertyId}`;

            const response = await fetch(endpoint, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.isFavorite = !this.isFavorite;
                this.updateFavoriteButton();
                
                const message = this.isFavorite ? 'Added to favorites' : 'Removed from favorites';
                authManager.showMessage(message, 'success');
            } else {
                throw new Error('Failed to update favorites');
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            authManager.showMessage('Failed to update favorites', 'error');
        }
    }

    // Display similar properties
    displaySimilarProperties(similarProperties) {
        const similarSection = document.getElementById('similarProperties');
        const similarGrid = document.getElementById('similarGrid');

        if (!similarProperties || similarProperties.length === 0) {
            return;
        }

        // Load property details for similar properties
        this.loadSimilarPropertyDetails(similarProperties);
        
        similarSection.style.display = 'block';
    }

    // Load similar property details
    async loadSimilarPropertyDetails(similarProperties) {
        const similarGrid = document.getElementById('similarGrid');
        
        try {
            const propertyPromises = similarProperties.map(async (similar) => {
                const response = await fetch(`${this.apiBaseUrl}/properties/${similar.property_id}`);
                if (response.ok) {
                    const data = await response.json();
                    return data.property;
                }
                return null;
            });

            const properties = await Promise.all(propertyPromises);
            const validProperties = properties.filter(p => p !== null);

            if (validProperties.length > 0) {
                this.displaySimilarGrid(validProperties);
            }
        } catch (error) {
            console.error('Error loading similar properties:', error);
        }
    }

    // Display similar properties grid
    displaySimilarGrid(properties) {
        const similarGrid = document.getElementById('similarGrid');
        
        const propertiesHTML = properties.map(property => {
            const formattedPrice = new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
            }).format(property.price);

            return `
                <div class="similar-card" onclick="viewProperty(${property.id})">
                    <div class="similar-image">
                        <i class="fas fa-home"></i>
                    </div>
                    <div class="similar-content">
                        <div class="similar-title">${property.title}</div>
                        <p style="color: #666; margin-bottom: 10px;">
                            <i class="fas fa-map-marker-alt"></i> ${property.city}
                        </p>
                        <p style="color: #666; margin-bottom: 10px;">
                            ${property.bhk} BHK • ${property.area} sq ft
                        </p>
                        <div class="similar-price">${formattedPrice}</div>
                    </div>
                </div>
            `;
        }).join('');

        similarGrid.innerHTML = propertiesHTML;
    }

    // Display error
    displayError(message) {
        const header = document.getElementById('propertyHeader');
        header.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ff4757; margin-bottom: 20px;"></i>
                <h3>Error</h3>
                <p>${message}</p>
                <button class="action-btn btn-primary" onclick="window.location.href='/properties'">
                    Back to Properties
                </button>
            </div>
        `;
    }
}

// Global functions
function initializePropertyDetails(propertyId) {
    window.propertyDetailsManager = new PropertyDetailsManager();
    propertyDetailsManager.loadPropertyDetails(propertyId);
}

function toggleFavorite() {
    if (window.propertyDetailsManager) {
        window.propertyDetailsManager.toggleFavorite();
    }
}

function viewProperty(propertyId) {
    window.location.href = `/properties/${propertyId}`;
}

function contactOwner() {
    authManager.showMessage('Contact feature coming soon!', 'info');
}

function scheduleVisit() {
    authManager.showMessage('Visit scheduling feature coming soon!', 'info');
}

function shareProperty() {
    if (navigator.share) {
        navigator.share({
            title: document.querySelector('.property-title')?.textContent || 'Property',
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            authManager.showMessage('Property link copied to clipboard!', 'success');
        });
    }
}

// Export for use in other files
window.initializePropertyDetails = initializePropertyDetails;
