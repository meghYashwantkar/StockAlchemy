/**
 * Portfolio Management JavaScript functionality
 * Handles client-side interactions for the portfolio management pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Stock symbols autocomplete and validation
    setupStockSymbolSearch();
    
    // Quick sell button functionality
    setupSellModalTriggers();
    
    // Calculate total values
    calculateFormTotals();
});

/**
 * Sets up event listeners for stock symbol search
 */
function setupStockSymbolSearch() {
    const searchButtons = document.querySelectorAll('.stock-search-btn');
    
    searchButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const inputField = this.closest('.input-group').querySelector('input');
            const feedbackElement = this.closest('.mb-3').querySelector('.form-text');
            const priceField = document.getElementById('price') || document.getElementById('priceTransaction');
            
            if (!inputField.value) {
                if (feedbackElement) {
                    feedbackElement.innerHTML = '<span class="text-warning">Please enter a stock symbol</span>';
                }
                return;
            }
            
            if (feedbackElement) {
                feedbackElement.innerHTML = '<span class="text-info">Checking symbol...</span>';
            }
            
            fetch(`/search_stock?symbol=${inputField.value}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        if (feedbackElement) {
                            feedbackElement.innerHTML = `<span class="text-danger">${data.error}</span>`;
                        }
                    } else {
                        if (feedbackElement) {
                            feedbackElement.innerHTML = `<span class="text-success">${data.company_name} - Current price: $${data.current_price.toFixed(2)}</span>`;
                        }
                        if (priceField) {
                            priceField.value = data.current_price.toFixed(2);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (feedbackElement) {
                        feedbackElement.innerHTML = '<span class="text-danger">Error checking symbol</span>';
                    }
                });
        });
    });
}

/**
 * Sets up sell button event listeners
 */
function setupSellModalTriggers() {
    const sellButtons = document.querySelectorAll('.sell-stock-btn');
    
    sellButtons.forEach(button => {
        button.addEventListener('click', function() {
            const stockId = this.getAttribute('data-stock-id');
            showSellModal(stockId);
        });
    });
}

/**
 * Displays the sell stock modal with stock information
 * @param {number} stockId - The ID of the stock to sell
 */
function showSellModal(stockId) {
    const sellModal = new bootstrap.Modal(document.getElementById('sellStockModal'));
    const modalContent = document.getElementById('sellModalContent');
    
    // Load sell form content
    fetch(`/sell_stock.html?stock_id=${stockId}`)
        .then(response => response.text())
        .then(html => {
            modalContent.innerHTML = html;
            
            // Add event listeners to the new form
            const quantityField = modalContent.querySelector('#quantity');
            const priceField = modalContent.querySelector('#price');
            
            if (quantityField && priceField) {
                const calculateTotal = function() {
                    const quantity = parseFloat(quantityField.value) || 0;
                    const price = parseFloat(priceField.value) || 0;
                    const totalElement = modalContent.querySelector('#total-value');
                    
                    if (totalElement) {
                        totalElement.textContent = `$${(quantity * price).toFixed(2)}`;
                    }
                };
                
                quantityField.addEventListener('input', calculateTotal);
                priceField.addEventListener('input', calculateTotal);
                
                // Initial calculation
                calculateTotal();
            }
            
            sellModal.show();
        })
        .catch(error => {
            console.error('Error loading sell form:', error);
            modalContent.innerHTML = '<div class="alert alert-danger">Error loading sell form</div>';
        });
}

/**
 * Sets up real-time calculation of transaction totals in forms
 */
function calculateFormTotals() {
    const quantityFields = document.querySelectorAll('.quantity-field');
    const priceFields = document.querySelectorAll('.price-field');
    
    // Function to calculate and update total
    const updateTotal = function(quantityField, priceField, totalElement) {
        const quantity = parseFloat(quantityField.value) || 0;
        const price = parseFloat(priceField.value) || 0;
        const total = quantity * price;
        
        if (totalElement) {
            totalElement.textContent = `$${total.toFixed(2)}`;
        }
    };
    
    // Set up event listeners for quantity and price fields
    quantityFields.forEach(field => {
        const formGroup = field.closest('form');
        if (formGroup) {
            const priceField = formGroup.querySelector('.price-field');
            const totalElement = formGroup.querySelector('.total-value');
            
            if (priceField && totalElement) {
                field.addEventListener('input', function() {
                    updateTotal(field, priceField, totalElement);
                });
                
                priceField.addEventListener('input', function() {
                    updateTotal(field, priceField, totalElement);
                });
                
                // Initial calculation
                updateTotal(field, priceField, totalElement);
            }
        }
    });
}
