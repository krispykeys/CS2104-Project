// Home Value Estimator - Clean Implementation

// Simple page navigation
const pages = {
    'home': 'home-page',
    'demo': 'demo-page',
    'marketplace': 'marketplace-page',
    'property-details': 'property-details-page',
    'pricing': 'pricing-page',
    'signin': 'signin-page',
    'signup': 'signup-page',
    'analyzer': 'analyzer-page',
    'chat': 'chat-page',
    'agent-connect': 'agent-connect-page'
};

let currentPage = 'home';
let selectedProperty = null;

// Sample property data
const PROPERTIES = [
    {
        id: "p_001",
        address1: "123 Oak Street",
        city: "Austin",
        state: "TX",
        zip: "78701",
        beds: 3,
        baths: 2,
        sqft: 1850,
        lotSqft: 7200,
        yearBuilt: 2018,
        hasGarage: true,
        type: "Single Family",
        listPrice: 485000,
        estValue: 510000,
        photo: "hero-house.jpg",
        photos: ["hero-house.jpg", "houses-grid.jpg"]
    },
    {
        id: "p_002",
        address1: "456 Pine Avenue",
        city: "Dallas",
        state: "TX",
        zip: "75201",
        beds: 4,
        baths: 3,
        sqft: 2200,
        lotSqft: 8500,
        yearBuilt: 2020,
        hasGarage: true,
        type: "Single Family",
        listPrice: 625000,
        estValue: 645000,
        photo: "houses-grid.jpg",
        photos: ["houses-grid.jpg", "investment-house.jpg"]
    },
    {
        id: "p_003",
        address1: "789 Maple Drive",
        city: "Houston",
        state: "TX",
        zip: "77001",
        beds: 2,
        baths: 2,
        sqft: 1200,
        lotSqft: 5000,
        yearBuilt: 2015,
        hasGarage: false,
        type: "Condo",
        listPrice: 285000,
        estValue: 295000,
        photo: "investment-house.jpg",
        photos: ["investment-house.jpg", "hero-house.jpg"]
    }
];

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Home Value Estimator - Clean Version Loaded!');
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Set up navigation
    setupNavigation();
    
    // Initialize marketplace when loaded
    if (document.getElementById('marketplace-page')) {
        initializeMarketplace();
    }
    
    // Set up property details functionality
    setupPropertyDetails();
    
    // Initialize chatbot
    initializeChatbot();
    
    // Initialize demo page functionality
    if (document.getElementById('demo-page')) {
        setTimeout(() => {
            initDemoPage();
        }, 100);
    }
});

// Simple navigation system
function setupNavigation() {
    // Handle nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = link.getAttribute('data-page');
            showPage(pageId);
        });
    });
    
    // Logo click goes home
    const logo = document.querySelector('.navbar-brand');
    if (logo) {
        logo.addEventListener('click', (e) => {
            e.preventDefault();
            showPage('home');
        });
    }
}

function showPage(pageId) {
    console.log('Showing page:', pageId);
    
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.style.display = 'none';
    });
    
    // Show target page
    const targetPageId = pages[pageId] || pages['home'];
    const targetPage = document.getElementById(targetPageId);
    if (targetPage) {
        targetPage.style.display = 'block';
        currentPage = pageId;
        
        // Initialize page-specific functionality
        if (pageId === 'marketplace') {
            renderProperties();
        } else if (pageId === 'demo') {
            setTimeout(() => {
                initDemoPage();
                // Re-initialize Lucide icons
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }, 100);
        } else if (pageId === 'pricing') {
            setTimeout(() => {
                initPricingPage();
                // Re-initialize Lucide icons
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }, 100);
        } else if (pageId === 'analyzer') {
            setTimeout(() => {
                initAnalyzerPage();
                // Re-initialize Lucide icons
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }, 100);
        } else if (pageId === 'chat') {
            setTimeout(() => {
                initChatPage();
                // Re-initialize Lucide icons
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }, 100);
        }
    }
    
    // Re-initialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Marketplace functionality
function initializeMarketplace() {
    console.log('Marketplace initialized');
}

