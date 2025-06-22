// ===== MOBILE-OPTIMIZED: voice-handler.js =====

class VoiceHandler {
    constructor(roleplayManager) {
        this.roleplayManager = roleplayManager;
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        
        // MOBILE DETECTION
        this.isMobile = this.detectMobile();
        this.isIOS = this.detectIOS();
        
        // Audio state management
        this.currentAudio = null;
        this.isAudioPlaying = false;
        this.audioQueue = [];
        
        // Conversation state
        this.isUserTurn = false;
        this.isAITurn = false;
        this.conversationActive = false;
        
        // Callback interface
        this.onTranscript = null;
        this.onError = null;
        
        // MOBILE-SPECIFIC: Different settings for mobile vs desktop
        this.settings = this.isMobile ? {
            continuous: false,        // MOBILE: Don't use continuous mode
            interimResults: false,    // MOBILE: Only final results
            language: 'en-US',
            maxAlternatives: 1,
            autoRestart: false       // MOBILE: No auto-restart
        } : {
            continuous: true,         // DESKTOP: Use continuous mode
            interimResults: true,     // DESKTOP: Show interim results
            language: 'en-US',
            maxAlternatives: 1,
            autoRestart: true        // DESKTOP: Allow auto-restart
        };
        
        // State management
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.silenceTimer = null;
        this.isAutoListening = false;
        
        // MOBILE-SPECIFIC: Gentler silence detection
        this.silenceThreshold = this.isMobile ? 3000 : 2000;  // 3s on mobile, 2s on desktop
        this.lastSpeechTime = null;
        this.silenceCheckInterval = null;
        
        // Roleplay silence specifications
        this.impatience_threshold = 10000;
        this.hangup_threshold = 15000;
        this.total_silence_start = null;
        this.impatience_triggered = false;
        this.hangupSilenceTimer = null;
        
        // MOBILE-SPECIFIC: Manual control flags
        this.manualMode = this.isMobile;  // Use manual mode on mobile
        this.shouldRestart = false;
        this.wasPausedBySystem = false;
        this.lastStartTime = 0;
        
        console.log(`🎤 VoiceHandler initialized - Mobile: ${this.isMobile}, iOS: ${this.isIOS}`);
        this.init();
    }

    // ===== MOBILE DETECTION =====

    detectMobile() {
        const userAgent = navigator.userAgent.toLowerCase();
        const mobileKeywords = ['mobile', 'android', 'iphone', 'ipad', 'tablet'];
        const isMobileUA = mobileKeywords.some(keyword => userAgent.includes(keyword));
        const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        const isSmallScreen = window.innerWidth <= 768;
        
        return isMobileUA || (isTouchDevice && isSmallScreen);
    }

    detectIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent);
    }

    init() {
        console.log('🎤 Initializing Voice Handler...');
        
        this.checkBrowserSupport();
        this.initializeUIElements();
        this.setupEventListeners();
        
        if (this.isSupported) {
            this.initializeSpeechRecognition();
        }
        
        // Show mobile-specific instructions
        if (this.isMobile) {
            this.showMobileInstructions();
        }
        
        console.log(`✅ Voice Handler initialized. Mobile: ${this.isMobile}, Supported: ${this.isSupported}`);
    }

    checkBrowserSupport() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.isSupported = true;
            this.SpeechRecognition = SpeechRecognition;
            console.log('✅ Web Speech API supported');
            
            // MOBILE WARNING: Some mobile browsers have limited support
            if (this.isMobile) {
                console.log('📱 Mobile detected - using optimized settings');
            }
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
            this.triggerError('Voice recognition not supported in this browser.');
        } else {
            if (micButton) {
                if (this.isMobile) {
                    micButton.title = 'Tap to speak (Mobile Mode)';
                    micButton.innerHTML = '<i class="fas fa-microphone"></i><br><small>Tap to Talk</small>';
                } else {
                    micButton.title = 'Voice recognition ready';
                }
            }
        }
    }

    showMobileInstructions() {
        const instructionElement = document.getElementById('live-transcript');
        if (instructionElement && this.isMobile) {
            const mobileInstructions = document.createElement('div');
            mobileInstructions.id = 'mobile-instructions';
            mobileInstructions.style.cssText = `
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
                font-size: 12px;
                color: rgba(255, 255, 255, 0.9);
                text-align: center;
            `;
            mobileInstructions.innerHTML = `
                <i class="fas fa-mobile-alt"></i> <strong>Mobile Mode:</strong><br>
                Tap the microphone button when it's your turn to speak.<br>
                Speak clearly and wait for processing.
            `;
            
            instructionElement.prepend(mobileInstructions);
        }
    }

    initializeUIElements() {
        this.micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        this.transcriptElement = document.getElementById('live-transcript');
        this.errorElement = document.getElementById('voice-error');
        
        if (this.transcriptElement) {
            this.transcriptElement.textContent = this.isMobile ? 
                'Mobile voice recognition ready - Tap mic when it\'s your turn' : 
                'Voice recognition ready...';
        }
    }

    setupEventListeners() {
        // MOBILE-SPECIFIC: Touch events for better mobile experience
        if (this.micButton) {
            if (this.isMobile) {
                // MOBILE: Use touch events and manual control
                this.micButton.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    this.handleMobileTouch();
                });
                
                this.micButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleMobileTouch();
                });
            } else {
                // DESKTOP: Normal click behavior
                this.micButton.addEventListener('click', () => {
                    console.log('🎤 Manual mic button clicked');
                    if (this.isListening) {
                        this.stopListening();
                    } else {
                        this.startListening(false);
                    }
                });
            }
        }
        
        // Keyboard shortcuts (desktop only)
        if (!this.isMobile) {
            this.handleKeydown = (e) => {
                if (e.code === 'Space' && !e.target.matches('input, textarea')) {
                    e.preventDefault();
                    if (!this.isListening && this.isUserTurn) {
                        this.startListening(false);
                    }
                }
                
                if (e.code === 'Escape' && this.isListening) {
                    this.stopListening();
                }
            };
            
            document.addEventListener('keydown', this.handleKeydown);
        }
        
        // Handle page visibility changes
        this.handleVisibilityChange = () => {
            if (document.hidden) {
                this.pauseAllAudio();
                if (this.isListening) {
                    this.pauseListening();
                }
            } else if (!document.hidden) {
                // MOBILE: Don't auto-resume on mobile
                if (!this.isMobile) {
                    this.resumeListening();
                }
            }
        };
        
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
    }

    // ===== MOBILE-SPECIFIC METHODS =====

    handleMobileTouch() {
        console.log('📱 Mobile touch detected');
        
        // Prevent rapid tapping
        const now = Date.now();
        if (now - this.lastStartTime < 1000) {
            console.log('📱 Ignoring rapid tap');
            return;
        }
        this.lastStartTime = now;
        
        if (this.isListening) {
            console.log('📱 Stopping mobile listening');
            this.stopListening();
        } else if (this.isUserTurn && !this.isAudioPlaying) {
            console.log('📱 Starting mobile listening');
            this.startMobileListening();
        } else if (this.isAudioPlaying) {
            console.log('📱 Cannot start - AI is speaking');
            this.showMobileMessage('Wait for AI to finish speaking');
        } else {
            console.log('📱 Cannot start - not your turn');
            this.showMobileMessage('Wait for your turn to speak');
        }
    }

    startMobileListening() {
        if (!this.isSupported || this.isListening) return;
        
        console.log('📱 Starting mobile listening mode');
        
        try {
            this.shouldRestart = false;  // MOBILE: No auto-restart
            this.finalTranscript = '';
            this.currentTranscript = '';
            this.lastSpeechTime = null;
            
            this.requestMicrophonePermission().then(() => {
                if (this.recognition && !this.isAudioPlaying) {
                    this.recognition.start();
                }
                
                this.updateTranscript('📱 Listening - speak now (will stop automatically)');
                this.showMobileMessage('Speak now...', 'success');
            }).catch(error => {
                console.error('❌ Mobile microphone permission failed:', error);
                this.triggerError('Microphone permission required');
            });
            
        } catch (error) {
            console.error('❌ Failed to start mobile listening:', error);
            this.triggerError('Failed to start voice recognition');
        }
    }

    showMobileMessage(message, type = 'info') {
        // Create temporary mobile message
        const existingMessage = document.getElementById('mobile-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.id = 'mobile-message';
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10000;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
            color: white;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideDown 0.3s ease-out;
        `;
        
        messageDiv.textContent = message;
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            if (messageDiv && messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 2000);
    }

    initializeSpeechRecognition() {
        if (!this.isSupported) return;
        
        try {
            this.recognition = new this.SpeechRecognition();
            
            // Configure based on device type
            this.recognition.continuous = this.settings.continuous;
            this.recognition.interimResults = this.settings.interimResults;
            this.recognition.lang = this.settings.language;
            this.recognition.maxAlternatives = this.settings.maxAlternatives;
            
            this.setupRecognitionEventHandlers();
            
            console.log('🎤 Speech recognition initialized for', this.isMobile ? 'mobile' : 'desktop');
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
            
            // MOBILE: Show feedback
            if (this.isMobile) {
                this.showMobileMessage('Listening...', 'success');
            }
            
            // Start silence tracking only if user's turn
            if (this.isUserTurn) {
                this.total_silence_start = Date.now();
                this.impatience_triggered = false;
                if (!this.isMobile) {  // MOBILE: No hang-up detection
                    this.startHangupSilenceDetection();
                }
            }
        };
        
        // Recognition ends
        this.recognition.onend = () => {
            console.log('🛑 Voice recognition ended');
            this.isListening = false;
            this.updateMicrophoneUI(false);
            this.stopSilenceDetection();
            this.stopHangupSilenceDetection();
            
            // MOBILE: No auto-restart
            if (!this.isMobile && this.shouldRestart && this.isSupported && this.isUserTurn && !this.isAudioPlaying) {
                console.log('🔄 Auto-restarting recognition (desktop)...');
                setTimeout(() => {
                    this.startListening(this.isAutoListening);
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
        
        // Speech detection events
        this.recognition.onspeechstart = () => {
            console.log('🗣️ Speech detected');
            this.lastSpeechTime = Date.now();
            
            // Stop any playing audio when user starts speaking
            if (this.isAudioPlaying) {
                console.log('⚡ User interrupted AI - stopping audio');
                this.stopAllAudio();
                this.setAITurn(false);
                this.setUserTurn(true);
            }
            
            // Reset hang-up silence timer
            this.total_silence_start = null;
            this.impatience_triggered = false;
        };
        
        this.recognition.onspeechend = () => {
            console.log('🤐 Speech ended');
            this.lastSpeechTime = Date.now();
            
            // MOBILE: Process immediately, don't wait for silence
            if (this.isMobile) {
                setTimeout(() => {
                    this.processFinalUserSpeech();
                }, 500);  // Short delay for mobile
            } else {
                // DESKTOP: Use silence detection
                this.startSilenceDetection();
            }
            
            // Restart hang-up silence tracking
            this.total_silence_start = Date.now();
        };
    }

    handleRecognitionResult(event) {
        // Only process if it's user's turn
        if (!this.isUserTurn) {
            console.log('🚫 Ignoring speech - not user turn');
            return;
        }
        
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
        
        // MOBILE: Show immediate feedback
        if (this.isMobile && (finalTranscript || interimTranscript)) {
            this.updateTranscript(`📱 You: "${this.currentTranscript}"`);
        } else if (!this.isMobile) {
            this.updateTranscript(`🎤 You: "${this.currentTranscript}"`);
        }
        
        // Process final results
        if (finalTranscript.trim().length > 0) {
            this.finalTranscript += finalTranscript;
            
            // MOBILE: Process immediately
            if (this.isMobile) {
                // Small delay to catch any additional final results
                setTimeout(() => {
                    if (this.finalTranscript.trim()) {
                        this.processFinalUserSpeech();
                    }
                }, 300);
            } else {
                this.startSilenceDetection();
            }
        }
    }

    handleRecognitionError(event) {
        console.error('❌ Voice recognition error:', event.error);
        
        const errorMessages = {
            'network': 'Network error. Check internet connection.',
            'not-allowed': 'Microphone access denied. Please allow microphone access.',
            'no-speech': this.isMobile ? 'No speech detected. Try tapping and speaking clearly.' : 'No speech detected. Try speaking louder.',
            'aborted': 'Voice recognition aborted.',
            'audio-capture': 'No microphone found. Connect microphone.',
            'service-not-allowed': 'Voice recognition service not allowed.',
        };
        
        const message = errorMessages[event.error] || `Voice recognition error: ${event.error}`;
        this.triggerError(message);
        
        // MOBILE: Show error message
        if (this.isMobile) {
            this.showMobileMessage(message, 'error');
        }
        
        // Handle specific errors
        if (event.error === 'not-allowed') {
            this.handlePermissionDenied();
        } else if (event.error === 'network') {
            setTimeout(() => {
                if (this.shouldRestart && this.isUserTurn && !this.isMobile) {
                    console.log('🔄 Retrying after network error...');
                    this.startListening(this.isAutoListening);
                }
            }, 2000);
        }
    }

    // ===== MODIFIED AUDIO MANAGEMENT =====

    async playAudio(text, isInterruptible = true) {
        console.log(`🔊 Playing audio: "${text.substring(0, 50)}..." (Mobile: ${this.isMobile})`);
        
        // Stop any existing audio first
        this.stopAllAudio();
        
        // Set AI turn state
        this.setAITurn(true);
        this.setUserTurn(false);
        
        try {
            const response = await fetch('/api/roleplay/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            
            if (response.ok) {
                const audioBlob = await response.blob();
                
                if (audioBlob.size > 100) {
                    const audioUrl = URL.createObjectURL(audioBlob);
                    this.currentAudio = new Audio(audioUrl);
                    this.isAudioPlaying = true;
                    
                    // Setup event handlers
                    this.currentAudio.onended = () => {
                        console.log('✅ Audio finished playing');
                        this.cleanupAudio(audioUrl);
                        
                        // Switch to user turn after audio ends
                        this.setAITurn(false);
                        this.setUserTurn(true);
                        this.startAutoListeningForUser();
                    };
                    
                    this.currentAudio.onerror = () => {
                        console.log('❌ Audio playback error');
                        this.cleanupAudio(audioUrl);
                        this.setAITurn(false);
                        this.setUserTurn(true);
                        this.startAutoListeningForUser();
                    };
                    
                    // Play the audio
                    await this.currentAudio.play();
                    console.log('🎵 Audio playing successfully');
                    
                } else {
                    console.log('📢 Audio too small, simulating speech time');
                    await this.simulateSpeakingTime(text);
                    this.setAITurn(false);
                    this.setUserTurn(true);
                    this.startAutoListeningForUser();
                }
            } else {
                console.log('🎵 TTS failed, simulating speech time');
                await this.simulateSpeakingTime(text);
                this.setAITurn(false);
                this.setUserTurn(true);
                this.startAutoListeningForUser();
            }
        } catch (error) {
            console.error('❌ Audio playback failed:', error);
            await this.simulateSpeakingTime(text);
            this.setAITurn(false);
            this.setUserTurn(true);
            this.startAutoListeningForUser();
        }
    }

    stopAllAudio() {
        console.log('🔇 Stopping all audio');
        
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
        this.audioQueue = [];
    }

    pauseAllAudio() {
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
            console.log('⏸️ Audio paused');
        }
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
        
        console.log(`🕐 Simulating speaking time: ${speakingTime}ms for ${words} words`);
        
        return new Promise(resolve => {
            setTimeout(() => {
                console.log('✅ Simulated speaking complete');
                resolve();
            }, speakingTime);
        });
    }

    // ===== TURN MANAGEMENT =====

    setUserTurn(isUserTurn) {
        this.isUserTurn = isUserTurn;
        console.log(`👤 User turn: ${isUserTurn} (Mobile: ${this.isMobile})`);
        
        if (isUserTurn) {
            if (this.isMobile) {
                this.updateTranscript('📱 Your turn - tap microphone to speak');
                this.showMobileMessage('Your turn! Tap mic to speak');
            } else {
                this.updateTranscript('🎤 Your turn - speak when ready...');
            }
        }
    }

    setAITurn(isAITurn) {
        this.isAITurn = isAITurn;
        console.log(`🤖 AI turn: ${isAITurn}`);
        
        if (isAITurn) {
            // Stop listening when AI is speaking
            this.stopListening();
            
            if (this.isMobile) {
                this.showMobileMessage('AI is speaking...');
            }
        }
    }

    startAutoListeningForUser() {
        if (this.isUserTurn && !this.isAudioPlaying && !this.isAITurn) {
            console.log('🎤 Starting auto-listening for user turn');
            
            if (this.isMobile) {
                // MOBILE: Don't auto-start, just show instruction
                this.updateTranscript('📱 Your turn - tap microphone when ready');
                this.showMobileMessage('Your turn! Tap mic to speak');
            } else {
                // DESKTOP: Auto-start as before
                setTimeout(() => {
                    this.startAutoListening();
                }, 500);
            }
        }
    }

    // ===== PUBLIC METHODS =====

    startAutoListening() {
        if (this.isMobile) {
            // MOBILE: Manual mode only
            console.log('📱 Auto-listening disabled on mobile - use manual tap');
            return;
        }
        
        console.log('🤖 Starting auto-listening mode...');
        this.startListening(true);
    }

    startListening(isAutoMode = false) {
        // Don't start listening if AI is speaking
        if (this.isAITurn || this.isAudioPlaying) {
            console.log('🚫 Cannot start listening - AI is speaking');
            return;
        }
        
        if (!this.isSupported || this.isListening) return;
        
        console.log(`🎤 Starting listening - Auto mode: ${isAutoMode} (Mobile: ${this.isMobile})`);
        this.isAutoListening = isAutoMode;
        
        try {
            this.shouldRestart = !this.isMobile;  // MOBILE: No auto-restart
            this.finalTranscript = '';
            this.currentTranscript = '';
            this.lastSpeechTime = null;
            
            this.requestMicrophonePermission().then(() => {
                if (this.recognition && !this.isAudioPlaying) {
                    this.recognition.start();
                }
                
                if (this.isMobile) {
                    this.updateTranscript('📱 Listening - speak clearly...');
                } else if (isAutoMode) {
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

    // ===== SILENCE DETECTION (MODIFIED FOR MOBILE) =====

    startSilenceDetection() {
        // MOBILE: Use shorter detection on mobile
        if (this.isMobile) return;  // Skip silence detection on mobile
        
        this.stopSilenceDetection();
        
        console.log('🤫 Starting silence detection...');
        
        this.silenceCheckInterval = setInterval(() => {
            if (this.lastSpeechTime && this.isUserTurn) {
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
            this.setUserTurn(false);
            
            // MOBILE: Show processing message
            if (this.isMobile) {
                this.showMobileMessage('Processing...', 'info');
            }
            
            // Trigger callback
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
        } else if (this.isMobile) {
            // MOBILE: No speech detected
            this.showMobileMessage('No speech detected. Try again.', 'error');
            this.setUserTurn(true);  // Let them try again
        }
    }

    // ===== HANG-UP SILENCE DETECTION (DISABLED ON MOBILE) =====

    startHangupSilenceDetection() {
        if (this.isMobile) return;  // Skip on mobile
        
        this.stopHangupSilenceDetection();
        console.log('⏰ Starting hang-up silence detection');
        
        this.hangupSilenceTimer = setInterval(() => {
            if (this.total_silence_start && this.isListening && this.isUserTurn) {
                const totalSilence = Date.now() - this.total_silence_start;
                
                if (totalSilence >= this.impatience_threshold && 
                    !this.impatience_triggered &&
                    totalSilence < this.hangup_threshold) {
                    console.log('⏰ 10-second silence - triggering impatience');
                    this.handleImpatience();
                }
                
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
        
        if (this.onTranscript && typeof this.onTranscript === 'function') {
            this.onTranscript('[SILENCE_HANGUP]');
        } else if (this.roleplayManager && this.roleplayManager.handleVoiceInput) {
            this.roleplayManager.handleVoiceInput('[SILENCE_HANGUP]');
        }
    }

    // ===== UI METHODS =====

    updateMicrophoneUI(isListening) {
        const micButton = document.getElementById('mic-button') || document.getElementById('mic-btn');
        
        if (micButton) {
            if (isListening) {
                micButton.classList.add('listening');
                micButton.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                micButton.innerHTML = this.isMobile ? 
                    '<i class="fas fa-microphone"></i><br><small>Listening...</small>' :
                    '<i class="fas fa-microphone"></i>';
                micButton.title = this.isMobile ? 'Listening - speak now' : 'Listening - click to stop';
            } else {
                micButton.classList.remove('listening');
                micButton.style.background = 'rgba(255, 255, 255, 0.1)';
                micButton.innerHTML = this.isMobile ? 
                    '<i class="fas fa-microphone"></i><br><small>Tap to Talk</small>' :
                    '<i class="fas fa-microphone"></i>';
                micButton.title = this.isMobile ? 'Tap to speak' : 'Click to start listening';
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
        
        if (this.onError && typeof this.onError === 'function') {
            this.onError(message);
        } else {
            this.showErrorInUI(message);
        }
        
        // MOBILE: Also show mobile message
        if (this.isMobile) {
            this.showMobileMessage(message, 'error');
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
        
        if (this.isMobile) {
            this.showMobileMessage('Microphone access required', 'error');
        }
    }

    pauseListening() {
        if (this.isListening) {
            this.wasPausedBySystem = true;
            this.stopListening();
        }
    }

    resumeListening() {
        if (this.wasPausedBySystem && this.shouldRestart && this.isUserTurn && !this.isMobile) {
            this.wasPausedBySystem = false;
            this.startListening(this.isAutoListening);
        }
    }

    getListeningStatus() {
        return {
            isListening: this.isListening,
            isAutoListening: this.isAutoListening,
            isSupported: this.isSupported,
            isUserTurn: this.isUserTurn,
            isAITurn: this.isAITurn,
            isAudioPlaying: this.isAudioPlaying,
            isMobile: this.isMobile,
            manualMode: this.manualMode
        };
    }

    destroy() {
        console.log('🧹 Destroying Voice Handler...');
        
        this.stopListening();
        this.stopAllAudio();
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
        
        // Clean up mobile instructions
        const mobileInstructions = document.getElementById('mobile-instructions');
        if (mobileInstructions) {
            mobileInstructions.remove();
        }
        
        const mobileMessage = document.getElementById('mobile-message');
        if (mobileMessage) {
            mobileMessage.remove();
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

console.log('✅ Mobile-optimized Voice Handler class loaded successfully');