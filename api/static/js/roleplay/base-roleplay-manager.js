// ===== FIXED: static/js/roleplay/base-roleplay-manager.js =====

class BaseRoleplayManager {
    constructor(options = {}) {
        this.containerId = options.containerId || null;
        this.selectedMode = null;
        this.callState = 'idle'; // idle, dialing, ringing, connected, ended
        this.callStartTime = null;
        this.durationInterval = null;
        this.currentSession = null;
        this.isActive = false;
        this.voiceHandler = null;
        this.isProcessing = false;
        this.conversationHistory = [];
        
        // Enhanced session management
        this.sessionRetryCount = 0;
        this.maxRetries = 3;
        
        // Debug flag
        this.debugMode = options.debugMode || true;
    }
    
    init() {
        console.log('🚀 Initializing Base Roleplay Manager...');
        
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        
        this.loadRoleplayData();
        this.setupEventListeners();
        this.initializeModeSelection();
        
        // Initialize voice handler
        if (typeof VoiceHandler !== 'undefined') {
            this.voiceHandler = new VoiceHandler(this);
            console.log('✅ Voice Handler initialized');
        } else {
            console.warn('⚠️ VoiceHandler not available');
        }
    }
    
    updateTime() {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: false 
        });
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = time;
        }
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            },
            ...options
        };
        
        try {
            console.log('🌐 API call:', endpoint, options.method || 'GET');
            const response = await fetch(endpoint, defaultOptions);
            
            if (!response.ok) {
                if (response.status === 401) {
                    console.error('🔐 Authentication required');
                    window.location.href = '/login';
                    throw new Error('Authentication required');
                } else if (response.status === 404) {
                    console.error('🔍 Endpoint not found:', endpoint);
                    throw new Error('Endpoint not found - please check API routing');
                } else {
                    const errorText = await response.text();
                    console.error('❌ API error:', response.status, errorText);
                    throw new Error(`API Error ${response.status}: ${errorText}`);
                }
            }
            
            return response;
        } catch (error) {
            console.error('❌ API call failed:', error);
            throw error;
        }
    }

    loadRoleplayData() {
        const roleplayData = document.getElementById('roleplay-data');
        if (roleplayData) {
            const roleplayId = roleplayData.dataset.roleplayId || '1.1';
            const isAuthenticated = roleplayData.dataset.userAuthenticated === 'true';
            
            console.log('📊 Roleplay data:', { roleplayId, isAuthenticated });
            
            if (!isAuthenticated) {
                this.showError('Please log in to access roleplay training');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
                return;
            }
            
            if (roleplayId) {
                this.loadRoleplayInfo(roleplayId);
            }
        }
    }
    
    async loadRoleplayInfo(roleplayId) {
        try {
            console.log('📡 Loading roleplay info for ID:', roleplayId);
            const response = await this.apiCall(`/api/roleplay/info/${roleplayId}`);
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Roleplay info loaded:', data);
                this.updateRoleplayUI(data);
            } else {
                console.error('❌ Failed to load roleplay info:', await response.text());
                this.updateRoleplayUI({
                    name: `Roleplay ${roleplayId}`,
                    job_title: 'CTO',
                    industry: 'Technology'
                });
            }
        } catch (error) {
            console.error('❌ Error loading roleplay info:', error);
            this.updateRoleplayUI({
                name: `Roleplay ${roleplayId}`,
                job_title: 'CTO',
                industry: 'Technology'
            });
        }
    }
    
    updateRoleplayUI(roleplayData) {
        const titleElement = document.getElementById('roleplay-title');
        if (titleElement) {
            titleElement.textContent = `${roleplayData.name || 'Roleplay Training'}`;
        }
        
        this.updateProspectInfo(roleplayData);
    }
    
    updateProspectInfo(roleplayData) {
        const avatarElement = document.getElementById('contact-avatar');
        const nameElement = document.getElementById('contact-name');
        const infoElement = document.getElementById('contact-info');
        
        if (nameElement) {
            nameElement.textContent = this.generateProspectName(roleplayData.job_title || 'CTO');
        }
        
        if (infoElement) {
            infoElement.textContent = `${roleplayData.job_title || 'CTO'} • ${roleplayData.industry || 'Technology'}`;
        }
        
        if (avatarElement) {
            const avatarUrl = this.getAvatarUrl(roleplayData.job_title || 'CTO');
            avatarElement.src = avatarUrl;
            avatarElement.alt = `Roleplay prospect`;
            
            avatarElement.onerror = function() {
                this.src = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face';
                this.onerror = null;
            };
        }
    }
    
    getAvatarUrl(jobTitle) {
        const avatarMapping = {
            'CEO': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
            'CTO': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
            'VP of Sales': 'https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=150&h=150&fit=crop&crop=face'
        };
        
        return avatarMapping[jobTitle] || avatarMapping['CTO'];
    }
    
    generateProspectName(jobTitle) {
        const names = {
            'CEO': ['Alex Morgan', 'Sarah Chen', 'Michael Rodriguez'],
            'CTO': ['David Kim', 'Jennifer Walsh', 'Robert Singh'],
            'VP of Sales': ['Lisa Thompson', 'Mark Johnson', 'Amanda Garcia']
        };
        
        const nameList = names[jobTitle] || ['Jordan Smith', 'Taylor Brown', 'Casey Jones'];
        return nameList[Math.floor(Math.random() * nameList.length)];
    }
    
    setupEventListeners() {
        console.log('🔧 Setting up event listeners...');
        
        // Mode selection
        document.querySelectorAll('.mode-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const mode = option.dataset.mode;
                console.log('📋 Mode selected:', mode);
                this.selectMode(mode);
            });
        });
        
        // Start call button
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🚀 Start call button clicked');
                if (!this.isProcessing) {
                    this.startCall();
                }
            });
        }
        
        // Microphone button
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🎤 Mic button clicked');
                
                if (this.voiceHandler) {
                    if (this.voiceHandler.isListening) {
                        this.voiceHandler.stopListening();
                    } else {
                        this.voiceHandler.startListening(false);
                    }
                }
            });
        }
        
        // FIXED: End call button - make sure it's visible during calls
        const endCallBtn = document.getElementById('end-call-btn');
        if (endCallBtn) {
            endCallBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('📞 End call button clicked');
                this.endCall();
            });
        }
        
        // Feedback actions
        const tryAgainBtn = document.getElementById('try-again-btn');
        if (tryAgainBtn) {
            tryAgainBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🔄 Try again clicked');
                this.tryAgain();
            });
        }
        
        const newModeBtn = document.getElementById('new-mode-btn');
        if (newModeBtn) {
            newModeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🆕 New mode clicked');
                this.showModeSelection();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.callState === 'connected' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                this.handleSpacebarPress();
            }
            
            if (e.code === 'Escape' && this.callState === 'connected') {
                e.preventDefault();
                console.log('⌨️ Escape key pressed - end call');
                this.endCall();
            }
        });
        
        console.log('✅ Event listeners setup complete');
    }
    
    handleSpacebarPress() {
        // To be implemented by subclasses
        console.log('Space pressed - implement in subclass');
    }
    
    initializeModeSelection() {
        console.log('🎯 Initializing mode selection...');
        
        document.getElementById('mode-selection').style.display = 'flex';
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'none';
        
        this.callState = 'idle';
        this.isActive = false;
        this.isProcessing = false;
        this.conversationHistory = [];
        this.sessionRetryCount = 0;
        
        // Stop any active audio or voice recognition
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
        }
    }
    
    selectMode(mode) {
        if (!mode || this.isProcessing) return;
        
        console.log('✅ Mode selected:', mode);
        this.selectedMode = mode;
        
        // Update UI
        document.querySelectorAll('.mode-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        const selectedOption = document.querySelector(`[data-mode="${mode}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        // Update start button
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = `Start ${this.capitalizeFirst(mode)} Mode`;
        }
    }
    
    updateStartButton(text, disabled = false) {
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = disabled;
            if (disabled) {
                startBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${text}`;
            } else {
                startBtn.textContent = text;
            }
        }
    }
    
    async startPhoneCallSequence(initialResponse) {
        console.log('📞 Starting phone call sequence...');
        
        // Hide mode selection, show call interface
        document.getElementById('mode-selection').style.display = 'none';
        document.getElementById('phone-container').style.display = 'block';
        document.getElementById('call-interface').style.display = 'flex';
        
        // FIXED: Make sure end call button is visible
        const endCallBtn = document.getElementById('end-call-btn');
        if (endCallBtn) {
            endCallBtn.style.display = 'block';
        }
        
        await this.dialingState();
        await this.ringingState();
        await this.connectedState(initialResponse);
    }

    async dialingState() {
        console.log('📱 Dialing state...');
        this.callState = 'dialing';
        this.updateCallStatus('Calling...', 'dialing');
        
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.add('calling');
        }
        
        await this.delay(2000);
    }
    
    async ringingState() {
        console.log('📳 Ringing state...');
        this.callState = 'ringing';
        this.updateCallStatus('Ringing...', 'ringing');
        
        await this.delay(3000);
    }
    
    async connectedState(initialResponse) {
        console.log('✅ Connected - Roleplay active!');
        this.callState = 'connected';
        this.updateCallStatus('Connected', 'connected');
        
        // Update UI
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.remove('calling');
            avatar.classList.add('roleplay-active');
        }
        
        // Start call timer
        this.callStartTime = Date.now();
        this.startCallTimer();
        
        // Show live transcript
        const transcript = document.getElementById('live-transcript');
        if (transcript) {
            transcript.classList.add('show');
        }
        
        // Clear conversation history
        this.conversationHistory = [];
        
        // Play initial AI response or start user turn
        if (initialResponse) {
            console.log('🎯 Playing initial AI response:', initialResponse);
            await this.playAIResponseAndWaitForUser(initialResponse);
        } else {
            console.log('🎤 No initial response, starting user turn');
            this.startUserTurn();
        }
    }
    
    updateCallStatus(text, state) {
        const callInterface = document.getElementById('call-interface');
        const statusText = document.getElementById('call-status-text');
        
        if (callInterface) {
            callInterface.className = `call-interface ${state}`;
        }
        
        if (statusText) {
            statusText.textContent = text;
        }
    }
    
    startCallTimer() {
        this.durationInterval = setInterval(() => {
            const elapsed = Date.now() - this.callStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            const durationElement = document.getElementById('call-duration');
            if (durationElement) {
                durationElement.textContent = 
                    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    addToConversationHistory(sender, message) {
        this.conversationHistory.push({
            sender: sender,
            message: message,
            timestamp: new Date()
        });
        console.log(`📝 Added to conversation: ${sender} - ${message.substring(0, 50)}...`);
    }
    
    updateTranscript(text) {
        const transcriptElement = document.getElementById('live-transcript');
        if (transcriptElement) {
            transcriptElement.textContent = text;
        }
    }

    addPulseToMicButton() {
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.classList.add('pulse-animation');
            setTimeout(() => {
                if(micBtn) micBtn.classList.remove('pulse-animation');
            }, 3000);
        }
    }
    
    async simulateSpeakingTime(text) {
        const wordsPerMinute = 150;
        const words = text ? text.split(' ').length : 0;
        const speakingTimeMs = (words / wordsPerMinute) * 60 * 1000;
        const minTime = 1000;
        const maxTime = 5000;
        
        const delayTime = Math.max(minTime, Math.min(maxTime, speakingTimeMs));
        console.log(`⏱️ Simulating speaking time: ${delayTime}ms for ${words} words`);
        
        return new Promise(resolve => setTimeout(resolve, delayTime));
    }
    
    updateUI(className) {
        const container = document.getElementById('phone-container');
        if (container) {
            container.classList.add(className);
        }
    }
    
    showError(message) {
        console.error('❌ Error:', message);
        this.updateTranscript(`❌ Error: ${message}`);
        
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        alertDiv.innerHTML = `<strong>Error:</strong> ${message}`;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    tryAgain() {
        console.log('🔄 Trying again');
        this.showModeSelection();
    }
    
    showModeSelection() {
        console.log('🎯 Showing mode selection');
        
        // Hide phone and feedback, show mode selection
        document.getElementById('phone-container').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'none';
        document.getElementById('mode-selection').style.display = 'flex';
        
        this.initializeModeSelection();
        
        this.selectedMode = null;
        this.currentSession = null;
        
        document.querySelectorAll('.mode-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.textContent = 'Select a mode to start';
        }
    }
    
    getRoleplayId() {
        const roleplayData = document.getElementById('roleplay-data');
        return roleplayData ? (roleplayData.dataset.roleplayId || '1.1') : '1.1';
    }
    
    capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    animateScore(targetScore) {
        const scoreElement = document.getElementById('score-circle');
        if (!scoreElement) return;
        
        let currentScore = 0;
        const increment = targetScore / 40;
        
        const timer = setInterval(() => {
            currentScore += increment;
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(timer);
            }
            scoreElement.textContent = Math.round(currentScore);
        }, 50);
    }
    
    updateScoreCircleColor(score) {
        const scoreCircle = document.getElementById('score-circle');
        if (scoreCircle) {
            scoreCircle.classList.remove('excellent', 'good', 'needs-improvement');
            
            if (score >= 85) {
                scoreCircle.classList.add('excellent');
            } else if (score >= 70) {
                scoreCircle.classList.add('good');
            } else {
                scoreCircle.classList.add('needs-improvement');
            }
        }
    }
    
    destroy() {
        console.log('🧹 Destroying Roleplay Manager');
        
        if (this.voiceHandler) {
            this.voiceHandler.destroy();
        }
        
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
        }
        
        this.isActive = false;
        this.currentSession = null;
        this.isProcessing = false;
    }
    
    // ENHANCED: Retry session recovery
    async retrySessionRecovery() {
        if (this.sessionRetryCount >= this.maxRetries) {
            console.error('❌ Max session recovery retries reached');
            this.showError('Session recovery failed. Please start a new call.');
            this.showModeSelection();
            return false;
        }
        
        this.sessionRetryCount++;
        console.log(`🔄 Attempting session recovery... attempt ${this.sessionRetryCount}/${this.maxRetries}`);
        
        try {
            // Try to get session debug info
            const response = await this.apiCall('/api/roleplay/session/debug');
            if (response.ok) {
                const debugData = await response.json();
                console.log('🔍 Session debug info:', debugData);
                
                // If we find active sessions, try to continue
                if (debugData.engine_sessions && debugData.engine_sessions.length > 0) {
                    const activeSession = debugData.engine_sessions.find(s => s.active);
                    if (activeSession) {
                        console.log('✅ Found active session, continuing...');
                        return true;
                    }
                }
            }
        } catch (error) {
            console.error('❌ Session recovery failed:', error);
        }
        
        return false;
    }
    
    // Abstract methods to be implemented by subclasses
    async startCall() {
        throw new Error('startCall must be implemented by subclass');
    }
    
    async processUserInput(transcript) {
        throw new Error('processUserInput must be implemented by subclass');
    }
    
    async endCall(forcedEnd = false) {
        if (!this.isActive) return;

        console.log('📞 Ending call. Forced:', forcedEnd);
        this.isProcessing = true;
        this.isActive = false;

        // Stop timer and voice recognition
        clearInterval(this.durationInterval);
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
        }

        this.updateCallStatus('Call Ended', 'ended');

        try {
            const response = await this.apiCall('/api/roleplay/end', {
                method: 'POST',
                body: JSON.stringify({ forced_end: forcedEnd })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('📊 Final session data received:', data);
                this.showFeedback(data.coaching, data.overall_score);
            } else {
                console.error('❌ Failed to end session gracefully.');
                this.showError('Could not retrieve final feedback.');
                this.showFeedback({}, 50);
            }
        } catch (error) {
            console.error('❌ Error during endCall API request:', error);
            this.showError('An error occurred while ending the call.');
            this.showFeedback({}, 50);
        } finally {
            this.isProcessing = false;
        }
    }

    createModeSelectionUI(modes) {
        const modeGrid = document.getElementById('mode-grid');
        if (!modeGrid) return;

        modeGrid.innerHTML = '';

        modes.forEach(mode => {
            const modeCard = document.createElement('div');
            modeCard.className = 'mode-option';
            modeCard.dataset.mode = mode.id;

            modeCard.innerHTML = `
                <h5><i class="fas fa-${mode.icon} me-2"></i>${mode.name}</h5>
                <small>${mode.description}</small>
            `;
            
            modeCard.addEventListener('click', () => this.selectMode(mode.id));
            modeGrid.appendChild(modeCard);
        });
    }

    showFeedback(coaching, score = 75) {
        console.log('📊 Base: Showing feedback screen.');
        
        const callInterface = document.getElementById('call-interface');
        const feedbackSection = document.getElementById('feedback-section');
        if (callInterface) callInterface.style.display = 'none';
        if (feedbackSection) feedbackSection.style.display = 'flex';

        this.animateScore(score);
        this.updateScoreCircleColor(score);
        
        const content = document.getElementById('feedback-content');
        if (!content) return;
        
        if (coaching && Object.keys(coaching).length > 0) {
             content.innerHTML = Object.entries(coaching).map(([key, value]) => {
                if(typeof value !== 'string') return '';
                const title = key.replace(/_/g, ' ').replace(/(^\w|\s\w)/g, m => m.toUpperCase());
                return `<div class="feedback-item"><h5>${title}</h5><p>${value}</p></div>`;
             }).join('');
        } else {
            content.innerHTML = `<div class="feedback-item"><p>Great job completing the session! Keep practicing.</p></div>`;
        }
    }

    async playAIResponseAndWaitForUser(text) {
        throw new Error('playAIResponseAndWaitForUser must be implemented by subclass');
    }

    async playAIResponse(text) {
        if (this.voiceHandler) {
            await this.voiceHandler.playAudio(text);
        } else {
            console.warn("Voice handler not available, simulating speech time.");
            await this.simulateSpeakingTime(text);
            this.startUserTurn();
        }
    }

    startUserTurn() {
        console.log('👤 Base: Starting user turn.');
        if (this.voiceHandler) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        this.updateTranscript('🎤 Your turn... speak now.');
        this.addPulseToMicButton();
    }
}

// Export for global access
window.BaseRoleplayManager = BaseRoleplayManager;