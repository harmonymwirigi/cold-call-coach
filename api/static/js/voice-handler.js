// ===== FIXED: static/js/voice-handler.js - Enhanced Error Handling =====

class VoiceHandler {
    constructor(roleplayManager) {
        this.roleplayManager = roleplayManager;
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        
        // Device detection
        this.isMobile = this.detectMobile();
        this.isIOS = this.detectIOS();
        
        // Audio state management
        this.currentAudio = null;
        this.isAudioPlaying = false;
        
        // Conversation state
        this.isUserTurn = false;
        this.isAITurn = false;
        this.isInterruptible = false;
        
        // Callback interface
        this.onTranscript = null;
        this.onError = null;
        
        // Enhanced error handling
        this.sessionErrors = 0;
        this.maxSessionErrors = 3;
        this.lastSessionError = null;
        
        // SIMPLE APPROACH: Minimal auto-restart, maximum reliability
        this.autoRestartEnabled = !this.isMobile;
        this.shouldRestart = false;
        this.restartTimeout = null;
        this.lastSuccessfulStart = 0;
        this.consecutiveFailures = 0;
        this.maxConsecutiveFailures = 2;
        
        // Recognition settings (optimized for reliability)
        this.settings = {
            continuous: true,
            interimResults: !this.isMobile,
            language: 'en-US',
            maxAlternatives: 1
        };
        
        // State management
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.isAutoListening = false;
        
        // Simplified silence detection
        this.silenceThreshold = this.isMobile ? 3000 : 2000;
        this.lastSpeechTime = null;
        this.silenceTimer = null;
        
        // Hang-up silence (disabled on mobile for reliability)
        this.impatience_threshold = 10000;
        this.hangup_threshold = 15000;
        this.total_silence_start = null;
        this.impatience_triggered = false;
        this.hangupSilenceTimer = null;
        this.hangupDetectionEnabled = !this.isMobile;
        
        console.log(`🎤 Enhanced Voice Handler - Mobile: ${this.isMobile}, Auto-restart: ${this.autoRestartEnabled}`);
        this.init();
    }

    enableInterruption() {
        console.log('⚡️ Interruptions enabled for AI speech.');
        this.isInterruptible = true;
    }

    setAITurn(isAITurn) {
        this.isAITurn = isAITurn;
        if (isAITurn) {
            this.isUserTurn = false;
            if (this.isListening) {
                this.stopListening(false);
            }
        }
    }

