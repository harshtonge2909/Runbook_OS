// RunbookOS Main JavaScript

// Retrieve CSRF token from meta tag
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// Global fetch wrapper with automatic CSRF token and JSON headers
async function apiRequest(url, options = {}) {
    const defaultHeaders = {
        'Accept': 'application/json',
        'X-CSRFToken': getCsrfToken(),
    };

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
        defaultHeaders['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    options.headers = { ...defaultHeaders, ...(options.headers || {}) };

    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    
    if (!response.ok) {
        throw new Error(data.message || `Request failed with status ${response.status}`);
    }
    return data;
}

// Toast Notification System
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0 show mb-2`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4500);
}

// Universal Delete Confirmation Handler
function confirmDelete(title, message, formElement) {
    const modalEl = document.getElementById('universalConfirmModal');
    if (!modalEl) {
        if (confirm(`${title}\n\n${message}`)) {
            formElement.submit();
        }
        return;
    }
    
    document.getElementById('confirmModalTitle').innerText = title;
    document.getElementById('confirmModalBody').innerText = message;
    
    const confirmBtn = document.getElementById('confirmModalSubmitBtn');
    confirmBtn.onclick = function() {
        formElement.submit();
    };

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}
