// ===== COMPLETE FIXED STATIC/JS/VOICE-HANDLER.JS =====

class VoiceHandler {
    constructor(roleplayManager) {
        this.roleplayManager = roleplayManager;
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        this.micButton = null;
        this.transcriptElement = null;
        this.errorElement = null;
        
        // Voice recognition settings
        this.settings = {
            continuous: true,
            interimResults: true,
            language: 'en-US',
            maxAlternatives: 1
        };
        
        // State management - FIXED
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.silenceTimer = null;
        this.silenceThreshold = 4000; // Increased to 4 seconds
        this.shouldRestart = false;
        this.wasPausedBySystem = false;
        this.silenceTimeoutSent = false; // NEW: Prevent spam
        this.lastSpeechTime = 0; // NEW: Track when speech last occurred
        
        this.init();
    }

    init() {
        console.log('Initializing Voice Handler...');
        
        // Check browser support
        this.checkBrowserSupport();
        
        // Initialize UI elements
        this.initializeUIElements();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize speech recognition if supported
        if (this.isSupported) {
            this.initializeSpeechRecognition();
        }
        
        console.log(`Voice Handler initialized. Supported: ${this.isSupported}`);
    }

    checkBrowserSupport() {
        // Check for Web Speech API support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.isSupported = true;
            this.SpeechRecognition = SpeechRecognition;
            console.log('Web Speech API supported');
        } else {
            this.isSupported = false;
            console.error('Web Speech API not supported in this browser');
        }
        