function renderProperties() {
    const container = document.getElementById('properties-grid');
    if (!container) return;
    
    console.log('Rendering', PROPERTIES.length, 'properties');
    
    const propertiesHTML = PROPERTIES.map(property => {
        const savings = property.estValue - property.listPrice;
        const savingsClass = savings > 0 ? 'positive' : savings < 0 ? 'negative' : 'neutral';
        const savingsText = savings > 0 ? `You save ${formatMoney(savings)}` : savings < 0 ? `${formatMoney(savings)}` : 'Fair value';
        
        return `
            <div class="property-card" onclick="showPropertyDetails('${property.id}')">
                <img src="${property.photo}" alt="${property.address1}" class="property-photo">
                <div class="property-info">
                    <div class="property-address">${property.address1}</div>
                    <div class="property-location">${property.city}, ${property.state} ${property.zip}</div>
                    <div class="property-details">
                        <span>${property.beds} beds</span>
                        <span>${property.baths} baths</span>
                        <span>${property.type}</span>
                    </div>
                    <div class="property-prices">
                        <div class="property-list-price">${formatMoney(property.listPrice)}</div>
                        <div class="property-est-value">Est. Value: ${formatMoney(property.estValue)}</div>
                        <div class="property-savings ${savingsClass}">${savingsText}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = propertiesHTML;
    console.log('Properties rendered to container');
}

// Property details functionality
function setupPropertyDetails() {
    // Back button
    const backButton = document.querySelector('.back-to-results');
    if (backButton) {
        backButton.addEventListener('click', () => {
            showPage('marketplace');
        });
    }
}

function showPropertyDetails(propertyId) {
    console.log('📋 Showing property details for:', propertyId);
    
    const property = PROPERTIES.find(p => p.id === propertyId);
    if (!property) {
        console.error('Property not found:', propertyId);
        return;
    }
    
    selectedProperty = property;
    
    // Show property details page
    showPage('property-details');
    
    // Render the property details
    renderPropertyDetails(property);
}

function renderPropertyDetails(property) {
    console.log('Rendering details for:', property.address1);
    
    // Update hero image
    const heroImage = document.getElementById('property-hero-image');
    if (heroImage) {
        heroImage.src = property.photo;
        heroImage.alt = `${property.address1}, ${property.city}`;
    }
    
    // Update address
    const addressElement = document.getElementById('property-address');
    if (addressElement) {
        addressElement.textContent = `${property.address1}, ${property.city}, ${property.state} ${property.zip}`;
    }
    
    // Update prices
    const listPriceElement = document.getElementById('property-list-price');
    if (listPriceElement) {
        listPriceElement.textContent = formatMoney(property.listPrice);
    }
    
    const estValueElement = document.getElementById('property-est-value');
    if (estValueElement) {
        estValueElement.textContent = formatMoney(property.estValue);
    }
    
    // Update savings
    const savings = property.estValue - property.listPrice;
    const savingsElement = document.getElementById('property-savings');
    if (savingsElement) {
        if (savings > 0) {
            savingsElement.textContent = `You save ${formatMoney(savings)}`;
            savingsElement.className = 'savings-pill positive';
        } else if (savings < 0) {
            savingsElement.textContent = `${formatMoney(savings)}`;
            savingsElement.className = 'savings-pill negative';
        } else {
            savingsElement.textContent = 'Fair value';
            savingsElement.className = 'savings-pill neutral';
        }
    }
    
    // Update facts
    const factsGrid = document.getElementById('property-facts');
    if (factsGrid) {
        factsGrid.innerHTML = `
            <div class="fact-item">
                <dt>Bedrooms</dt>
                <dd>${property.beds}</dd>
            </div>
            <div class="fact-item">
                <dt>Bathrooms</dt>
                <dd>${property.baths}</dd>
            </div>
            <div class="fact-item">
                <dt>Square Feet</dt>
                <dd>${property.sqft ? property.sqft.toLocaleString() : 'N/A'}</dd>
            </div>
            <div class="fact-item">
                <dt>Lot Size</dt>
                <dd>${property.lotSqft ? property.lotSqft.toLocaleString() + ' sqft' : 'N/A'}</dd>
            </div>
            <div class="fact-item">
                <dt>Year Built</dt>
                <dd>${property.yearBuilt || 'N/A'}</dd>
            </div>
            <div class="fact-item">
                <dt>Garage</dt>
                <dd>${property.hasGarage ? 'Yes' : 'No'}</dd>
            </div>
            <div class="fact-item">
                <dt>Property Type</dt>
                <dd>${property.type}</dd>
            </div>
        `;
    }
    
    // Update photo thumbnails
    const photoStrip = document.getElementById('photo-strip');
    if (photoStrip && property.photos && property.photos.length > 1) {
        photoStrip.style.display = 'block';
        photoStrip.innerHTML = property.photos.map(photo => `
            <img src="${photo}" alt="Property photo" class="photo-thumbnail" onclick="updateMainPhoto('${photo}')">
        `).join('');
    } else if (photoStrip) {
        photoStrip.style.display = 'none';
    }
}

function updateMainPhoto(photoSrc) {
    const heroImage = document.getElementById('property-hero-image');
    if (heroImage) {
        heroImage.src = photoSrc;
    }
}

// Utility functions
function formatMoney(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// ===== TRY HOME VALUE ESTIMATOR DEMO PAGE FUNCTIONALITY =====

// Demo page state
let demoPageInitialized = false;
let chatSession = null;

// Initialize demo page functionality
function initDemoPage() {
    if (demoPageInitialized) return;
    
    console.log('Initializing Try Home Value Estimator demo page...');
    
    // Initialize location examples
    initLocationExamples();
    
    // Initialize budget functionality
    initBudgetFunctionality();
    
    // Initialize search functionality
    initSearchFunctionality();
    
    // Initialize chat functionality
    initChatFunctionality();
    
    demoPageInitialized = true;
    console.log('✅ Demo page initialized successfully');
}

// Location examples functionality
function initLocationExamples() {
    const examples = document.querySelectorAll('.demo-example');
    const locationInput = document.getElementById('demo-location');
    
    if (!locationInput) return;
    
    examples.forEach(example => {
        example.addEventListener('click', function() {
            locationInput.value = this.textContent.trim();
            locationInput.focus();
            
            // Add a subtle animation to show the input was updated
            locationInput.style.transform = 'scale(1.02)';
            setTimeout(() => {
                locationInput.style.transform = 'scale(1)';
            }, 150);
        });
    });
}

// Budget functionality
function initBudgetFunctionality() {
    const customBudgetToggle = document.getElementById('custom-budget-toggle');
    const customBudgetInputs = document.getElementById('custom-budget-inputs');
    const minPriceSelect = document.getElementById('min-price');
    const maxPriceSelect = document.getElementById('max-price');
    
    if (!customBudgetToggle || !customBudgetInputs) {
        console.warn('Budget elements not found');
        return;
    }
    
    // Handle custom budget toggle
    customBudgetToggle.addEventListener('change', function() {
        if (this.checked) {
            customBudgetInputs.style.display = 'grid';
            // Disable select dropdowns when using custom inputs
            if (minPriceSelect) minPriceSelect.disabled = true;
            if (maxPriceSelect) maxPriceSelect.disabled = true;
        } else {
            customBudgetInputs.style.display = 'none';
            // Re-enable select dropdowns
            if (minPriceSelect) minPriceSelect.disabled = false;
            if (maxPriceSelect) maxPriceSelect.disabled = false;
        }
    });
    
    // Format number inputs with commas as user types
    const customMinPrice = document.getElementById('custom-min-price');
    const customMaxPrice = document.getElementById('custom-max-price');
    
    if (customMinPrice) {
        customMinPrice.addEventListener('input', formatNumberInput);
    }
    
    if (customMaxPrice) {
        customMaxPrice.addEventListener('input', formatNumberInput);
    }
    
    // Validation for min/max relationship
    function validateBudgetRange() {
        const isCustom = customBudgetToggle.checked;
        let minVal, maxVal;
        
        if (isCustom) {
            minVal = parseInt(customMinPrice?.value) || 0;
            maxVal = parseInt(customMaxPrice?.value) || 0;
        } else {
            minVal = parseInt(minPriceSelect?.value) || 0;
            maxVal = parseInt(maxPriceSelect?.value) || 0;
        }
        
        if (minVal > 0 && maxVal > 0 && minVal >= maxVal) {
            // Show validation message
            console.warn('Minimum price should be less than maximum price');
            return false;
        }
        
        return true;
    }
    
    // Add change listeners for validation
    if (minPriceSelect) {
        minPriceSelect.addEventListener('change', validateBudgetRange);
    }
    
    if (maxPriceSelect) {
        maxPriceSelect.addEventListener('change', validateBudgetRange);
    }
    
    if (customMinPrice) {
        customMinPrice.addEventListener('blur', validateBudgetRange);
    }
    
    if (customMaxPrice) {
        customMaxPrice.addEventListener('blur', validateBudgetRange);
    }
}

function formatNumberInput(event) {
    let value = event.target.value.replace(/,/g, '');
    if (value && !isNaN(value)) {
        // Add commas for thousands
        event.target.value = parseInt(value).toLocaleString();
    }
}

// Search functionality
function initSearchFunctionality() {
    const searchButton = document.getElementById('demo-search-btn');
    
    if (!searchButton) {
        console.warn('Search button not found');
        return;
    }
    
    searchButton.addEventListener('click', handleSearch);
}

async function handleSearch() {
    console.log('🔍 Handling property search...');
    
    // Get form data
    const searchData = getSearchFormData();
    console.log('📝 Form data collected:', searchData);
    
    if (!validateSearchData(searchData)) {
        console.log('❌ Validation failed, stopping search');
        return;
    }
    
    console.log('✅ Validation passed, starting chatbot with form data');
    
    // Show loading state
    showLoadingState();
    
    try {
        // Start chatbot with form data
        await startChatbotWithFormData(searchData);
        
    } catch (error) {
        console.error('Search failed:', error);
        showSearchError(error.message);
    } finally {
        hideLoadingState();
    }
}

async function startChatbotWithFormData(searchData) {
    console.log('🤖 Starting chatbot with form data:', searchData);
    
    const CHATBOT_API_BASE = 'http://localhost:8000';
    
    try {
        // Prepare frontend data for the chatbot
        const frontendData = {
            location: searchData.location,
            property_types: searchData.propertyTypes,
            budget_min: searchData.budget.min || null,
            budget_max: searchData.budget.max || null
        };
        
        console.log('📤 Sending to chatbot API:', frontendData);
        
        // Check if the chatbot widget exists and get its instance
        const chatbotWidget = document.getElementById('chatbot-widget');
        if (!chatbotWidget) {
            throw new Error('Chatbot widget not found');
        }
        
        // Get the existing chatbot instance (assuming it's stored globally)
        let chatbot = window.chatbot;
        if (!chatbot) {
            console.log('🔄 No existing chatbot instance, will create new session with form data');
        }
        
        // Start chatbot session with form data
        const startResponse = await fetch(`${CHATBOT_API_BASE}/chat/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                frontend_data: frontendData
            })
        });
        
        console.log('📥 API Response status:', startResponse.status);
        
        if (!startResponse.ok) {
            const errorText = await startResponse.text();
            console.error('❌ API Error:', errorText);
            throw new Error(`HTTP error! status: ${startResponse.status} - ${errorText}`);
        }
        
        const chatSession = await startResponse.json();
        console.log('✅ Chatbot session started:', chatSession);
        
        // Update the existing chatbot widget instead of creating new interface
        updateExistingChatbot(chatSession, frontendData);
        
    } catch (error) {
        console.error('❌ Failed to start chatbot:', error);
        
        // Show user-friendly error message
        alert(`Sorry, there was an error connecting to the chatbot: ${error.message}. Please make sure the chatbot server is running on port 8001.`);
        
        throw error;
    }
}

