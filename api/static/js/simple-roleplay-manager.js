// ===== static/js/simple-roleplay-manager.js =====

class SimpleRoleplayManager {
    constructor() {
        this.isActive = false;
        this.sessionId = null;
        this.currentRoleplayId = this.extractRoleplayId();
        this.mode = 'practice';
        this.callTimer = null;
        this.callStartTime = null;
        this.voiceHandler = null; // Add this
        
        console.log(`🚀 Simple Roleplay Manager initialized for: ${this.currentRoleplayId}`);
        
        this.initializeElements();
        this.bindEvents();
        this.setupInterface();
        this.initializeVoiceHandler(); // Add this
    }

    // NEW METHOD: Initialize voice handler properly
    initializeVoiceHandler() {
        try {
            if (typeof VoiceHandler !== 'undefined') {
                this.voiceHandler = new VoiceHandler(this);
                console.log('🎤 Voice handler initialized successfully');
                
                // Set up callbacks
                this.voiceHandler.onTranscript = (transcript) => this.handleVoiceInput(transcript);
                this.voiceHandler.onError = (error) => this.showError(error);
                
                // Check if supported
                if (this.voiceHandler.isSupported) {
                    console.log('✅ Voice recognition supported and ready');
                } else {
                    console.warn('⚠️ Voice recognition not supported in this browser');
                }
            } else {
                console.warn('⚠️ VoiceHandler class not available');
                setTimeout(() => this.initializeVoiceHandler(), 1000); // Retry after 1 second
            }
        } catch (error) {
            console.error('❌ Failed to initialize voice handler:', error);
        }
    }
    
    extractRoleplayId() {
        // Get from URL
        const pathParts = window.location.pathname.split('/');
        const roleplayIndex = pathParts.indexOf('roleplay');
        
        if (roleplayIndex !== -1 && pathParts[roleplayIndex + 1]) {
            return pathParts[roleplayIndex + 1];
        }
        
        // Get from data attribute
        const dataElement = document.getElementById('roleplay-data');
        if (dataElement) {
            return dataElement.dataset.roleplayId || '1.1';
        }
        
        return '1.1';
    }
    
    initializeElements() {
        this.elements = {
            modeSelection: document.getElementById('mode-selection'),
            callInterface: document.getElementById('call-interface'),
            feedbackSection: document.getElementById('feedback-section'),
            startCallBtn: document.getElementById('start-call-btn'),
            endCallBtn: document.getElementById('end-call-btn'),
            liveTranscript: document.getElementById('live-transcript'),
            roleplayTitle: document.getElementById('roleplay-title'),
            roleplayVersion: document.getElementById('roleplay-version'),
            modeGrid: document.getElementById('mode-grid'),
            contactName: document.getElementById('contact-name'),
            contactInfo: document.getElementById('contact-info'),
            callDuration: document.getElementById('call-duration'),
            scoreCircle: document.getElementById('score-circle'),
            feedbackContent: document.getElementById('feedback-content'),
            tryAgainBtn: document.getElementById('try-again-btn'),
            newModeBtn: document.getElementById('new-mode-btn'),
            micBtn: document.getElementById('mic-btn'),
            currentTime: document.getElementById('current-time')
        };
        
        // Log which elements were found
        const foundElements = Object.keys(this.elements).filter(key => this.elements[key]);
        const missingElements = Object.keys(this.elements).filter(key => !this.elements[key]);
        
        console.log(`✅ Found elements: ${foundElements.join(', ')}`);
        if (missingElements.length > 0) {
            console.warn(`⚠️ Missing elements: ${missingElements.join(', ')}`);
        }
    }
    
    bindEvents() {
        if (this.elements.startCallBtn) {
            this.elements.startCallBtn.addEventListener('click', () => this.startCall());
        }
        
        if (this.elements.endCallBtn) {
            this.elements.endCallBtn.addEventListener('click', () => this.endCall());
        }
        
        if (this.elements.tryAgainBtn) {
            this.elements.tryAgainBtn.addEventListener('click', () => this.resetInterface());
        }
        
        if (this.elements.newModeBtn) {
            this.elements.newModeBtn.addEventListener('click', () => {
                window.location.href = '/dashboard';
            });
        }
        
        // Voice handler integration
        if (window.voiceHandler) {
            window.voiceHandler.onTranscript = (transcript) => this.handleVoiceInput(transcript);
            window.voiceHandler.onError = (error) => this.showError(error);
            console.log('🎤 Voice handler integrated');
        } else {
            console.warn('⚠️ Voice handler not available');
        }
        
        console.log('📎 Events bound successfully');
    }
    
