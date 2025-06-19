// ===== UPDATED STATIC/JS/VOICE-HANDLER.JS - ROLEPLAY 1.1 COMPLIANT =====

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
        
        // State management
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.silenceTimer = null;
        
        // ===== ROLEPLAY 1.1 SILENCE SPECIFICATIONS =====
        this.impatience_threshold = 10000;  // 10 seconds for impatience trigger
        this.hangup_threshold = 15000;      // 15 seconds for hang-up
        this.current_silence_time = 0;      // Track current silence duration
        this.silence_start_time = null;     // When silence started
        this.impatience_triggered = false;  // Prevent multiple impatience triggers
        
        this.shouldRestart = false;
        this.wasPausedBySystem = false;
        
        // Impatience phrases from specifications
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
        console.log('Initializing Voice Handler for Roleplay 1.1...');
        
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
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.isSupported = true;
            this.SpeechRecognition = SpeechRecognition;
            console.log('Web Speech API supported - Roleplay 1.1 ready');
        } else {
            this.isSupported = false;
            console.error('Web Speech API not supported - Roleplay 1.1 disabled');
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
                micButton.title = 'Voice recognition not supported - use Chrome/Edge/Safari';
            }
            
            if (errorElement) {
                this.showVoiceError('Voice recognition not supported. Use Chrome, Edge, or Safari for Roleplay 1.1.');
            }
        } else {
            if (micButton) {
                micButton.title = 'Hold to speak (Space key) - Roleplay 1.1 Active';
            }
        }
    }

    initializeUIElements() {
        this.micButton = document.getElementById('mic-button');
        this.transcriptElement = document.getElementById('live-transcript');
        this.errorElement = document.getElementById('voice-error');
        
        if (this.transcriptElement) {
            this.transcriptElement.textContent = 'Roleplay 1.1 ready - Hold microphone to speak...';
        }
    }

    setupEventListeners() {
        // Microphone button events
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                console.log('Microphone button clicked - Roleplay 1.1');
                this.toggleListening();
            });
        }
        
        // Keyboard shortcuts for Roleplay 1.1
        this.handleKeydown = (e) => {
            if (e.ctrlKey && e.code === 'Space') {
                e.preventDefault();
                console.log('Ctrl+Space - toggle mic for Roleplay 1.1');
                this.toggleListening();
            }
            
            if (e.code === 'Escape' && this.isListening) {
                console.log('Escape - stop listening');
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
        
        // Window focus/blur handlers
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
            
            // Configure recognition settings for Roleplay 1.1
            this.recognition.continuous = this.settings.continuous;
            this.recognition.interimResults = this.settings.interimResults;
            this.recognition.lang = this.settings.language;
            this.recognition.maxAlternatives = this.settings.maxAlternatives;
            
            // Set up event handlers
            this.setupRecognitionEventHandlers();
            
            console.log('Speech recognition initialized for Roleplay 1.1 with settings:', this.settings);
        } catch (error) {
            console.error('Failed to initialize speech recognition:', error);
            this.showVoiceError('Failed to initialize voice recognition. Check microphone permissions.');
        }
    }

    setupRecognitionEventHandlers() {
        if (!this.recognition) return;
        
        // Recognition starts
        this.recognition.onstart = () => {
            console.log('Voice recognition started - Roleplay 1.1 active');
            this.isListening = true;
            this.updateMicrophoneUI(true);
            this.clearVoiceError();
            this.startSilenceDetection();
        };
        
        // Recognition ends
        this.recognition.onend = () => {
            console.log('Voice recognition ended');
            this.isListening = false;
            this.updateMicrophoneUI(false);
            this.stopSilenceDetection();
            
            // Auto-restart if still supposed to be listening
            if (this.shouldRestart && this.isSupported) {
                console.log('Auto-restarting recognition...');
                setTimeout(() => {
                    this.startListening();
                }, 100);
            }
        };
        
        // Recognition results
        this.recognition.onresult = (event) => {
            this.handleRecognitionResult(event);
        };
        
        // Recognition errors
        this.recognition.onerror = (event) => {
            this.handleRecognitionError(event);
        };
        
        // No speech detected
        this.recognition.onnomatch = () => {
            console.log('No speech recognized in Roleplay 1.1');
            this.updateTranscript('No speech detected. Please try speaking again.');
        };
        
        // Audio starts
        this.recognition.onaudiostart = () => {
            console.log('Audio input started - Roleplay 1.1');
        };
        
        // Audio ends
        this.recognition.onaudioend = () => {
            console.log('Audio input ended - Roleplay 1.1');
        };
        
        // Speech starts - RESET silence timer when speech detected
        this.recognition.onspeechstart = () => {
            console.log('Speech detected - resetting silence timer for Roleplay 1.1');
            this.resetSilenceTimer();
        };
        
        // Speech ends - START silence timer when speech stops
        this.recognition.onspeechend = () => {
            console.log('Speech ended - starting silence detection for Roleplay 1.1');
            this.silence_start_time = Date.now();
            this.impatience_triggered = false; // Reset for new silence period
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
                console.log(`Final transcript received (confidence: ${confidence}):`, transcript);
                
                // Log low-confidence words for pronunciation coaching
                if (confidence < 0.70) {
                    this.logPronunciationIssue(transcript, confidence);
                }
                
                // Reset silence detection when we get final transcript
                this.resetSilenceTimer();
            } else {
                interimTranscript += transcript;
                console.log('Interim transcript:', transcript);
                
                // Reset silence detection even for interim results
                if (transcript.trim().length > 0) {
                    this.silence_start_time = Date.now();
                    this.impatience_triggered = false;
                }
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
    }

    logPronunciationIssue(word, confidence) {
        console.log(`Pronunciation logged for coaching: "${word}" (confidence: ${confidence})`);
        
        // Store for coaching feedback
        if (!window.pronunciationIssues) {
            window.pronunciationIssues = [];
        }
        
        window.pronunciationIssues.push({
            word: word,
            confidence: confidence,
            timestamp: new Date().toISOString()
        });
    }

    handleRecognitionError(event) {
        console.error('Voice recognition error:', event.error);
        
        const errorMessages = {
            'network': 'Network error. Check internet connection.',
            'not-allowed': 'Microphone access denied. Allow microphone for Roleplay 1.1.',
            'no-speech': 'No speech detected. Try speaking louder.',
            'aborted': 'Voice recognition aborted.',
            'audio-capture': 'No microphone found. Connect microphone for Roleplay 1.1.',
            'service-not-allowed': 'Voice recognition service not allowed.',
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
                setTimeout(() => {
                    if (this.shouldRestart) {
                        console.log('Retrying after network error...');
                        this.startListening();
                    }
                }, 2000);
                break;
            case 'no-speech':
                this.clearVoiceError();
                break;
        }
    }

    handlePermissionDenied() {
        console.error('Microphone permission denied - Roleplay 1.1 disabled');
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
                <h6>Microphone Permission Required for Roleplay 1.1</h6>
                <p>To use voice training with Roleplay 1.1:</p>
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

    // ===== ROLEPLAY 1.1 SILENCE DETECTION =====
    
    startSilenceDetection() {
        console.log('Starting Roleplay 1.1 silence detection (10s impatience, 15s hang-up)');
        this.silence_start_time = Date.now();
        this.current_silence_time = 0;
        this.impatience_triggered = false;
        this.resetSilenceTimer();
    }

    stopSilenceDetection() {
        console.log('Stopping Roleplay 1.1 silence detection');
        if (this.silenceTimer) {
            clearInterval(this.silenceTimer);
            this.silenceTimer = null;
        }
        this.silence_start_time = null;
        this.current_silence_time = 0;
        this.impatience_triggered = false;
    }

    resetSilenceTimer() {
        this.stopSilenceDetection();
        this.startSilenceTimer();
    }

    startSilenceTimer() {
        // Check every second for silence thresholds
        this.silenceTimer = setInterval(() => {
            if (this.silence_start_time && this.isListening) {
                this.current_silence_time = Date.now() - this.silence_start_time;
                
                // 10-second impatience trigger (only once per silence period)
                if (this.current_silence_time >= this.impatience_threshold && 
                    !this.impatience_triggered &&
                    this.current_silence_time < this.hangup_threshold) {
                    console.log('10-second silence - triggering impatience phrase');
                    this.handleImpatience();
                }
                
                // 15-second hang-up trigger
                if (this.current_silence_time >= this.hangup_threshold) {
                    console.log('15-second silence - triggering hang-up');
                    this.handleSilenceHangup();
                }
            }
        }, 1000);
    }

    handleImpatience() {
        console.log('Handling 10-second silence - sending impatience trigger');
        this.impatience_triggered = true;
        
        // Select random impatience phrase
        const phrase = this.impatience_phrases[Math.floor(Math.random() * this.impatience_phrases.length)];
        
        // Update transcript to show impatience
        this.updateTranscript(`⏰ 10 seconds of silence... Prospect: "${phrase}"`);
        
        // Send impatience trigger to roleplay manager
        if (this.roleplayManager && this.roleplayManager.isActive) {
            this.roleplayManager.processUserInput('[SILENCE_IMPATIENCE]');
        }
    }

    handleSilenceHangup() {
        console.log('Handling 15-second silence - triggering hang-up');
        
        // Stop listening immediately
        this.stopListening();
        
        // Update transcript
        this.updateTranscript('📞 15 seconds of silence - The prospect hung up.');
        
        // Send hang-up trigger to roleplay manager
        if (this.roleplayManager && this.roleplayManager.isActive) {
            this.roleplayManager.processUserInput('[SILENCE_HANGUP]');
        }
    }

    // ===== MAIN CONTROL METHODS =====

    async toggleListening() {
        console.log('Toggling listening for Roleplay 1.1, current state:', this.isListening);
        
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
            console.log('Starting voice recognition for Roleplay 1.1...');
            
            // Request microphone permission if needed
            await this.requestMicrophonePermission();
            
            this.shouldRestart = true;
            this.finalTranscript = '';
            this.currentTranscript = '';
            
            // Start recognition
            this.recognition.start();
            
        } catch (error) {
            console.error('Failed to start voice recognition:', error);
            this.showVoiceError('Failed to start voice recognition. Check microphone.');
        }
    }

    stopListening() {
        if (!this.isListening) {
            console.log('Not listening, nothing to stop');
            return;
        }
        
        console.log('Stopping voice recognition for Roleplay 1.1...');
        this.shouldRestart = false;
        
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
            console.log('Requesting microphone permission for Roleplay 1.1...');
            
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            
            console.log('Microphone permission granted for Roleplay 1.1');
            return true;
        } catch (error) {
            console.error('Microphone permission denied:', error);
            throw new Error('Microphone permission denied');
        }
    }

    // ===== UI UPDATE METHODS =====

    updateMicrophoneUI(isListening) {
        if (!this.micButton) return;
        
        if (isListening) {
            this.micButton.classList.add('listening', 'btn-danger');
            this.micButton.classList.remove('btn-primary');
            this.micButton.innerHTML = '<i class="fas fa-stop"></i>';
            this.micButton.title = 'Stop listening (Ctrl+Space) | Roleplay 1.1: 10s=impatience, 15s=hangup';
        } else {
            this.micButton.classList.remove('listening', 'btn-danger');
            this.micButton.classList.add('btn-primary');
            this.micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            this.micButton.title = 'Start listening (Ctrl+Space) | Roleplay 1.1 Ready';
        }
    }

    updateTranscript(text) {
        if (this.transcriptElement) {
            // Add silence indicator if tracking silence
            let displayText = text;
            
            if (this.silence_start_time && this.isListening) {
                const silenceSeconds = Math.floor(this.current_silence_time / 1000);
                if (silenceSeconds >= 3) {
                    displayText += ` ⏱️ (${silenceSeconds}s silence)`;
                    if (silenceSeconds >= 8) {
                        displayText += ` - Impatience coming...`;
                    }
                }
            }
            
            this.transcriptElement.textContent = displayText;
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

    // ===== ROLEPLAY MANAGER INTEGRATION =====

    processFinalTranscript(transcript) {
        console.log('Processing final transcript for Roleplay 1.1:', transcript);
        
        // Stop silence detection since we have a complete response
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

    // ===== UTILITY METHODS =====

    getSilenceStatus() {
        return {
            isListening: this.isListening,
            silenceStartTime: this.silence_start_time,
            currentSilenceTime: this.current_silence_time,
            impatience_threshold: this.impatience_threshold,
            hangup_threshold: this.hangup_threshold,
            silenceSeconds: this.silence_start_time ? Math.floor(this.current_silence_time / 1000) : 0,
            impatience_triggered: this.impatience_triggered,
            roleplay_version: '1.1'
        };
    }

    setLanguage(language) {
        this.settings.language = language;
        if (this.recognition) {
            this.recognition.lang = language;
        }
    }

    setSilenceThreshold(milliseconds) {
        this.silenceThreshold = milliseconds;
    }

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

    // ===== CLEANUP =====

    destroy() {
        console.log('Destroying Voice Handler for Roleplay 1.1...');
        
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
        
        console.log('Voice Handler for Roleplay 1.1 destroyed');
    }
}

// Enhanced CSS for Roleplay 1.1
const roleplay11Style = document.createElement('style');
roleplay11Style.textContent = `
    .pulse-animation {
        animation: pulse 1.5s infinite !important;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .mic-button.listening {
        position: relative;
        animation: listening-glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes listening-glow {
        from { box-shadow: 0 0 5px rgba(220, 53, 69, 0.5); }
        to { box-shadow: 0 0 20px rgba(220, 53, 69, 0.8), 0 0 30px rgba(220, 53, 69, 0.6); }
    }
    
    .silence-indicator {
        font-family: monospace;
        color: #ffc107;
        font-weight: bold;
    }
    
    .roleplay-11-active {
        border: 2px solid #22c55e;
        border-radius: 10px;
        padding: 10px;
        background: rgba(34, 197, 94, 0.1);
    }
    
    .impatience-warning {
        color: #f59e0b !important;
        font-weight: bold;
        animation: warning-pulse 1s infinite;
    }
    
    @keyframes warning-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .hangup-warning {
        color: #ef4444 !important;
        font-weight: bold;
        animation: critical-pulse 0.5s infinite;
    }
    
    @keyframes critical-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
`;
document.head.appendChild(roleplay11Style);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceHandler;
} else {
    window.VoiceHandler = VoiceHandler;
}

console.log('Roleplay 1.1 Voice Handler loaded successfully');