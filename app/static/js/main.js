// Main JavaScript file

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Back to top button
    window.addEventListener('scroll', function() {
        var backToTop = document.getElementById('backToTop');
        if (window.scrollY > 300) {
            backToTop.style.display = 'block';
        } else {
            backToTop.style.display = 'none';
        }
    });
    
    // Quantity input validation
    document.querySelectorAll('input[type="number"][name="quantity"]').forEach(input => {
        input.addEventListener('change', function() {
            const min = parseInt(this.min) || 0;
            const max = parseInt(this.max) || 999;
            let value = parseInt(this.value) || min;
            
            if (value < min) value = min;
            if (value > max) value = max;
            
            this.value = value;
        });
    });
    
    // Image preview for file inputs
    const imageInput = document.querySelector('input[type="file"][accept*="image"]');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = document.querySelector('.image-preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'image-preview img-thumbnail mt-2';
                        imageInput.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Add to cart animation
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Adding...';
            this.disabled = true;
            
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 1000);
        });
    });
    
    // Search suggestions
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value;
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    fetch(`/api/search-suggestions?q=${encodeURIComponent(query)}`)
                        .then(response => response.json())
                        .then(data => {
                            showSearchSuggestions(data.suggestions);
                        });
                }, 300);
            }
        });
    }
});

// Scroll to top function
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Show search suggestions
function showSearchSuggestions(suggestions) {
    const searchForm = document.querySelector('form[action*="search"]');
    let suggestionsDiv = document.getElementById('search-suggestions');
    
    if (!suggestionsDiv) {
        suggestionsDiv = document.createElement('div');
        suggestionsDiv.id = 'search-suggestions';
        suggestionsDiv.className = 'position-absolute bg-white border rounded shadow-sm mt-1';
        suggestionsDiv.style.width = searchForm.offsetWidth + 'px';
        suggestionsDiv.style.zIndex = '1000';
        searchForm.appendChild(suggestionsDiv);
    }
    
    if (suggestions.length > 0) {
        let html = '<div class="list-group">';
        suggestions.forEach(suggestion => {
            html += `
                <a href="/search?q=${encodeURIComponent(suggestion.name)}" class="list-group-item list-group-item-action">
                    <div class="d-flex align-items-center">
                        <img src="${suggestion.image || 'https://via.placeholder.com/40'}" 
                             alt="${suggestion.name}" style="width: 40px; height: 40px; object-fit: cover;" class="me-2">
                        <div>
                            <div>${suggestion.name}</div>
                            <small class="text-muted">₦${suggestion.price}</small>
                        </div>
                    </div>
                </a>
            `;
        });
        html += '</div>';
        suggestionsDiv.innerHTML = html;
        suggestionsDiv.style.display = 'block';
    } else {
        suggestionsDiv.style.display = 'none';
    }
}

// Hide search suggestions when clicking outside
document.addEventListener('click', function(event) {
    const suggestionsDiv = document.getElementById('search-suggestions');
    const searchInput = document.querySelector('input[name="q"]');
    
    if (suggestionsDiv && searchInput && !searchInput.contains(event.target) && !suggestionsDiv.contains(event.target)) {
        suggestionsDiv.style.display = 'none';
    }
});

// Update cart quantity
function updateCart(productId, quantity) {
    fetch(`/update-cart/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    })
    .catch(error => console.error('Error:', error));
}

// Format currency
function formatCurrency(amount) {
    return '₦' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Show notification
function showNotification(message, type = 'info', duration = 3000) {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.querySelector('.toast-container').appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, duration);
}

// Confirm action
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}