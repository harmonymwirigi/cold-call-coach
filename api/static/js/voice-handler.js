// ===== FIXED: voice-handler.js - Callback Interface =====

class VoiceHandler {
    constructor(roleplayManager) {
        this.roleplayManager = roleplayManager;
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        this.micButton = null;
        this.transcriptElement = null;
        this.errorElement = null;
        
        // FIXED: Proper callback interface
        this.onTranscript = null; // Will be set by roleplay manager
        this.onError = null; // Will be set by roleplay manager
        
        // Natural conversation settings
        this.settings = {
            continuous: true,
            interimResults: true,
            language: 'en-US',
            maxAlternatives: 1
        };
        
        // State management
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.silenceTimer = null;
        this.isAutoListening = false;
        this.canInterrupt = false;
        
        // Silence detection for natural conversation
        this.silenceThreshold = 2000;  // 2 seconds of silence = user finished speaking
        this.lastSpeechTime = null;
        this.silenceCheckInterval = null;
        
        // Roleplay 1.1 silence specifications
        this.impatience_threshold = 10000;  // 10 seconds for impatience trigger
        this.hangup_threshold = 15000;      // 15 seconds for hang-up
        this.total_silence_start = null;
        this.impatience_triggered = false;
        this.hangupSilenceTimer = null;
        
        this.shouldRestart = false;
        this.wasPausedBySystem = false;
        
        console.log('🎤 VoiceHandler constructor called');
        this.init();
    }

    init() {
        console.log('🎤 Initializing Voice Handler...');
        
        this.checkBrowserSupport();
        this.initializeUIElements();
        this.setupEventListeners();
        
        if (this.isSupported) {
            this.initializeSpeechRecognition();
        }
        
        console.log(`✅ Voice Handler initialized. Supported: ${this.isSupported}`);
    }