function updateExistingChatbot(chatSession, frontendData) {
    console.log('🔄 Updating existing chatbot widget with session data');
    
    // Get or create the chatbot instance
    let chatbot = window.chatbot;
    if (!chatbot) {
        console.log('📱 No existing chatbot found, initializing new one');
        initializeChatbot();
        chatbot = window.chatbot;
    }
    
    // If chatbot already has a session, we need to handle this carefully
    if (chatbot.sessionId && chatbot.sessionId !== chatSession.session_id) {
        console.log('🔄 Chatbot has existing session, updating with new session that has form data');
        // Clear existing messages to avoid confusion
        chatbot.elements.messages.innerHTML = '';
    }
    
    // Update the chatbot's session ID with the new one that has form data
    chatbot.sessionId = chatSession.session_id;
    
    // Open the chatbot widget if it's not already open
    if (!chatbot.isOpen) {
        chatbot.openChat();
    }
    
    // Add the initial message that acknowledges the form data
    chatbot.addMessage('assistant', chatSession.message);
    
    // Add a visual indicator that form data was processed
    const formSummary = createFormDataSummary(frontendData);
    if (formSummary) {
        chatbot.addMessage('system', `📋 ${formSummary}`);
    }
    
    console.log('✅ Chatbot widget updated successfully');
    
    // Show success message to user
    showSuccessMessage('Form data sent to chatbot! The chat widget is now updated with your preferences.');
}

