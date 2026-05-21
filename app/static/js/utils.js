/**
 * Utilidades para iLoveDB - Copiar, exportar, notificaciones
 */

/* ============================================
   TOAST NOTIFICATIONS
   ============================================ */

class Toast {
    constructor(title, message, type = 'info', duration = 3000) {
        this.title = title;
        this.message = message;
        this.type = type; // success, error, warning, info
        this.duration = duration;
        this.element = null;
    }

    show() {
        const container = document.getElementById('toast-container') || this.createContainer();
        
        this.element = document.createElement('div');
        this.element.className = `toast toast--${this.type}`;
        this.element.innerHTML = `
            <div class="toast__content">
                <div class="toast__title">${this.title}</div>
                ${this.message ? `<p class="toast__message">${this.message}</p>` : ''}
            </div>
            <button type="button" class="toast__close" aria-label="Cerrar notificación">×</button>
        `;

        this.element.querySelector('.toast__close').addEventListener('click', () => this.hide());
        container.appendChild(this.element);

        if (this.duration > 0) {
            setTimeout(() => this.hide(), this.duration);
        }

        return this.element;
    }

    hide() {
        if (!this.element) return;
        this.element.classList.add('toast--exit');
        setTimeout(() => this.element?.remove(), 300);
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.bottom = '2rem';
        container.style.right = '2rem';
        container.style.zIndex = '1000';
        container.style.display = 'flex';
        container.style.flexDirection = 'column-reverse';
        container.style.gap = '0.75rem';
        document.body.appendChild(container);
        return container;
    }
}

function showToast(title, message, type = 'info', duration = 3000) {
    const toast = new Toast(title, message, type, duration);
    toast.show();
    return toast;
}

function showSuccess(title, message, duration = 3000) {
    return showToast(title, message, 'success', duration);
}

function showError(title, message, duration = 5000) {
    return showToast(title, message, 'error', duration);
}

function showWarning(title, message, duration = 4000) {
    return showToast(title, message, 'warning', duration);
}

function showInfo(title, message, duration = 3000) {
    return showToast(title, message, 'info', duration);
}

/* ============================================
   CLIPBOARD UTILITIES
   ============================================ */

async function copyToClipboard(text, elementId = null) {
    try {
        await navigator.clipboard.writeText(text);
        showSuccess('¡Copiado!', 'El contenido se copió al portapapeles');
        
        // Cambiar botón por un momento si existe
        if (elementId) {
            const btn = document.getElementById(elementId);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓ Copiado';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }
        }
        return true;
    } catch (err) {
        console.error('Error al copiar:', err);
        showError('Error', 'No se pudo copiar al portapapeles');
        return false;
    }
}

async function copyCode(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        showError('Error', 'Elemento no encontrado');
        return;
    }

    const text = element.textContent || element.innerText;
    return copyToClipboard(text, elementId);
}

/* ============================================
   EXPORT/DOWNLOAD UTILITIES
   ============================================ */

function downloadFile(content, filename, mimeType = 'text/plain') {
    try {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        showSuccess('¡Descargado!', `Se descargó ${filename}`);
        return true;
    } catch (err) {
        console.error('Error al descargar:', err);
        showError('Error', 'No se pudo descargar el archivo');
        return false;
    }
}

function downloadSQL(content, filename = 'query.sql') {
    return downloadFile(content, filename, 'text/sql');
}

function downloadCSV(content, filename = 'data.csv') {
    return downloadFile(content, filename, 'text/csv');
}

function downloadJSON(content, filename = 'data.json') {
    const json = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
    return downloadFile(json, filename, 'application/json');
}

/* ============================================
   LOADING STATES
   ============================================ */

function setButtonLoading(buttonId, isLoading = true) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    if (isLoading) {
        btn.disabled = true;
        btn.classList.add('btn--loading');
        const spinner = document.createElement('span');
        spinner.className = 'spinner';
        spinner.id = `spinner-${buttonId}`;
        btn.insertBefore(spinner, btn.firstChild);
    } else {
        btn.disabled = false;
        btn.classList.remove('btn--loading');
        const spinner = btn.querySelector(`#spinner-${buttonId}`);
        if (spinner) spinner.remove();
    }
}