    checkBrowserSupport() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.isSupported = true;
            this.SpeechRecognition = SpeechRecognition;
            console.log('✅ Web Speech API supported');
        } else {
            this.isSupported = false;
            console.error('❌ Web Speech API not supported');
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
            
            this.triggerError('Voice recognition not supported. Use Chrome, Edge, or Safari.');
        } else {
            if (micButton) {
                micButton.title = 'Voice recognition ready';
            }
        }
    }

    initializeUIElements() {
        this.micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        this.transcriptElement = document.getElementById('live-transcript');
        this.errorElement = document.getElementById('voice-error');
        
        if (this.transcriptElement) {
            this.transcriptElement.textContent = 'Voice recognition ready...';
        }
    }

    setupEventListeners() {
        // Microphone button click
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                console.log('🎤 Manual mic button clicked');
                if (this.isListening) {
                    this.stopListening();
                } else {
                    this.startListening(false); // Manual activation
                }
            });
        }
        
        // Keyboard shortcuts
        this.handleKeydown = (e) => {
            if (e.code === 'Space' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                if (!this.isListening) {
                    this.startListening(false);
                }
            }
            
            if (e.code === 'Escape' && this.isListening) {
                this.stopListening();
            }
        };
        
        document.addEventListener('keydown', this.handleKeydown);
        
        // Handle page visibility changes
        this.handleVisibilityChange = () => {
            if (document.hidden && this.isListening) {
                console.log('👁️ Page hidden - pausing recognition');
                this.pauseListening();
            } else if (!document.hidden && this.recognition) {
                console.log('👁️ Page visible - resuming recognition');
                this.resumeListening();
            }
        };
        
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
    }

    initializeSpeechRecognition() {
        if (!this.isSupported) return;
        
        try {
            this.recognition = new this.SpeechRecognition();
            
            // Configure for natural conversation
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = this.settings.language;
            this.recognition.maxAlternatives = this.settings.maxAlternatives;
            
            this.setupRecognitionEventHandlers();
            
            console.log('🎤 Speech recognition initialized');
        } catch (error) {
            console.error('❌ Failed to initialize speech recognition:', error);
            this.triggerError('Failed to initialize voice recognition');
        }
    }

    setupRecognitionEventHandlers() {
        if (!this.recognition) return;
        
        // Recognition starts
        this.recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            this.isListening = true;
            this.updateMicrophoneUI(true);
            this.clearError();
            
            // Start silence tracking
            this.total_silence_start = Date.now();
            this.impatience_triggered = false;
            this.startHangupSilenceDetection();
        };
        
        // Recognition ends
        this.recognition.onend = () => {
            console.log('🛑 Voice recognition ended');
            this.isListening = false;
            this.updateMicrophoneUI(false);
            this.stopSilenceDetection();
            this.stopHangupSilenceDetection();
            
            // Auto-restart if still supposed to be listening
            if (this.shouldRestart && this.isSupported) {
                console.log('🔄 Auto-restarting recognition...');
                setTimeout(() => {
                    this.startListening(this.isAutoListening);
                }, 100);
            }
        };
        
        // Recognition results - MAIN CONVERSATION HANDLER
        this.recognition.onresult = (event) => {
            this.handleRecognitionResult(event);
        };
        
        // Recognition errors
        this.recognition.onerror = (event) => {
            this.handleRecognitionError(event);
        };
        
        // Speech detection events
        this.recognition.onspeechstart = () => {
            console.log('🗣️ Speech detected');
            this.lastSpeechTime = Date.now();
            
            // Reset hang-up silence timer
            this.total_silence_start = null;
            this.impatience_triggered = false;
        };
        
        this.recognition.onspeechend = () => {
            console.log('🤐 Speech ended');
            this.lastSpeechTime = Date.now();
            
            // Start checking for silence to detect when user finished
            this.startSilenceDetection();
            
            // Restart hang-up silence tracking
            this.total_silence_start = Date.now();
        };
    }

    handleRecognitionResult(event) {
        let interimTranscript = '';
        let finalTranscript = '';
        
        // Process all results
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            
            if (result.isFinal) {
                finalTranscript += transcript + ' ';
                console.log(`✅ Final transcript: "${transcript}"`);
                this.lastSpeechTime = Date.now();
            } else {
                interimTranscript += transcript;
                this.lastSpeechTime = Date.now();
            }
        }
        
        // Update current transcript
        this.currentTranscript = finalTranscript + interimTranscript;
        this.updateTranscript(`🎤 You: "${this.currentTranscript}"`);
        
        // Process final results
        if (finalTranscript.trim().length > 0) {
            this.finalTranscript += finalTranscript;
            this.startSilenceDetection();
        }
    }

    handleRecognitionError(event) {
        console.error('❌ Voice recognition error:', event.error);
        
        const errorMessages = {
            'network': 'Network error. Check internet connection.',
            'not-allowed': 'Microphone access denied. Please allow microphone access.',
            'no-speech': 'No speech detected. Try speaking louder.',
            'aborted': 'Voice recognition aborted.',
            'audio-capture': 'No microphone found. Connect microphone.',
            'service-not-allowed': 'Voice recognition service not allowed.',
        };
        
        const message = errorMessages[event.error] || `Voice recognition error: ${event.error}`;
        this.triggerError(message);
        
        // Handle specific errors
        if (event.error === 'not-allowed') {
            this.handlePermissionDenied();
        } else if (event.error === 'network') {
            setTimeout(() => {
                if (this.shouldRestart) {
                    console.log('🔄 Retrying after network error...');
                    this.startListening(this.isAutoListening);
                }
            }, 2000);
        }
    }

    // ===== PUBLIC METHODS =====

    startAutoListening() {
        console.log('🤖 Starting auto-listening mode...');
        this.startListening(true);
    }

    startListening(isAutoMode = false) {
        if (!this.isSupported || this.isListening) return;
        
        console.log(`🎤 Starting listening - Auto mode: ${isAutoMode}`);
        this.isAutoListening = isAutoMode;
        
        try {
            this.shouldRestart = true;
            this.finalTranscript = '';
            this.currentTranscript = '';
            this.lastSpeechTime = null;
            
            // Request microphone permission if needed
            this.requestMicrophonePermission().then(() => {
                if (this.recognition) {
                    this.recognition.start();
                }
                
                if (isAutoMode) {
                    this.updateTranscript('🎤 Auto-listening active - speak naturally...');
                } else {
                    this.updateTranscript('🎤 Listening - speak when ready...');
                }
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
        
        console.log('🛑 Stopping voice recognition...');
        this.shouldRestart = false;
        this.isAutoListening = false;
        
        if (this.recognition) {
            this.recognition.stop();
        }
        
        this.stopSilenceDetection();
        this.stopHangupSilenceDetection();
    }

    // ===== SILENCE DETECTION =====

    startSilenceDetection() {
        this.stopSilenceDetection();
        
        console.log('🤫 Starting silence detection...');
        
        this.silenceCheckInterval = setInterval(() => {
            if (this.lastSpeechTime) {
                const silenceDuration = Date.now() - this.lastSpeechTime;
                
                if (silenceDuration >= this.silenceThreshold) {
                    console.log(`🤫 User finished speaking (${silenceDuration}ms silence)`);
                    this.processFinalUserSpeech();
                }
            }
        }, 200);
    }

    stopSilenceDetection() {
        if (this.silenceCheckInterval) {
            clearInterval(this.silenceCheckInterval);
            this.silenceCheckInterval = null;
        }
    }

    processFinalUserSpeech() {
        const transcript = this.finalTranscript.trim();
        
        if (transcript.length > 0) {
            console.log(`✅ Processing final speech: "${transcript}"`);
            
            // Stop listening since we're processing
            this.stopListening();
            
            // FIXED: Trigger callback properly
            if (this.onTranscript && typeof this.onTranscript === 'function') {
                this.onTranscript(transcript);
            } else if (this.roleplayManager && this.roleplayManager.handleVoiceInput) {
                this.roleplayManager.handleVoiceInput(transcript);
            } else {
                console.warn('⚠️ No callback available for transcript');
            }
            
            // Clear transcript
            this.finalTranscript = '';
            this.currentTranscript = '';
        }
    }

    // ===== HANG-UP SILENCE DETECTION =====

    startHangupSilenceDetection() {
        this.stopHangupSilenceDetection();
        console.log('⏰ Starting hang-up silence detection');
        
        this.hangupSilenceTimer = setInterval(() => {
            if (this.total_silence_start && this.isListening) {
                const totalSilence = Date.now() - this.total_silence_start;
                
                // 10-second impatience trigger
                if (totalSilence >= this.impatience_threshold && 
                    !this.impatience_triggered &&
                    totalSilence < this.hangup_threshold) {
                    console.log('⏰ 10-second silence - triggering impatience');
                    this.handleImpatience();
                }
                
                // 15-second hang-up trigger
                if (totalSilence >= this.hangup_threshold) {
                    console.log('📞 15-second silence - triggering hang-up');
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
        console.log('⏰ Handling impatience');
        this.impatience_triggered = true;
        
        const phrases = [
            "Hello? Are you still with me?",
            "Can you hear me?",
            "Just checking you're there…",
            "Still on the line?"
        ];
        
        const phrase = phrases[Math.floor(Math.random() * phrases.length)];
        this.updateTranscript(`⏰ Prospect: "${phrase}"`);
        
        // Trigger callback
        if (this.onTranscript && typeof this.onTranscript === 'function') {
            this.onTranscript('[SILENCE_IMPATIENCE]');
        } else if (this.roleplayManager && this.roleplayManager.handleVoiceInput) {
            this.roleplayManager.handleVoiceInput('[SILENCE_IMPATIENCE]');
        }
    }

    handleSilenceHangup() {
        console.log('📞 Handling silence hang-up');
        
        this.stopListening();
        this.updateTranscript('📞 15 seconds of silence - The prospect hung up.');
        
        // Trigger callback
        if (this.onTranscript && typeof this.onTranscript === 'function') {
            this.onTranscript('[SILENCE_HANGUP]');
        } else if (this.roleplayManager && this.roleplayManager.handleVoiceInput) {
            this.roleplayManager.handleVoiceInput('[SILENCE_HANGUP]');
        }
    }

    // ===== UI METHODS =====

    updateMicrophoneUI(isListening) {
        if (this.micButton) {
            if (isListening) {
                this.micButton.classList.add('listening');
                this.micButton.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                this.micButton.title = 'Listening - click to stop';
            } else {
                this.micButton.classList.remove('listening');
                this.micButton.style.background = 'rgba(255, 255, 255, 0.1)';
                this.micButton.title = 'Click to start listening';
            }
        }
    }

    updateTranscript(text) {
        if (this.transcriptElement) {
            this.transcriptElement.textContent = text;
        }
    }

    triggerError(message) {
        console.error('❌ Voice error:', message);
        
        // Use callback if available
        if (this.onError && typeof this.onError === 'function') {
            this.onError(message);
        } else {
            // Fallback to direct UI update
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
        
        if (this.micButton) {
            this.micButton.disabled = true;
            this.micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        }
        
        this.updateTranscript('Microphone permission denied. Please refresh and allow access.');
    }

    pauseListening() {
        if (this.isListening) {
            this.wasPausedBySystem = true;
            this.stopListening();
        }
    }

    resumeListening() {
        if (this.wasPausedBySystem && this.shouldRestart) {
            this.wasPausedBySystem = false;
            this.startListening(this.isAutoListening);
        }
    }

    getListeningStatus() {
        return {
            isListening: this.isListening,
            isAutoListening: this.isAutoListening,
            isSupported: this.isSupported
        };
    }

    destroy() {
        console.log('🧹 Destroying Voice Handler...');
        
        this.stopListening();
        this.shouldRestart = false;
        
        if (this.recognition) {
            this.recognition.onstart = null;
            this.recognition.onend = null;
            this.recognition.onresult = null;
            this.recognition.onerror = null;
            this.recognition = null;
        }
        
        this.stopSilenceDetection();
        this.stopHangupSilenceDetection();
        
        // Remove event listeners
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

console.log('✅ Voice Handler class loaded successfully');