function createFormDataSummary(frontendData) {
    const parts = [];
    
    if (frontendData.location) {
        parts.push(`📍 ${frontendData.location}`);
    }
    
    if (frontendData.property_types && frontendData.property_types.length > 0) {
        const typeNames = frontendData.property_types.map(type => {
            const typeMap = {
                'primary-residence': 'Primary Residence',
                'fix-flip': 'Fix & Flip',
                'rental-property': 'Rental Property',
                'multi-family': 'Multi-Family',
                'quick-deals': 'Quick Deals'
            };
            return typeMap[type] || type;
        });
        parts.push(`🏠 ${typeNames.join(', ')}`);
    }
    
    if (frontendData.budget_min || frontendData.budget_max) {
        const budget = [];
        if (frontendData.budget_min) budget.push(`$${frontendData.budget_min.toLocaleString()}`);
        if (frontendData.budget_max) budget.push(`$${frontendData.budget_max.toLocaleString()}`);
        parts.push(`💰 ${budget.join(' - ')}`);
    }
    
    return parts.join(' • ');
}

function showSuccessMessage(message) {
    // Create a temporary success notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Remove after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
    
    // Add CSS animation
    if (!document.getElementById('success-animation-styles')) {
        const style = document.createElement('style');
        style.id = 'success-animation-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
}

function getSearchFormData() {
    console.log('📋 Collecting form data...');
    
    const customBudgetEnabled = document.getElementById('custom-budget-toggle')?.checked;
    console.log('💰 Custom budget enabled:', customBudgetEnabled);
    
    let minPrice, maxPrice;
    
    if (customBudgetEnabled) {
        minPrice = parseInt(document.getElementById('custom-min-price')?.value) || 0;
        maxPrice = parseInt(document.getElementById('custom-max-price')?.value) || 0;
    } else {
        minPrice = parseInt(document.getElementById('min-price')?.value) || 0;
        maxPrice = parseInt(document.getElementById('max-price')?.value) || 0;
    }
    
    const location = document.getElementById('demo-location')?.value || '';
    const propertyTypes = getSelectedStrategies();
    
    console.log('📍 Location:', location);
    console.log('🏠 Property types:', propertyTypes);
    console.log('💵 Budget:', { min: minPrice, max: maxPrice });
    
    const formData = {
        location: location,
        propertyTypes: propertyTypes,
        budget: {
            min: minPrice,
            max: maxPrice,
            customBudget: customBudgetEnabled
        }
    };
    
    console.log('📦 Complete form data:', formData);
    return formData;
}

function getSelectedStrategies() {
    console.log('🎯 Checking selected strategies...');
    
    const strategies = [];
    
    const primaryResidence = document.getElementById('primary-residence')?.checked;
    const fixFlip = document.getElementById('fix-flip')?.checked;
    const rentalProperty = document.getElementById('rental-property')?.checked;
    const multiFamily = document.getElementById('multi-family')?.checked;
    const quickDeals = document.getElementById('quick-deals')?.checked;
    
    console.log('✓ Primary residence:', primaryResidence);
    console.log('✓ Fix & flip:', fixFlip);
    console.log('✓ Rental property:', rentalProperty);
    console.log('✓ Multi-family:', multiFamily);
    console.log('✓ Quick deals:', quickDeals);
    
    if (primaryResidence) {
        strategies.push('primary-residence');
    }
    if (fixFlip) {
        strategies.push('fix-flip');
    }
    if (rentalProperty) {
        strategies.push('rental-property');
    }
    if (multiFamily) {
        strategies.push('multi-family');
    }
    if (quickDeals) {
        strategies.push('quick-deals');
    }
    
    console.log('📋 Selected strategies:', strategies);
    return strategies;
}

function validateSearchData(data) {
    if (!data.location || data.location.trim() === '') {
        alert('Please enter a location (city, state, ZIP code, or address)');
        return false;
    }
    
    if (data.propertyTypes.length === 0) {
        alert('Please select at least one property type');
        return false;
    }
    
    return true;
}

// Chat functionality
function initChatFunctionality() {
    console.log('💬 Initializing chat functionality');
    // Chatbot functionality will be handled by the main chatbot manager
}

// Loading states
function showLoadingState() {
    const loading = document.getElementById('demo-loading');
    if (loading) {
        loading.style.display = 'flex';
    }
}

function hideLoadingState() {
    const loading = document.getElementById('demo-loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

function showSearchError(message) {
    alert(`Search Error: ${message}`);
}

// ================================
// CHATBOT FUNCTIONALITY
// ================================

class ChatbotManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.sessionId = null;
        this.isOpen = false;
        this.isTyping = false;
        
        this.elements = {
            widget: document.getElementById('chatbot-widget'),
            toggle: document.getElementById('chatbot-toggle'),
            window: document.getElementById('chatbot-window'),
            minimize: document.getElementById('chatbot-minimize'),
            messages: document.getElementById('chatbot-messages'),
            input: document.getElementById('chatbot-input'),
            send: document.getElementById('chatbot-send'),
            typing: document.getElementById('chatbot-typing'),
            notification: document.getElementById('chat-notification')
        };
        
        this.bindEvents();
    }
    
    bindEvents() {
        // Toggle chatbot
        this.elements.toggle.addEventListener('click', () => this.toggleChat());
        this.elements.minimize.addEventListener('click', () => this.closeChat());
        
        // Send message
        this.elements.send.addEventListener('click', () => this.sendMessage());
        this.elements.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize input
        this.elements.input.addEventListener('input', () => {
            this.elements.input.style.height = 'auto';
            this.elements.input.style.height = Math.min(this.elements.input.scrollHeight, 100) + 'px';
        });
    }
    
    async toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            await this.openChat();
        }
    }
    
    async openChat() {
        this.isOpen = true;
        this.elements.toggle.classList.add('active');
        this.elements.window.classList.remove('hidden');
        this.hideNotification();
        
        // Small delay for animation
        setTimeout(() => {
            this.elements.window.classList.add('visible');
            this.elements.input.focus();
        }, 10);
        
        // Start session if not already started
        if (!this.sessionId) {
            await this.startSession();
        }
    }
    
    closeChat() {
        this.isOpen = false;
        this.elements.toggle.classList.remove('active');
        this.elements.window.classList.remove('visible');
        
        setTimeout(() => {
            this.elements.window.classList.add('hidden');
        }, 300);
    }
    
    async startSession() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });
            
            if (!response.ok) {
                throw new Error('Failed to start chat session');
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            // Add initial message
            this.addMessage('assistant', data.message);
            
        } catch (error) {
            console.error('Error starting chat session:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error starting our conversation. Please try refreshing the page.');
        }
    }
    
    async sendMessage() {
        const message = this.elements.input.value.trim();
        if (!message || this.isTyping) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.elements.input.value = '';
        this.elements.input.style.height = 'auto';
        
        // Show typing indicator
        this.showTyping();
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to send message');
            }
            
            const data = await response.json();
            
            // Hide typing indicator
            this.hideTyping();
            
            // Add assistant response
            this.addMessage('assistant', data.message);
            
            // Check if conversation is complete
            if (data.completed && data.preferences_collected) {
                setTimeout(() => {
                    this.addMessage('assistant', 'Perfect! I have all the information I need. Our property finding team will now search for investments that match your criteria. You should hear from us soon with some exciting opportunities!');
                }, 1000);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTyping();
            this.addMessage('assistant', 'Sorry, I encountered an error processing your message. Please try again.');
        }
    }
    
    addMessage(role, content) {
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${role}`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let iconType = 'home'; // default for assistant
        if (role === 'user') iconType = 'user';
        else if (role === 'system') iconType = 'settings';
        
        messageEl.innerHTML = `
            <div class="chat-message-avatar">
                <i data-lucide="${iconType}"></i>
            </div>
            <div class="chat-message-content">
                ${this.formatMessage(content)}
                <div class="chat-message-time">${time}</div>
            </div>
        `;
        
        this.elements.messages.appendChild(messageEl);
        this.scrollToBottom();
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
    
    formatMessage(content) {
        // Convert line breaks to <br> tags
        let formatted = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Check if this looks like a property listing response with dual pricing
        if (content.includes('🏠 **Property') && content.includes('📍')) {
            // Enhanced property pattern to capture both AI fair value and listed price
            const propertyPattern = /🏠 \*\*Property (\d+)\*\*<br>📍 ([^<]+)(?:<br>[🎯📊📈💰] \*\*Fair Value \(AI\)\*\*: ([^<]+))?(?:<br>�️ \*\*Listed Price\*\*: ([^<]+))?(?:<br>�🏡 ([^<]+))?(?:<br>📅 Built: ([^<]+))?(?:<br>🤖 ([^<]+))?/g;
            
            let propertyHtml = '<div class="property-results">';
            let match;
            let hasProperties = false;
            
            // Extract intro text (before properties)
            const introMatch = content.match(/^(.*?)🏠 \*\*Property/s);
            if (introMatch) {
                propertyHtml += `<div class="property-intro">${introMatch[1].replace(/\n/g, '<br>')}</div>`;
            }
            
            while ((match = propertyPattern.exec(formatted)) !== null) {
                hasProperties = true;
                const [, number, address, aiPrice, listedPrice, details, yearBuilt, aiConfidence] = match;
                
                propertyHtml += `
                    <div class="property-card-chat">
                        <div class="property-header">
                            <span class="property-number">#${number}</span>
                            <div class="property-prices">
                                ${aiPrice ? `<div class="ai-price"><span class="price-label">AI Fair Value:</span> <span class="price-value">${aiPrice}</span></div>` : ''}
                                ${listedPrice ? `<div class="listed-price"><span class="price-label">Listed Price:</span> <span class="price-value">${listedPrice}</span></div>` : ''}
                            </div>
                        </div>
                        <div class="property-address">${address}</div>
                        ${details ? `<div class="property-details">${details}</div>` : ''}
                        ${yearBuilt ? `<div class="property-year">Built: ${yearBuilt}</div>` : ''}
                        ${aiConfidence ? `<div class="ai-confidence">${aiConfidence}</div>` : ''}
                    </div>
                `;
            }
            
            // Extract outro text (after properties)
            const outroMatch = content.match(/🤖 [^<]+<br><br>(.*)$/s);
            if (outroMatch) {
                propertyHtml += `<div class="property-outro">${outroMatch[1].replace(/\n/g, '<br>')}</div>`;
            }
            
            propertyHtml += '</div>';
            
            if (hasProperties) {
                return propertyHtml;
            }
        }
        
        return formatted;
    }
    
    showTyping() {
        this.isTyping = true;
        this.elements.typing.style.display = 'flex';
        this.elements.send.disabled = true;
        this.scrollToBottom();
    }
    
    hideTyping() {
        this.isTyping = false;
        this.elements.typing.style.display = 'none';
        this.elements.send.disabled = false;
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
        }, 100);
    }
    
    showNotification() {
        this.elements.notification.style.display = 'block';
    }
    
    hideNotification() {
        this.elements.notification.style.display = 'none';
    }
}

// Initialize chatbot
function initializeChatbot() {
    const chatbot = new ChatbotManager();
    
    // Store chatbot instance globally so it can be accessed from form handlers
    window.chatbot = chatbot;
    
    // Show notification after a delay if chat hasn't been opened
    setTimeout(() => {
        if (!chatbot.isOpen) {
            chatbot.showNotification();
        }
    }, 10000); // Show after 10 seconds
}

// Pricing page functionality
function initPricingPage() {
    // Handle pricing CTA buttons
    document.querySelectorAll('.pricing-cta').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            
            if (button.textContent.includes('Start Free Trial')) {
                // Navigate to signup page
                showPage('signup');
            } else if (button.textContent.includes('Contact Sales')) {
                // Open contact form or redirect to sales page
                alert('Thank you for your interest! Our sales team will contact you within 24 hours.');
            }
        });
    });
    
    // Handle final CTA buttons
    document.querySelectorAll('.pricing-final-cta .btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            
            if (button.textContent.includes('Start Free Trial')) {
                showPage('signup');
            } else if (button.textContent.includes('Book a Demo')) {
                alert('Demo booking coming soon! Please contact us for a personalized demonstration.');
            }
        });
    });
}

// Initialize pricing page when shown
document.addEventListener('DOMContentLoaded', function() {
    // Add pricing page initialization to the existing DOMContentLoaded event
    setTimeout(() => {
        if (currentPage === 'pricing') {
            initPricingPage();
        }
    }, 100);
    
    // Initialize image loading enhancements
    initImageEnhancements();
});

// Image enhancement functionality
function initImageEnhancements() {
    // Add loading states to all images
    const images = document.querySelectorAll('img');
    
    images.forEach(img => {
        if (img.complete && img.naturalHeight !== 0) {
            img.classList.add('loaded');
        } else {
            img.classList.add('loading');
            
            img.addEventListener('load', function() {
                this.classList.remove('loading');
                this.classList.add('loaded');
            });
            
            img.addEventListener('error', function() {
                this.classList.remove('loading');
                this.style.display = 'none';
                console.log('Failed to load image:', this.src);
            });
        }
    });
    
    // Add hover effects to property cards
    const propertyCards = document.querySelectorAll('.property-card');
    propertyCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
            this.style.boxShadow = 'var(--shadow-elegant)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'var(--shadow-card)';
        });
    });
    
    // Add image overlay effects
    const overlayImages = document.querySelectorAll('.hero-img, .demo-section img');
    overlayImages.forEach(img => {
        const wrapper = img.parentElement;
        if (!wrapper.classList.contains('image-overlay')) {
            wrapper.classList.add('image-overlay');
        }
    });
}

// Deal Analyzer functionality
function initAnalyzerPage() {
    console.log('Deal Analyzer page initialized');
    
    // Simulate loading state
    const loadingElement = document.getElementById('analyzer-loading');
    const resultsElement = document.getElementById('property-results');
    
    if (loadingElement && resultsElement) {
        // Show loading initially
        loadingElement.style.display = 'flex';
        resultsElement.style.display = 'none';
        
        // Simulate data loading after 2 seconds
        setTimeout(() => {
            loadingElement.style.display = 'none';
            resultsElement.style.display = 'block';
            
            // Add animation to property cards
            const propertyCards = document.querySelectorAll('.analyzed-property-card');
            propertyCards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    card.style.transition = 'all 0.5s ease';
                    
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, 50);
                }, index * 200);
            });
        }, 2000);
    }
}

// Analyzer page functions (placeholders for backend integration)
function refreshAnalyzerData() {
    console.log('Refreshing analyzer data...');
    
    // Show loading state
    const loadingElement = document.getElementById('analyzer-loading');
    const resultsElement = document.getElementById('property-results');
    
    if (loadingElement && resultsElement) {
        loadingElement.style.display = 'flex';
        resultsElement.style.display = 'none';
        
        // TODO: Replace with actual backend call
        // Example: await fetch('/api/analyzer/refresh', { method: 'POST' });
        
        // Simulate refresh
        setTimeout(() => {
            loadingElement.style.display = 'none';
            resultsElement.style.display = 'block';
            
            // Show success notification
            showNotification('Analysis refreshed successfully!', 'success');
        }, 1500);
    }
}

function exportAnalyzerResults() {
    console.log('Exporting analyzer results...');
    
    // TODO: Replace with actual backend call
    // Example: const data = await fetch('/api/analyzer/export');
    
    // Simulate export
    showNotification('Export started! Check your downloads folder.', 'info');
}

function editPreferences() {
    console.log('Opening preferences editor...');
    
    // TODO: Open preferences modal or navigate to preferences page
    // For now, show alert
    alert('Preferences editor will open here. This will be connected to your backend API.');
}

function runNewAnalysis() {
    console.log('Running new analysis...');
    
    // Show loading state
    const loadingElement = document.getElementById('analyzer-loading');
    const resultsElement = document.getElementById('property-results');
    
    if (loadingElement && resultsElement) {
        loadingElement.style.display = 'flex';
        resultsElement.style.display = 'none';
        
        // TODO: Replace with actual backend call
        // Example: await fetch('/api/analyzer/analyze', { method: 'POST', body: preferences });
        
        // Simulate analysis
        setTimeout(() => {
            loadingElement.style.display = 'none';
            resultsElement.style.display = 'block';
            
            showNotification('New analysis complete! Found 3 new opportunities.', 'success');
        }, 3000);
    }
}

function viewPropertyDetails(propertyId) {
    console.log('Viewing property details for:', propertyId);
    
    // TODO: Replace with actual property details navigation
    // Example: showPage('property-details', { propertyId });
    
    // For now, show alert
    alert(`Property details for ${propertyId} will load here. This will connect to your property details API.`);
}

function saveProperty(propertyId) {
    console.log('Saving property:', propertyId);
    
    // TODO: Replace with actual backend call
    // Example: await fetch('/api/properties/save', { method: 'POST', body: { propertyId } });
    
    // Simulate save
    const button = event.target.closest('button');
    const originalText = button.innerHTML;
    button.innerHTML = '<i data-lucide="check"></i>Saved';
    button.classList.add('btn-success');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('btn-success');
    }, 2000);
    
    showNotification('Property saved to your watchlist!', 'success');
}

function contactAgent(propertyId) {
    console.log('Contacting agent for property:', propertyId);
    
    // TODO: Replace with actual agent contact flow
    // Example: await fetch('/api/properties/contact-agent', { method: 'POST', body: { propertyId } });
    
    // For now, show alert
    alert(`Agent contact form for property ${propertyId} will open here. This will connect to your agent network API.`);
}

// Notification system for analyzer feedback
function showNotification(message, type = 'info') {
    // Create notification element if it doesn't exist
    let notification = document.getElementById('analyzer-notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'analyzer-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 400px;
        `;
        document.body.appendChild(notification);
    }
    
    // Set notification style based on type
    const styles = {
        success: { background: 'hsl(120 100% 40%)', color: 'white' },
        error: { background: 'hsl(0 100% 60%)', color: 'white' },
        info: { background: 'hsl(210 100% 50%)', color: 'white' },
        warning: { background: 'hsl(45 100% 50%)', color: 'black' }
    };
    
    const style = styles[type] || styles.info;
    notification.style.background = style.background;
    notification.style.color = style.color;
    notification.textContent = message;
    
    // Show notification
    notification.style.transform = 'translateX(0)';
    
    // Hide after 4 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
    }, 4000);
}

