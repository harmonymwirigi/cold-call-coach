// ===== MARATHON MODE ROLEPLAY MANAGER - roleplay.js =====

class PhoneRoleplayManager {
    constructor() {
        this.selectedMode = null;
        this.callState = 'idle'; // idle, dialing, ringing, connected, ended
        this.callStartTime = null;
        this.durationInterval = null;
        this.isRecording = false;
        this.isMuted = false;
        this.speakerOn = false;
        this.currentSession = null;
        this.isActive = false;
        this.voiceHandler = null;
        this.aiIsSpeaking = false;
        this.isProcessing = false;
        this.conversationHistory = [];
        
        // Natural conversation state
        this.currentAudio = null;
        this.naturalMode = true;
        
        // Marathon Mode state
        this.marathonState = {
            currentCall: 1,
            maxCalls: 1,
            callsPassed: 0,
            callsFailed: 0,
            passThreshold: 1,
            isMarathonMode: false,
            isLegendMode: false,
            betweenCalls: false,
            runComplete: false,
            runSuccess: false,
            finalStats: null
        };
        
        // Debug flag
        this.debugMode = true;
        
        this.init();
    }

    init() {
        console.log('🚀 Initializing Marathon Mode Roleplay Manager...');
        
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        
        this.loadRoleplayData();
        this.setupEventListeners();
        this.initializeModeSelection();
        
        // Initialize natural voice handler
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

    loadRoleplayData() {
        const roleplayData = document.getElementById('roleplay-data');
        if (roleplayData) {
            const roleplayId = parseInt(roleplayData.dataset.roleplayId);
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
            }
        } catch (error) {
            console.error('❌ Error loading roleplay info:', error);
        }
    }

    updateRoleplayUI(roleplayData) {
        const titleElement = document.getElementById('roleplay-title');
        if (titleElement) {
            const baseTitle = roleplayData.name || 'Phone Training';
            titleElement.textContent = baseTitle;
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

        // End call button
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
            // Space bar to interrupt or start speaking
            if (e.code === 'Space' && this.callState === 'connected' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                
                if (this.aiIsSpeaking) {
                    console.log('⚡ Space pressed - interrupting AI');
                    this.handleUserInterruption();
                } else if (this.voiceHandler && !this.voiceHandler.isListening) {
                    console.log('🎤 Space pressed - manual start listening');
                    this.voiceHandler.startListening(false);
                }
            }
            
            // Escape to end call
            if (e.code === 'Escape' && this.callState === 'connected') {
                e.preventDefault();
                console.log('⌨️ Escape key pressed - end call');
                this.endCall();
            }
        });