    setUserTurn(isUserTurn) {
        this.isUserTurn = isUserTurn;
        if (isUserTurn) {
            this.isAITurn = false;
            // Reset session error count on new turn
            this.sessionErrors = 0;
        }
    }

    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (window.innerWidth <= 768 && 'ontouchstart' in window);
    }

    detectIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent);
    }

    init() {
        console.log('🎤 Initializing Enhanced Voice Handler...');
        
        this.checkBrowserSupport();
        this.initializeUIElements();
        this.setupEventListeners();
        
        if (this.isSupported) {
            this.initializeSpeechRecognition();
        }
        
        console.log(`✅ Enhanced Voice Handler ready. Mobile mode: ${this.isMobile}`);
    }

    checkBrowserSupport() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.isSupported = true;
            this.SpeechRecognition = SpeechRecognition;
            console.log('✅ Speech recognition supported');
        } else {
            this.isSupported = false;
            console.error('❌ Speech recognition not supported');
        }
        
        this.updateSupportUI();
    }

    updateSupportUI() {
        const micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        
        if (!this.isSupported) {
            if (micButton) {
                micButton.disabled = true;
                micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                micButton.title = 'Voice recognition not supported';
            }
            this.triggerError('Voice recognition not supported. Please use Chrome, Edge, or Safari.');
        } else {
            if (micButton) {
                micButton.title = this.isMobile ? 
                    'Voice ready - will auto-start when it\'s your turn' : 
                    'Voice recognition ready';
            }
        }
    }

    initializeUIElements() {
        this.micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        this.transcriptElement = document.getElementById('live-transcript');
        this.errorElement = document.getElementById('voice-error');
        
        if (this.transcriptElement) {
            this.transcriptElement.textContent = this.isMobile ? 
                'Voice ready for mobile - will start automatically' : 
                'Voice recognition ready...';
        }
    }

    setupEventListeners() {
        // Microphone button (manual trigger)
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                console.log('🎤 Manual mic button clicked');
                this.handleManualMicClick();
            });
        }
        
        // Keyboard shortcuts (desktop only)
        if (!this.isMobile) {
            this.handleKeydown = (e) => {
                if (e.code === 'Space' && !e.target.matches('input, textarea')) {
                    e.preventDefault();
                    if (!this.isListening && this.isUserTurn) {
                        this.startListening();
                    }
                }
                
                if (e.code === 'Escape' && this.isListening) {
                    this.stopListening();
                }
            };
            
            document.addEventListener('keydown', this.handleKeydown);
        }
        
        // Page visibility (simple handling)
        this.handleVisibilityChange = () => {
            if (document.hidden && this.isListening) {
                console.log('📱 Page hidden - stopping recognition');
                this.stopListening();
            }
        };
        
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
    }

    handleManualMicClick() {
        if (this.isListening) {
            console.log('🛑 Manual stop requested');
            this.stopListening();
        } else if (this.isUserTurn && !this.isAudioPlaying) {
            console.log('🎤 Manual start requested');
            this.startListening();
        } else if (this.isAudioPlaying) {
            console.log('⚡ User wants to interrupt AI');
            this.stopAllAudio();
        } else {
            console.log('⏳ Not user turn yet');
            this.showMessage('Wait for your turn to speak', 'info');
        }
    }

    initializeSpeechRecognition() {
        if (!this.isSupported) return;
        
        try {
            this.recognition = new this.SpeechRecognition();
            
            // Simple, reliable configuration
            this.recognition.continuous = this.settings.continuous;
            this.recognition.interimResults = this.settings.interimResults;
            this.recognition.lang = this.settings.language;
            this.recognition.maxAlternatives = this.settings.maxAlternatives;
            
            this.setupRecognitionEventHandlers();
            
            console.log('🎤 Speech recognition configured');
        } catch (error) {
            console.error('❌ Failed to initialize speech recognition:', error);
            this.triggerError('Failed to initialize voice recognition');
        }
    }

    setupRecognitionEventHandlers() {
        if (!this.recognition) return;
        
        this.recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            this.isListening = true;
            this.updateMicrophoneUI(true);
            this.clearError();
            this.lastSuccessfulStart = Date.now();
            this.consecutiveFailures = 0;
            
            if (this.hangupDetectionEnabled && this.isUserTurn) {
                this.total_silence_start = Date.now();
                this.impatience_triggered = false;
                this.startHangupSilenceDetection();
            }
        };
        
        this.recognition.onend = () => {
            console.log('🛑 Voice recognition ended');
            this.isListening = false;
            this.updateMicrophoneUI(false);
            this.stopSilenceDetection();
            this.stopHangupSilenceDetection();
            
            this.handleSimpleRestart();
        };

        this.recognition.onresult = (event) => {
            this.handleRecognitionResult(event);
        };
        
        this.recognition.onerror = (event) => {
            this.handleRecognitionError(event);
        };

        this.recognition.onspeechstart = () => {
            console.log('🗣️ Speech detected');
            this.lastSpeechTime = Date.now();
            
            if (this.isInterruptible && this.isAudioPlaying) {
                console.log('⚡ User interrupted - stopping AI audio');
                this.stopAllAudio();
                
                if (this.roleplayManager && typeof this.roleplayManager.handleUserInterruption === 'function') {
                    this.roleplayManager.handleUserInterruption();
                } else {
                    this.setAITurn(false);
                    this.setUserTurn(true);
                }
            }
            
            // Reset hang-up timer
            this.total_silence_start = null;
            this.impatience_triggered = false;
        };
        
        this.recognition.onspeechend = () => {
            console.log('🤫 Speech ended');
            this.lastSpeechTime = Date.now();
            this.startSilenceDetection();
            if (this.hangupDetectionEnabled) {
                this.total_silence_start = Date.now();
            }
        };
    }

    handleSimpleRestart() {
        // Clear any pending restart
        if (this.restartTimeout) {
            clearTimeout(this.restartTimeout);
            this.restartTimeout = null;
        }
        
        // Don't restart if conditions aren't perfect
        if (!this.shouldRestart || 
            !this.isUserTurn || 
            this.isAudioPlaying || 
            !this.isSupported ||
            this.consecutiveFailures >= this.maxConsecutiveFailures) {
            
            if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
                console.log('🔴 Too many failures - manual restart required');
                this.showManualRestartMessage();
            }
            return;
        }
        
        // MOBILE: No auto-restart, show manual instruction
        if (!this.autoRestartEnabled) {
            console.log('📱 Mobile: No auto-restart - showing manual instruction');
            this.showMobileInstruction();
            return;
        }
        
        // DESKTOP: Simple auto-restart with delay
        const timeSinceLastStart = Date.now() - this.lastSuccessfulStart;
        const restartDelay = Math.max(1000, 2000 - timeSinceLastStart);
        
        console.log(`🔄 Auto-restart in ${restartDelay}ms`);
        
        this.restartTimeout = setTimeout(() => {
            if (this.shouldRestart && this.isUserTurn && !this.isAudioPlaying && !this.isListening) {
                console.log('🔄 Executing auto-restart');
                this.startListening();
            }
        }, restartDelay);
    }

    showMobileInstruction() {
        this.updateTranscript('📱 Your turn - tap the microphone to speak');
        this.showMessage('Your turn! Tap the microphone', 'info');
    }

    showManualRestartMessage() {
        this.updateTranscript('🎤 Voice recognition paused - click microphone to continue');
        this.showMessage('Click the microphone to continue', 'info');
    }

    handleRecognitionResult(event) {
        // Only process if it's user's turn
        if (!this.isUserTurn) {
            console.log('🚫 Ignoring speech - not user turn');
            return;
        }
        
        let interimTranscript = '';
        let finalTranscript = '';
        
        // Process results
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            
            if (result.isFinal) {
                finalTranscript += transcript + ' ';
                console.log(`✅ Final transcript: "${transcript}"`);
                this.lastSpeechTime = Date.now();
            } else if (!this.isMobile) {
                interimTranscript += transcript;
                this.lastSpeechTime = Date.now();
            }
        }
        
        // Update transcript display
        this.currentTranscript = finalTranscript + interimTranscript;
        if (this.currentTranscript.trim()) {
            this.updateTranscript(`🎤 You: "${this.currentTranscript.trim()}"`);
        }
        
        // Process final results
        if (finalTranscript.trim().length > 0) {
            this.finalTranscript += finalTranscript;
            this.startSilenceDetection();
        }
    }

    handleRecognitionError(event) {
        console.error('❌ Voice recognition error:', event.error);
        this.consecutiveFailures++;
        
        const errorMessages = {
            'network': 'Network error. Check your internet connection.',
            'not-allowed': 'Microphone access denied. Please allow microphone access and refresh.',
            'no-speech': 'No speech detected. Try speaking louder or closer to the microphone.',
            'aborted': 'Voice recognition was interrupted.',
            'audio-capture': 'No microphone found. Please connect a microphone.',
            'service-not-allowed': 'Voice service not allowed.',
        };
        
        const message = errorMessages[event.error] || `Voice error: ${event.error}`;
        this.triggerError(message);
        
        // Handle specific errors
        if (event.error === 'not-allowed') {
            this.handlePermissionDenied();
        } else if (event.error === 'no-speech') {
            // Don't count no-speech as a "real" failure
            this.consecutiveFailures = Math.max(0, this.consecutiveFailures - 1);
            
            if (this.isMobile) {
                this.showMessage('No speech heard. Tap mic to try again.', 'warning');
            }
        }
    }

    // ===== AUDIO MANAGEMENT =====

    async playAudio(text, isInterruptible = true) {
        console.log(`🔊 Playing audio: "${text.substring(0, 50)}..."`);
        
        this.stopAllAudio();
        this.setAITurn(true);
        this.setUserTurn(false);
        
        try {
            const response = await fetch('/api/roleplay/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            
            if (response.ok) {
                const audioBlob = await response.blob();
                
                if (audioBlob.size > 100) {
                    const audioUrl = URL.createObjectURL(audioBlob);
                    this.currentAudio = new Audio(audioUrl);
                    this.isAudioPlaying = true;
                    
                    this.currentAudio.onended = () => {
                        console.log('✅ Audio finished');
                        this.cleanupAudio(audioUrl);
                        this.transitionToUserTurn();
                    };
                    
                    this.currentAudio.onerror = () => {
                        console.log('❌ Audio error');
                        this.cleanupAudio(audioUrl);
                        this.transitionToUserTurn();
                    };
                    
                    await this.currentAudio.play();
                    console.log('🎵 Audio playing');
                    
                } else {
                    console.log('📢 Audio too small, simulating');
                    await this.simulateSpeakingTime(text);
                    this.transitionToUserTurn();
                }
            } else {
                console.log('🎵 TTS failed, simulating');
                await this.simulateSpeakingTime(text);
                this.transitionToUserTurn();
            }
        } catch (error) {
            console.error('❌ Audio failed:', error);
            await this.simulateSpeakingTime(text);
            this.transitionToUserTurn();
        }
    }

    transitionToUserTurn() {
        this.setAITurn(false);
        this.setUserTurn(true);
        
        // Start listening after a brief delay
        setTimeout(() => {
            if (this.isUserTurn && !this.isAudioPlaying) {
                this.startAutoListening();
            }
        }, this.isMobile ? 1000 : 500);
    }

    stopAllAudio() {
        if (this.currentAudio) {
            try {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
                this.currentAudio = null;
            } catch (e) {
                console.warn('Error stopping audio:', e);
            }
        }
        this.isAudioPlaying = false;
    }

    cleanupAudio(audioUrl) {
        this.currentAudio = null;
        this.isAudioPlaying = false;
        if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
        }
    }

    async simulateSpeakingTime(text) {
        const words = text.split(' ').length;
        const speakingTime = Math.max(1000, (words / 150) * 60 * 1000);
        
        return new Promise(resolve => {
            setTimeout(resolve, speakingTime);
        });
    }

    // ===== TURN MANAGEMENT =====

    setUserTurn(isUserTurn) {
        this.isUserTurn = isUserTurn;
        console.log(`👤 User turn: ${isUserTurn}`);
        
        if (isUserTurn) {
            this.consecutiveFailures = 0;
            this.sessionErrors = 0; // Reset session errors on new turn
            
            if (this.isMobile) {
                this.updateTranscript('📱 Your turn - voice will start automatically');
            } else {
                this.updateTranscript('🎤 Your turn - speak when ready...');
            }
        }
    }

    setAITurn(isAITurn) {
        this.isAITurn = isAITurn;
        console.log(`🤖 AI turn: ${isAITurn}`);
        
        if (isAITurn) {
            this.stopListening();
        }
    }

    // ===== PUBLIC METHODS =====

    startAutoListening() {
        if (!this.isUserTurn || this.isAudioPlaying) {
            console.log('🚫 Cannot start auto-listening - wrong turn or audio playing');
            return;
        }
        
        console.log('🤖 Starting auto-listening...');
        this.startListening();
    }

    startListening() {
        if (this.isAITurn || this.isAudioPlaying || !this.isSupported || this.isListening) {
            console.log('🚫 Cannot start listening - conditions not met');
            return;
        }
        
        console.log(`🎤 Starting listening (Mobile: ${this.isMobile})`);
        
        try {
            this.shouldRestart = this.autoRestartEnabled;
            this.finalTranscript = '';
            this.currentTranscript = '';
            this.lastSpeechTime = null;
            
            this.requestMicrophonePermission().then(() => {
                if (this.recognition && !this.isAudioPlaying) {
                    this.recognition.start();
                }
                
                this.updateTranscript('🎤 Listening - speak naturally...');
            }).catch(error => {
                console.error('❌ Microphone permission failed:', error);
                this.triggerError('Microphone permission required');
            });
            
        } catch (error) {
            console.error('❌ Failed to start listening:', error);
            this.triggerError('Failed to start voice recognition');
        }
    }

    stopListening() {
        if (!this.isListening) return;
        
        console.log('🛑 Stopping listening...');
        this.shouldRestart = false;
        
        if (this.recognition) {
            this.recognition.stop();
        }
        
        if (this.restartTimeout) {
            clearTimeout(this.restartTimeout);
            this.restartTimeout = null;
        }
        
        this.stopSilenceDetection();
        this.stopHangupSilenceDetection();
    }

    // ===== SILENCE DETECTION =====

    startSilenceDetection() {
        this.stopSilenceDetection();
        
        console.log('🤫 Starting silence detection...');
        
        this.silenceTimer = setTimeout(() => {
            if (this.lastSpeechTime && this.isUserTurn) {
                console.log('🤫 User finished speaking');
                this.processFinalUserSpeech();
            }
        }, this.silenceThreshold);
    }

    stopSilenceDetection() {
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
    }

    // ===== ENHANCED: Process final speech with session error handling =====
    processFinalUserSpeech() {
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }

        const final_transcript = this.finalTranscript.trim();
        if (final_transcript.length > 0) {
            console.log(`✅ Processing final speech: "${final_transcript}"`);
            this.stopListening();
            
            // ENHANCED: Check if callback exists and handle errors gracefully
            if (this.onTranscript && typeof this.onTranscript === 'function') {
                // Enhanced error handling for session issues
                try {
                    this.onTranscript(final_transcript);
                } catch (error) {
                    console.error('❌ Error in transcript callback:', error);
                    this.handleSessionError(error);
                }
            } else {
                console.warn('⚠️ No callback available for transcript');
                this.triggerError("Could not process speech. Please try again.");
            }
        }
        
        // Reset transcripts for the next turn
        this.finalTranscript = '';
        this.currentTranscript = '';
    }

    // ===== NEW: Enhanced session error handling =====
    handleSessionError(error) {
        this.sessionErrors++;
        this.lastSessionError = error;
        
        console.error(`❌ Session error ${this.sessionErrors}/${this.maxSessionErrors}:`, error);
        
        // If error mentions session expiration or 404, try recovery
        const errorMessage = error.message || error.toString();
        if (errorMessage.includes('Session not found') || 
            errorMessage.includes('expired') || 
            errorMessage.includes('404')) {
            
            if (this.sessionErrors < this.maxSessionErrors) {
                console.log('🔄 Attempting session recovery...');
                this.updateTranscript('🔄 Session issue detected. Attempting recovery...');
                
                // Try to recover session through roleplay manager
                if (this.roleplayManager && typeof this.roleplayManager.retrySessionRecovery === 'function') {
                    this.roleplayManager.retrySessionRecovery().then(recovered => {
                        if (recovered) {
                            console.log('✅ Session recovered, retrying...');
                            this.updateTranscript('✅ Session recovered. Please speak again.');
                            this.startAutoListening();
                        } else {
                            console.log('❌ Session recovery failed');
                            this.handleSessionRecoveryFailure();
                        }
                    }).catch(recoveryError => {
                        console.error('❌ Session recovery error:', recoveryError);
                        this.handleSessionRecoveryFailure();
                    });
                } else {
                    this.handleSessionRecoveryFailure();
                }
            } else {
                console.log('❌ Max session errors reached');
                this.handleSessionRecoveryFailure();
            }
        } else {
            // For other errors, just show the error and try to continue
            this.triggerError('Error processing speech. Please try again.');
            setTimeout(() => {
                if (this.isUserTurn) {
                    this.startAutoListening();
                }
            }, 2000);
        }
    }

    handleSessionRecoveryFailure() {
        this.updateTranscript('❌ Session expired. Please start a new call.');
        this.triggerError('Session expired. Please start a new call.');
        
        // Inform the roleplay manager that the session has failed
        if (this.roleplayManager && typeof this.roleplayManager.showModeSelection === 'function') {
            setTimeout(() => {
                this.roleplayManager.showModeSelection();
            }, 3000);
        }
    }

    // ===== HANG-UP DETECTION (DESKTOP ONLY) =====

    startHangupSilenceDetection() {
        if (!this.hangupDetectionEnabled) return;
        
        this.stopHangupSilenceDetection();
        console.log('⏰ Starting hang-up detection');
        
        this.hangupSilenceTimer = setInterval(() => {
            if (this.total_silence_start && this.isListening && this.isUserTurn) {
                const totalSilence = Date.now() - this.total_silence_start;
                
                if (totalSilence >= this.impatience_threshold && 
                    !this.impatience_triggered &&
                    totalSilence < this.hangup_threshold) {
                    this.handleImpatience();
                }
                
                if (totalSilence >= this.hangup_threshold) {
                    this.handleSilenceHangup();
                }
            }
        }, 1000);
    }

    stopHangupSilenceDetection() {
        if (this.hangupSilenceTimer) {
            clearInterval(this.hangupSilenceTimer);
            this.hangupSilenceTimer = null;
        }
    }

    handleImpatience() {
        this.impatience_triggered = true;
        const phrases = [
            "Hello? Are you still with me?",
            "Can you hear me?",
            "Just checking you're there…",
            "Still on the line?"
        ];
        
        const phrase = phrases[Math.floor(Math.random() * phrases.length)];
        this.updateTranscript(`⏰ Prospect: "${phrase}"`);
        
        if (this.onTranscript) {
            try {
                this.onTranscript('[SILENCE_IMPATIENCE]');
            } catch (error) {
                console.error('❌ Error handling impatience:', error);
                this.handleSessionError(error);
            }
        }
    }

    handleSilenceHangup() {
        this.stopListening();
        this.updateTranscript('📞 15 seconds of silence - The prospect hung up.');
        
        if (this.onTranscript) {
            try {
                this.onTranscript('[SILENCE_HANGUP]');
            } catch (error) {
                console.error('❌ Error handling silence hangup:', error);
                this.handleSessionError(error);
            }
        }
    }

    // ===== UI METHODS =====

    updateMicrophoneUI(isListening) {
        const micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        
        if (micButton) {
            if (isListening) {
                micButton.classList.add('listening');
                micButton.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                micButton.title = 'Listening - click to stop';
            } else {
                micButton.classList.remove('listening');
                micButton.style.background = 'rgba(255, 255, 255, 0.1)';
                micButton.title = this.isMobile ? 'Tap to speak' : 'Click to start listening';
            }
        }
    }

    updateTranscript(text) {
        if (this.transcriptElement) {
            this.transcriptElement.textContent = text;
        }
    }

    showMessage(message, type = 'info') {
        console.log(`📢 ${type.toUpperCase()}: ${message}`);
    }

    triggerError(message) {
        console.error('❌ Voice error:', message);
        
        if (this.onError && typeof this.onError === 'function') {
            this.onError(message);
        } else {
            this.showErrorInUI(message);
        }
    }

    showErrorInUI(message) {
        if (this.errorElement) {
            const errorText = this.errorElement.querySelector('#voice-error-text');
            if (errorText) {
                errorText.textContent = message;
            }
            this.errorElement.style.display = 'block';
            
            setTimeout(() => {
                this.errorElement.style.display = 'none';
            }, 5000);
        }
    }

    clearError() {
        if (this.errorElement) {
            this.errorElement.style.display = 'none';
        }
    }

    // ===== UTILITY METHODS =====

    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            throw new Error('Microphone permission denied');
        }
    }

    handlePermissionDenied() {
        this.stopListening();
        this.shouldRestart = false;
        
        const micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        if (micButton) {
            micButton.disabled = true;
            micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        }
        
        this.updateTranscript('Microphone permission denied. Please refresh and allow access.');
    }

    getListeningStatus() {
        return {
            isListening: this.isListening,
            isSupported: this.isSupported,
            isUserTurn: this.isUserTurn,
            isAITurn: this.isAITurn,
            isAudioPlaying: this.isAudioPlaying,
            isMobile: this.isMobile,
            autoRestartEnabled: this.autoRestartEnabled,
            consecutiveFailures: this.consecutiveFailures,
            sessionErrors: this.sessionErrors,
            lastSessionError: this.lastSessionError
        };
    }

    destroy() {
        console.log('🧹 Destroying Voice Handler...');
        
        this.stopListening();
        this.stopAllAudio();
        
        if (this.recognition) {
            this.recognition.onstart = null;
            this.recognition.onend = null;
            this.recognition.onresult = null;
            this.recognition.onerror = null;
            this.recognition = null;
        }
        
        if (this.restartTimeout) {
            clearTimeout(this.restartTimeout);
        }
        
        this.stopSilenceDetection();
        this.stopHangupSilenceDetection();
        
        if (this.handleKeydown) {
            document.removeEventListener('keydown', this.handleKeydown);
        }
        if (this.handleVisibilityChange) {
            document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        }
        
        console.log('✅ Voice Handler destroyed');
    }
}

// Export for global access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceHandler;
} else {
    window.VoiceHandler = VoiceHandler;
}

console.log('✅ Enhanced Voice Handler with session error handling loaded');