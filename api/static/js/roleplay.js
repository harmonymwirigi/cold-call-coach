// ===== FIXED STATIC/JS/ROLEPLAY.JS - FRONTEND WORKING VERSION =====

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
        
        // Debug flag
        this.debugMode = true;
        
        this.init();
    }

    init() {
        console.log('🚀 Initializing Roleplay 1.1 Phone Manager...');
        
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        
        this.loadRoleplayData();
        this.setupEventListeners();
        this.initializeModeSelection();
        
        // Initialize voice handler
        if (typeof VoiceHandler !== 'undefined') {
            this.voiceHandler = new VoiceHandler(this);
            console.log('✅ Voice handler initialized for Roleplay 1.1');
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
            titleElement.textContent = 'Roleplay 1.1: ' + (roleplayData.name || 'Phone Training');
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
            avatarElement.alt = `Roleplay 1.1 prospect`;
            
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

        // Call controls
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            // Hold to talk functionality
            micBtn.addEventListener('mousedown', (e) => {
                e.preventDefault();
                console.log('🎤 Mic button pressed');
                this.startRecording();
            });

            micBtn.addEventListener('mouseup', (e) => {
                e.preventDefault();
                console.log('🎤 Mic button released');
                this.stopRecording();
            });

            micBtn.addEventListener('mouseleave', (e) => {
                console.log('🎤 Mic button left');
                this.stopRecording();
            });

            // Touch events for mobile
            micBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                console.log('📱 Mic touch start');
                this.startRecording();
            });

            micBtn.addEventListener('touchend', (e) => {
                e.preventDefault();
                console.log('📱 Mic touch end');
                this.stopRecording();
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
            if (e.code === 'Space' && this.callState === 'connected' && !this.isRecording) {
                e.preventDefault();
                console.log('⌨️ Space key pressed - start recording');
                this.startRecording();
            }
            
            if (e.code === 'Escape' && this.callState === 'connected') {
                e.preventDefault();
                console.log('⌨️ Escape key pressed - end call');
                this.endCall();
            }
        });

        document.addEventListener('keyup', (e) => {
            if (e.code === 'Space' && this.isRecording) {
                e.preventDefault();
                console.log('⌨️ Space key released - stop recording');
                this.stopRecording();
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
    }

    selectMode(mode) {
        if (!mode || this.isProcessing) return;
        
        console.log('✅ Roleplay 1.1 mode selected:', mode);
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
            startBtn.textContent = `Start Roleplay 1.1 ${this.capitalizeFirst(mode)} Call`;
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

        console.log('🚀 Starting Roleplay 1.1 phone call:', { roleplayId, mode: this.selectedMode });

        this.isProcessing = true;
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connecting to Roleplay 1.1...';
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
                console.log('✅ Roleplay 1.1 started successfully:', data);
                
                this.currentSession = data;
                this.isActive = true;
                
                await this.startPhoneCallSequence(data.initial_response);
                
            } else {
                const errorData = await response.json();
                console.error('❌ Failed to start Roleplay 1.1:', errorData);
                this.showError(errorData.error || 'Failed to start Roleplay 1.1 call');
            }
        } catch (error) {
            console.error('❌ Error starting Roleplay 1.1:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.isProcessing = false;
            
            if (!this.isActive && startBtn) {
                startBtn.disabled = false;
                startBtn.textContent = `Start Roleplay 1.1 ${this.capitalizeFirst(this.selectedMode)} Call`;
            }
        }
    }

    async startPhoneCallSequence(initialResponse) {
        console.log('📞 Starting Roleplay 1.1 phone call sequence...');
        
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
        console.log('✅ Connected state - Roleplay 1.1 active!');
        this.callState = 'connected';
        this.updateCallStatus('Connected - Roleplay 1.1 Active', 'connected');
        
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
        
        // Enable call controls
        this.enableCallControls();
        
        // Clear conversation history
        this.conversationHistory = [];
        
        // Play initial AI response
        if (initialResponse) {
            console.log('🎯 Playing Roleplay 1.1 initial response:', initialResponse);
            await this.playAIResponseAndWaitForUser(initialResponse);
        } else {
            console.log('🎤 No initial response, prompting user for Roleplay 1.1');
            this.promptUserToSpeak('The prospect answered. Start your Roleplay 1.1 opener!');
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

    enableCallControls() {
        const micBtn = document.getElementById('mic-btn');
        const muteBtn = document.getElementById('mute-btn');
        const speakerBtn = document.getElementById('speaker-btn');
        
        if (micBtn) {
            micBtn.disabled = false;
            micBtn.title = 'Hold to speak - Roleplay 1.1';
        }
        if (muteBtn) muteBtn.disabled = false;
        if (speakerBtn) speakerBtn.disabled = false;
    }

    startRecording() {
        if (this.callState !== 'connected' || this.isMuted || this.aiIsSpeaking || this.isProcessing) {
            console.log('❌ Cannot start recording:', { 
                callState: this.callState, 
                isMuted: this.isMuted, 
                aiIsSpeaking: this.aiIsSpeaking, 
                isProcessing: this.isProcessing 
            });
            return;
        }
        
        console.log('🎤 Starting recording for Roleplay 1.1...');
        this.isRecording = true;
        
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.classList.add('recording');
        }
        
        this.updateTranscript('🎤 You are speaking... (Roleplay 1.1 active)');
        
        // Start voice recognition
        if (this.voiceHandler && !this.voiceHandler.isListening) {
            this.voiceHandler.startListening();
        }
    }

    stopRecording() {
        if (!this.isRecording) return;
        
        console.log('⏹️ Stopping recording for Roleplay 1.1...');
        this.isRecording = false;
        
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.classList.remove('recording');
        }
        
        // Stop voice recognition
        if (this.voiceHandler && this.voiceHandler.isListening) {
            this.voiceHandler.stopListening();
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || !this.currentSession || this.isProcessing || this.aiIsSpeaking) {
            console.log('❌ Cannot process user input - invalid state');
            return;
        }

        // Handle silence triggers
        if (transcript === '[SILENCE_IMPATIENCE]' || transcript === '[SILENCE_HANGUP]') {
            console.log('⏰ Handling silence trigger:', transcript);
            await this.handleSilenceTrigger(transcript);
            return;
        }

        console.log('💬 Processing Roleplay 1.1 user input:', transcript);
        this.isProcessing = true;

        this.addToConversationHistory('user', transcript);
        this.updateTranscript('Processing your Roleplay 1.1 response...');

        try {
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST',
                body: JSON.stringify({
                    user_input: transcript
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Roleplay 1.1 AI response received:', data);
                
                // Check if call should end
                if (!data.call_continues) {
                    console.log('📞 Roleplay 1.1 call ending...');
                    setTimeout(() => {
                        this.endCall(data.session_success);
                    }, 2000);
                    return;
                }
                
                // Play AI response and wait for user
                await this.playAIResponseAndWaitForUser(data.ai_response);
                
            } else {
                const errorData = await response.json();
                console.error('❌ Roleplay 1.1 API error:', errorData);
                this.showError(errorData.error || 'Failed to process input');
                this.promptUserToSpeak('Sorry, please try again...');
            }
        } catch (error) {
            console.error('❌ Error processing Roleplay 1.1 user input:', error);
            this.showError('Network error during call');
            this.promptUserToSpeak('Network error, please try again...');
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
            console.log('🎭 Playing Roleplay 1.1 AI response:', text.substring(0, 50) + '...');
            this.aiIsSpeaking = true;
            
            this.addToConversationHistory('ai', text);
            this.updateTranscript(`🎯 Prospect: "${text}" (Roleplay 1.1)`);

            // Try to play TTS audio
            try {
                const response = await this.apiCall('/api/roleplay/tts', {
                    method: 'POST',
                    body: JSON.stringify({ text: text })
                });

                if (response.ok) {
                    const audioBlob = await response.blob();
                    
                    if (audioBlob.size > 100) {
                        console.log('🔊 Playing Roleplay 1.1 audio, size:', audioBlob.size);
                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audio = new Audio(audioUrl);
                        
                        await new Promise((resolve) => {
                            audio.onended = () => {
                                console.log('✅ Roleplay 1.1 audio playback finished');
                                URL.revokeObjectURL(audioUrl);
                                resolve();
                            };
                            
                            audio.onerror = () => {
                                console.log('❌ Roleplay 1.1 audio playback failed');
                                URL.revokeObjectURL(audioUrl);
                                resolve();
                            };
                            
                            audio.play().catch((error) => {
                                console.log('❌ Roleplay 1.1 audio play failed:', error);
                                resolve();
                            });
                        });
                    } else {
                        console.log('📢 Audio blob too small, simulating speaking time');
                        await this.simulateSpeakingTime(text);
                    }
                } else {
                    console.log('🎵 TTS request failed, simulating speaking time');
                    await this.simulateSpeakingTime(text);
                }
            } catch (ttsError) {
                console.log('🔊 Roleplay 1.1 TTS error:', ttsError);
                await this.simulateSpeakingTime(text);
            }

            this.aiIsSpeaking = false;
            console.log('✅ Roleplay 1.1 AI finished speaking, prompting user');
            this.promptUserToSpeak('Your turn! Hold the microphone to respond... (Roleplay 1.1)');
            
        } catch (error) {
            console.error('❌ Error playing Roleplay 1.1 AI response:', error);
            this.aiIsSpeaking = false;
            await this.simulateSpeakingTime(text);
            this.promptUserToSpeak('Your turn! Hold the microphone to respond... (Roleplay 1.1)');
        }
    }

    async simulateSpeakingTime(text) {
        const wordsPerMinute = 150;
        const words = text.split(' ').length;
        const speakingTimeMs = (words / wordsPerMinute) * 60 * 1000;
        const minTime = 1000;
        const maxTime = 5000;
        
        const delay = Math.max(minTime, Math.min(maxTime, speakingTimeMs));
        console.log(`⏱️ Simulating Roleplay 1.1 speaking time: ${delay}ms for ${words} words`);
        
        return new Promise(resolve => setTimeout(resolve, delay));
    }

    promptUserToSpeak(message) {
        console.log('🎤 Prompting user to speak for Roleplay 1.1:', message);
        this.updateTranscript(message);
        
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.classList.add('pulse-animation');
            setTimeout(() => {
                micBtn.classList.remove('pulse-animation');
            }, 3000);
        }
    }

    addToConversationHistory(sender, message) {
        this.conversationHistory.push({
            sender: sender,
            message: message,
            timestamp: new Date(),
            roleplay_version: '1.1'
        });
        
        console.log(`📝 Added to Roleplay 1.1 conversation: ${sender} - ${message.substring(0, 50)}...`);
    }

    updateTranscript(text) {
        const transcriptElement = document.getElementById('live-transcript');
        if (transcriptElement) {
            transcriptElement.textContent = text;
        }
    }

    async endCall(success = false) {
        if (!this.isActive) {
            console.log('📞 Roleplay 1.1 call already ended or not active');
            return;
        }

        console.log('📞 Ending Roleplay 1.1 call, success:', success);

        this.callState = 'ended';
        this.updateCallStatus('Roleplay 1.1 Call ended', 'ended');
        this.isActive = false;
        this.aiIsSpeaking = false;
        
        // Clear timers
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
            this.durationInterval = null;
        }
        
        // Stop voice recognition
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
        }
        
        this.stopRecording();
        
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
                console.log('✅ Roleplay 1.1 call ended successfully:', data);
                
                setTimeout(() => {
                    this.showFeedback(data.coaching, data.overall_score);
                }, 2000);
            } else {
                console.error('❌ Failed to end Roleplay 1.1 call properly');
                setTimeout(() => {
                    this.showFeedback(null, 50);
                }, 2000);
            }
        } catch (error) {
            console.error('❌ Error ending Roleplay 1.1 call:', error);
            setTimeout(() => {
                this.showFeedback(null, 50);
            }, 2000);
        }
    }

    showFeedback(coaching, score = 75) {
        console.log('📊 Showing Roleplay 1.1 feedback screen');
        
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'flex';
        
        const feedbackHeader = document.querySelector('.feedback-header h4');
        if (feedbackHeader) {
            feedbackHeader.textContent = 'Roleplay 1.1 Complete!';
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
                { key: 'sales_coaching', icon: 'chart-line', title: 'Sales Performance (Roleplay 1.1)' },
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
                    <h6><i class="fas fa-info-circle me-2"></i>Roleplay 1.1 Session Complete</h6>
                    <p style="margin: 0; font-size: 14px;">Your Roleplay 1.1 call has been completed. Keep practicing!</p>
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
        console.log('🔄 Trying again with same Roleplay 1.1 mode');
        this.showModeSelection();
        
        if (this.selectedMode) {
            setTimeout(() => {
                this.selectMode(this.selectedMode);
            }, 100);
        }
    }

    showModeSelection() {
        console.log('🎯 Showing Roleplay 1.1 mode selection screen');
        
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
            startBtn.textContent = 'Select a mode to start Roleplay 1.1 call';
        }
    }

    showError(message) {
        console.error('❌ Roleplay 1.1 Error:', message);
        this.updateTranscript(`❌ Error: ${message}`);
        
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        alertDiv.innerHTML = `<strong>Roleplay 1.1 Error:</strong> ${message}`;
        
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

        console.log('🌐 Making Roleplay 1.1 API call to:', endpoint, options.method || 'GET');

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            console.error('🔐 Authentication required for Roleplay 1.1, redirecting to login');
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
        console.log('🧹 Destroying Roleplay 1.1 Phone Manager');
        
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
        console.log('🚀 Initializing Roleplay 1.1 phone manager on page load');
        window.roleplayManager = new PhoneRoleplayManager();
    }
});

// Export for global access
window.PhoneRoleplayManager = PhoneRoleplayManager;

console.log('✅ Roleplay 1.1 Phone Manager loaded successfully');