// ===== CHAT DASHBOARD FUNCTIONALITY =====

// Chat state management
let currentChat = 'chat-1';
let chatSettings = {
    responseStyle: 'detailed',
    searchArea: 'Austin, TX',
    budgetMin: 400000,
    budgetMax: 500000,
    autoSave: true,
    emailNotifications: true,
    desktopNotifications: false
};

let chats = {
    'chat-1': {
        title: 'Property Analysis - Austin',
        type: 'property',
        lastMessage: 'Found 3 undervalued properties in your target area...',
        time: '2m ago',
        unread: 3,
        messages: []
    },
    'chat-2': {
        title: 'ROI Calculator',
        type: 'analysis',
        lastMessage: 'Let me calculate the potential returns for this property...',
        time: '15m ago',
        unread: 0,
        messages: []
    },
    'chat-3': {
        title: 'Market Analysis - Dallas',
        type: 'analysis',
        lastMessage: 'The Dallas market shows strong growth potential...',
        time: '1h ago',
        unread: 0,
        messages: []
    },
    'chat-4': {
        title: 'Getting Started',
        type: 'support',
        lastMessage: 'Welcome to Home Value Estimator! Here\'s how to get started...',
        time: '2d ago',
        unread: 0,
        messages: []
    }
};

function initChatPage() {
    console.log('Chat Dashboard initialized');
    
    // Auto-resize chat input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }
    
    // Initialize chat list
    renderChatList();
    
    // Select first chat by default
    selectChat(currentChat);
}

