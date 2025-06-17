// ===== STATIC/JS/MAIN.JS (FIXED) =====
class ColdCallingApp {
    constructor() {
        this.currentUser = null;
        this.accessToken = localStorage.getItem('access_token');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
    }

    setupEventListeners() {
        // Auth buttons
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');

        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }

        // Check for auth forms
        this.setupAuthForms();
    }

    setupAuthForms() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin(new FormData(loginForm));
            });
        }

        // Email verification form
        const verifyForm = document.getElementById('verify-form');
        if (verifyForm) {
            verifyForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleEmailVerification(new FormData(verifyForm));
            });
        }

        // Send verification code button (this now handles the complete registration flow)
        const sendCodeBtn = document.getElementById('send-verification-btn');
        if (sendCodeBtn) {
            sendCodeBtn.addEventListener('click', () => {
                this.sendVerificationCode();
            });
        }
    }

    async checkAuthStatus() {
        if (!this.accessToken) {
            this.updateAuthUI(false);
            return;
        }

        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.updateAuthUI(true);
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.logout();
        }
    }

    updateAuthUI(isAuthenticated) {
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');

        if (isAuthenticated) {
            if (loginBtn) loginBtn.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = 'block';
        } else {
            if (loginBtn) loginBtn.style.display = 'block';
            if (logoutBtn) logoutBtn.style.display = 'none';
        }
    }

    validateRegistrationForm() {
        const email = document.getElementById('register-email')?.value?.trim();
        const password = document.getElementById('register-password')?.value;
        const firstName = document.getElementById('register-first-name')?.value?.trim();
        const jobTitle = document.getElementById('prospect-job-title')?.value;
        const industry = document.getElementById('prospect-industry')?.value;

        if (!email) {
            this.showMessage('Please enter your email address', 'error');
            return false;
        }

        if (!password || password.length < 6) {
            this.showMessage('Password must be at least 6 characters long', 'error');
            return false;
        }

        if (!firstName) {
            this.showMessage('Please enter your first name', 'error');
            return false;
        }

        if (!jobTitle) {
            this.showMessage('Please select a prospect job title', 'error');
            return false;
        }

        if (!industry) {
            this.showMessage('Please select a prospect industry', 'error');
            return false;
        }

        return true;
    }

    async sendVerificationCode() {
        // Validate all form fields first
        if (!this.validateRegistrationForm()) {
            return;
        }

        // Collect all form data
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const firstName = document.getElementById('register-first-name').value.trim();
        const jobTitle = document.getElementById('prospect-job-title').value;
        const industry = document.getElementById('prospect-industry').value;
        const customNotes = document.getElementById('custom-ai-notes')?.value?.trim() || '';

        const button = document.getElementById('send-verification-btn');
        const originalText = button.textContent;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';

        try {
            const response = await fetch('/api/auth/send-verification', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    first_name: firstName,
                    prospect_job_title: jobTitle,
                    prospect_industry: industry,
                    custom_ai_notes: customNotes
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Verification code sent! Check your email.', 'success');
                
                // Update step indicator
                document.getElementById('step-1')?.classList.remove('active');
                document.getElementById('step-1')?.classList.add('completed');
                document.getElementById('step-2')?.classList.add('active');
                
                // Show verification form
                const verificationSection = document.getElementById('verification-section');
                if (verificationSection) {
                    verificationSection.style.display = 'block';
                    // Copy email to verification form
                    const verifyEmailInput = document.getElementById('verify-email');
                    if (verifyEmailInput) {
                        verifyEmailInput.value = email;
                    }
                    // Scroll to verification section
                    verificationSection.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                this.showMessage(data.error || 'Failed to send verification code', 'error');
            }
        } catch (error) {
            console.error('Network error:', error);
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    async handleEmailVerification(formData) {
        const button = document.querySelector('#verify-form button[type="submit"]');
        const originalText = button.textContent;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying...';

        try {
            const response = await fetch('/api/auth/verify-and-register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: formData.get('email'),
                    code: formData.get('code')
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Update step indicator
                document.getElementById('step-2')?.classList.remove('active');
                document.getElementById('step-2')?.classList.add('completed');
                document.getElementById('step-3')?.classList.add('active');
                
                this.showMessage('Account created successfully! You can now log in.', 'success');
                
                // Redirect to login after a brief delay
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                this.showMessage(data.error || 'Verification failed', 'error');
            }
        } catch (error) {
            console.error('Network error:', error);
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    async handleLogin(formData) {
        const button = document.querySelector('#login-form button[type="submit"]');
        const originalText = button.textContent;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Logging In...';

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: formData.get('email'),
                    password: formData.get('password')
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.accessToken = data.access_token;
                localStorage.setItem('access_token', this.accessToken);
                this.currentUser = data.user;
                
                this.showMessage('Login successful!', 'success');
                
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);
            } else {
                this.showMessage(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Network error:', error);
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    async logout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        }

        this.accessToken = null;
        this.currentUser = null;
        localStorage.removeItem('access_token');
        this.updateAuthUI(false);
        
        window.location.href = '/';
    }

    showMessage(message, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.alert-message');
        existingMessages.forEach(msg => msg.remove());

        // Create new message
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show alert-message`;
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Utility method for API calls
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.accessToken && { 'Authorization': `Bearer ${this.accessToken}` })
            }
        };

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            this.logout();
            throw new Error('Authentication required');
        }

        return response;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.coldCallingApp = new ColdCallingApp();
});