function setButtonLoadingText(buttonId, isLoading = true, loadingText = 'Procesando...') {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    const originalText = btn.getAttribute('data-original-text') || btn.textContent;
    if (!btn.getAttribute('data-original-text')) {
        btn.setAttribute('data-original-text', originalText);
    }

    if (isLoading) {
        btn.textContent = loadingText;
        btn.disabled = true;
        btn.classList.add('btn--loading');
    } else {
        btn.textContent = originalText;
        btn.disabled = false;
        btn.classList.remove('btn--loading');
    }
}

/* ============================================
   INPUT VALIDATION DISPLAY
   ============================================ */

function showInputError(inputId, message) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.classList.add('input-error');
    
    let errorElement = document.getElementById(`${inputId}-error`);
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = `${inputId}-error`;
        errorElement.className = 'input-message input-message--error';
        input.parentNode.insertBefore(errorElement, input.nextSibling);
    }
    
    errorElement.textContent = message;
}

function clearInputError(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.classList.remove('input-error');
    
    const errorElement = document.getElementById(`${inputId}-error`);
    if (errorElement) {
        errorElement.textContent = '';
    }
}

function showInputSuccess(inputId, message) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.classList.remove('input-error');
    
    let messageElement = document.getElementById(`${inputId}-message`);
    if (!messageElement) {
        messageElement = document.createElement('div');
        messageElement.id = `${inputId}-message`;
        messageElement.className = 'input-message input-message--success';
        input.parentNode.insertBefore(messageElement, input.nextSibling);
    }
    
    messageElement.textContent = message;
}

/* ============================================
   FORMAT UTILITIES
   ============================================ */

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/* ============================================
   RESULT FORMATTING
   ============================================ */

function createResultCard(content, type = 'success', title = '', subtitle = '') {
    const card = document.createElement('div');
    card.className = `result-card result-card--${type}`;
    
    let html = '';
    if (title) {
        html += `<div class="result-card__title">${title}</div>`;
    }
    if (subtitle) {
        html += `<div class="result-card__subtitle">${subtitle}</div>`;
    }
    html += `<div class="result-card__body">${content}</div>`;
    
    card.innerHTML = html;
    return card;
}

function showResultError(container, message, title = 'Error') {
    const card = createResultCard(message, 'error', title);
    container.innerHTML = '';
    container.appendChild(card);
}

function showResultSuccess(container, content, title = 'Éxito', subtitle = '') {
    const card = createResultCard(content, 'success', title, subtitle);
    container.innerHTML = '';
    container.appendChild(card);
}

function showResultWarning(container, content, title = 'Advertencia', subtitle = '') {
    const card = createResultCard(content, 'warning', title, subtitle);
    container.innerHTML = '';
    container.appendChild(card);
}

/* ============================================
   FETCH WRAPPER WITH ERROR HANDLING
   ============================================ */

async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `Error ${response.status}`);
        }

        return { success: true, data };
    } catch (error) {
        console.error('API Error:', error);
        return {
            success: false,
            error: error.message || 'Error desconocido'
        };
    }
}

/* ============================================
   DEBOUNCE & THROTTLE
   ============================================ */

function debounce(fn, delay = 300) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
}

function throttle(fn, delay = 300) {
    let lastCall = 0;
    return function(...args) {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            fn(...args);
        }
    };
}

/* ============================================
   EXPORT FOR USE
   ============================================ */

// Hacer funciones disponibles globalmente
window.Toast = Toast;
window.showToast = showToast;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;
window.copyToClipboard = copyToClipboard;
window.copyCode = copyCode;
window.downloadFile = downloadFile;
window.downloadSQL = downloadSQL;
window.downloadCSV = downloadCSV;
window.downloadJSON = downloadJSON;
window.setButtonLoading = setButtonLoading;
window.setButtonLoadingText = setButtonLoadingText;
window.showInputError = showInputError;
window.clearInputError = clearInputError;
window.showInputSuccess = showInputSuccess;
window.formatBytes = formatBytes;
window.formatNumber = formatNumber;
window.createResultCard = createResultCard;
window.showResultError = showResultError;
window.showResultSuccess = showResultSuccess;
window.showResultWarning = showResultWarning;
window.apiFetch = apiFetch;
window.debounce = debounce;
window.throttle = throttle;