function startNewChat() {
    const chatId = 'chat-' + Date.now();
    chats[chatId] = {
        title: 'New Conversation',
        type: 'property',
        lastMessage: 'How can I help you today?',
        time: 'now',
        unread: 0,
        messages: []
    };
    
    renderChatList();
    selectChat(chatId);
    
    // Focus on input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.focus();
    }
    
    showNotification('New chat started!', 'success');
}

function filterChats(type) {
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Filter and render chat list
    renderChatList(type);
}

function renderChatList(filterType = 'all') {
    const chatList = document.getElementById('chat-list');
    if (!chatList) return;
    
    const filteredChats = Object.entries(chats).filter(([id, chat]) => {
        if (filterType === 'all') return true;
        return chat.type === filterType;
    });
    
    chatList.innerHTML = filteredChats.map(([id, chat]) => `
        <div class="chat-item ${id === currentChat ? 'active' : ''}" onclick="selectChat('${id}')">
            <div class="chat-avatar">
                <i data-lucide="${getChatIcon(chat.type)}"></i>
            </div>
            <div class="chat-info">
                <div class="chat-title">${chat.title}</div>
                <div class="chat-preview">${chat.lastMessage}</div>
                <div class="chat-time">${chat.time}</div>
            </div>
            ${chat.unread > 0 ? `<div class="chat-badge">${chat.unread}</div>` : ''}
        </div>
    `).join('');
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function getChatIcon(type) {
    const icons = {
        property: 'home',
        analysis: 'calculator',
        support: 'help-circle'
    };
    return icons[type] || 'message-circle';
}

function selectChat(chatId) {
    currentChat = chatId;
    const chat = chats[chatId];
    
    if (!chat) return;
    
    // Update chat list selection
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Find and activate the selected chat item
    const selectedItem = document.querySelector(`[onclick="selectChat('${chatId}')"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
    
    // Update chat header
    updateChatHeader(chat);
    
    // Mark as read
    chat.unread = 0;
    renderChatList();
    
    console.log('Selected chat:', chatId);
}

function updateChatHeader(chat) {
    const headerTitle = document.querySelector('.chat-header-text h3');
    const headerIcon = document.querySelector('.chat-header .chat-avatar i');
    
    if (headerTitle) headerTitle.textContent = chat.title;
    if (headerIcon && typeof lucide !== 'undefined') {
        headerIcon.setAttribute('data-lucide', getChatIcon(chat.type));
        lucide.createIcons();
    }
}

function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    if (!chatInput || !chatInput.value.trim()) return;
    
    const messageText = chatInput.value.trim();
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Add user message to chat
    addMessage('user', messageText);
    
    // Show typing indicator
    showTypingIndicator();
    
    // Simulate AI response after delay
    setTimeout(() => {
        hideTypingIndicator();
        handleAIResponse(messageText);
    }, Math.random() * 2000 + 1000);
}

function sendQuickMessage(message) {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = message;
        sendMessage();
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function addMessage(type, text, properties = null) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    const messageTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const isUser = type === 'user';
    
    const messageHTML = `
        <div class="message ${isUser ? 'user-message' : 'ai-message'}">
            ${!isUser ? `
                <div class="message-avatar">
                    <i data-lucide="bot"></i>
                </div>
            ` : ''}
            <div class="message-content">
                <div class="message-text">
                    ${text}
                    ${properties ? generatePropertyCards(properties) : ''}
                </div>
                <div class="message-time">${messageTime}</div>
            </div>
            ${isUser ? `
                <div class="message-avatar">
                    <i data-lucide="user"></i>
                </div>
            ` : ''}
        </div>
    `;
    
    // Remove typing indicator if present
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator && typingIndicator.style.display !== 'none') {
        typingIndicator.remove();
    }
    
    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function generatePropertyCards(properties) {
    return `
        <div class="message-properties">
            ${properties.map(prop => `
                <div class="chat-property-card">
                    <img src="${prop.image}" alt="Property">
                    <div class="property-details">
                        <h4>${prop.address}</h4>
                        <p>${prop.location} • ${prop.beds} bed, ${prop.baths} bath • ${prop.sqft} sqft</p>
                        <div class="property-metrics">
                            <span class="metric positive">$${prop.savings}k under market</span>
                            <span class="metric">${prop.roi}% ROI potential</span>
                        </div>
                        <div class="property-price">$${prop.price.toLocaleString()}</div>
                    </div>
                    <button class="btn btn-sm btn-primary">View Details</button>
                </div>
            `).join('')}
        </div>
    `;
}

function handleAIResponse(userMessage) {
    const lowerMessage = userMessage.toLowerCase();
    
    let response = '';
    let properties = null;
    
    if (lowerMessage.includes('property') || lowerMessage.includes('house') || lowerMessage.includes('find')) {
        response = `I found several excellent investment opportunities that match your criteria. Here are the top properties with significant upside potential:`;
        properties = [
            {
                address: '789 Elm Street',
                location: 'Austin, TX',
                beds: 3,
                baths: 2,
                sqft: '1,920',
                savings: 28,
                roi: 16,
                price: 462000,
                image: 'hero-house.jpg'
            },
            {
                address: '321 Maple Ave',
                location: 'Austin, TX',
                beds: 4,
                baths: 3,
                sqft: '2,150',
                savings: 22,
                roi: 13,
                price: 478000,
                image: 'houses-grid.jpg'
            }
        ];
    } else if (lowerMessage.includes('market') || lowerMessage.includes('trend')) {
        response = `The Austin market is showing strong fundamentals with 12% year-over-year appreciation. Key trends include:<br><br>
                   • Inventory levels down 15% from last year<br>
                   • Average days on market: 28 days<br>
                   • Price growth concentrated in suburbs<br>
                   • Investment opportunities in emerging neighborhoods<br><br>
                   Would you like me to analyze specific areas in more detail?`;
    } else if (lowerMessage.includes('roi') || lowerMessage.includes('return') || lowerMessage.includes('calculate')) {
        response = `I can help you calculate ROI for any property. For a typical $450,000 investment property in Austin:<br><br>
                   • Monthly rent: $2,800<br>
                   • Annual rental income: $33,600<br>
                   • Operating expenses: $8,400<br>
                   • Net operating income: $25,200<br>
                   • Cash-on-cash return: 14.2%<br><br>
                   Would you like me to run calculations for a specific property?`;
    } else {
        response = `I understand you're looking for real estate investment guidance. I can help you with:<br><br>
                   • Finding undervalued properties<br>
                   • Market analysis and trends<br>
                   • ROI calculations<br>
                   • Investment strategy recommendations<br><br>
                   What specific aspect would you like to explore?`;
    }
    
    addMessage('ai', response, properties);
    
    // Update chat preview
    const chat = chats[currentChat];
    if (chat) {
        chat.lastMessage = response.replace(/<[^>]*>/g, '').substring(0, 50) + '...';
        chat.time = 'now';
        renderChatList();
    }
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    const typingHTML = `
        <div class="message ai-message typing-message" id="typing-indicator">
            <div class="message-avatar">
                <i data-lucide="bot"></i>
            </div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function exportChat() {
    const chat = chats[currentChat];
    if (!chat) return;
    
    showNotification(`Exporting "${chat.title}" conversation...`, 'info');
    
    // TODO: Implement actual export functionality
    setTimeout(() => {
        showNotification('Chat exported successfully!', 'success');
    }, 1500);
}

function clearChat() {
    if (confirm('Are you sure you want to clear this conversation? This action cannot be undone.')) {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="message ai-message">
                    <div class="message-avatar">
                        <i data-lucide="bot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-text">
                            How can I help you with your real estate investment needs today?
                        </div>
                        <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                </div>
            `;
            
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
        
        showNotification('Chat cleared successfully!', 'success');
    }
}

function toggleChatSettings() {
    const settingsPanel = document.getElementById('chat-settings');
    if (!settingsPanel) return;
    
    const isOpen = settingsPanel.style.display !== 'none';
    settingsPanel.style.display = isOpen ? 'none' : 'block';
    
    if (!isOpen) {
        // Load current settings into form
        loadSettingsForm();
    }
}

function loadSettingsForm() {
    // TODO: Load settings from chatSettings object into form elements
    console.log('Loading chat settings form');
}

function attachFile() {
    // TODO: Implement file attachment functionality
    showNotification('File attachment coming soon!', 'info');
}