    setupInterface() {
        // Update title and info
        this.updateRoleplayInfo();
        
        // Create simple mode selection
        this.createModeSelection();
        
        // Update time display
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        
        console.log('🎯 Interface setup complete');
    }
    
    async updateRoleplayInfo() {
        try {
            // Map parent IDs to specific ones for API calls
            let apiRoleplayId = this.currentRoleplayId;
            if (apiRoleplayId === '1') {
                apiRoleplayId = '1.1';
            } else if (apiRoleplayId === '2') {
                apiRoleplayId = '2.1';
            }
            
            // Try to get info from API first
            const response = await fetch(`/api/roleplay/info/${apiRoleplayId}`);
            let roleplayInfo;
            
            if (response.ok) {
                roleplayInfo = await response.json();
                console.log('📋 Loaded roleplay info from API:', roleplayInfo);
            } else {
                // Fallback to hardcoded info
                roleplayInfo = this.getFallbackRoleplayInfo();
                console.log('📋 Using fallback roleplay info:', roleplayInfo);
            }
            
            // Update UI elements
            if (this.elements.roleplayTitle) {
                this.elements.roleplayTitle.textContent = roleplayInfo.name || `Roleplay ${this.currentRoleplayId}`;
            }
            
            if (this.elements.roleplayVersion) {
                this.elements.roleplayVersion.textContent = roleplayInfo.description || `Training Mode - ${this.currentRoleplayId}`;
            }
            
        } catch (error) {
            console.warn('⚠️ Failed to load roleplay info, using fallback:', error);
            this.updateRoleplayInfoFallback();
        }
    }
    
    getFallbackRoleplayInfo() {
        const fallbackInfo = {
            '1.1': { name: 'Practice Mode', description: 'Single call with detailed coaching' },
            '1.2': { name: 'Marathon Mode', description: '10 calls, need 6 to pass' },
            '1.3': { name: 'Legend Mode', description: '6 perfect calls in a row' },
            '2.1': { name: 'Pitch Practice', description: 'Advanced pitch training' },
            '2.2': { name: 'Pitch Marathon', description: '10 advanced calls' },
            '3': { name: 'Warm-up Challenge', description: '25 rapid-fire questions' },
            '4': { name: 'Full Cold Call', description: 'Complete simulation' },
            '5': { name: 'Power Hour', description: '10 consecutive calls' }
        };
        
        return fallbackInfo[this.currentRoleplayId] || { 
            name: `Roleplay ${this.currentRoleplayId}`, 
            description: 'Cold calling training' 
        };
    }
    
    updateRoleplayInfoFallback() {
        const info = this.getFallbackRoleplayInfo();
        
        if (this.elements.roleplayTitle) {
            this.elements.roleplayTitle.textContent = info.name;
        }
        
        if (this.elements.roleplayVersion) {
            this.elements.roleplayVersion.textContent = info.description;
        }
    }
    
    createModeSelection() {
        if (!this.elements.modeGrid) {
            console.warn('⚠️ Mode grid element not found');
            return;
        }
        
        // Clear existing content
        this.elements.modeGrid.innerHTML = '';
        
        // Create simple mode option
        const modeOption = document.createElement('div');
        modeOption.className = 'mode-option selected';
        modeOption.dataset.mode = 'practice';
        
        modeOption.innerHTML = `
            <i class="fas fa-user-graduate fa-2x" style="color: #60a5fa; margin-bottom: 12px;"></i>
            <h5 style="margin: 12px 0 8px 0; color: white; font-size: 18px;">Practice Mode</h5>
            <small style="color: rgba(255, 255, 255, 0.8); font-size: 14px;">Single call with detailed coaching</small>
        `;
        
        // Add click handler
        modeOption.addEventListener('click', () => {
            this.selectMode('practice');
        });
        
        this.elements.modeGrid.appendChild(modeOption);
        
        // Auto-select practice mode
        this.selectMode('practice');
        
        console.log('🎮 Mode selection created');
    }
    
