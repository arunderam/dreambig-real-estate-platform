// Services JavaScript Module
class ServicesManager {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.currentFilters = {};
        this.loadServices();
    }

    // Load services
    async loadServices() {
        try {
            const params = new URLSearchParams();
            
            // Add filters
            Object.keys(this.currentFilters).forEach(key => {
                if (this.currentFilters[key]) {
                    params.append(key, this.currentFilters[key]);
                }
            });

            const response = await fetch(`${this.apiBaseUrl}/services/?${params.toString()}`);
            
            if (response.ok) {
                const services = await response.json();
                this.displayServices(services);
            } else {
                throw new Error('Failed to load services');
            }
        } catch (error) {
            console.error('Error loading services:', error);
            this.displayError('Failed to load services. Please try again.');
        }
    }

    // Display services
    displayServices(services) {
        const grid = document.getElementById('servicesGrid');
        if (!grid) return;

        if (!services || services.length === 0) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-tools" style="font-size: 3rem; color: #ccc; margin-bottom: 20px;"></i>
                    <h3>No services found</h3>
                    <p>Try adjusting your search filters or search terms</p>
                </div>
            `;
            return;
        }

        const servicesHTML = services.map(service => this.createServiceCard(service)).join('');
        grid.innerHTML = servicesHTML;
    }

    // Create service card HTML
    createServiceCard(service) {
        const formattedPrice = service.price ? 
            new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
            }).format(service.price) : 'Contact for Price';

        const rating = service.rating || 4.5;
        const starsHTML = this.generateStars(rating);

        return `
            <div class="service-card" onclick="viewService(${service.id})">
                <div class="service-image">
                    <i class="fas fa-${this.getServiceIcon(service.service_type)}"></i>
                    <div class="service-badge">${service.service_type || 'Service'}</div>
                </div>
                <div class="service-content">
                    <div class="service-title">${service.name}</div>
                    <div class="service-provider">
                        <i class="fas fa-envelope"></i>
                        ${service.email}
                    </div>
                    <div class="service-description">
                        <i class="fas fa-info-circle"></i>
                        ${service.description || 'Professional service provider'}
                    </div>
                    <div class="service-details">
                        <span><i class="fas fa-phone"></i> ${service.contact_number}</span>
                        <span><i class="fas fa-shield-alt"></i> ${service.is_verified ? 'Verified' : 'Unverified'}</span>
                    </div>
                    <div class="service-actions" onclick="event.stopPropagation()">
                        <button class="action-button btn-primary" onclick="bookService(${service.id})">
                            Book Now
                        </button>
                        <button class="action-button btn-secondary" onclick="viewService(${service.id})">
                            View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Get service icon based on service type
    getServiceIcon(serviceType) {
        const icons = {
            'legal': 'gavel',
            'financial': 'calculator',
            'maintenance': 'tools',
            'inspection': 'search',
            'cleaning': 'broom',
            'security': 'shield-alt',
            'landscaping': 'leaf',
            'electrical': 'bolt',
            'plumbing': 'wrench',
            'painting': 'paint-brush',
            'hvac': 'fan',
            'moving': 'truck',
            'interior': 'couch',
            'pest_control': 'bug',
            'default': 'concierge-bell'
        };
        return icons[serviceType] || icons.default;
    }

    // Generate star rating HTML
    generateStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        let starsHTML = '';

        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star" style="color: #ffc107;"></i>';
        }

        if (hasHalfStar) {
            starsHTML += '<i class="fas fa-star-half-alt" style="color: #ffc107;"></i>';
        }

        const emptyStars = 5 - Math.ceil(rating);
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star" style="color: #ffc107;"></i>';
        }

        return starsHTML;
    }

    // Search services
    async searchServices() {
        const searchInput = document.getElementById('searchInput');
        const categoryFilter = document.getElementById('categoryFilter');
        const locationFilter = document.getElementById('locationFilter');
        const priceFilter = document.getElementById('priceFilter');
        const ratingFilter = document.getElementById('ratingFilter');

        // Build filters
        this.currentFilters = {};
        
        if (searchInput?.value) this.currentFilters.query = searchInput.value;
        if (categoryFilter?.value) this.currentFilters.category = categoryFilter.value;
        if (locationFilter?.value) this.currentFilters.location = locationFilter.value;
        if (priceFilter?.value) this.currentFilters.price_range = priceFilter.value;
        if (ratingFilter?.value) this.currentFilters.min_rating = parseFloat(ratingFilter.value);

        // Load services with filters
        await this.loadServices();
    }

    // Display error
    displayError(message) {
        const grid = document.getElementById('servicesGrid');
        if (grid) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ff4757; margin-bottom: 20px;"></i>
                    <h3>Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    // Book service
    async bookService(serviceId) {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                authManager.showMessage('Please log in to book services', 'error');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
                return;
            }

            // Show booking modal
            this.showBookingModal(serviceId);

        } catch (error) {
            console.error('Error booking service:', error);
            authManager.showMessage('Failed to book service. Please try again.', 'error');
        }
    }

    // Show booking modal
    showBookingModal(serviceId) {
        const modal = document.createElement('div');
        modal.className = 'booking-modal-overlay';
        modal.innerHTML = `
            <div class="booking-modal">
                <div class="booking-modal-header">
                    <h3>Book Service</h3>
                    <button class="close-modal" onclick="this.closest('.booking-modal-overlay').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="booking-modal-body">
                    <form id="serviceBookingForm">
                        <div class="form-group">
                            <label>Service Type</label>
                            <select id="serviceType" required>
                                <option value="">Select Service Type</option>
                                <option value="cleaning">Cleaning</option>
                                <option value="maintenance">Maintenance</option>
                                <option value="security">Security</option>
                                <option value="landscaping">Landscaping</option>
                                <option value="interior_design">Interior Design</option>
                                <option value="legal">Legal Services</option>
                                <option value="financial">Financial Services</option>
                                <option value="inspection">Inspection</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Property (Optional)</label>
                            <select id="propertyId">
                                <option value="">Select Property</option>
                                <option value="1">Property 1</option>
                                <option value="2">Property 2</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Service Details</label>
                            <div class="details-grid">
                                <input type="text" id="serviceRequested" placeholder="Service Requested" required>
                                <input type="date" id="preferredDate" required>
                                <input type="time" id="preferredTime" required>
                                <select id="urgency">
                                    <option value="low">Low Priority</option>
                                    <option value="medium" selected>Medium Priority</option>
                                    <option value="high">High Priority</option>
                                    <option value="urgent">Urgent</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="description" rows="3" placeholder="Describe your requirements..."></textarea>
                        </div>

                        <div class="form-group">
                            <label>Estimated Duration</label>
                            <select id="estimatedDuration">
                                <option value="1 hour">1 Hour</option>
                                <option value="2 hours" selected>2 Hours</option>
                                <option value="3 hours">3 Hours</option>
                                <option value="4 hours">4 Hours</option>
                                <option value="Half day">Half Day</option>
                                <option value="Full day">Full Day</option>
                            </select>
                        </div>

                        <div class="booking-actions">
                            <button type="button" class="btn-secondary" onclick="this.closest('.booking-modal-overlay').remove()">
                                Cancel
                            </button>
                            <button type="submit" class="btn-primary">
                                Book Service
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Add modal styles
        if (!document.getElementById('booking-modal-styles')) {
            const styles = document.createElement('style');
            styles.id = 'booking-modal-styles';
            styles.textContent = `
                .booking-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                .booking-modal {
                    background: white;
                    border-radius: 15px;
                    width: 90%;
                    max-width: 600px;
                    max-height: 90vh;
                    overflow-y: auto;
                }
                .booking-modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid #eee;
                }
                .booking-modal-body {
                    padding: 20px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 600;
                    color: #333;
                }
                .form-group input, .form-group select, .form-group textarea {
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    font-size: 1rem;
                }
                .details-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                }
                .booking-actions {
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                    margin-top: 20px;
                }
                .close-modal {
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    color: #666;
                }
                @media (max-width: 768px) {
                    .details-grid {
                        grid-template-columns: 1fr;
                    }
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(modal);

        // Handle form submission
        const form = document.getElementById('serviceBookingForm');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitServiceBooking(serviceId, modal);
        });

        // Set minimum date to today
        const dateInput = document.getElementById('preferredDate');
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
        dateInput.value = today;

        // Set default time
        const timeInput = document.getElementById('preferredTime');
        timeInput.value = '10:00';
    }

    // Submit service booking
    async submitServiceBooking(serviceId, modal) {
        try {
            const token = await authManager.getCurrentUserToken();

            const bookingData = {
                service_type: document.getElementById('serviceType').value,
                service_provider_id: parseInt(serviceId),
                property_id: document.getElementById('propertyId').value ?
                    parseInt(document.getElementById('propertyId').value) : null,
                details: {
                    service_requested: document.getElementById('serviceRequested').value,
                    preferred_date: document.getElementById('preferredDate').value,
                    preferred_time: document.getElementById('preferredTime').value,
                    description: document.getElementById('description').value,
                    urgency: document.getElementById('urgency').value,
                    estimated_duration: document.getElementById('estimatedDuration').value
                }
            };

            const response = await fetch(`${this.apiBaseUrl}/services/bookings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(bookingData)
            });

            if (response.ok) {
                const result = await response.json();
                authManager.showMessage('Service booked successfully! You will receive a confirmation shortly.', 'success');
                modal.remove();

                // Optionally redirect to bookings page
                setTimeout(() => {
                    if (confirm('Would you like to view your bookings?')) {
                        window.location.href = '/dashboard#bookings';
                    }
                }, 2000);
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to book service');
            }
        } catch (error) {
            console.error('Error submitting booking:', error);
            authManager.showMessage(`Failed to book service: ${error.message}`, 'error');
        }
    }
}

// Global functions
function initializeServices() {
    window.servicesManager = new ServicesManager();

    // Setup search on Enter key
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchServices();
            }
        });
    }

    // Setup filter change listeners
    const filters = ['categoryFilter', 'locationFilter', 'priceFilter', 'ratingFilter'];
    filters.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', () => {
                searchServices();
            });
        }
    });
}

function searchServices() {
    if (window.servicesManager) {
        window.servicesManager.searchServices();
    }
}

function viewService(serviceId) {
    window.location.href = `/services/${serviceId}`;
}

function bookService(serviceId) {
    if (window.servicesManager) {
        window.servicesManager.bookService(serviceId);
    }
}

// Export for use in other files
window.initializeServices = initializeServices;