        console.log('✅ Event listeners setup complete');
    }

    initializeModeSelection() {
        console.log('🎯 Initializing mode selection...');
        
        document.getElementById('mode-selection').style.display = 'flex';
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'none';
        
        this.callState = 'idle';
        this.isActive = false;
        this.aiIsSpeaking = false;
        this.isProcessing = false;
        this.conversationHistory = [];
        
        // Reset Marathon state
        this.marathonState = {
            currentCall: 1,
            maxCalls: 1,
            callsPassed: 0,
            callsFailed: 0,
            passThreshold: 1,
            isMarathonMode: false,
            isLegendMode: false,
            betweenCalls: false,
            runComplete: false,
            runSuccess: false,
            finalStats: null
        };
        
        // Stop any active audio or voice recognition
        this.stopCurrentAudio();
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
        }
    }

    selectMode(mode) {
        if (!mode || this.isProcessing) return;
        
        console.log('✅ Mode selected:', mode);
        this.selectedMode = mode;
        
        // Set Marathon/Legend flags
        this.marathonState.isMarathonMode = (mode === 'marathon');
        this.marathonState.isLegendMode = (mode === 'legend');
        
        // Update mode-specific settings
        if (mode === 'marathon') {
            this.marathonState.maxCalls = 10;
            this.marathonState.passThreshold = 6;
        } else if (mode === 'legend') {
            this.marathonState.maxCalls = 6;
            this.marathonState.passThreshold = 6;
        } else {
            this.marathonState.maxCalls = 1;
            this.marathonState.passThreshold = 1;
        }
        
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
            
            let buttonText = `Start ${this.capitalizeFirst(mode)}`;
            if (mode === 'marathon') {
                buttonText += ' (10 calls, need 6 to pass)';
            } else if (mode === 'legend') {
                buttonText += ' (6 perfect calls)';
            }
            
            startBtn.textContent = buttonText;
        }
    }

    async startCall() {
        if (!this.selectedMode || this.isProcessing) {
            console.log('❌ Cannot start call: missing mode or already processing');
            return;
        }

        const roleplayId = this.getRoleplayId();
        if (!roleplayId) {
            this.showError('Invalid roleplay configuration');
            return;
        }

        console.log('🚀 Starting call:', { roleplayId, mode: this.selectedMode });

        this.isProcessing = true;
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Starting session...';
        }

        try {
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST',
                body: JSON.stringify({
                    roleplay_id: roleplayId,
                    mode: this.selectedMode
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Session started successfully:', data);
                
                this.currentSession = data;
                this.isActive = true;
                
                // Update Marathon state from response
                if (data.call_info) {
                    this.marathonState.currentCall = data.call_info.current_call || 1;
                    this.marathonState.maxCalls = data.call_info.max_calls || 1;
                    this.marathonState.passThreshold = data.call_info.pass_threshold || 1;
                }
                
                await this.startPhoneCallSequence(data.initial_response);
                
            } else {
                const errorData = await response.json();
                console.error('❌ Failed to start session:', errorData);
                this.showError(errorData.error || 'Failed to start call');
            }
        } catch (error) {
            console.error('❌ Error starting call:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.isProcessing = false;
            
            if (!this.isActive && startBtn) {
                startBtn.disabled = false;
                startBtn.textContent = `Start ${this.capitalizeFirst(this.selectedMode)}`;
            }
        }
    }

    async startPhoneCallSequence(initialResponse) {
        console.log('📞 Starting phone call sequence...');
        
        // Hide mode selection, show call interface
        document.getElementById('mode-selection').style.display = 'none';
        document.getElementById('call-interface').style.display = 'flex';

        // Update UI for Marathon mode
        this.updateMarathonUI();

        await this.dialingState();
        await this.ringingState();
        await this.connectedState(initialResponse);
    }

    updateMarathonUI() {
        // Update call counter for Marathon/Legend modes
        if (this.marathonState.isMarathonMode || this.marathonState.isLegendMode) {
            const statusText = document.getElementById('call-status-text');
            if (statusText) {
                const mode = this.marathonState.isLegendMode ? 'Legend' : 'Marathon';
                statusText.textContent = `${mode} Mode - Call ${this.marathonState.currentCall}/${this.marathonState.maxCalls}`;
            }
            
            // Add progress indicators
            this.updateCallProgress();
        }
    }

    updateCallProgress() {
        // Create or update progress display
        let progressElement = document.getElementById('marathon-progress');
        if (!progressElement) {
            progressElement = document.createElement('div');
            progressElement.id = 'marathon-progress';
            progressElement.className = 'marathon-progress';
            
            const callInterface = document.getElementById('call-interface');
            if (callInterface) {
                callInterface.insertBefore(progressElement, callInterface.firstChild);
            }
        }
        
        const mode = this.marathonState.isLegendMode ? 'Legend' : 'Marathon';
        progressElement.innerHTML = `
            <div class="progress-header">
                <span class="mode-badge">${mode}</span>
                <span class="call-counter">Call ${this.marathonState.currentCall}/${this.marathonState.maxCalls}</span>
            </div>
            <div class="progress-stats">
                <span class="stat passed">✓ ${this.marathonState.callsPassed}</span>
                <span class="stat failed">✗ ${this.marathonState.callsFailed}</span>
                <span class="stat target">Target: ${this.marathonState.passThreshold}/${this.marathonState.maxCalls}</span>
            </div>
        `;
    }

    async dialingState() {
        console.log('📱 Dialing state...');
        this.callState = 'dialing';
        this.updateCallStatus('Calling...', 'dialing');
        
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.add('calling');
        }
        
        await this.delay(1500); // Shorter for Marathon mode
    }

    async ringingState() {
        console.log('📳 Ringing state...');
        this.callState = 'ringing';
        this.updateCallStatus('Ringing...', 'ringing');
        
        await this.delay(2000); // Shorter for Marathon mode
    }

    async connectedState(initialResponse) {
        console.log('✅ Connected!');
        this.callState = 'connected';
        
        const mode = this.marathonState.isMarathonMode ? 'Marathon' : 
                    this.marathonState.isLegendMode ? 'Legend' : 'Practice';
        this.updateCallStatus(`${mode} Mode - Connected`, 'connected');
        
        // Update UI
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.remove('calling');
            avatar.classList.add('connected');
        }
        
        // Start call timer
        this.callStartTime = Date.now();
        this.startCallTimer();
        
        // Show live transcript
        const transcript = document.getElementById('live-transcript');
        if (transcript) {
            transcript.classList.add('show');
        }
        
        // Enable natural conversation features
        this.enableNaturalConversation();
        
        // Clear conversation history for this call
        this.conversationHistory = [];
        
        // Play initial AI response
        if (initialResponse) {
            console.log('🎯 Playing initial AI response:', initialResponse);
            await this.playAIResponseAndWaitForUser(initialResponse);
        } else {
            console.log('🎤 No initial response, starting auto-listening');
            this.startUserTurn();
        }
    }

    enableNaturalConversation() {
        console.log('🤖 Enabling natural conversation features...');
        
        // Enable interruption capability
        if (this.voiceHandler) {
            this.voiceHandler.enableInterruption();
        }
        
        // Update UI to show mode-specific features
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.disabled = false;
            micBtn.classList.add('natural-mode');
            
            if (this.selectedMode === 'practice') {
                micBtn.title = 'Practice Mode - Real-time coaching available';
                micBtn.classList.add('practice-mode');
            } else if (this.marathonState.isMarathonMode || this.marathonState.isLegendMode) {
                micBtn.title = 'Marathon/Legend Mode - No feedback until end of run';
                micBtn.classList.add(this.marathonState.isLegendMode ? 'legend-mode' : 'marathon-mode');
            }
        }
        
        // Update transcript for mode-specific styling
        const transcript = document.getElementById('live-transcript');
        if (transcript) {
            if (this.selectedMode === 'practice') {
                transcript.classList.add('practice-mode');
            } else if (this.marathonState.isMarathonMode) {
                transcript.classList.add('marathon-active');
            } else if (this.marathonState.isLegendMode) {
                transcript.classList.add('legend-active');
            }
        }
        
        // Update call interface styling
        const callInterface = document.getElementById('call-interface');
        if (callInterface) {
            if (this.selectedMode === 'practice') {
                callInterface.classList.add('practice-mode');
            } else if (this.marathonState.isMarathonMode) {
                callInterface.classList.add('marathon-mode');
            } else if (this.marathonState.isLegendMode) {
                callInterface.classList.add('legend-mode');
            }
        }
        
        // Show mode-specific instructions
        const modeText = this.selectedMode === 'practice' ? 'Practice (Real-time coaching)' : 
                        this.marathonState.isMarathonMode ? 'Marathon' : 
                        this.marathonState.isLegendMode ? 'Legend' : 'Training';
        this.updateTranscript(`🤖 ${modeText} mode ready - speak when you want!`);
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

    // ===== NATURAL CONVERSATION METHODS =====

    startUserTurn() {
        console.log('👤 Starting user turn - auto-listening activated');
        
        this.aiIsSpeaking = false;
        
        // Start auto-listening for natural conversation
        if (this.voiceHandler) {
            this.voiceHandler.startAutoListening();
        }
        
        // Update UI
        this.updateTranscript('🎤 Your turn - speak naturally...');
        this.addPulseTomicButton();
    }

    handleUserInterruption() {
        console.log('⚡ User interrupted AI - switching to user turn');
        
        // Stop AI audio immediately
        this.stopCurrentAudio();
        
        // Mark AI as no longer speaking
        this.aiIsSpeaking = false;
        
        // If voice handler not already listening, start it
        if (this.voiceHandler && !this.voiceHandler.isListening) {
            this.voiceHandler.startAutoListening();
        }
        
        // Update UI
        this.updateTranscript('⚡ You interrupted - keep speaking...');
    }

    stopCurrentAudio() {
        if (this.currentAudio) {
            console.log('🔇 Stopping current AI audio');
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
    }

    addPulseTomicButton() {
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.classList.add('pulse-animation');
            setTimeout(() => {
                micBtn.classList.remove('pulse-animation');
            }, 3000);
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || !this.currentSession || this.isProcessing) {
            console.log('❌ Cannot process user input - invalid state');
            return;
        }

        // Handle silence triggers
        if (transcript === '[SILENCE_IMPATIENCE]' || transcript === '[SILENCE_HANGUP]') {
            console.log('⏰ Handling silence trigger:', transcript);
            await this.handleSilenceTrigger(transcript);
            return;
        }

        console.log('💬 Processing user input:', transcript);
        this.isProcessing = true;

        this.addToConversationHistory('user', transcript);
        this.updateTranscript('🤖 Processing your response...');

        try {
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST',
                body: JSON.stringify({
                    user_input: transcript
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ AI response received:', data);
                
                // Handle real-time coaching for Practice mode
                if (data.live_coaching && this.selectedMode === 'practice') {
                    this.displayLiveCoaching(data.live_coaching);
                }
                
                // Update Marathon state if provided
                if (data.call_info) {
                    this.marathonState.currentCall = data.call_info.current_call || this.marathonState.currentCall;
                    this.marathonState.callsPassed = data.call_info.calls_passed || this.marathonState.callsPassed;
                    this.marathonState.callsFailed = data.call_info.calls_failed || this.marathonState.callsFailed;
                    this.updateCallProgress();
                }
                
                // Handle next call in Marathon/Legend mode
                if (data.next_call) {
                    console.log('🔄 Starting next call in sequence...');
                    await this.handleNextCall(data);
                    return;
                }
                
                // Handle run completion (Marathon/Legend)
                if (data.run_complete) {
                    console.log('🏁 Run completed!');
                    await this.handleRunCompletion(data);
                    return;
                }
                
                // Handle single call end (Practice mode)
                if (!data.call_continues) {
                    console.log('📞 Call ending...');
                    setTimeout(() => {
                        this.endCall(data.session_success);
                    }, 2000);
                    return;
                }
                
                // Continue current call
                await this.playAIResponseAndWaitForUser(data.ai_response);
                
            } else {
                const errorData = await response.json();
                console.error('❌ API error:', errorData);
                this.showError(errorData.error || 'Failed to process input');
                this.startUserTurn(); // Resume user turn on error
            }
        } catch (error) {
            console.error('❌ Error processing user input:', error);
            this.showError('Network error during call');
            this.startUserTurn(); // Resume user turn on error
        } finally {
            this.isProcessing = false;
        }
    }

    async handleNextCall(data) {
        console.log('🔄 Handling next call in Marathon/Legend sequence');
        
        // Show transition message
        const lastCallResponse = data.call_info?.last_call_response || 'Call completed.';
        this.updateTranscript(`📞 ${lastCallResponse}`);
        
        // Update call counter
        this.marathonState.currentCall = data.call_info.current_call;
        this.updateCallProgress();
        
        // Brief pause between calls
        await this.delay(2000);
        
        // Start next call sequence
        this.updateTranscript('📞 Dialing next prospect...');
        await this.delay(1000);
        
        // Generate new prospect info for variety
        this.updateProspectInfo({ job_title: 'CTO', industry: 'Technology' });
        
        // Play new pickup response
        await this.playAIResponseAndWaitForUser(data.ai_response);
    }

    async handleRunCompletion(data) {
        console.log('🏁 Handling run completion');
        
        this.marathonState.runComplete = true;
        this.marathonState.runSuccess = data.run_success;
        this.marathonState.finalStats = data.final_stats;
        
        // Show final message
        let finalMessage = data.ai_response || 'Run completed!';
        if (data.sudden_death) {
            finalMessage = 'Legend attempt failed - one mistake and you\'re out!';
        } else if (data.perfect_run) {
            finalMessage = 'Perfect Legend run - six for six! Legendary performance!';
        }
        
        this.updateTranscript(`🏁 ${finalMessage}`);
        
        // Wait a moment then show final results
        setTimeout(() => {
            this.showMarathonResults(data);
        }, 3000);
    }

    async handleSilenceTrigger(trigger) {
        console.log('⏰ Handling silence trigger:', trigger);
        
        if (trigger === '[SILENCE_IMPATIENCE]') {
            this.updateTranscript('⏰ 10 seconds of silence... The prospect is getting impatient...');
        } else if (trigger === '[SILENCE_HANGUP]') {
            this.updateTranscript('📞 The prospect hung up due to 15 seconds of silence.');
            setTimeout(() => {
                this.endCall(false);
            }, 2000);
            return;
        }

        // Process through API
        await this.processUserInput(trigger);
    }

    async playAIResponseAndWaitForUser(text) {
        try {
            console.log('🎭 Playing AI response:', text.substring(0, 50) + '...');
            this.aiIsSpeaking = true;
            
            this.addToConversationHistory('ai', text);
            this.updateTranscript(`🤖 Prospect: "${text}"`);

            // Try to play TTS audio (interruptible)
            try {
                const response = await this.apiCall('/api/roleplay/tts', {
                    method: 'POST',
                    body: JSON.stringify({ text: text })
                });

                if (response.ok) {
                    const audioBlob = await response.blob();
                    
                    if (audioBlob.size > 100) {
                        console.log('🔊 Playing AI audio');
                        const audioUrl = URL.createObjectURL(audioBlob);
                        this.currentAudio = new Audio(audioUrl);
                        
                        this.currentAudio.onended = () => {
                            console.log('✅ AI audio finished - starting user turn');
                            URL.revokeObjectURL(audioUrl);
                            this.currentAudio = null;
                            
                            if (this.aiIsSpeaking) {
                                this.startUserTurn();
                            }
                        };
                        
                        this.currentAudio.onerror = () => {
                            console.log('❌ AI audio error - starting user turn');
                            URL.revokeObjectURL(audioUrl);
                            this.currentAudio = null;
                            
                            if (this.aiIsSpeaking) {
                                this.startUserTurn();
                            }
                        };
                        
                        await this.currentAudio.play();
                        
                    } else {
                        console.log('📢 Audio too small, simulating speech time');
                        await this.simulateSpeakingTime(text);
                        this.startUserTurn();
                    }
                } else {
                    console.log('🎵 TTS failed, simulating speech time');
                    await this.simulateSpeakingTime(text);
                    this.startUserTurn();
                }
            } catch (ttsError) {
                console.log('🔊 TTS error:', ttsError);
                await this.simulateSpeakingTime(text);
                this.startUserTurn();
            }
            
        } catch (error) {
            console.error('❌ Error playing AI response:', error);
            this.aiIsSpeaking = false;
            await this.simulateSpeakingTime(text);
            this.startUserTurn();
        }
    }

    async simulateSpeakingTime(text) {
        const wordsPerMinute = 150;
        const words = text.split(' ').length;
        const speakingTimeMs = (words / wordsPerMinute) * 60 * 1000;
        const minTime = 1000;
        const maxTime = 4000;
        
        const delay = Math.max(minTime, Math.min(maxTime, speakingTimeMs));
        console.log(`⏱️ Simulating speaking time: ${delay}ms for ${words} words`);
        
        return new Promise(resolve => setTimeout(resolve, delay));
    }

    displayLiveCoaching(coaching) {
        console.log('📚 Displaying live coaching for Practice mode:', coaching);
        
        // Create or update live coaching display
        let coachingDisplay = document.getElementById('live-coaching-display');
        if (!coachingDisplay) {
            coachingDisplay = document.createElement('div');
            coachingDisplay.id = 'live-coaching-display';
            coachingDisplay.className = 'live-coaching-display';
            
            // Insert after the live transcript
            const transcript = document.getElementById('live-transcript');
            if (transcript && transcript.parentNode) {
                transcript.parentNode.insertBefore(coachingDisplay, transcript.nextSibling);
            }
        }
        
        // Determine coaching style based on feedback
        const isPositive = coaching.feedback.toLowerCase().includes('great') || 
                          coaching.feedback.toLowerCase().includes('excellent') || 
                          coaching.feedback.toLowerCase().includes('perfect');
        
        const coachingClass = isPositive ? 'positive' : 'improvement';
        const icon = isPositive ? '✅' : '💡';
        
        coachingDisplay.innerHTML = `
            <div class="coaching-content ${coachingClass}">
                <div class="coaching-header">
                    <span class="coaching-icon">${icon}</span>
                    <span class="coaching-stage">${coaching.stage.toUpperCase()} FEEDBACK</span>
                </div>
                <div class="coaching-feedback">${coaching.feedback}</div>
                ${coaching.tip ? `<div class="coaching-tip">💡 ${coaching.tip}</div>` : ''}
            </div>
        `;
        
        // Show the coaching display
        coachingDisplay.style.display = 'block';
        coachingDisplay.classList.add('show');
        
        // Auto-hide after 8 seconds unless it's improvement feedback
        if (isPositive) {
            setTimeout(() => {
                if (coachingDisplay) {
                    coachingDisplay.classList.remove('show');
                    setTimeout(() => {
                        if (coachingDisplay && coachingDisplay.parentNode) {
                            coachingDisplay.style.display = 'none';
                        }
                    }, 300);
                }
            }, 5000);
        }
        // Keep improvement feedback visible longer
    }

    addToConversationHistory(sender, message) {
        this.conversationHistory.push({
            sender: sender,
            message: message,
            timestamp: new Date(),
            mode: this.selectedMode,
            call_number: this.marathonState.currentCall
        });
        
        console.log(`📝 Added to conversation: ${sender} - ${message.substring(0, 50)}...`);
    }

    updateTranscript(text) {
        const transcriptElement = document.getElementById('live-transcript');
        if (transcriptElement) {
            transcriptElement.textContent = text;
        }
    }

    showMarathonResults(data) {
        console.log('📊 Showing Marathon/Legend results');
        
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'flex';
        
        const feedbackHeader = document.querySelector('.feedback-header h4');
        if (feedbackHeader) {
            const mode = this.marathonState.isLegendMode ? 'Legend' : 'Marathon';
            const success = data.run_success ? 'Complete!' : 'Complete';
            feedbackHeader.textContent = `${mode} Mode ${success}`;
        }
        
        // Populate Marathon-specific feedback
        this.populateMarathonFeedback(data);
        
        this.animateScore(data.overall_score || 50);
        this.updateScoreCircleColor(data.overall_score || 50);
    }

    populateMarathonFeedback(data) {
        const content = document.getElementById('feedback-content');
        if (!content) return;
        
        const stats = data.final_stats || this.marathonState.finalStats;
        const coaching = data.coaching || {};
        const mode = this.marathonState.isLegendMode ? 'Legend' : 'Marathon';
        const success = data.run_success;
        
        content.innerHTML = '';

        // Show run results
        const resultClass = success ? 'success' : 'needs-improvement';
        content.innerHTML += `
            <div class="feedback-item marathon-results ${resultClass}">
                <h6><i class="fas fa-chart-bar me-2"></i>${mode} Results</h6>
                <div class="marathon-stats">
                    <div class="stat-row">
                        <span>Calls Passed:</span>
                        <span class="stat-value">${stats?.calls_passed || 0}/${stats?.total_calls || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span>Pass Rate:</span>
                        <span class="stat-value">${Math.round(stats?.pass_rate || 0)}%</span>
                    </div>
                    <div class="stat-row ${success ? 'success' : 'failed'}">
                        <span>Result:</span>
                        <span class="stat-value">${success ? 'PASSED' : 'FAILED'}</span>
                    </div>
                </div>
                ${this.getMarathonMessage(mode, success, stats)}
            </div>
        `;

        // Show coaching if available (only 2 items per category as per spec)
        if (coaching && Object.keys(coaching).length > 0) {
            const feedbackItems = [
                { key: 'sales_coaching', icon: 'chart-line', title: 'Sales Performance' },
                { key: 'grammar_coaching', icon: 'spell-check', title: 'Grammar (CEFR A2)' },
                { key: 'vocabulary_coaching', icon: 'book', title: 'Vocabulary' },
                { key: 'pronunciation_coaching', icon: 'volume-up', title: 'Pronunciation' },
                { key: 'rapport_assertiveness', icon: 'handshake', title: 'Rapport & Confidence' }
            ];

            feedbackItems.forEach(item => {
                if (coaching[item.key]) {
                    content.innerHTML += `
                        <div class="feedback-item">
                            <h6><i class="fas fa-${item.icon} me-2"></i>${item.title}</h6>
                            <p style="margin: 0; font-size: 14px;">${coaching[item.key]}</p>
                        </div>
                    `;
                }
            });
        }
    }

    getMarathonMessage(mode, success, stats) {
        if (mode === 'Legend') {
            if (success) {
                return '<p class="result-message success">🏆 Legendary! Six perfect calls - very few reps pull this off!</p>';
            } else {
                return '<p class="result-message failed">💪 Legend attempt failed this time. Pass Marathon again to earn another shot!</p>';
            }
        } else {
            if (success) {
                return '<p class="result-message success">🎯 Marathon passed! You\'ve unlocked Legend Mode and modules 2.1 & 2.2 for 24 hours.</p>';
            } else {
                return '<p class="result-message">📈 Keep practicing! The more reps you get, the easier it becomes.</p>';
            }
        }
    }

    async endCall(success = false) {
        if (!this.isActive) {
            console.log('📞 Call already ended');
            return;
        }

        console.log('📞 Ending call, success:', success);

        this.callState = 'ended';
        this.updateCallStatus('Call ended', 'ended');
        this.isActive = false;
        this.aiIsSpeaking = false;
        
        // Stop all audio and voice recognition
        this.stopCurrentAudio();
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
            this.voiceHandler.disableInterruption();
        }
        
        // Clear timers
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
            this.durationInterval = null;
        }
        
        // Hide transcript
        const transcript = document.getElementById('live-transcript');
        if (transcript) {
            transcript.classList.remove('show');
        }

        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.remove('connected');
        }

        try {
            const response = await this.apiCall('/api/roleplay/end', {
                method: 'POST',
                body: JSON.stringify({ 
                    success: success,
                    forced_end: false 
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Call ended successfully:', data);
                
                setTimeout(() => {
                    if (data.mode === 'practice') {
                        this.showFeedback(data.coaching, data.overall_score);
                    } else {
                        this.showMarathonResults(data);
                    }
                }, 2000);
            } else {
                console.error('❌ Failed to end call properly');
                setTimeout(() => {
                    this.showFeedback(null, 50);
                }, 2000);
            }
        } catch (error) {
            console.error('❌ Error ending call:', error);
            setTimeout(() => {
                this.showFeedback(null, 50);
            }, 2000);
        }
    }

    showFeedback(coaching, score = 75) {
        console.log('📊 Showing Practice mode feedback');
        
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'flex';
        
        // Add Practice mode styling
        const feedbackSection = document.getElementById('feedback-section');
        if (feedbackSection) {
            feedbackSection.classList.add('practice-mode');
        }
        
        const feedbackHeader = document.querySelector('.feedback-header h4');
        if (feedbackHeader) {
            feedbackHeader.textContent = 'Practice Mode Complete!';
        }
        
        // Update feedback badge
        const feedbackBadge = document.getElementById('feedback-mode-badge');
        if (feedbackBadge) {
            feedbackBadge.className = 'practice-badge';
            feedbackBadge.textContent = 'Practice v1.1';
        }
        
        if (coaching) {
            this.populatePracticeFeedback(coaching);
        }
        
        this.animateScore(score);
        this.updateScoreCircleColor(score);
    }

    populatePracticeFeedback(coaching) {
        const content = document.getElementById('feedback-content');
        if (!content) return;
        
        content.innerHTML = '';

        if (coaching) {
            const feedbackItems = [
                { key: 'sales_coaching', icon: 'chart-line', title: 'Sales Performance' },
                { key: 'grammar_coaching', icon: 'spell-check', title: 'Grammar & Structure' },
                { key: 'vocabulary_coaching', icon: 'book', title: 'Vocabulary' },
                { key: 'pronunciation_coaching', icon: 'volume-up', title: 'Pronunciation' },
                { key: 'rapport_assertiveness', icon: 'handshake', title: 'Rapport & Confidence' }
            ];

            feedbackItems.forEach(item => {
                if (coaching[item.key]) {
                    content.innerHTML += `
                        <div class="feedback-item">
                            <h6><i class="fas fa-${item.icon} me-2"></i>${item.title}</h6>
                            <p style="margin: 0; font-size: 14px;">${coaching[item.key]}</p>
                        </div>
                    `;
                }
            });
        } else {
            content.innerHTML = `
                <div class="feedback-item">
                    <h6><i class="fas fa-info-circle me-2"></i>Practice Complete</h6>
                    <p style="margin: 0; font-size: 14px;">Your practice call is complete. Great job!</p>
                </div>
            `;
        }
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

    tryAgain() {
        console.log('🔄 Trying again');
        this.showModeSelection();
        
        if (this.selectedMode) {
            setTimeout(() => {
                this.selectMode(this.selectedMode);
            }, 100);
        }
    }

    showModeSelection() {
        console.log('🎯 Showing mode selection');
        
        document.getElementById('feedback-section').style.display = 'none';
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

    getRoleplayId() {
        const roleplayData = document.getElementById('roleplay-data');
        return roleplayData ? parseInt(roleplayData.dataset.roleplayId) : 1;
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            }
        };

        console.log('🌐 API call:', endpoint, options.method || 'GET');

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            console.error('🔐 Authentication required');
            window.location.href = '/login';
            throw new Error('Authentication required');
        }

        return response;
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    destroy() {
        console.log('🧹 Destroying Roleplay Manager');
        
        this.stopCurrentAudio();
        
        if (this.voiceHandler) {
            this.voiceHandler.destroy();
        }
        
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
        }
        
        this.isActive = false;
        this.currentSession = null;
        this.isProcessing = false;
        this.aiIsSpeaking = false;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/roleplay/')) {
        console.log('🚀 Initializing Marathon Mode Roleplay Manager');
        window.roleplayManager = new PhoneRoleplayManager();
    }
});

// Export for global access
window.PhoneRoleplayManager = PhoneRoleplayManager;

console.log('✅ Marathon Mode Roleplay Manager loaded successfully');