        // Update UI based on support
        this.updateSupportUI();
    }

    updateSupportUI() {
        const micButton = document.getElementById('mic-button');
        const errorElement = document.getElementById('voice-error');
        
        if (!this.isSupported) {
            if (micButton) {
                micButton.disabled = true;
                micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                micButton.title = 'Voice recognition not supported in this browser';
            }
            
            if (errorElement) {
                this.showVoiceError('Voice recognition is not supported in this browser. Please use Chrome, Edge, or Safari for the best experience.');
            }
        } else {
            if (micButton) {
                micButton.title = 'Click to start/stop voice recognition (Ctrl+Space)';
            }
        }
    }

    initializeUIElements() {
        this.micButton = document.getElementById('mic-button');
        this.transcriptElement = document.getElementById('live-transcript');
        this.errorElement = document.getElementById('voice-error');
        
        // Initialize transcript display
        if (this.transcriptElement) {
            this.transcriptElement.textContent = 'Click the microphone to start speaking...';
        }
    }

    setupEventListeners() {
        // Microphone button click
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                console.log('Microphone button clicked');
                this.toggleListening();
            });
        }
        
        // Keyboard shortcuts
        this.handleKeydown = (e) => {
            // Ctrl + Space to toggle microphone
            if (e.ctrlKey && e.code === 'Space') {
                e.preventDefault();
                console.log('Ctrl+Space pressed');
                this.toggleListening();
            }
            
            // Escape to stop listening
            if (e.code === 'Escape' && this.isListening) {
                console.log('Escape pressed - stopping listening');
                this.stopListening();
            }
        };
        
        document.addEventListener('keydown', this.handleKeydown);
        
        // Handle page visibility changes
        this.handleVisibilityChange = () => {
            if (document.hidden && this.isListening) {
                console.log('Page hidden - pausing recognition');
                this.pauseListening();
            } else if (!document.hidden && this.recognition) {
                console.log('Page visible - resuming recognition');
                this.resumeListening();
            }
        };
        
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Handle window focus/blur
        this.handleWindowBlur = () => {
            if (this.isListening) {
                console.log('Window blurred - pausing recognition');
                this.pauseListening();
            }
        };
        
        this.handleWindowFocus = () => {
            console.log('Window focused - resuming recognition');
            this.resumeListening();
        };
        
        window.addEventListener('blur', this.handleWindowBlur);
        window.addEventListener('focus', this.handleWindowFocus);
    }

    initializeSpeechRecognition() {
        if (!this.isSupported) return;
        
        try {
            this.recognition = new this.SpeechRecognition();
            
            // Configure recognition settings
            this.recognition.continuous = this.settings.continuous;
            this.recognition.interimResults = this.settings.interimResults;
            this.recognition.lang = this.settings.language;
            this.recognition.maxAlternatives = this.settings.maxAlternatives;
            
            // Set up event handlers
            this.setupRecognitionEventHandlers();
            
            console.log('Speech recognition initialized with settings:', this.settings);
        } catch (error) {
            console.error('Failed to initialize speech recognition:', error);
            this.showVoiceError('Failed to initialize voice recognition. Please check your microphone permissions.');
        }
    }

    setupRecognitionEventHandlers() {
        if (!this.recognition) return;
        
        // Recognition starts
        this.recognition.onstart = () => {
            console.log('Voice recognition started');
            this.isListening = true;
            this.updateMicrophoneUI(true);
            this.clearVoiceError();
            this.silenceTimeoutSent = false; // Reset timeout flag
            this.lastSpeechTime = Date.now();
            this.startSilenceDetection();
        };
        
        // Speech starts - FIXED
        this.recognition.onspeechstart = () => {
            console.log('Speech detected');
            this.resetSilenceTimer();
            this.silenceTimeoutSent = false; // Reset when speech starts
        };
        
        // Speech ends - FIXED
        this.recognition.onspeechend = () => {
            console.log('Speech ended');
            this.lastSpeechTime = Date.now();
            this.startSilenceTimer();
        };

        // Recognition results - FIXED
        this.recognition.onresult = (event) => {
            this.handleRecognitionResult(event);
            
            // Reset silence tracking when we get results
            this.silenceTimeoutSent = false;
            this.lastSpeechTime = Date.now();
        };
        
        // Recognition errors
        this.recognition.onerror = (event) => {
            this.handleRecognitionError(event);
        };
        
        // No speech detected
        this.recognition.onnomatch = () => {
            console.log('No speech was recognized');
            this.updateTranscript('No speech detected. Please try speaking again.');
        };
        
        // Audio starts
        this.recognition.onaudiostart = () => {
            console.log('Audio input started');
        };
        
        // Audio ends
        this.recognition.onaudioend = () => {
            console.log('Audio input ended');
        };
        
        // Speech starts
        this.recognition.onspeechstart = () => {
            console.log('Speech detected');
            this.resetSilenceTimer();
        };
        
        // Speech ends
        this.recognition.onspeechend = () => {
            console.log('Speech ended');
            this.startSilenceTimer();
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
                console.log('Final transcript received:', transcript);
            } else {
                interimTranscript += transcript;
                console.log('Interim transcript:', transcript);
            }
        }
        
        // Update current transcript
        this.currentTranscript = finalTranscript + interimTranscript;
        
        // Update UI
        this.updateTranscript(this.currentTranscript);
        
        // Process final results
        if (finalTranscript.trim().length > 0) {
            this.finalTranscript += finalTranscript;
            this.processFinalTranscript(finalTranscript.trim());
        }
        
        // Reset silence timer when speech is detected
        this.resetSilenceTimer();
    }

    handleRecognitionError(event) {
        console.error('Voice recognition error:', event.error);
        
        const errorMessages = {
            'network': 'Network error. Please check your internet connection.',
            'not-allowed': 'Microphone access denied. Please allow microphone permissions and try again.',
            'no-speech': 'No speech detected. Please try speaking again.',
            'aborted': 'Voice recognition was aborted.',
            'audio-capture': 'No microphone found. Please connect a microphone and try again.',
            'service-not-allowed': 'Voice recognition service is not allowed.',
            'bad-grammar': 'Grammar error in speech recognition.',
            'language-not-supported': 'Language not supported.'
        };
        
        const message = errorMessages[event.error] || `Voice recognition error: ${event.error}`;
        this.showVoiceError(message);
        
        // Handle specific errors
        switch (event.error) {
            case 'not-allowed':
                this.handlePermissionDenied();
                break;
            case 'network':
                // Retry after a delay
                setTimeout(() => {
                    if (this.shouldRestart) {
                        console.log('Retrying after network error...');
                        this.startListening();
                    }
                }, 2000);
                break;
            case 'no-speech':
                // Don't show error for no speech, just continue
                this.clearVoiceError();
                break;
        }
    }

    handlePermissionDenied() {
        console.error('Microphone permission denied');
        this.stopListening();
        this.shouldRestart = false;
        
        if (this.micButton) {
            this.micButton.disabled = true;
            this.micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        }
        
        // Show permission instructions
        this.showPermissionInstructions();
    }

    showPermissionInstructions() {
        const instructions = `
            <div class="permission-instructions">
                <h6>Microphone Permission Required</h6>
                <p>To use voice training, please:</p>
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

    processFinalTranscript(transcript) {
        console.log('Processing final transcript:', transcript);
        
        // Clear timeout state since we have actual input
        this.silenceTimeoutSent = false;
        this.stopSilenceDetection();
        
        // Send to roleplay manager if available and active
        if (this.roleplayManager && this.roleplayManager.isActive) {
            console.log('Sending transcript to roleplay manager:', transcript);
            this.roleplayManager.processUserInput(transcript);
        } else {
            console.log('Roleplay manager not active, ignoring transcript');
        }
        
        // Clear the current transcript after processing
        this.currentTranscript = '';
        setTimeout(() => {
            this.updateTranscript('Listening for your response...');
        }, 1000);
    }


    // Silence detection methods
    startSilenceDetection() {
        this.resetSilenceTimer();
    }

    stopSilenceDetection() {
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
    }

    resetSilenceTimer() {
        this.stopSilenceDetection();
        this.startSilenceTimer();
        
        // Reset timeout flag when there's activity
        this.silenceTimeoutSent = false;
        this.lastSpeechTime = Date.now();
    }

    startSilenceTimer() {
        this.silenceTimer = setTimeout(() => {
            if (this.isListening) {
                console.log('Silence timeout reached');
                this.handleSilenceTimeout();
            }
        }, this.silenceThreshold);
    }

    handleSilenceTimeout() {
        console.log('Handling silence timeout');
        
        // Only send timeout once per listening session
        if (this.silenceTimeoutSent) {
            console.log('Silence timeout already sent for this session');
            return;
        }
        
        // Only trigger if we haven't had speech for a while
        const timeSinceLastSpeech = Date.now() - this.lastSpeechTime;
        if (timeSinceLastSpeech < this.silenceThreshold) {
            console.log('Speech detected recently, skipping timeout');
            return;
        }
        
        // Show a prompt to encourage speaking
        this.updateTranscript('Still listening... Please continue speaking or click the microphone to stop.');
        
        // Mark that we've sent a timeout for this session
        this.silenceTimeoutSent = true;
        
        // Send SILENCE_TIMEOUT to roleplay manager only if appropriate
        if (this.roleplayManager && this.roleplayManager.isActive && this.currentTranscript.trim() === '') {
            console.log('Sending silence timeout to roleplay manager');
            
            // Only send timeout after significant silence and if we haven't already
            setTimeout(() => {
                if (this.isListening && this.currentTranscript.trim() === '' && this.silenceTimeoutSent) {
                    this.roleplayManager.processUserInput('[SILENCE_TIMEOUT]');
                }
            }, 1000);
        }
    }

    // Main control methods
    async toggleListening() {
        console.log('Toggling listening, current state:', this.isListening);
        
        if (this.isListening) {
            this.stopListening();
        } else {
            await this.startListening();
        }
    }

    async startListening() {
        if (!this.isSupported || this.isListening) {
            console.log('Cannot start listening - not supported or already listening');
            return;
        }
        
        try {
            console.log('Starting voice recognition...');
            
            // Request microphone permission if needed
            await this.requestMicrophonePermission();
            
            this.shouldRestart = true;
            this.finalTranscript = '';
            this.currentTranscript = '';
            
            // Start recognition
            this.recognition.start();
            
        } catch (error) {
            console.error('Failed to start voice recognition:', error);
            this.showVoiceError('Failed to start voice recognition. Please check your microphone.');
        }
    }

    stopListening() {
        if (!this.isListening) {
            console.log('Not listening, nothing to stop');
            return;
        }
        
        console.log('Stopping voice recognition...');
        this.shouldRestart = false;
        this.silenceTimeoutSent = false; // Reset timeout state
        
        if (this.recognition) {
            this.recognition.stop();
        }
        
        this.stopSilenceDetection();
        this.updateTranscript('Voice recognition stopped.');
    }
    pauseListening() {
        if (this.isListening) {
            console.log('Pausing voice recognition...');
            this.wasPausedBySystem = true;
            this.stopListening();
        }
    }

    resumeListening() {
        if (this.wasPausedBySystem && this.shouldRestart) {
            console.log('Resuming voice recognition...');
            this.wasPausedBySystem = false;
            this.startListening();
        }
    }

    async requestMicrophonePermission() {
        try {
            console.log('Requesting microphone permission...');
            
            // Use getUserMedia to request permission
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Immediately stop the stream since we just needed permission
            stream.getTracks().forEach(track => track.stop());
            
            console.log('Microphone permission granted');
            return true;
        } catch (error) {
            console.error('Microphone permission denied:', error);
            throw new Error('Microphone permission denied');
        }
    }

    // UI update methods
    updateMicrophoneUI(isListening) {
        if (!this.micButton) return;
        
        if (isListening) {
            this.micButton.classList.add('listening', 'btn-danger');
            this.micButton.classList.remove('btn-primary');
            this.micButton.innerHTML = '<i class="fas fa-stop"></i>';
            this.micButton.title = 'Click to stop listening (Ctrl+Space)';
        } else {
            this.micButton.classList.remove('listening', 'btn-danger');
            this.micButton.classList.add('btn-primary');
            this.micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            this.micButton.title = 'Click to start listening (Ctrl+Space)';
        }
    }

    updateTranscript(text) {
        if (this.transcriptElement) {
            this.transcriptElement.textContent = text;
        }
    }

    showVoiceError(message) {
        console.error('Voice error:', message);
        
        if (this.errorElement) {
            const errorText = this.errorElement.querySelector('#voice-error-text');
            if (errorText) {
                errorText.textContent = message;
            }
            this.errorElement.style.display = 'block';
        }
    }

    clearVoiceError() {
        if (this.errorElement) {
            this.errorElement.style.display = 'none';
        }
    }

    // Configuration methods
    setLanguage(language) {
        this.settings.language = language;
        if (this.recognition) {
            this.recognition.lang = language;
        }
    }

    setSilenceThreshold(milliseconds) {
        this.silenceThreshold = milliseconds;
    }

    // Utility methods
    isRecognitionSupported() {
        return this.isSupported;
    }

    getCurrentTranscript() {
        return this.currentTranscript;
    }

    getFinalTranscript() {
        return this.finalTranscript;
    }

    getListeningStatus() {
        return this.isListening;
    }

    // Cleanup method
    destroy() {
        console.log('Destroying Voice Handler...');
        
        this.stopListening();
        this.shouldRestart = false;
        
        if (this.recognition) {
            this.recognition.onstart = null;
            this.recognition.onend = null;
            this.recognition.onresult = null;
            this.recognition.onerror = null;
            this.recognition.onnomatch = null;
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
        if (this.handleWindowBlur) {
            window.removeEventListener('blur', this.handleWindowBlur);
        }
        if (this.handleWindowFocus) {
            window.removeEventListener('focus', this.handleWindowFocus);
        }
        
        console.log('Voice Handler destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceHandler;
} else {
    window.VoiceHandler = VoiceHandler;
}