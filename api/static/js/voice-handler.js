// ===== NATURAL CONVERSATION VOICE HANDLER - voice-handler.js =====

class VoiceHandler {
    constructor(roleplayManager) {
        this.roleplayManager = roleplayManager;
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        this.micButton = null;
        this.transcriptElement = null;
        this.errorElement = null;
        
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
        this.isAutoListening = false;  // NEW: Track if auto-listening is active
        this.canInterrupt = false;     // NEW: Track if user can interrupt AI
        
        // Silence detection for natural conversation
        this.silenceThreshold = 2000;  // 2 seconds of silence = user finished speaking
        this.lastSpeechTime = null;
        this.silenceCheckInterval = null;
        
        // Roleplay 1.1 silence specifications (for hang-up detection)
        this.impatience_threshold = 10000;  // 10 seconds for impatience trigger
        this.hangup_threshold = 15000;      // 15 seconds for hang-up
        this.total_silence_start = null;    // Track total silence from start of listening
        this.impatience_triggered = false;
        
        this.shouldRestart = false;
        this.wasPausedBySystem = false;
        
        // Impatience phrases
        this.impatience_phrases = [
            "Hello? Are you still with me?",
            "Can you hear me?",
            "Just checking you're there…",
            "Still on the line?",
            "I don't have much time for this.",
            "Sounds like you are gone.",
            "Are you an idiot.",
            "What is going on.",
            "Are you okay to continue?",
            "I am afraid I have to go"
        ];
        
        this.init();
    }

    init() {
        console.log('🎤 Initializing Natural Conversation Voice Handler...');
        
        this.checkBrowserSupport();
        this.initializeUIElements();
        this.setupEventListeners();
        
        if (this.isSupported) {
            this.initializeSpeechRecognition();
        }
        
        console.log(`✅ Natural Voice Handler initialized. Supported: ${this.isSupported}`);
    }

