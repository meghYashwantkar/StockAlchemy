/**
 * Chart.js configuration utilities for Stock Portfolio Management System
 * This file contains helper functions for chart creation and configuration
 */

/**
 * Creates and returns a portfolio allocation pie chart
 * @param {string} elementId - The ID of the canvas element 
 * @param {Array} labels - Array of stock symbols
 * @param {Array} values - Array of current values
 * @param {Array} colors - Array of colors for each slice
 * @returns {Chart} The created Chart instance
 */
function createPortfolioPieChart(elementId, labels, values, colors) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a performance line chart tracking portfolio value over time
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} labels - Array of time periods (dates/months)
 * @param {Array} values - Array of portfolio values
 * @returns {Chart} The created Chart instance
 */
function createPerformanceLineChart(elementId, labels, values) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value',
                data: values,
                borderColor: '#4dc9f6',
                backgroundColor: 'rgba(77, 201, 246, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Value: $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a bar chart comparing stock performance
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} labels - Array of stock symbols
 * @param {Array} returns - Array of percentage returns
 * @returns {Chart} The created Chart instance
 */
function createStockPerformanceBarChart(elementId, labels, returns) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Generate colors based on positive or negative returns
    const backgroundColors = returns.map(value => 
        value >= 0 ? 'rgba(40, 167, 69, 0.7)' : 'rgba(220, 53, 69, 0.7)'
    );
    
    const borderColors = returns.map(value => 
        value >= 0 ? 'rgb(40, 167, 69)' : 'rgb(220, 53, 69)'
    );
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Return %',
                data: returns,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Return: ' + context.parsed.y.toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}
