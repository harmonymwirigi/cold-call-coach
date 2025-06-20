// ===== NATURAL CONVERSATION ROLEPLAY MANAGER - roleplay.js =====

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
        this.currentAudio = null;  // Track current AI audio
        this.naturalMode = true;   // Enable natural conversation features
        
        // Debug flag
        this.debugMode = true;
        
        this.init();
    }

    init() {
        console.log('🚀 Initializing Natural Conversation Roleplay Manager...');
        
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        
        this.loadRoleplayData();
        this.setupEventListeners();
        this.initializeModeSelection();
        
        // Initialize natural voice handler
        if (typeof VoiceHandler !== 'undefined') {
            this.voiceHandler = new VoiceHandler(this);
            console.log('✅ Natural Voice Handler initialized');
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
                this.showError('Please log in to access Roleplay 1.1 training');
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
            console.log('📡 Loading Roleplay 1.1 info for ID:', roleplayId);
            const response = await this.apiCall(`/api/roleplay/info/${roleplayId}`);
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Roleplay 1.1 info loaded:', data);
                this.updateRoleplayUI(data);
            }
        } catch (error) {
            console.error('❌ Error loading Roleplay 1.1 info:', error);
        }
    }

    updateRoleplayUI(roleplayData) {
        const titleElement = document.getElementById('roleplay-title');
        if (titleElement) {
            titleElement.textContent = 'Natural Roleplay 1.1: ' + (roleplayData.name || 'Phone Training');
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
            avatarElement.alt = `Natural Roleplay 1.1 prospect`;
            
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
        console.log('🔧 Setting up event listeners for natural conversation...');
        
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

        // Microphone button - now shows natural conversation status
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🎤 Mic button clicked (natural mode)');
                
                if (this.voiceHandler) {
                    if (this.voiceHandler.isListening) {
                        this.voiceHandler.stopListening();
                    } else {
                        this.voiceHandler.startListening(false); // Manual start
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

        // Keyboard shortcuts for natural conversation
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

        console.log('✅ Natural conversation event listeners setup complete');
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
        
        // Stop any active audio or voice recognition
        this.stopCurrentAudio();
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
        }
    }

    selectMode(mode) {
        if (!mode || this.isProcessing) return;
        
        console.log('✅ Natural Roleplay 1.1 mode selected:', mode);
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
            startBtn.textContent = `Start Natural Roleplay 1.1 ${this.capitalizeFirst(mode)}`;
        }
    }

    async startCall() {
        if (!this.selectedMode || this.isProcessing) {
            console.log('❌ Cannot start call: missing mode or already processing');
            return;
        }

        const roleplayId = this.getRoleplayId();
        if (!roleplayId) {
            this.showError('Invalid Roleplay 1.1 configuration');
            return;
        }

        console.log('🚀 Starting Natural Roleplay 1.1 call:', { roleplayId, mode: this.selectedMode });

        this.isProcessing = true;
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connecting to Natural Roleplay 1.1...';
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
                console.log('✅ Natural Roleplay 1.1 started successfully:', data);
                
                this.currentSession = data;
                this.isActive = true;
                
                await this.startPhoneCallSequence(data.initial_response);
                
            } else {
                const errorData = await response.json();
                console.error('❌ Failed to start Natural Roleplay 1.1:', errorData);
                this.showError(errorData.error || 'Failed to start Natural Roleplay 1.1 call');
            }
        } catch (error) {
            console.error('❌ Error starting Natural Roleplay 1.1:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.isProcessing = false;
            
            if (!this.isActive && startBtn) {
                startBtn.disabled = false;
                startBtn.textContent = `Start Natural Roleplay 1.1 ${this.capitalizeFirst(this.selectedMode)}`;
            }
        }
    }

    async startPhoneCallSequence(initialResponse) {
        console.log('📞 Starting Natural Roleplay 1.1 call sequence...');
        
        // Hide mode selection, show call interface
        document.getElementById('mode-selection').style.display = 'none';
        document.getElementById('call-interface').style.display = 'flex';

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
        console.log('✅ Connected - Natural Roleplay 1.1 active!');
        this.callState = 'connected';
        this.updateCallStatus('Connected - Natural Conversation Active', 'connected');
        
        // Update UI
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.remove('calling');
            avatar.classList.add('roleplay-11-active');
        }
        
        // Start call timer
        this.callStartTime = Date.now();
        this.startCallTimer();
        
        // Show live transcript
        const transcript = document.getElementById('live-transcript');
        if (transcript) {
            transcript.classList.add('show');
            transcript.classList.add('roleplay-11-active');
        }
        
        // Enable natural conversation features
        this.enableNaturalConversation();
        
        // Clear conversation history
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
        
        // Update UI to show natural mode
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.disabled = false;
            micBtn.title = 'Natural conversation active - speak anytime or use Space bar';
            micBtn.classList.add('natural-mode');
        }
        
        // Show natural conversation instructions
        this.updateTranscript('🤖 Natural conversation ready - speak when you want!');
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

        console.log('💬 Processing natural conversation input:', transcript);
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
                
                // Check if call should end
                if (!data.call_continues) {
                    console.log('📞 Call ending...');
                    setTimeout(() => {
                        this.endCall(data.session_success);
                    }, 2000);
                    return;
                }
                
                // Play AI response and automatically start next user turn
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
            console.log('🎭 Playing AI response (interruptible):', text.substring(0, 50) + '...');
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
                        console.log('🔊 Playing interruptible AI audio');
                        const audioUrl = URL.createObjectURL(audioBlob);
                        this.currentAudio = new Audio(audioUrl);
                        
                        // Setup audio event handlers
                        this.currentAudio.onended = () => {
                            console.log('✅ AI audio finished - starting user turn');
                            URL.revokeObjectURL(audioUrl);
                            this.currentAudio = null;
                            
                            // Only start user turn if AI is still speaking (not interrupted)
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
                        
                        // Play the audio
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
        const maxTime = 5000;
        
        const delay = Math.max(minTime, Math.min(maxTime, speakingTimeMs));
        console.log(`⏱️ Simulating speaking time: ${delay}ms for ${words} words`);
        
        return new Promise(resolve => setTimeout(resolve, delay));
    }

    addToConversationHistory(sender, message) {
        this.conversationHistory.push({
            sender: sender,
            message: message,
            timestamp: new Date(),
            roleplay_version: '1.1',
            natural_conversation: true
        });
        
        console.log(`📝 Added to conversation: ${sender} - ${message.substring(0, 50)}...`);
    }

    updateTranscript(text) {
        const transcriptElement = document.getElementById('live-transcript');
        if (transcriptElement) {
            transcriptElement.textContent = text;
        }
    }

    async endCall(success = false) {
        if (!this.isActive) {
            console.log('📞 Call already ended');
            return;
        }

        console.log('📞 Ending Natural Roleplay 1.1 call, success:', success);

        this.callState = 'ended';
        this.updateCallStatus('Natural Roleplay 1.1 Call ended', 'ended');
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
            transcript.classList.remove('roleplay-11-active');
        }

        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.remove('roleplay-11-active');
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
                    this.showFeedback(data.coaching, data.overall_score);
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
        console.log('📊 Showing Natural Roleplay 1.1 feedback');
        
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'flex';
        
        const feedbackHeader = document.querySelector('.feedback-header h4');
        if (feedbackHeader) {
            feedbackHeader.textContent = 'Natural Roleplay 1.1 Complete!';
        }
        
        if (coaching) {
            this.populateRoleplay11Feedback(coaching);
        }
        
        this.animateScore(score);
        this.updateScoreCircleColor(score);
    }

    populateRoleplay11Feedback(coaching) {
        const content = document.getElementById('feedback-content');
        if (!content) return;
        
        content.innerHTML = '';

        if (coaching) {
            const feedbackItems = [
                { key: 'sales_coaching', icon: 'chart-line', title: 'Sales Performance (Natural Conversation)' },
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
                    <h6><i class="fas fa-info-circle me-2"></i>Natural Roleplay 1.1 Complete</h6>
                    <p style="margin: 0; font-size: 14px;">Your natural conversation call is complete. Great job!</p>
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
        console.log('🔄 Trying again with Natural Roleplay 1.1');
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
            startBtn.textContent = 'Select a mode for Natural Roleplay 1.1';
        }
    }

    showError(message) {
        console.error('❌ Error:', message);
        this.updateTranscript(`❌ Error: ${message}`);
        
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        alertDiv.innerHTML = `<strong>Natural Roleplay 1.1 Error:</strong> ${message}`;
        
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
        console.log('🧹 Destroying Natural Roleplay Manager');
        
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
        console.log('🚀 Initializing Natural Conversation Roleplay Manager');
        window.roleplayManager = new PhoneRoleplayManager();
    }
});

// Export for global access
window.PhoneRoleplayManager = PhoneRoleplayManager;

console.log('✅ Natural Conversation Roleplay Manager loaded successfully');