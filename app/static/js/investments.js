// Investments JavaScript Module
class InvestmentsManager {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.currentTab = 'my-investments';
        this.loadPortfolioSummary();
        this.loadMyInvestments();
    }

    // Load portfolio summary
    async loadPortfolioSummary() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/investments/analytics`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const analytics = await response.json();
                this.displayPortfolioSummary(analytics);
            }
        } catch (error) {
            console.error('Error loading portfolio summary:', error);
            this.displayDefaultSummary();
        }
    }

    // Display portfolio summary
    displayPortfolioSummary(analytics) {
        const totalInvestments = document.getElementById('totalInvestments');
        const totalValue = document.getElementById('totalValue');
        const avgROI = document.getElementById('avgROI');
        const monthlyReturns = document.getElementById('monthlyReturns');

        if (totalInvestments) {
            totalInvestments.textContent = analytics.total_investments || 0;
        }
        
        if (totalValue) {
            const formattedValue = new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
            }).format(analytics.total_value || 0);
            totalValue.textContent = formattedValue;
        }
        
        if (avgROI) {
            avgROI.textContent = `${(analytics.average_roi || 0).toFixed(1)}%`;
        }
        
        if (monthlyReturns) {
            const formattedReturns = new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
            }).format(analytics.monthly_returns || 0);
            monthlyReturns.textContent = formattedReturns;
        }
    }

    // Display default summary when no data
    displayDefaultSummary() {
        const elements = ['totalInvestments', 'totalValue', 'avgROI', 'monthlyReturns'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = id === 'totalInvestments' ? '0' : 
                                   id === 'avgROI' ? '0%' : '₹0';
            }
        });
    }

    // Load my investments
    async loadMyInvestments() {
        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/investments/`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const investments = await response.json();
                this.displayMyInvestments(investments);
            } else {
                throw new Error('Failed to load investments');
            }
        } catch (error) {
            console.error('Error loading investments:', error);
            this.displayEmptyInvestments();
        }
    }

    // Display my investments
    displayMyInvestments(investments) {
        const grid = document.getElementById('myInvestmentsGrid');
        if (!grid) return;

        if (!investments || investments.length === 0) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-chart-line" style="font-size: 3rem; color: #ccc; margin-bottom: 20px;"></i>
                    <h3>No investments yet</h3>
                    <p>Start building your real estate investment portfolio</p>
                    <button class="auth-button" onclick="addInvestment()" style="margin-top: 20px;">
                        Add Your First Investment
                    </button>
                </div>
            `;
            return;
        }

        const investmentsHTML = investments.map(investment => this.createInvestmentCard(investment)).join('');
        grid.innerHTML = investmentsHTML;
    }

    // Display empty investments message
    displayEmptyInvestments() {
        const grid = document.getElementById('myInvestmentsGrid');
        if (grid) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ff4757; margin-bottom: 20px;"></i>
                    <h3>Unable to load investments</h3>
                    <p>Please try again later</p>
                </div>
            `;
        }
    }

    // Create investment card HTML
    createInvestmentCard(investment) {
        const formattedAmount = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(investment.amount);

        const formattedCurrentValue = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(investment.current_value || investment.amount);

        const roi = investment.roi || 0;
        const roiClass = roi >= 0 ? 'positive' : 'negative';

        return `
            <div class="investment-card" onclick="viewInvestment(${investment.id})">
                <div class="investment-image">
                    <i class="fas fa-chart-line"></i>
                    <div class="investment-badge">${investment.investment_type || 'Property'}</div>
                </div>
                <div class="investment-content">
                    <div class="investment-title">${investment.title || 'Investment Property'}</div>
                    <div class="investment-location">
                        <i class="fas fa-map-marker-alt"></i>
                        ${investment.location || 'Location not specified'}
                    </div>
                    <div class="investment-details">
                        <div class="detail-item">
                            <div class="detail-value">${formattedAmount}</div>
                            <div class="detail-label">Invested</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-value">${formattedCurrentValue}</div>
                            <div class="detail-label">Current Value</div>
                        </div>
                    </div>
                    <div class="investment-details">
                        <div class="detail-item">
                            <div class="detail-value ${roiClass}">${roi.toFixed(1)}%</div>
                            <div class="detail-label">ROI</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-value">${investment.duration || 'N/A'}</div>
                            <div class="detail-label">Duration</div>
                        </div>
                    </div>
                    <div class="investment-actions" onclick="event.stopPropagation()">
                        <button class="action-button btn-primary" onclick="viewInvestment(${investment.id})">
                            View Details
                        </button>
                        <button class="action-button btn-secondary" onclick="editInvestment(${investment.id})">
                            Edit
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Load investment opportunities
    async loadInvestmentOpportunities() {
        try {
            const token = await authManager.getCurrentUserToken();
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${this.apiBaseUrl}/investments/opportunities`, {
                headers: headers
            });

            if (response.ok) {
                const opportunities = await response.json();
                this.displayOpportunities(opportunities);
            } else {
                throw new Error('Failed to load opportunities');
            }
        } catch (error) {
            console.error('Error loading opportunities:', error);
            this.displayEmptyOpportunities();
        }
    }

    // Display investment opportunities
    displayOpportunities(opportunities) {
        const grid = document.getElementById('opportunitiesGrid');
        if (!grid) return;

        if (!opportunities || opportunities.length === 0) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-search" style="font-size: 3rem; color: #ccc; margin-bottom: 20px;"></i>
                    <h3>No opportunities available</h3>
                    <p>Check back later for new investment opportunities</p>
                </div>
            `;
            return;
        }

        const opportunitiesHTML = opportunities.map(opportunity => this.createOpportunityCard(opportunity)).join('');
        grid.innerHTML = opportunitiesHTML;
    }

    // Display empty opportunities
    displayEmptyOpportunities() {
        const grid = document.getElementById('opportunitiesGrid');
        if (grid) {
            grid.innerHTML = `
                <div class="empty-message">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ff4757; margin-bottom: 20px;"></i>
                    <h3>Unable to load opportunities</h3>
                    <p>Please try again later</p>
                </div>
            `;
        }
    }

    // Create opportunity card HTML
    createOpportunityCard(opportunity) {
        const formattedMinInvestment = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(opportunity.min_investment || 0);

        const expectedROI = opportunity.expected_roi || 0;

        return `
            <div class="investment-card" onclick="viewOpportunity(${opportunity.id})">
                <div class="investment-image">
                    <i class="fas fa-building"></i>
                    <div class="investment-badge">Opportunity</div>
                </div>
                <div class="investment-content">
                    <div class="investment-title">${opportunity.title || 'Investment Opportunity'}</div>
                    <div class="investment-location">
                        <i class="fas fa-map-marker-alt"></i>
                        ${opportunity.location || 'Location not specified'}
                    </div>
                    <div class="investment-details">
                        <div class="detail-item">
                            <div class="detail-value">${formattedMinInvestment}</div>
                            <div class="detail-label">Min Investment</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-value">${expectedROI.toFixed(1)}%</div>
                            <div class="detail-label">Expected ROI</div>
                        </div>
                    </div>
                    <div class="investment-details">
                        <div class="detail-item">
                            <div class="detail-value">${opportunity.risk_level || 'Medium'}</div>
                            <div class="detail-label">Risk Level</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-value">${opportunity.duration || 'N/A'}</div>
                            <div class="detail-label">Duration</div>
                        </div>
                    </div>
                    <div class="investment-actions" onclick="event.stopPropagation()">
                        <button class="action-button btn-primary" onclick="investNow(${opportunity.id})">
                            Invest Now
                        </button>
                        <button class="action-button btn-secondary" onclick="viewOpportunity(${opportunity.id})">
                            Learn More
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Load investment analytics
    async loadInvestmentAnalytics() {
        const analyticsTab = document.getElementById('analyticsTab');
        if (!analyticsTab) return;

        analyticsTab.innerHTML = `
            <div class="loading-message">Loading analytics...</div>
        `;

        try {
            const token = await authManager.getCurrentUserToken();
            if (!token) {
                analyticsTab.innerHTML = `
                    <div class="empty-message">
                        <h3>Login Required</h3>
                        <p>Please log in to view your investment analytics</p>
                    </div>
                `;
                return;
            }

            const response = await fetch(`${this.apiBaseUrl}/investments/analytics`, {
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
            analyticsTab.innerHTML = `
                <div class="empty-message">
                    <h3>Unable to load analytics</h3>
                    <p>Please try again later</p>
                </div>
            `;
        }
    }

    // Display analytics
    displayAnalytics(analytics) {
        const analyticsTab = document.getElementById('analyticsTab');
        if (!analyticsTab) return;

        analyticsTab.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);">
                    <h3 style="margin-bottom: 20px; color: #333;">Performance Overview</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                            <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">${(analytics.total_return || 0).toFixed(1)}%</div>
                            <div style="color: #666; font-size: 0.9rem;">Total Return</div>
                        </div>
                        <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                            <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">${(analytics.annualized_return || 0).toFixed(1)}%</div>
                            <div style="color: #666; font-size: 0.9rem;">Annualized Return</div>
                        </div>
                    </div>
                </div>
                
                <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);">
                    <h3 style="margin-bottom: 20px; color: #333;">Portfolio Breakdown</h3>
                    <div style="display: grid; gap: 10px;">
                        <div style="display: flex; justify-content: space-between; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                            <span>Residential</span>
                            <span>${(analytics.residential_percentage || 0).toFixed(1)}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                            <span>Commercial</span>
                            <span>${(analytics.commercial_percentage || 0).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

// Global functions
function initializeInvestments() {
    window.investmentsManager = new InvestmentsManager();
}

function loadInvestmentOpportunities() {
    if (window.investmentsManager) {
        window.investmentsManager.loadInvestmentOpportunities();
    }
}

function loadInvestmentAnalytics() {
    if (window.investmentsManager) {
        window.investmentsManager.loadInvestmentAnalytics();
    }
}

function viewInvestment(investmentId) {
    window.location.href = `/investments/${investmentId}`;
}

function editInvestment(investmentId) {
    window.location.href = `/investments/${investmentId}/edit`;
}

function viewOpportunity(opportunityId) {
    window.location.href = `/investment-opportunities/${opportunityId}`;
}

function investNow(opportunityId) {
    window.location.href = `/invest/${opportunityId}`;
}

// Export for use in other files
window.initializeInvestments = initializeInvestments;
