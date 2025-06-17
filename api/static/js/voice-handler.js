// ===== STATIC/JS/VOICE-HANDLER.JS =====

class VoiceHandler {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isRecording = false;
        this.silenceTimer = null;
        this.warningTimer = null;
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.isProcessingResponse = false;
        
        // Voice settings
        this.maxSilenceTime = 15000; // 15 seconds total silence = hang up
        this.warningTime = 10000;    // 10 seconds = warning
        
        // Audio elements
        this.audioElement = null;
        this.audioQueue = [];
        this.isPlayingAudio = false;
        
        // UI elements
        this.micButton = null;
        this.transcriptDisplay = null;
        this.aiStatusDisplay = null;
        this.voiceErrorDisplay = null;
        
        // Event callbacks
        this.onVoiceInput = null;
        this.onSilenceWarning = null;
        this.onSilenceTimeout = null;
        this.onVoiceError = null;
        
        this.initializeVoiceRecognition();
        this.setupKeyboardShortcuts();
    }

    initializeVoiceRecognition() {
        try {
            // Check for Web Speech API support
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                throw new Error('Web Speech API not supported in this browser');
            }

            // Initialize speech recognition
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            // Configure recognition settings
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            this.recognition.maxAlternatives = 1;
            
            // Set up event listeners
            this.recognition.onstart = () => {
                console.log('Voice recognition started');
                this.isListening = true;
                this.updateMicrophoneUI(true);
                this.updateAIStatus('Listening...');
                this.startSilenceTimer();
            };

            this.recognition.onresult = (event) => {
                this.handleSpeechResult(event);
            };

            this.recognition.onerror = (event) => {
                this.handleSpeechError(event);
            };

            this.recognition.onend = () => {
                console.log('Voice recognition ended');
                this.isListening = false;
                this.updateMicrophoneUI(false);
                this.clearSilenceTimer();
                
                // Auto-restart if we should still be listening
                if (this.isRecording && !this.isProcessingResponse) {
                    setTimeout(() => this.startListening(), 100);
                }
            };

            console.log('Voice recognition initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize voice recognition:', error);
            this.showVoiceError('Voice recognition not supported in this browser. Please use Chrome, Edge, or Safari.');
        }
    }

    setupKeyboardShortcuts() {
        // Ctrl/Cmd + Space to toggle microphone
        document.addEventListener('keydown', (event) => {
            if ((event.ctrlKey || event.metaKey) && event.code === 'Space') {
                event.preventDefault();
                this.toggleMicrophone();
            }
        });
    }

    initializeUI(micButtonId, transcriptId, aiStatusId, voiceErrorId) {
        this.micButton = document.getElementById(micButtonId);
        this.transcriptDisplay = document.getElementById(transcriptId);
        this.aiStatusDisplay = document.getElementById(aiStatusId);
        this.voiceErrorDisplay = document.getElementById(voiceErrorId);

        if (this.micButton) {
            this.micButton.addEventListener('click', () => this.toggleMicrophone());
        }

        // Initialize audio element for TTS playback
        this.audioElement = new Audio();
        this.audioElement.addEventListener('ended', () => this.playNextAudio());
        this.audioElement.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            this.playNextAudio(); // Try next audio in queue
        });
    }

    startListening() {
        if (!this.recognition) {
            this.showVoiceError('Voice recognition not available');
            return false;
        }

        if (this.isListening) {
            console.log('Already listening');
            return false;
        }

        try {
            this.isRecording = true;
            this.clearTranscript();
            this.hideVoiceError();
            this.recognition.start();
            return true;
        } catch (error) {
            console.error('Error starting voice recognition:', error);
            this.showVoiceError('Failed to start voice recognition');
            return false;
        }
    }

    stopListening() {
        if (!this.isListening) {
            return;
        }

        try {
            this.isRecording = false;
            this.recognition.stop();
            this.clearSilenceTimer();
            this.updateAIStatus('Processing...');
        } catch (error) {
            console.error('Error stopping voice recognition:', error);
        }
    }

    toggleMicrophone() {
        if (this.isRecording) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    handleSpeechResult(event) {
        let interimTranscript = '';
        let finalTranscript = '';

        // Process recognition results
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        // Update current transcript
        this.currentTranscript = finalTranscript;
        
        // Update UI
        this.updateTranscriptDisplay(finalTranscript, interimTranscript);

        // Reset silence timer if we got speech
        if (finalTranscript.trim() || interimTranscript.trim()) {
            this.resetSilenceTimer();
        }

        // Process final transcript
        if (finalTranscript.trim()) {
            this.processFinalTranscript(finalTranscript.trim());
        }
    }

    processFinalTranscript(transcript) {
        console.log('Final transcript:', transcript);
        
        // Stop listening while processing
        this.stopListening();
        this.isProcessingResponse = true;
        
        // Clear silence timers
        this.clearSilenceTimer();
        
        // Update UI
        this.updateAIStatus('Thinking...');
        
        // Send to callback if set
        if (this.onVoiceInput && typeof this.onVoiceInput === 'function') {
            this.onVoiceInput(transcript);
        }
    }

    handleSpeechError(event) {
        console.error('Speech recognition error:', event.error);
        
        const errorMessages = {
            'network': 'Network error. Please check your internet connection.',
            'not-allowed': 'Microphone access denied. Please allow microphone access.',
            'no-speech': 'No speech detected. Please try speaking clearly.',
            'audio-capture': 'No microphone found. Please check your microphone.',
            'aborted': 'Speech recognition was stopped.',
            'language-not-supported': 'Language not supported.',
            'service-not-allowed': 'Speech service not allowed.'
        };

        const userMessage = errorMessages[event.error] || `Speech recognition error: ${event.error}`;
        this.showVoiceError(userMessage);

        // Handle specific errors
        if (event.error === 'not-allowed') {
            this.isRecording = false;
            this.updateMicrophoneUI(false);
        } else if (event.error === 'no-speech') {
            // Ignore no-speech errors, they're normal
            this.hideVoiceError();
        }
    }

    startSilenceTimer() {
        this.clearSilenceTimer();
        
        // Warning timer (10 seconds)
        this.warningTimer = setTimeout(() => {
            console.log('Silence warning triggered');
            this.handleSilenceWarning();
            
            // Final timeout timer (5 more seconds)
            this.silenceTimer = setTimeout(() => {
                console.log('Silence timeout triggered');
                this.handleSilenceTimeout();
            }, 5000);
            
        }, this.warningTime);
    }

    resetSilenceTimer() {
        this.clearSilenceTimer();
        if (this.isRecording && !this.isProcessingResponse) {
            this.startSilenceTimer();
        }
    }

    clearSilenceTimer() {
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
            this.warningTimer = null;
        }
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
    }

    handleSilenceWarning() {
        console.log('Handling silence warning');
        this.updateAIStatus('Still there?');
        
        // Play impatience phrase
        this.playImpatientPrompt();
        
        // Trigger callback if set
        if (this.onSilenceWarning && typeof this.onSilenceWarning === 'function') {
            this.onSilenceWarning();
        }
    }

    handleSilenceTimeout() {
        console.log('Handling silence timeout - hanging up');
        this.stopListening();
        this.updateAIStatus('Call ended - no response');
        
        // Trigger callback if set
        if (this.onSilenceTimeout && typeof this.onSilenceTimeout === 'function') {
            this.onSilenceTimeout();
        }
    }

    async playImpatientPrompt() {
        const impatientPhrases = [
            "Hello? Are you still with me?",
            "Can you hear me?", 
            "Just checking you're there…",
            "Still on the line?",
            "I don't have much time for this."
        ];
        
        const randomPhrase = impatientPhrases[Math.floor(Math.random() * impatientPhrases.length)];
        await this.playAIResponse(randomPhrase);
    }

    async playAIResponse(text, priority = false) {
        try {
            console.log('Playing AI response:', text);
            
            // Get TTS audio from server
            const response = await fetch('/api/roleplay/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error(`TTS request failed: ${response.status}`);
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            // Add to queue or play immediately
            if (priority || this.audioQueue.length === 0) {
                if (priority) {
                    this.audioQueue.unshift(audioUrl);
                } else {
                    this.audioQueue.push(audioUrl);
                }
                
                if (!this.isPlayingAudio) {
                    this.playNextAudio();
                }
            } else {
                this.audioQueue.push(audioUrl);
            }

        } catch (error) {
            console.error('Error playing AI response:', error);
            this.showVoiceError('Audio playback failed');
        }
    }

    playNextAudio() {
        if (this.audioQueue.length === 0) {
            this.isPlayingAudio = false;
            this.onAudioFinished();
            return;
        }

        const audioUrl = this.audioQueue.shift();
        this.isPlayingAudio = true;
        this.updateAIStatus('Speaking...');
        
        this.audioElement.src = audioUrl;
        this.audioElement.play().catch(error => {
            console.error('Audio play error:', error);
            this.playNextAudio(); // Try next audio
        });
    }

    onAudioFinished() {
        // Called when all audio has finished playing
        this.isProcessingResponse = false;
        
        // Resume listening if we should be
        if (this.isRecording) {
            setTimeout(() => {
                this.updateAIStatus('Listening...');
                this.startListening();
            }, 500);
        } else {
            this.updateAIStatus('Waiting...');
        }
    }

    stopAllAudio() {
        this.audioQueue = [];
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
        }
        this.isPlayingAudio = false;
    }

    updateMicrophoneUI(isActive) {
        if (!this.micButton) return;

        if (isActive) {
            this.micButton.classList.add('recording');
            this.micButton.classList.remove('btn-primary');
            this.micButton.classList.add('btn-danger');
            this.micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            this.micButton.title = 'Click to stop recording (Ctrl+Space)';
        } else {
            this.micButton.classList.remove('recording');
            this.micButton.classList.remove('btn-danger');
            this.micButton.classList.add('btn-primary');
            this.micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            this.micButton.title = 'Click to start recording (Ctrl+Space)';
        }
    }

    updateTranscriptDisplay(finalText, interimText = '') {
        if (!this.transcriptDisplay) return;

        const displayText = finalText + (interimText ? ` <span class="interim">${interimText}</span>` : '');
        this.transcriptDisplay.innerHTML = displayText || 'Listening...';
    }

    updateAIStatus(status) {
        if (!this.aiStatusDisplay) return;
        this.aiStatusDisplay.textContent = status;
        
        // Update status indicator classes
        this.aiStatusDisplay.className = 'ai-status';
        
        if (status.includes('Listening')) {
            this.aiStatusDisplay.classList.add('listening');
        } else if (status.includes('Speaking') || status.includes('Thinking')) {
            this.aiStatusDisplay.classList.add('speaking');
        } else if (status.includes('ended') || status.includes('timeout')) {
            this.aiStatusDisplay.classList.add('ended');
        }
    }

    clearTranscript() {
        this.currentTranscript = '';
        this.finalTranscript = '';
        if (this.transcriptDisplay) {
            this.transcriptDisplay.innerHTML = 'Listening...';
        }
    }

    showVoiceError(message) {
        if (!this.voiceErrorDisplay) {
            console.error('Voice Error:', message);
            return;
        }

        this.voiceErrorDisplay.textContent = message;
        this.voiceErrorDisplay.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => this.hideVoiceError(), 5000);

        // Trigger callback if set
        if (this.onVoiceError && typeof this.onVoiceError === 'function') {
            this.onVoiceError(message);
        }
    }

    hideVoiceError() {
        if (this.voiceErrorDisplay) {
            this.voiceErrorDisplay.style.display = 'none';
        }
    }

    // Public methods for external control
    enable() {
        if (this.micButton) {
            this.micButton.disabled = false;
        }
    }

    disable() {
        this.stopListening();
        this.stopAllAudio();
        if (this.micButton) {
            this.micButton.disabled = true;
        }
    }

    reset() {
        this.stopListening();
        this.stopAllAudio();
        this.clearTranscript();
        this.clearSilenceTimer();
        this.isProcessingResponse = false;
        this.updateAIStatus('Ready');
        this.hideVoiceError();
    }

    // Getter methods
    isCurrentlyListening() {
        return this.isListening;
    }

    isCurrentlyRecording() {
        return this.isRecording;
    }

    getCurrentTranscript() {
        return this.currentTranscript;
    }

    // Test methods for debugging
    testTTS(text = "Hello, this is a test of the text to speech system.") {
        this.playAIResponse(text);
    }

    testMicrophone() {
        if (this.recognition) {
            console.log('Testing microphone...');
            this.startListening();
            setTimeout(() => {
                console.log('Stopping microphone test');
                this.stopListening();
            }, 5000);
        } else {
            console.error('Microphone test failed - no recognition available');
        }
    }
}

// Export for use in other scripts
window.VoiceHandler = VoiceHandler;