    selectMode(modeId) {
        this.mode = modeId;
        
        // Update UI to show selected mode
        const modeOptions = document.querySelectorAll('.mode-option');
        modeOptions.forEach(option => {
            option.classList.remove('selected');
        });
        
        const selectedOption = document.querySelector(`[data-mode="${modeId}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        // Enable start button
        if (this.elements.startCallBtn) {
            this.elements.startCallBtn.disabled = false;
            this.elements.startCallBtn.textContent = `Start ${this.mode} call`;
            this.elements.startCallBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
        }
        
        console.log(`🎯 Mode selected: ${modeId}`);
    }
    
    async startCall() {
        if (this.isActive) {
            console.warn('⚠️ Call already active');
            return;
        }
        
        try {
            console.log(`🚀 Starting call: ${this.currentRoleplayId} (${this.mode})`);
            
            // Show loading state
            if (this.elements.startCallBtn) {
                this.elements.startCallBtn.textContent = 'Connecting...';
                this.elements.startCallBtn.disabled = true;
            }
            
            // Create timeout promise
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Request timeout after 30 seconds')), 30000)
            );
            
            // Create fetch promise
            const fetchPromise = fetch('/api/roleplay/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    roleplay_id: this.currentRoleplayId,
                    mode: this.mode
                })
            });
            
            // Race timeout vs fetch
            const response = await Promise.race([fetchPromise, timeoutPromise]);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('✅ Call start response:', data);
            
            // Validate response
            if (!data.session_id) {
                throw new Error('No session ID received from server');
            }
            
            if (!data.initial_response) {
                console.warn('⚠️ No initial response, using fallback');
                data.initial_response = 'Hello, this is Alex speaking.';
            }
            
            this.sessionId = data.session_id;
            this.isActive = true;
            
            // Show call interface
            this.showCallInterface();
            
            // Start call timer
            this.startCallTimer();
            
            // Handle initial response with small delay
            setTimeout(() => {
                this.addToTranscript('AI', data.initial_response);
                this.playAudio(data.initial_response);
                
                // FIXED: Start auto-listening after AI speaks (with delay for audio)
                setTimeout(() => {
                    this.addToTranscript('System', '🎤 Your turn - speak now...');
                    this.startAutoListening(); // NEW: Start auto-listening
                }, 3000); // Wait 3 seconds for AI audio to finish
            }, 500);
            
            console.log('✅ Call started successfully:', this.sessionId);
            
        } catch (error) {
            console.error('❌ Failed to start call:', error);
            this.showError(`Failed to start call: ${error.message}`);
            
            // Reset button state
            if (this.elements.startCallBtn) {
                this.elements.startCallBtn.textContent = 'Start Practice Call';
                this.elements.startCallBtn.disabled = false;
            }
        }
    }

    // NEW METHOD: Start auto-listening for natural conversation
    startAutoListening() {
        if (this.voiceHandler && this.voiceHandler.isSupported) {
            console.log('🎤 Starting auto-listening for natural conversation...');
            this.voiceHandler.startAutoListening();
            
            // Update UI to show listening state
            this.updateMicrophoneUI(true);
        } else {
            console.warn('⚠️ Voice handler not available for auto-listening');
            this.showError('Voice recognition not available. Please check browser compatibility.');
        }
    }

    // NEW METHOD: Stop auto-listening
    stopAutoListening() {
        if (this.voiceHandler) {
            console.log('🛑 Stopping auto-listening...');
            this.voiceHandler.stopListening();
            this.updateMicrophoneUI(false);
        }
    }
    addSystemMessage(message) {
        if (!this.elements.liveTranscript) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'transcript-message system';
        messageDiv.style.background = 'rgba(34, 197, 94, 0.2)';
        messageDiv.style.borderLeft = '3px solid #22c55e';
        messageDiv.style.fontStyle = 'italic';
        
        messageDiv.innerHTML = `
            <div class="speaker">System:</div>
            <div class="message">${message}</div>
        `;
        
        this.elements.liveTranscript.appendChild(messageDiv);
        this.elements.liveTranscript.scrollTop = this.elements.liveTranscript.scrollHeight;
        
        console.log(`📢 System: ${message}`);
    }
    showCallInterface() {
        console.log('📱 Showing call interface');
        
        if (this.elements.modeSelection) {
            this.elements.modeSelection.style.display = 'none';
        }
        if (this.elements.callInterface) {
            this.elements.callInterface.style.display = 'flex';
        }
        
        // Update contact info with random selection
        this.updateContactInfo();
        
        // Clear transcript
        if (this.elements.liveTranscript) {
            this.elements.liveTranscript.innerHTML = '';
        }
    }
    
    updateContactInfo() {
        const contacts = [
            { name: 'Alex Morgan', title: 'CTO', company: 'TechCorp' },
            { name: 'Sarah Chen', title: 'VP Marketing', company: 'GrowthCo' },
            { name: 'Mike Johnson', title: 'Head of Sales', company: 'ScaleCorp' },
            { name: 'Emma Davis', title: 'CFO', company: 'FinanceFirst' },
            { name: 'James Wilson', title: 'Operations Director', company: 'LogisticsPro' }
        ];
        
        const contact = contacts[Math.floor(Math.random() * contacts.length)];
        
        if (this.elements.contactName) {
            this.elements.contactName.textContent = contact.name;
        }
        
        if (this.elements.contactInfo) {
            this.elements.contactInfo.textContent = `${contact.title} • ${contact.company}`;
        }
        
        console.log(`👤 Contact: ${contact.name} (${contact.title})`);
    }
    
    startCallTimer() {
        this.callStartTime = Date.now();
        
        if (this.callTimer) {
            clearInterval(this.callTimer);
        }
        
        this.callTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.callStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            if (this.elements.callDuration) {
                this.elements.callDuration.textContent = 
                    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
        
        console.log('⏱️ Call timer started');
    }
    
    async handleVoiceInput(transcript) {
        if (!this.isActive || !this.sessionId) {
            console.warn('⚠️ Cannot process voice input: call not active');
            return;
        }
        
        try {
            console.log(`🎤 Processing voice input: "${transcript}"`);
            
            // Stop listening while processing
            this.stopAutoListening();
            
            this.addToTranscript('You', transcript);
            
            const response = await fetch('/api/roleplay/respond', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_input: transcript
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to process response');
            }
            
            const data = await response.json();
            
            // Add AI response to transcript
            this.addToTranscript('AI', data.ai_response);
            
            // Play audio response
            await this.playAudio(data.ai_response);
            
            // Check if call should continue
            if (data.call_continues) {
                // FIXED: Restart auto-listening after AI responds
                setTimeout(() => {
                    this.addToTranscript('System', '🎤 Your turn - speak now...');
                    this.startAutoListening();
                }, 2000); // Wait 2 seconds for AI audio
            } else {
                console.log('📞 Call ending...');
                setTimeout(() => this.handleCallEnd(data), 2000);
            }
            
        } catch (error) {
            console.error('❌ Failed to process voice input:', error);
            this.showError('Failed to process your response');
            
            // Restart listening on error
            setTimeout(() => {
                if (this.isActive) {
                    this.startAutoListening();
                }
            }, 3000);
        }
    }

    // NEW METHOD: Update microphone UI
    updateMicrophoneUI(isListening) {
        if (this.elements.micBtn) {
            if (isListening) {
                this.elements.micBtn.classList.add('listening');
                this.elements.micBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                this.elements.micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                this.elements.micBtn.title = 'Listening - speak naturally';
            } else {
                this.elements.micBtn.classList.remove('listening');
                this.elements.micBtn.style.background = 'rgba(255, 255, 255, 0.1)';
                this.elements.micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                this.elements.micBtn.title = 'Voice recognition ready';
            }
        }
    }
    
    addToTranscript(speaker, text) {
        if (!this.elements.liveTranscript) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `transcript-message ${speaker.toLowerCase()}`;
        
        messageDiv.innerHTML = `
            <div class="speaker">${speaker}:</div>
            <div class="message">${text}</div>
        `;
        
        this.elements.liveTranscript.appendChild(messageDiv);
        this.elements.liveTranscript.scrollTop = this.elements.liveTranscript.scrollHeight;
        
        console.log(`💬 ${speaker}: ${text.substring(0, 50)}${text.length > 50 ? '...' : ''}`);
    }
    
    async playAudio(text) {
        try {
            const response = await fetch('/api/roleplay/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text })
            });
            
            if (response.ok) {
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                
                audio.play().catch(e => {
                    console.warn('🔇 Audio play failed:', e);
                });
                
                // Clean up URL after playing
                audio.addEventListener('ended', () => {
                    URL.revokeObjectURL(audioUrl);
                });
                
                console.log('🔊 Audio played successfully');
            } else {
                console.warn('🔇 TTS request failed:', response.status);
            }
        } catch (error) {
            console.warn('🔇 TTS failed:', error);
        }
    }
    
    async endCall() {
        if (!this.isActive) {
            console.warn('⚠️ No active call to end');
            return;
        }
        
        try {
            console.log('📞 Ending call...');
            
            // Stop voice recognition
            this.stopAutoListening();
            
            const response = await fetch('/api/roleplay/end', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ forced_end: true })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handleCallEnd(data);
            } else {
                console.warn('⚠️ End call request failed:', response.status);
                // Force end anyway
                this.forceEndCall();
            }
            
        } catch (error) {
            console.error('❌ Failed to end call:', error);
            this.forceEndCall();
        }
    }
    
    forceEndCall() {
        console.log('🔧 Force ending call');
        this.isActive = false;
        
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
        
        // Show basic feedback
        this.showFeedback({
            overall_score: 75,
            coaching: {
                opening: 'Good effort on your call!',
                communication: 'Keep practicing to improve.',
                overall: 'Session ended early, but you\'re making progress!'
            }
        });
    }
    
    handleCallEnd(data) {
        console.log('📊 Processing call end data:', data);
        
        this.isActive = false;
        
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
        
        this.showFeedback(data);
    }
    
    showFeedback(data) {
        console.log('📊 Showing feedback');
        
        if (this.elements.callInterface) {
            this.elements.callInterface.style.display = 'none';
        }
        if (this.elements.feedbackSection) {
            this.elements.feedbackSection.style.display = 'block';
        }
        
        // Update score
        const score = data.overall_score || 75;
        if (this.elements.scoreCircle) {
            this.elements.scoreCircle.textContent = score;
            this.updateScoreCircleColor(score);
        }
        
        // Populate feedback content
        if (this.elements.feedbackContent) {
            const coaching = data.coaching || {};
            this.elements.feedbackContent.innerHTML = `
                <div class="feedback-category">
                    <h5><i class="fas fa-phone me-2"></i>Opening</h5>
                    <p>${coaching.opening || 'Good job on your opening!'}</p>
                </div>
                <div class="feedback-category">
                    <h5><i class="fas fa-bullhorn me-2"></i>Communication</h5>
                    <p>${coaching.communication || 'Your communication was clear and professional.'}</p>
                </div>
                <div class="feedback-category">
                    <h5><i class="fas fa-star me-2"></i>Overall Performance</h5>
                    <p>${coaching.overall || 'Keep practicing to improve your skills!'}</p>
                </div>
            `;
        }
        
        console.log(`📊 Feedback shown - Score: ${score}`);
    }
    
    updateScoreCircleColor(score) {
        if (!this.elements.scoreCircle) return;
        
        this.elements.scoreCircle.classList.remove('excellent', 'good', 'needs-improvement');
        
        if (score >= 85) {
            this.elements.scoreCircle.classList.add('excellent');
        } else if (score >= 70) {
            this.elements.scoreCircle.classList.add('good');
        } else {
            this.elements.scoreCircle.classList.add('needs-improvement');
        }
    }
    
    resetInterface() {
        console.log('🔄 Resetting interface');
        
        // Stop voice recognition
        this.stopAutoListening();
        
        // Reset state
        this.isActive = false;
        this.sessionId = null;
        
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
        
        // Reset UI
        if (this.elements.feedbackSection) {
            this.elements.feedbackSection.style.display = 'none';
        }
        
        if (this.elements.callInterface) {
            this.elements.callInterface.style.display = 'none';
        }
        
        if (this.elements.modeSelection) {
            this.elements.modeSelection.style.display = 'block';
        }
        
        // Clear transcript
        if (this.elements.liveTranscript) {
            this.elements.liveTranscript.innerHTML = 'Waiting for conversation...';
        }
        
        // Reset timer
        if (this.elements.callDuration) {
            this.elements.callDuration.textContent = '00:00';
        }
        
        // Re-enable start button
        if (this.elements.startCallBtn) {
            this.elements.startCallBtn.disabled = false;
            this.elements.startCallBtn.textContent = 'Start Practice Call';
        }
        
        // Reset microphone UI
        this.updateMicrophoneUI(false);
        
        console.log('✅ Interface reset complete');
    }

    destroy() {
        this.stopAutoListening();
        if (this.voiceHandler) {
            this.voiceHandler.destroy();
        }
    }
    
    updateTime() {
        if (this.elements.currentTime) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false 
            });
            this.elements.currentTime.textContent = timeString;
        }
    }
    
    showError(message) {
        console.error('❌ Error:', message);
        
        const errorDiv = document.getElementById('voice-error');
        const errorText = document.getElementById('voice-error-text');
        
        if (errorDiv && errorText) {
            errorText.textContent = message;
            errorDiv.style.display = 'block';
            
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
        
        // Also log to console for debugging
        console.error('Error details:', message);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM loaded, initializing Simple Roleplay Manager...');
    
    try {
        window.roleplayManager = new SimpleRoleplayManager();
        console.log('✅ Simple Roleplay Manager initialized successfully!');
    } catch (error) {
        console.error('❌ Failed to initialize Simple Roleplay Manager:', error);
        
        // Create minimal fallback
        window.roleplayManager = {
            isActive: false,
            showError: function(message) {
                console.error('Fallback error:', message);
                alert('Error: ' + message);
            }
        };
    }
});

console.log('📜 Simple Roleplay Manager script loaded');