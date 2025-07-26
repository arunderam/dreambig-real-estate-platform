// Properties Management JavaScript Module
class PropertiesManager {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.currentPage = 0;
        this.pageSize = 12;
        this.currentFilters = {};
        this.userFavorites = new Set();
        this.setupSearchSuggestions();
        this.loadUserFavorites();
    }

    // Setup search suggestions
    setupSearchSuggestions() {
        const searchInput = document.getElementById('searchInput');
        const suggestionsDropdown = document.getElementById('suggestionsDropdown');

        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.getSearchSuggestions(e.target.value);
                }, 300);
            });

            // Hide suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!searchInput.contains(e.target) && !suggestionsDropdown.contains(e.target)) {
                    suggestionsDropdown.style.display = 'none';
                }
            });
        }
    }

    // Get AI-powered search suggestions
    async getSearchSuggestions(query) {
        if (!query || query.length < 2) {
            document.getElementById('suggestionsDropdown').style.display = 'none';
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/search/smart-suggestions?query=${encodeURIComponent(query)}`);
            
            if (response.ok) {
                const suggestions = await response.json();
                this.displaySuggestions(suggestions);
            }
        } catch (error) {
            console.error('Error getting suggestions:', error);
        }
    }

    // Display search suggestions
    displaySuggestions(suggestions) {
        const dropdown = document.getElementById('suggestionsDropdown');
        if (!dropdown) return;

        let suggestionsHTML = '';

        // Add location suggestions
        if (suggestions.locations && suggestions.locations.size > 0) {
            Array.from(suggestions.locations).slice(0, 3).forEach(location => {
                suggestionsHTML += `
                    <div class="suggestion-item" onclick="selectSuggestion('${location}')">
                        <i class="fas fa-map-marker-alt"></i> ${location}
                    </div>
                `;
            });
        }

        // Add property type suggestions
        if (suggestions.property_types && suggestions.property_types.size > 0) {
            Array.from(suggestions.property_types).slice(0, 2).forEach(type => {
                suggestionsHTML += `
                    <div class="suggestion-item" onclick="selectSuggestion('${type}')">
                        <i class="fas fa-home"></i> ${type}
                    </div>
                `;
            });
        }

        if (suggestionsHTML) {
            dropdown.innerHTML = suggestionsHTML;
            dropdown.style.display = 'block';
        } else {
            dropdown.style.display = 'none';
        }
    }

    // Load user favorites
    async loadUserFavorites() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                console.log('No token available, skipping favorites load');
                return;
            }

            const response = await fetch(`${this.apiBaseUrl}/users/favorites`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const favorites = await response.json();
                this.userFavorites = new Set(favorites);
                console.log(`Loaded ${favorites.length} favorites`);
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('Failed to load favorites:', response.status, errorData);

                // Don't show error message for 401 (unauthorized) as user might not be logged in
                if (response.status !== 401) {
                    authManager.showMessage('Failed to load favorites', 'warning');
                }
            }
        } catch (error) {
            console.error('Error loading favorites:', error);
            // Only show error if it's not a network issue during page load
            if (error.name !== 'TypeError') {
                authManager.showMessage('Failed to load favorites', 'warning');
            }
        }
    }

    // Load properties with filters
    async loadProperties(page = 0) {
        try {
            this.currentPage = page;
            const skip = page * this.pageSize;
            
            // Build query parameters
            const params = new URLSearchParams({
                skip: skip.toString(),
                limit: this.pageSize.toString()
            });

            // Add filters
            Object.keys(this.currentFilters).forEach(key => {
                if (this.currentFilters[key]) {
                    params.append(key, this.currentFilters[key]);
                }
            });

            const response = await fetch(`${this.apiBaseUrl}/search/?${params.toString()}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayProperties(data.properties);
                this.updatePagination(data.has_more);
                
                // Display recommendations if available
                if (data.recommendations && data.recommendations.length > 0) {
                    this.displayRecommendations(data.recommendations);
                }
            } else {
                throw new Error('Failed to load properties');
            }
        } catch (error) {
            console.error('Error loading properties:', error);
            this.displayError('Failed to load properties. Please try again.');
        }
    }

    // Display properties
    displayProperties(properties) {
        const grid = document.getElementById('propertiesGrid');
        const resultsHeader = document.getElementById('resultsHeader');
        const propertyCount = document.getElementById('propertyCount');

        if (!grid) return;

        if (!properties || properties.length === 0) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-search-location"></i>
                    <h3>No properties found</h3>
                    <p>Try adjusting your search filters or search terms to find more properties</p>
                    <button class="action-btn btn-primary" onclick="window.location.href='/add-property'" style="margin-top: 20px;">
                        <i class="fas fa-plus"></i>
                        Add Your Property
                    </button>
                </div>
            `;
            if (resultsHeader) resultsHeader.style.display = 'none';
            return;
        }

        // Store properties for sorting
        this.currentProperties = properties;

        // Update results count
        if (propertyCount) {
            propertyCount.textContent = properties.length;
        }
        if (resultsHeader) {
            resultsHeader.style.display = 'flex';
        }

        const propertiesHTML = properties.map(property => this.createPropertyCard(property)).join('');
        grid.innerHTML = propertiesHTML;
    }

    // Sort properties
    sortProperties() {
        const sortValue = document.getElementById('sortDropdown')?.value;
        if (!this.currentProperties || !sortValue) return;

        let sortedProperties = [...this.currentProperties];

        switch (sortValue) {
            case 'price_asc':
                sortedProperties.sort((a, b) => a.price - b.price);
                break;
            case 'price_desc':
                sortedProperties.sort((a, b) => b.price - a.price);
                break;
            case 'area_desc':
                sortedProperties.sort((a, b) => b.area - a.area);
                break;
            case 'newest':
                sortedProperties.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                break;
            case 'bhk_asc':
                sortedProperties.sort((a, b) => a.bhk - b.bhk);
                break;
        }

        // Re-render with sorted properties
        const grid = document.getElementById('propertiesGrid');
        if (grid) {
            const propertiesHTML = sortedProperties.map(property => this.createPropertyCard(property)).join('');
            grid.innerHTML = propertiesHTML;
        }
    }

    // Create property card HTML
    createPropertyCard(property) {
        const isFavorite = this.userFavorites.has(property.id);

        // Get a sample image based on property type
        const getPropertyImage = (type) => {
            const images = {
                'apartment': 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600&h=400&fit=crop&auto=format',
                'villa': 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop&auto=format',
                'house': 'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=600&h=400&fit=crop&auto=format',
                'commercial': 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&h=400&fit=crop&auto=format'
            };
            return images[type] || images['apartment'];
        };

        // Format furnishing type
        const formatFurnishing = (furnishing) => {
            const types = {
                'furnished': 'Furnished',
                'semi_furnished': 'Semi-Furnished',
                'unfurnished': 'Unfurnished'
            };
            return types[furnishing] || furnishing;
        };

        // Calculate price per sqft
        const pricePerSqft = Math.round(property.price / property.area);

        return `
            <div class="property-card" onclick="viewProperty(${property.id})">
                <div class="property-image" style="background-image: url('${getPropertyImage(property.property_type)}')">
                    <div class="property-badge">${property.property_type}</div>
                    <button class="property-favorite ${isFavorite ? 'active' : ''}"
                            onclick="event.stopPropagation(); toggleFavorite(${property.id})"
                            title="${isFavorite ? 'Remove from favorites' : 'Add to favorites'}">
                        <i class="fas fa-heart"></i>
                    </button>
                </div>
                <div class="property-content">
                    <div class="property-main-info">
                        <div class="property-title">${property.title}</div>
                        <div class="property-location">
                            <i class="fas fa-map-marker-alt"></i>
                            ${property.city}, ${property.state}
                        </div>
                        <div class="property-description">
                            ${property.description || 'Beautiful property in prime location with modern amenities and excellent connectivity.'}
                        </div>
                        <div class="property-specs">
                            <div class="property-spec">
                                <i class="fas fa-bed"></i>
                                ${property.bhk} BHK
                            </div>
                            <div class="property-spec">
                                <i class="fas fa-expand-arrows-alt"></i>
                                ${property.area} sq ft
                            </div>
                            <div class="property-spec">
                                <i class="fas fa-couch"></i>
                                ${formatFurnishing(property.furnishing)}
                            </div>
                        </div>
                    </div>
                    <div class="property-bottom">
                        <div class="property-price">
                            ₹${property.price.toLocaleString()}
                            <div class="price-per-sqft">₹${pricePerSqft.toLocaleString()}/sq ft</div>
                        </div>
                        <div class="property-actions" onclick="event.stopPropagation()">
                            <button class="action-btn btn-primary" onclick="viewProperty(${property.id})">
                                <i class="fas fa-eye"></i>
                                View Details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Toggle favorite
    async toggleFavorite(propertyId) {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                authManager.showMessage('Please log in to add favorites', 'error');
                return;
            }

            const isFavorite = this.userFavorites.has(propertyId);
            const method = isFavorite ? 'DELETE' : 'POST';
            const endpoint = `${this.apiBaseUrl}/users/favorites/${propertyId}`;

            // Show loading state
            const button = document.querySelector(`.property-favorite[onclick*="${propertyId}"]`);
            if (button) {
                button.style.opacity = '0.6';
                button.style.pointerEvents = 'none';
            }

            const response = await fetch(endpoint, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                if (isFavorite) {
                    this.userFavorites.delete(propertyId);
                    authManager.showMessage('Removed from favorites', 'info');
                } else {
                    this.userFavorites.add(propertyId);
                    authManager.showMessage('Added to favorites', 'success');
                }

                // Update the button appearance
                if (button) {
                    button.classList.toggle('active');
                    button.title = isFavorite ? 'Add to favorites' : 'Remove from favorites';
                }
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('Failed to update favorites:', response.status, errorData);

                let errorMessage = 'Failed to update favorites';
                if (response.status === 400 && errorData.detail) {
                    errorMessage = errorData.detail;
                } else if (response.status === 404) {
                    errorMessage = 'Property not found';
                }

                authManager.showMessage(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            authManager.showMessage('Failed to update favorites. Please try again.', 'error');
        } finally {
            // Reset button state
            const button = document.querySelector(`.property-favorite[onclick*="${propertyId}"]`);
            if (button) {
                button.style.opacity = '1';
                button.style.pointerEvents = 'auto';
            }
        }
    }

    // Search properties
    async searchProperties() {
        const searchInput = document.getElementById('searchInput');
        const propertyType = document.getElementById('propertyType');
        const bhkFilter = document.getElementById('bhkFilter');
        const minPrice = document.getElementById('minPrice');
        const maxPrice = document.getElementById('maxPrice');
        const furnishing = document.getElementById('furnishing');
        const locationFilter = document.getElementById('locationFilter');

        // Build filters
        this.currentFilters = {};
        
        if (searchInput?.value) this.currentFilters.query = searchInput.value;
        if (propertyType?.value) this.currentFilters.property_type = propertyType.value;
        if (bhkFilter?.value) this.currentFilters.bhk = parseInt(bhkFilter.value);
        if (minPrice?.value) this.currentFilters.price_min = parseFloat(minPrice.value);
        if (maxPrice?.value) this.currentFilters.price_max = parseFloat(maxPrice.value);
        if (furnishing?.value) this.currentFilters.furnishing = furnishing.value;
        if (locationFilter?.value) this.currentFilters.location = locationFilter.value;

        // Hide suggestions
        document.getElementById('suggestionsDropdown').style.display = 'none';

        // Load properties with filters
        await this.loadProperties(0);
    }

    // Update pagination
    updatePagination(hasMore) {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        let paginationHTML = '';

        // Previous button
        if (this.currentPage > 0) {
            paginationHTML += `
                <button onclick="propertiesManager.loadProperties(${this.currentPage - 1})">
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
            `;
        }

        // Page numbers (simplified)
        const startPage = Math.max(0, this.currentPage - 2);
        const endPage = Math.min(startPage + 4, this.currentPage + 3);

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="${i === this.currentPage ? 'active' : ''}" 
                        onclick="propertiesManager.loadProperties(${i})">
                    ${i + 1}
                </button>
            `;
        }

        // Next button
        if (hasMore) {
            paginationHTML += `
                <button onclick="propertiesManager.loadProperties(${this.currentPage + 1})">
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            `;
        }

        pagination.innerHTML = paginationHTML;
        pagination.style.display = paginationHTML ? 'flex' : 'none';
    }

    // Display error
    displayError(message) {
        const grid = document.getElementById('propertiesGrid');
        if (grid) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-exclamation-triangle" style="color: #ff4757;"></i>
                    <h3>Oops! Something went wrong</h3>
                    <p>${message}</p>
                    <button class="action-btn btn-primary" onclick="window.location.reload()" style="margin-top: 20px;">
                        <i class="fas fa-refresh"></i>
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    // Display recommendations
    displayRecommendations(recommendations) {
        // This could be implemented to show recommendations in a separate section
        console.log('Recommendations:', recommendations);
    }
}

// Global functions
function initializeProperties() {
    window.propertiesManager = new PropertiesManager();

    // Load initial properties
    propertiesManager.loadProperties();

    // Setup search on Enter key
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchProperties();
            }
        });
    }

    // Setup filter change listeners
    const filters = ['propertyType', 'bhkFilter', 'minPrice', 'maxPrice', 'furnishing', 'locationFilter'];
    filters.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', () => {
                searchProperties();
            });
        }
    });

    // Retry loading favorites after a delay if user is authenticated
    setTimeout(() => {
        if (authManager.isAuthenticated() && propertiesManager.userFavorites.size === 0) {
            console.log('Retrying favorites load...');
            propertiesManager.loadUserFavorites();
        }
    }, 2000);
}

function searchProperties() {
    if (window.propertiesManager) {
        window.propertiesManager.searchProperties();
    }
}

function selectSuggestion(suggestion) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = suggestion;
        searchProperties();
    }
}

function viewProperty(propertyId) {
    window.location.href = `/properties/${propertyId}`;
}

function toggleFavorite(propertyId) {
    if (window.propertiesManager) {
        window.propertiesManager.toggleFavorite(propertyId);
    }
}

function addProperty() {
    // Check if user is authenticated and KYC verified
    if (!authManager.isAuthenticated()) {
        authManager.showMessage('Please log in to add a property', 'error');
        setTimeout(() => {
            window.location.href = '/login';
        }, 2000);
        return;
    }

    window.location.href = '/add-property';
}

function sortProperties() {
    if (window.propertiesManager) {
        window.propertiesManager.sortProperties();
    }
}

// Debug function to manually reload favorites
function reloadFavorites() {
    if (window.propertiesManager) {
        console.log('Manually reloading favorites...');
        window.propertiesManager.loadUserFavorites();
    }
}

// Export for use in other files
window.initializeProperties = initializeProperties;
window.reloadFavorites = reloadFavorites;
