// ===== UPDATED STATIC/JS/ROLEPLAY.JS - ROLEPLAY 1.1 COMPLIANT =====

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
        
        // ===== ROLEPLAY 1.1 SPECIFICATIONS =====
        this.roleplay11Specs = {
            silence_impatience_threshold: 10000,  // 10 seconds
            silence_hangup_threshold: 15000,      // 15 seconds
            opener_hangup_chance: 0.25,          // 20-30% chance
            pass_threshold: 3,                   // Need 3/4 criteria for most rubrics
            soft_discovery_threshold: 2         // Need 2/3 for soft discovery
        };
        
        // Track Roleplay 1.1 progress
        this.roleplay11Progress = {
            current_stage: 'phone_pickup',
            rubric_scores: {
                opener: { score: 0, criteria_met: [], passed: false },
                objection_handling: { score: 0, criteria_met: [], passed: false },
                mini_pitch: { score: 0, criteria_met: [], passed: false },
                soft_discovery: { score: 0, criteria_met: [], passed: false }
            },
            stage_progression: ['phone_pickup'],
            silence_events: [],
            overall_result: 'in_progress'
        };
        
        // Post-call message tracking
        this.consecutivePasses = 0;
        
        this.init();
    }

    init() {
        console.log('Initializing Roleplay 1.1 Phone Manager...');
        
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
        
        this.loadRoleplayData();
        this.setupEventListeners();
        this.initializeModeSelection();
        
        // Initialize voice handler for Roleplay 1.1
        if (typeof VoiceHandler !== 'undefined') {
            this.voiceHandler = new VoiceHandler(this);
            console.log('Voice handler initialized for Roleplay 1.1');
        } else {
            console.warn('VoiceHandler not available for Roleplay 1.1');
        }
    }

    updateTime() {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: false 
        });
        document.getElementById('current-time').textContent = time;
    }

    loadRoleplayData() {
        const roleplayData = document.getElementById('roleplay-data');
        if (roleplayData) {
            const roleplayId = parseInt(roleplayData.dataset.roleplayId);
            const isAuthenticated = roleplayData.dataset.userAuthenticated === 'true';
            
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
            console.log('Loading Roleplay 1.1 info for ID:', roleplayId);
            const response = await this.apiCall(`/api/roleplay/info/${roleplayId}`);
            if (response.ok) {
                const data = await response.json();
                console.log('Roleplay 1.1 info loaded:', data);
                this.updateRoleplayUI(data);
            }
        } catch (error) {
            console.error('Error loading Roleplay 1.1 info:', error);
        }
    }

    updateRoleplayUI(roleplayData) {
        // Update title to show Roleplay 1.1
        const titleElement = document.getElementById('roleplay-title');
        if (titleElement) {
            titleElement.textContent = 'Roleplay 1.1: ' + roleplayData.name;
        }

        // Update prospect information for Roleplay 1.1
        this.updateProspectInfo(roleplayData);
    }

    updateProspectInfo(roleplayData) {
        const avatarElement = document.getElementById('contact-avatar');
        const nameElement = document.getElementById('contact-name');
        const infoElement = document.getElementById('contact-info');

        // Generate prospect name for Roleplay 1.1
        if (nameElement) {
            nameElement.textContent = this.generateProspectName(roleplayData.job_title);
        }

        // Update prospect info for Roleplay 1.1
        if (infoElement) {
            infoElement.textContent = `${roleplayData.job_title} • ${roleplayData.industry}`;
        }

        // Update avatar for Roleplay 1.1
        if (avatarElement) {
            const avatarUrl = this.getAvatarUrl(roleplayData.job_title, roleplayData.industry);
            avatarElement.src = avatarUrl;
            avatarElement.alt = `${roleplayData.job_title} prospect - Roleplay 1.1`;
            
            // Fallback if image fails to load
            avatarElement.onerror = function() {
                this.src = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face';
                this.onerror = null;
            };
        }
    }

    getAvatarUrl(jobTitle, industry) {
        // Avatar mapping for Roleplay 1.1
        const avatarMapping = {
            'CEO': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
            'CTO': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
            'VP of Sales': 'https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=150&h=150&fit=crop&crop=face',
            'Marketing Manager': 'https://images.unsplash.com/photo-1494790108755-74612b16c1be?w=150&h=150&fit=crop&crop=face',
            'Director': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&h=150&fit=crop&crop=face',
            'Operations Manager': 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150&h=150&fit=crop&crop=face'
        };
        
        return avatarMapping[jobTitle] || avatarMapping['CTO'];
    }

    generateProspectName(jobTitle) {
        // Names for Roleplay 1.1 prospects
        const names = {
            'CEO': ['Alex Morgan', 'Sarah Chen', 'Michael Rodriguez', 'Jennifer Walsh', 'David Kim'],
            'CTO': ['David Kim', 'Jennifer Walsh', 'Robert Singh', 'Emily Chen', 'Mark Johnson'],
            'VP of Sales': ['Lisa Thompson', 'Mark Johnson', 'Amanda Garcia', 'Chris Wilson', 'Maria Lopez'],
            'Marketing Manager': ['Emily Davis', 'Chris Wilson', 'Maria Lopez', 'Sarah Thompson', 'Mike Rodriguez'],
            'Director': ['Patricia Williams', 'James Davis', 'Linda Miller', 'Robert Taylor', 'Mary Anderson'],
            'Operations Manager': ['Robert Taylor', 'Mary Anderson', 'John Wilson', 'Lisa Chen', 'David Brown']
        };

        const nameList = names[jobTitle] || ['Jordan Smith', 'Taylor Brown', 'Casey Jones', 'Alex Morgan', 'Sam Wilson'];
        return nameList[Math.floor(Math.random() * nameList.length)];
    }

    setupEventListeners() {
        // Mode selection for Roleplay 1.1
        document.querySelectorAll('.mode-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const mode = option.dataset.mode;
                this.selectMode(mode);
            });
        });

        // Start call button for Roleplay 1.1
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (!this.isProcessing) {
                    this.startCall();
                }
            });
        }

        // Call controls for Roleplay 1.1
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            // Use mousedown/mouseup for hold-to-talk in Roleplay 1.1
            micBtn.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.startRecording();
            });

            micBtn.addEventListener('mouseup', (e) => {
                e.preventDefault();
                this.stopRecording();
            });

            micBtn.addEventListener('mouseleave', (e) => {
                this.stopRecording();
            });

            // Touch events for mobile Roleplay 1.1
            micBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.startRecording();
            });

            micBtn.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.stopRecording();
            });
        }

        // Other controls
        const muteBtn = document.getElementById('mute-btn');
        if (muteBtn) {
            muteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMute();
            });
        }

        const speakerBtn = document.getElementById('speaker-btn');
        if (speakerBtn) {
            speakerBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleSpeaker();
            });
        }

        const endCallBtn = document.getElementById('end-call-btn');
        if (endCallBtn) {
            endCallBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.endCall();
            });
        }

        // Feedback actions for Roleplay 1.1
        const tryAgainBtn = document.getElementById('try-again-btn');
        if (tryAgainBtn) {
            tryAgainBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.tryAgain();
            });
        }

        const newModeBtn = document.getElementById('new-mode-btn');
        if (newModeBtn) {
            newModeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showModeSelection();
            });
        }

        // Keyboard shortcuts for Roleplay 1.1
        document.addEventListener('keydown', (e) => {
            // Space bar for push-to-talk
            if (e.code === 'Space' && this.callState === 'connected' && !this.isRecording) {
                e.preventDefault();
                this.startRecording();
            }
            
            // Escape to end call
            if (e.code === 'Escape' && this.callState === 'connected') {
                e.preventDefault();
                this.endCall();
            }
        });

        document.addEventListener('keyup', (e) => {
            if (e.code === 'Space' && this.isRecording) {
                e.preventDefault();
                this.stopRecording();
            }
        });
    }

    initializeModeSelection() {
        document.getElementById('mode-selection').style.display = 'flex';
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'none';
        
        // Reset Roleplay 1.1 state
        this.callState = 'idle';
        this.isActive = false;
        this.aiIsSpeaking = false;
        this.isProcessing = false;
        this.conversationHistory = [];
        this.resetRoleplay11Progress();
    }

    resetRoleplay11Progress() {
        this.roleplay11Progress = {
            current_stage: 'phone_pickup',
            rubric_scores: {
                opener: { score: 0, criteria_met: [], passed: false },
                objection_handling: { score: 0, criteria_met: [], passed: false },
                mini_pitch: { score: 0, criteria_met: [], passed: false },
                soft_discovery: { score: 0, criteria_met: [], passed: false }
            },
            stage_progression: ['phone_pickup'],
            silence_events: [],
            overall_result: 'in_progress'
        };
    }

    selectMode(mode) {
        if (!mode || this.isProcessing) return;
        
        console.log('Roleplay 1.1 mode selected:', mode);
        this.selectedMode = mode;
        
        // Update UI
        document.querySelectorAll('.mode-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        const selectedOption = document.querySelector(`[data-mode="${mode}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        // Update start button for Roleplay 1.1
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = `Start Roleplay 1.1 ${this.capitalizeFirst(mode)} Call`;
        }
    }

    async startCall() {
        if (!this.selectedMode || this.isProcessing) {
            console.log('Cannot start Roleplay 1.1 call: missing mode or already processing');
            return;
        }

        const roleplayId = this.getRoleplayId();
        if (!roleplayId) {
            this.showError('Invalid Roleplay 1.1 configuration');
            return;
        }

        console.log('Starting Roleplay 1.1 phone call:', { roleplayId, mode: this.selectedMode });

        // Prevent duplicate requests
        this.isProcessing = true;
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connecting to Roleplay 1.1...';
        }

        try {
            // Start Roleplay 1.1 session via API
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST',
                body: JSON.stringify({
                    roleplay_id: roleplayId,
                    mode: this.selectedMode
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Roleplay 1.1 started successfully:', data);
                
                this.currentSession = data;
                this.isActive = true;
                
                // Start the Roleplay 1.1 phone call sequence
                await this.startPhoneCallSequence(data.initial_response);
                
            } else {
                const errorData = await response.json();
                console.error('Failed to start Roleplay 1.1:', errorData);
                this.showError(errorData.error || 'Failed to start Roleplay 1.1 call');
            }
        } catch (error) {
            console.error('Error starting Roleplay 1.1:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.isProcessing = false;
            
            // Reset button if call didn't start successfully
            if (!this.isActive && startBtn) {
                startBtn.disabled = false;
                startBtn.textContent = `Start Roleplay 1.1 ${this.capitalizeFirst(this.selectedMode)} Call`;
            }
        }
    }

    async startPhoneCallSequence(initialResponse) {
        console.log('Starting Roleplay 1.1 phone call sequence...');
        
        // Hide mode selection, show call interface
        document.getElementById('mode-selection').style.display = 'none';
        document.getElementById('call-interface').style.display = 'flex';

        // Go through realistic call stages for Roleplay 1.1
        await this.dialingState();
        await this.ringingState();
        await this.connectedState(initialResponse);
    }

    async dialingState() {
        console.log('Roleplay 1.1 dialing state...');
        this.callState = 'dialing';
        this.updateCallStatus('Calling...', 'dialing');
        
        // Add calling animation to avatar
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.add('calling');
        }
        
        await this.delay(2000); // 2 seconds dialing
    }

    async ringingState() {
        console.log('Roleplay 1.1 ringing state...');
        this.callState = 'ringing';
        this.updateCallStatus('Ringing...', 'ringing');
        
        await this.delay(3000); // 3 seconds ringing
    }

    async connectedState(initialResponse) {
        console.log('Roleplay 1.1 connected state...');
        this.callState = 'connected';
        this.updateCallStatus('Connected - Roleplay 1.1 Active', 'connected');
        
        // Remove calling animation
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.remove('calling');
            avatar.classList.add('roleplay-11-active');
        }
        
        // Start call timer
        this.callStartTime = Date.now();
        this.startCallTimer();
        
        // Show live transcript with Roleplay 1.1 indicator
        const transcript = document.getElementById('live-transcript');
        if (transcript) {
            transcript.classList.add('show');
            transcript.classList.add('roleplay-11-active');
        }
        
        // Enable call controls
        this.enableCallControls();
        
        // Clear conversation history and start fresh
        this.conversationHistory = [];
        
        // Play initial AI response (prospect answers phone)
        if (initialResponse) {
            console.log('Playing Roleplay 1.1 initial response:', initialResponse);
            await this.playAIResponseAndWaitForUser(initialResponse);
        } else {
            console.log('No initial response, prompting user for Roleplay 1.1');
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
            micBtn.title = 'Hold to speak - Roleplay 1.1 (10s=impatience, 15s=hangup)';
        }
        if (muteBtn) muteBtn.disabled = false;
        if (speakerBtn) speakerBtn.disabled = false;
    }

    startRecording() {
        if (this.callState !== 'connected' || this.isMuted || this.aiIsSpeaking || this.isProcessing) {
            console.log('Cannot start recording:', { 
                callState: this.callState, 
                isMuted: this.isMuted, 
                aiIsSpeaking: this.aiIsSpeaking, 
                isProcessing: this.isProcessing 
            });
            return;
        }
        
        console.log('Starting recording for Roleplay 1.1...');
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
        
        console.log('Stopping recording for Roleplay 1.1...');
        this.isRecording = false;
        
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.classList.remove('recording');
        }
        
        // Stop voice recognition - this will trigger the final transcript processing
        if (this.voiceHandler && this.voiceHandler.isListening) {
            this.voiceHandler.stopListening();
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || !this.currentSession || this.isProcessing || this.aiIsSpeaking) {
            console.log('Cannot process user input - invalid state');
            return;
        }

        // Handle special Roleplay 1.1 silence triggers
        if (transcript === '[SILENCE_IMPATIENCE]') {
            await this.handleSilenceImpatience();
            return;
        }
        
        if (transcript === '[SILENCE_HANGUP]') {
            await this.handleSilenceHangup();
            return;
        }

        console.log('Processing Roleplay 1.1 user input:', transcript);
        this.isProcessing = true;

        // Add to conversation history
        this.addToConversationHistory('user', transcript);
        
        // Update transcript
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
                console.log('Roleplay 1.1 AI response received:', data);
                
                // Update Roleplay 1.1 progress tracking
                if (data.evaluation) {
                    this.updateRoleplay11Progress(data.evaluation);
                }
                
                // Check if call should end
                if (!data.call_continues) {
                    console.log('Roleplay 1.1 call ending...');
                    await this.endCall(data.session_success);
                    return;
                }
                
                // Play AI response and wait for user
                await this.playAIResponseAndWaitForUser(data.ai_response);
                
            } else {
                const errorData = await response.json();
                console.error('Roleplay 1.1 API error:', errorData);
                this.showError(errorData.error || 'Failed to process input');
                this.promptUserToSpeak('Sorry, please try again...');
            }
        } catch (error) {
            console.error('Error processing Roleplay 1.1 user input:', error);
            this.showError('Network error during call');
            this.promptUserToSpeak('Network error, please try again...');
        } finally {
            this.isProcessing = false;
        }
    }

    updateRoleplay11Progress(evaluation) {
        if (!evaluation) return;
        
        console.log('Updating Roleplay 1.1 progress:', evaluation);
        
        // Update current stage
        if (evaluation.stage) {
            this.roleplay11Progress.current_stage = evaluation.stage;
        }
        
        // Update rubric scores if provided
        if (evaluation.rubric_details) {
            const stage = evaluation.stage;
            if (stage && this.roleplay11Progress.rubric_scores[stage]) {
                this.roleplay11Progress.rubric_scores[stage] = {
                    score: evaluation.score || 0,
                    criteria_met: evaluation.criteria_met || [],
                    passed: evaluation.passed || false
                };
            }
        }
        
        // Track stage progression
        if (evaluation.next_stage && 
            !this.roleplay11Progress.stage_progression.includes(evaluation.next_stage)) {
            this.roleplay11Progress.stage_progression.push(evaluation.next_stage);
        }
        
        // Update overall result
        if (evaluation.overall_call_result) {
            this.roleplay11Progress.overall_result = evaluation.overall_call_result;
        }
    }

    async handleSilenceImpatience() {
        console.log('Handling Roleplay 1.1 silence impatience trigger');
        this.updateTranscript('⏰ 10 seconds of silence... The prospect is getting impatient...');
        
        // Record silence event
        this.roleplay11Progress.silence_events.push({
            type: 'impatience',
            timestamp: new Date().toISOString(),
            stage: this.roleplay11Progress.current_stage
        });
        
        // Send special impatience input to roleplay engine
        await this.processUserInput('[SILENCE_IMPATIENCE_ACTUAL]');
    }

    async handleSilenceHangup() {
        console.log('Handling Roleplay 1.1 silence hangup trigger');
        this.updateTranscript('📞 The prospect hung up due to 15 seconds of silence.');
        
        // Record silence event
        this.roleplay11Progress.silence_events.push({
            type: 'hangup',
            timestamp: new Date().toISOString(),
            stage: this.roleplay11Progress.current_stage
        });
        
        // Mark as failed due to silence
        this.roleplay11Progress.overall_result = 'fail';
        
        // End the call due to silence
        setTimeout(() => {
            this.endCall(false); // Mark as unsuccessful
        }, 2000);
    }

    async playAIResponseAndWaitForUser(text) {
        try {
            console.log('Playing Roleplay 1.1 AI response:', text.substring(0, 50) + '...');
            this.aiIsSpeaking = true;
            
            // Add to conversation history
            this.addToConversationHistory('ai', text);
            
            // Update transcript with Roleplay 1.1 indicator
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
                        console.log('Playing Roleplay 1.1 audio, size:', audioBlob.size);
                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audio = new Audio(audioUrl);
                        
                        // Wait for audio to finish
                        await new Promise((resolve) => {
                            audio.onended = () => {
                                console.log('Roleplay 1.1 audio playback finished');
                                URL.revokeObjectURL(audioUrl);
                                resolve();
                            };
                            
                            audio.onerror = () => {
                                console.log('Roleplay 1.1 audio playback failed');
                                URL.revokeObjectURL(audioUrl);
                                resolve();
                            };
                            
                            audio.play().catch((error) => {
                                console.log('Roleplay 1.1 audio play failed:', error);
                                resolve();
                            });
                        });
                    } else {
                        console.log('Audio blob too small, simulating speaking time');
                        await this.simulateSpeakingTime(text);
                    }
                } else {
                    console.log('TTS request failed, simulating speaking time');
                    await this.simulateSpeakingTime(text);
                }
            } catch (ttsError) {
                console.log('Roleplay 1.1 TTS error:', ttsError);
                await this.simulateSpeakingTime(text);
            }

            // AI finished speaking
            this.aiIsSpeaking = false;
            console.log('Roleplay 1.1 AI finished speaking, prompting user');
            this.promptUserToSpeak('Your turn! Hold the microphone to respond... (Roleplay 1.1)');
            
        } catch (error) {
            console.error('Error playing Roleplay 1.1 AI response:', error);
            this.aiIsSpeaking = false;
            await this.simulateSpeakingTime(text);
            this.promptUserToSpeak('Your turn! Hold the microphone to respond... (Roleplay 1.1)');
        }
    }

    async simulateSpeakingTime(text) {
        // Calculate realistic speaking time for Roleplay 1.1
        const wordsPerMinute = 150;
        const words = text.split(' ').length;
        const speakingTimeMs = (words / wordsPerMinute) * 60 * 1000;
        const minTime = 1000; // Minimum 1 second
        const maxTime = 5000; // Maximum 5 seconds
        
        const delay = Math.max(minTime, Math.min(maxTime, speakingTimeMs));
        console.log(`Simulating Roleplay 1.1 speaking time: ${delay}ms for ${words} words`);
        
        return new Promise(resolve => setTimeout(resolve, delay));
    }

    promptUserToSpeak(message) {
        console.log('Prompting user to speak for Roleplay 1.1:', message);
        this.updateTranscript(message);
        
        // Add visual indication
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
        
        console.log(`Added to Roleplay 1.1 conversation history: ${sender} - ${message.substring(0, 50)}...`);
    }

    updateTranscript(text) {
        const transcriptElement = document.getElementById('live-transcript');
        if (transcriptElement) {
            transcriptElement.textContent = text;
        }
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        console.log('Roleplay 1.1 mute toggled:', this.isMuted);
        
        const muteBtn = document.getElementById('mute-btn');
        if (muteBtn) {
            if (this.isMuted) {
                muteBtn.classList.add('active');
                muteBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                muteBtn.title = 'Unmute';
            } else {
                muteBtn.classList.remove('active');
                muteBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                muteBtn.title = 'Mute';
            }
        }
        
        // Stop recording if currently recording and muted
        if (this.isMuted && this.isRecording) {
            this.stopRecording();
        }
    }

    toggleSpeaker() {
        this.speakerOn = !this.speakerOn;
        console.log('Roleplay 1.1 speaker toggled:', this.speakerOn);
        
        const speakerBtn = document.getElementById('speaker-btn');
        if (speakerBtn) {
            if (this.speakerOn) {
                speakerBtn.classList.add('active');
                speakerBtn.title = 'Turn off speaker';
            } else {
                speakerBtn.classList.remove('active');
                speakerBtn.title = 'Turn on speaker';
            }
        }
    }

    async endCall(success = false) {
        if (!this.isActive) {
            console.log('Roleplay 1.1 call already ended or not active');
            return;
        }

        console.log('Ending Roleplay 1.1 call, success:', success);

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
        
        // Stop recording
        this.stopRecording();
        
        // Hide transcript
        const transcript = document.getElementById('live-transcript');
        if (transcript) {
            transcript.classList.remove('show');
            transcript.classList.remove('roleplay-11-active');
        }

        // Remove Roleplay 1.1 active indicator
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.classList.remove('roleplay-11-active');
        }

        try {
            // Call API to end Roleplay 1.1 session
            const response = await this.apiCall('/api/roleplay/end', {
                method: 'POST',
                body: JSON.stringify({ 
                    success: success,
                    forced_end: false 
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Roleplay 1.1 call ended successfully:', data);
                
                // Show feedback after a realistic delay
                setTimeout(() => {
                    this.showFeedback(data.coaching, data.overall_score);
                }, 2000);
            } else {
                console.error('Failed to end Roleplay 1.1 call properly');
                // Still show feedback screen
                setTimeout(() => {
                    this.showFeedback(null, 50);
                }, 2000);
            }
        } catch (error) {
            console.error('Error ending Roleplay 1.1 call:', error);
            // Still show feedback screen
            setTimeout(() => {
                this.showFeedback(null, 50);
            }, 2000);
        }
    }

    showFeedback(coaching, score = 75) {
        console.log('Showing Roleplay 1.1 feedback screen');
        
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'flex';
        
        // Add Roleplay 1.1 indicator to feedback
        const feedbackHeader = document.querySelector('.feedback-header h4');
        if (feedbackHeader) {
            feedbackHeader.textContent = 'Roleplay 1.1 Complete!';
        }
        
        // Populate feedback content
        if (coaching) {
            this.populateRoleplay11Feedback(coaching);
        }
        
        // Animate score
        this.animateScore(score);
        
        // Update consecutive passes tracking
        if (score >= 80) {
            this.consecutivePasses++;
        } else {
            this.consecutivePasses = 0;
        }
        
        // Show special message after 3 consecutive passes
        if (this.consecutivePasses >= 3) {
            this.showConsecutivePassesMessage();
        }
    }

    populateRoleplay11Feedback(coaching) {
        const content = document.getElementById('feedback-content');
        if (!content) return;
        
        content.innerHTML = '';

        if (coaching && coaching.coaching) {
            const feedbackItems = [
                { key: 'sales_coaching', icon: 'chart-line', title: 'Sales Performance (Roleplay 1.1)' },
                { key: 'grammar_coaching', icon: 'spell-check', title: 'Grammar & Structure' },
                { key: 'vocabulary_coaching', icon: 'book', title: 'Vocabulary' },
                { key: 'pronunciation_coaching', icon: 'volume-up', title: 'Pronunciation' },
                { key: 'rapport_assertiveness', icon: 'handshake', title: 'Rapport & Confidence' }
            ];

            feedbackItems.forEach(item => {
                if (coaching.coaching[item.key]) {
                    content.innerHTML += `
                        <div class="feedback-item">
                            <h6><i class="fas fa-${item.icon} me-2"></i>${item.title}</h6>
                            <p style="margin: 0; font-size: 14px;">${coaching.coaching[item.key]}</p>
                        </div>
                    `;
                }
            });
        } else {
            // Default feedback if no coaching data
            content.innerHTML = `
                <div class="feedback-item">
                    <h6><i class="fas fa-info-circle me-2"></i>Roleplay 1.1 Session Complete</h6>
                    <p style="margin: 0; font-size: 14px;">Your Roleplay 1.1 call has been completed. Keep practicing to improve your cold calling skills!</p>
                </div>
            `;
        }
    }

    showConsecutivePassesMessage() {
        const content = document.getElementById('feedback-content');
        if (content) {
            content.innerHTML = `
                <div class="feedback-item" style="background: rgba(34, 197, 94, 0.2); border: 2px solid #22c55e;">
                    <h6><i class="fas fa-trophy me-2" style="color: #22c55e;"></i>Excellent Progress!</h6>
                    <p style="margin: 0; font-size: 14px; color: #22c55e; font-weight: bold;">
                        You've completed 3 Roleplay 1.1 calls in a row—great job! 
                        You can go back to the main screen to try Marathon Mode, or keep practicing here.
                    </p>
                </div>
            ` + content.innerHTML;
        }
    }

    animateScore(targetScore) {
        const scoreElement = document.getElementById('score-circle');
        if (!scoreElement) return;
        
        let currentScore = 0;
        const increment = targetScore / 40; // 40 steps for smooth animation
        
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
        console.log('Trying again with same Roleplay 1.1 mode');
        this.showModeSelection();
        
        // Auto-select the previous mode
        if (this.selectedMode) {
            setTimeout(() => {
                this.selectMode(this.selectedMode);
            }, 100);
        }
    }

    showModeSelection() {
        console.log('Showing Roleplay 1.1 mode selection screen');
        
        document.getElementById('feedback-section').style.display = 'none';
        this.initializeModeSelection();
        
        // Reset state
        this.selectedMode = null;
        this.currentSession = null;
        
        // Reset UI
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
        console.error('Roleplay 1.1 Error:', message);
        this.updateTranscript(`❌ Error: ${message}`);
        
        // Also show a temporary alert
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
        return roleplayData ? parseInt(roleplayData.dataset.roleplayId) : 1; // Default to Roleplay 1.1
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            }
        };

        console.log('Making Roleplay 1.1 API call to:', endpoint, options.method || 'GET');

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            console.error('Authentication required for Roleplay 1.1, redirecting to login');
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

    // Cleanup method
    destroy() {
        console.log('Destroying Roleplay 1.1 Phone Manager');
        
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
        this.resetRoleplay11Progress();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/roleplay/')) {
        console.log('Initializing Roleplay 1.1 phone manager on page load');
        window.roleplayManager = new PhoneRoleplayManager();
    }
});