    checkBrowserSupport() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.isSupported = true;
            this.SpeechRecognition = SpeechRecognition;
            console.log('✅ Web Speech API supported - Natural conversation ready');
        } else {
            this.isSupported = false;
            console.error('❌ Web Speech API not supported');
        }
        
        this.updateSupportUI();
    }

    updateSupportUI() {
        const micButton = document.getElementById('mic-button');
        const errorElement = document.getElementById('voice-error');
        
        if (!this.isSupported) {
            if (micButton) {
                micButton.disabled = true;
                micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                micButton.title = 'Voice recognition not supported';
            }
            
            if (errorElement) {
                this.showVoiceError('Voice recognition not supported. Use Chrome, Edge, or Safari.');
            }
        } else {
            if (micButton) {
                micButton.title = 'Natural conversation mode - Mic auto-activates';
            }
        }
    }

    initializeUIElements() {
        this.micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        this.transcriptElement = document.getElementById('live-transcript');
        this.errorElement = document.getElementById('voice-error');
        
        if (this.transcriptElement) {
            this.transcriptElement.textContent = 'Natural conversation ready...';
        }
    }

    setupEventListeners() {
        // Microphone button - now optional since we have auto-listening
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
            // Space bar to manually trigger mic (even during auto-listening)
            if (e.code === 'Space' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                console.log('⌨️ Space pressed - manual mic trigger');
                if (!this.isListening) {
                    this.startListening(false);
                }
            }
            
            // Escape to stop listening
            if (e.code === 'Escape' && this.isListening) {
                console.log('⌨️ Escape pressed - stop listening');
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
            
            console.log('🎤 Speech recognition initialized for natural conversation');
        } catch (error) {
            console.error('❌ Failed to initialize speech recognition:', error);
            this.showVoiceError('Failed to initialize voice recognition. Check microphone permissions.');
        }
    }

    setupRecognitionEventHandlers() {
        if (!this.recognition) return;
        
        // Recognition starts
        this.recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            this.isListening = true;
            this.updateMicrophoneUI(true);
            this.clearVoiceError();
            
            // Start silence tracking for hang-up detection
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
            
            // Auto-restart if still supposed to be listening
            if (this.shouldRestart && this.isSupported) {
                console.log('🔄 Auto-restarting recognition...');
                setTimeout(() => {
                    this.startListening(this.isAutoListening);
                }, 100);
            }
        };
        
        // Recognition results - THE MAIN CONVERSATION HANDLER
        this.recognition.onresult = (event) => {
            this.handleRecognitionResult(event);
        };
        
        // Recognition errors
        this.recognition.onerror = (event) => {
            this.handleRecognitionError(event);
        };
        
        // Speech detection events
        this.recognition.onspeechstart = () => {
            console.log('🗣️ Speech detected - user is speaking');
            this.lastSpeechTime = Date.now();
            
            // If user interrupts AI, handle it immediately
            if (this.canInterrupt && this.roleplayManager?.aiIsSpeaking) {
                console.log('⚡ User interrupted AI - stopping AI speech');
                this.handleInterruption();
            }
            
            // Reset hang-up silence timer since user is speaking
            this.total_silence_start = null;
            this.impatience_triggered = false;
        };
        
        this.recognition.onspeechend = () => {
            console.log('🤐 Speech ended - checking for completion');
            this.lastSpeechTime = Date.now();
            
            // Start checking for silence to detect when user finished
            this.startSilenceDetection();
            
            // Also restart hang-up silence tracking
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
            const confidence = result[0].confidence;
            
            if (result.isFinal) {
                finalTranscript += transcript + ' ';
                console.log(`✅ Final transcript: "${transcript}" (confidence: ${confidence})`);
                
                // Reset silence detection since we got final speech
                this.lastSpeechTime = Date.now();
            } else {
                interimTranscript += transcript;
                console.log(`💭 Interim: "${transcript}"`);
                
                // Reset silence tracking for interim results too
                this.lastSpeechTime = Date.now();
            }
        }
        
        // Update current transcript
        this.currentTranscript = finalTranscript + interimTranscript;
        this.updateTranscript(`🎤 You: "${this.currentTranscript}"`);
        
        // Process final results
        if (finalTranscript.trim().length > 0) {
            this.finalTranscript += finalTranscript;
            
            // For natural conversation, wait a bit to see if user continues speaking
            // If not, we'll process what we have
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
        this.showVoiceError(message);
        
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

    // ===== NATURAL CONVERSATION METHODS =====

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
                this.recognition.start();
                
                if (isAutoMode) {
                    this.updateTranscript('🎤 Auto-listening active - speak naturally...');
                } else {
                    this.updateTranscript('🎤 Listening - speak when ready...');
                }
            }).catch(error => {
                console.error('❌ Microphone permission failed:', error);
                this.showVoiceError('Microphone permission required for conversation');
            });
            
        } catch (error) {
            console.error('❌ Failed to start listening:', error);
            this.showVoiceError('Failed to start voice recognition');
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
    }

    // Enable/disable interruption capability
    enableInterruption() {
        console.log('⚡ Interruption enabled - user can speak over AI');
        this.canInterrupt = true;
    }

    disableInterruption() {
        console.log('⚡ Interruption disabled');
        this.canInterrupt = false;
    }

    handleInterruption() {
        console.log('⚡ Handling user interruption of AI');
        
        // Tell roleplay manager to stop AI speech
        if (this.roleplayManager) {
            this.roleplayManager.handleUserInterruption();
        }
        
        // Update UI to show user is taking over
        this.updateTranscript('⚡ You interrupted - speak now...');
    }

    // ===== SILENCE DETECTION FOR NATURAL CONVERSATION =====

    startSilenceDetection() {
        this.stopSilenceDetection();
        
        console.log('🤫 Starting silence detection for natural conversation...');
        
        this.silenceCheckInterval = setInterval(() => {
            if (this.lastSpeechTime) {
                const silenceDuration = Date.now() - this.lastSpeechTime;
                
                // If user has been silent for threshold, process their speech
                if (silenceDuration >= this.silenceThreshold) {
                    console.log(`🤫 User finished speaking (${silenceDuration}ms silence)`);
                    this.processFinalUserSpeech();
                }
            }
        }, 200); // Check every 200ms
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
            console.log(`✅ Processing final user speech: "${transcript}"`);
            
            // Stop listening since we're processing
            this.stopListening();
            
            // Send to roleplay manager
            if (this.roleplayManager) {
                this.roleplayManager.processUserInput(transcript);
            }
            
            // Clear transcript
            this.finalTranscript = '';
            this.currentTranscript = '';
        }
    }

    // ===== HANG-UP SILENCE DETECTION (Original Roleplay 1.1 specs) =====

    startHangupSilenceDetection() {
        console.log('⏰ Starting hang-up silence detection (10s impatience, 15s hangup)');
        
        this.hangupSilenceTimer = setInterval(() => {
            if (this.total_silence_start && this.isListening) {
                const totalSilence = Date.now() - this.total_silence_start;
                
                // 10-second impatience trigger
                if (totalSilence >= this.impatience_threshold && 
                    !this.impatience_triggered &&
                    totalSilence < this.hangup_threshold) {
                    console.log('⏰ 10-second total silence - triggering impatience');
                    this.handleImpatience();
                }
                
                // 15-second hang-up trigger
                if (totalSilence >= this.hangup_threshold) {
                    console.log('📞 15-second total silence - triggering hang-up');
                    this.handleSilenceHangup();
                }
            }
        }, 1000);
    }

    handleImpatience() {
        console.log('⏰ Handling 10-second silence impatience');
        this.impatience_triggered = true;
        
        const phrase = this.impatience_phrases[Math.floor(Math.random() * this.impatience_phrases.length)];
        this.updateTranscript(`⏰ 10 seconds of silence... Prospect: "${phrase}"`);
        
        if (this.roleplayManager && this.roleplayManager.isActive) {
            this.roleplayManager.processUserInput('[SILENCE_IMPATIENCE]');
        }
    }

    handleSilenceHangup() {
        console.log('📞 Handling 15-second silence hang-up');
        
        this.stopListening();
        this.updateTranscript('📞 15 seconds of silence - The prospect hung up.');
        
        if (this.roleplayManager && this.roleplayManager.isActive) {
            this.roleplayManager.processUserInput('[SILENCE_HANGUP]');
        }
    }

    // ===== UI METHODS =====

    updateMicrophoneUI(isListening) {
        if (!this.micButton) return;
        
        if (isListening) {
            this.micButton.classList.add('listening');
            this.micButton.classList.remove('btn-primary');
            this.micButton.classList.add('btn-success');
            this.micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            this.micButton.title = this.isAutoListening ? 
                'Auto-listening active (natural conversation)' : 
                'Listening - click to stop';
        } else {
            this.micButton.classList.remove('listening', 'btn-success');
            this.micButton.classList.add('btn-primary');
            this.micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            this.micButton.title = 'Click to start listening manually';
        }
    }

    updateTranscript(text) {
        if (this.transcriptElement) {
            this.transcriptElement.textContent = text;
        }
    }

    showVoiceError(message) {
        console.error('❌ Voice error:', message);
        
        if (this.errorElement) {
            const errorText = this.errorElement.querySelector('#voice-error-text');
            if (errorText) {
                errorText.textContent = message;
            }
            this.errorElement.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                this.errorElement.style.display = 'none';
            }, 5000);
        }
    }

    clearVoiceError() {
        if (this.errorElement) {
            this.errorElement.style.display = 'none';
        }
    }

    // ===== UTILITY METHODS =====

    async requestMicrophonePermission() {
        try {
            console.log('🎤 Requesting microphone permission...');
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            console.log('✅ Microphone permission granted');
            return true;
        } catch (error) {
            console.error('❌ Microphone permission denied:', error);
            throw new Error('Microphone permission denied');
        }
    }

    handlePermissionDenied() {
        console.error('❌ Microphone permission permanently denied');
        this.stopListening();
        this.shouldRestart = false;
        
        if (this.micButton) {
            this.micButton.disabled = true;
            this.micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        }
        
        this.showPermissionInstructions();
    }

    showPermissionInstructions() {
        const instructions = `
            <div class="permission-instructions">
                <h6>Microphone Permission Required</h6>
                <p>For natural conversation:</p>
                <ol>
                    <li>Click the microphone icon in your browser's address bar</li>
                    <li>Select "Allow" for microphone access</li>
                    <li>Refresh this page and try again</li>
                </ol>
                <button class="btn btn-primary btn-sm" onclick="location.reload()">
                    <i class="fas fa-refresh me-1"></i>Refresh Page
                </button>
            </div>
        `;
        
        if (this.transcriptElement) {
            this.transcriptElement.innerHTML = instructions;
        }
    }

    pauseListening() {
        if (this.isListening) {
            console.log('⏸️ Pausing voice recognition...');
            this.wasPausedBySystem = true;
            this.stopListening();
        }
    }

    resumeListening() {
        if (this.wasPausedBySystem && this.shouldRestart) {
            console.log('▶️ Resuming voice recognition...');
            this.wasPausedBySystem = false;
            this.startListening(this.isAutoListening);
        }
    }

    // ===== GETTERS =====

    getListeningStatus() {
        return {
            isListening: this.isListening,
            isAutoListening: this.isAutoListening,
            canInterrupt: this.canInterrupt,
            isSupported: this.isSupported
        };
    }

    // ===== CLEANUP =====

    destroy() {
        console.log('🧹 Destroying Natural Voice Handler...');
        
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
        
        // Remove event listeners
        if (this.handleKeydown) {
            document.removeEventListener('keydown', this.handleKeydown);
        }
        if (this.handleVisibilityChange) {
            document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        }
        
        console.log('✅ Natural Voice Handler destroyed');
    }
}

// Export for global access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceHandler;
} else {
    window.VoiceHandler = VoiceHandler;
}

console.log('✅ Natural Conversation Voice Handler loaded successfully');