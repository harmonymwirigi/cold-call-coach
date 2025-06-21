// ===== static/js/utils/ui-helpers.js =====

class UIHelpers {
    static showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        notification.innerHTML = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
    
    static showError(message) {
        this.showNotification(`<strong>Error:</strong> ${message}`, 'danger');
    }
    
    static showSuccess(message) {
        this.showNotification(`<strong>Success:</strong> ${message}`, 'success');
    }
    
    static showWarning(message) {
        this.showNotification(`<strong>Warning:</strong> ${message}`, 'warning');
    }
    
    static showLoading(element, text = 'Loading...') {
        if (element) {
            element.disabled = true;
            element.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${text}`;
        }
    }
    
    static hideLoading(element, originalText) {
        if (element) {
            element.disabled = false;
            element.innerHTML = originalText;
        }
    }
    
    static animateScore(element, targetScore, duration = 2000) {
        if (!element) return;
        
        let currentScore = 0;
        const increment = targetScore / (duration / 50);
        
        const timer = setInterval(() => {
            currentScore += increment;
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(timer);
            }
            element.textContent = Math.round(currentScore);
        }, 50);
    }
    
    static capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    static formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    static debounce(func, wait) {
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
    
    static throttle(func, limit) {
        let lastFunc;
        let lastRan;
        return function executedFunction(...args) {
            if (!lastRan) {
                func(...args);
                lastRan = Date.now();
            } else {
                clearTimeout(lastFunc);
                lastFunc = setTimeout(() => {
                    if ((Date.now() - lastRan) >= limit) {
                        func(...args);
                        lastRan = Date.now();
                    }
                }, limit - (Date.now() - lastRan));
            }
        };
    }
}

// Global access
window.UIHelpers = UIHelpers;