// Add CSS for Roleplay 1.1 animations
const phoneRoleplay11Style = document.createElement('style');
phoneRoleplay11Style.textContent = `
    .pulse-animation {
        animation: pulse 1.5s infinite !important;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Roleplay 1.1 specific styles */
    .roleplay-11-active {
        border: 2px solid #22c55e !important;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.3) !important;
    }
    
    .live-transcript.roleplay-11-active {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(0, 0, 0, 0.8)) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
    }
    
    .call-interface.connected .contact-avatar.roleplay-11-active {
        animation: roleplay-11-glow 3s ease-in-out infinite alternate;
    }
    
    @keyframes roleplay-11-glow {
        from { 
            border-color: rgba(34, 197, 94, 0.5);
            box-shadow: 0 0 15px rgba(34, 197, 94, 0.3);
        }
        to { 
            border-color: rgba(34, 197, 94, 0.9);
            box-shadow: 0 0 25px rgba(34, 197, 94, 0.6);
        }
    }
    
    /* Prevent text selection on control buttons */
    .control-btn, .mode-option, .start-call-btn, .end-call-btn, .feedback-btn {
        user-select: none;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
    }
    
    /* Improve touch targets for mobile Roleplay 1.1 */
    @media (max-width: 768px) {
        .control-btn {
            width: 70px;
            height: 70px;
            font-size: 22px;
        }
        
        .end-call-btn {
            width: 70px;
            height: 70px;
            font-size: 26px;
        }
    }
    
    /* Consecutive passes message styling */
    .feedback-item.consecutive-passes {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.1)) !important;
        border: 2px solid #22c55e !important;
        animation: celebrate 2s ease-in-out !important;
    }
    
    @keyframes celebrate {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
`;
document.head.appendChild(phoneRoleplay11Style);

// Export for global access
window.PhoneRoleplayManager = PhoneRoleplayManager;

console.log('Roleplay 1.1 Phone Manager loaded successfully');