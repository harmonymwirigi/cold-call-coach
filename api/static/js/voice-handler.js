// ===== NATURAL MOBILE: voice-handler.js - Smart Auto-Restart =====

class VoiceHandler {
    constructor(roleplayManager) {
        this.roleplayManager = roleplayManager;
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        
        // Mobile detection
        this.isMobile = this.detectMobile();
        this.isIOS = this.detectIOS();
        
        // Audio state management
        this.currentAudio = null;
        this.isAudioPlaying = false;
        
        // Conversation state
        this.isUserTurn = false;
        this.isAITurn = false;
        this.conversationActive = false;
        
        // Callback interface
        this.onTranscript = null;
        this.onError = null;
        
        // SMART MOBILE: Intelligent restart prevention
        this.lastStartTime = 0;
        this.restartAttempts = 0;
        this.maxRestartAttempts = 3;
        this.restartCooldown = 2000; // 2 seconds between restart attempts
        this.isInCooldown = false;
        this.pendingRestart = false;
        
        // Natural conversation settings
        this.settings = {
            continuous: true,
            interimResults: this.isMobile ? false : true, // Simpler on mobile
            language: 'en-US',
            maxAlternatives: 1
        };
        
        // State management
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.silenceTimer = null;
        this.isAutoListening = false;
        
        // Silence detection (gentler on mobile)
        this.silenceThreshold = this.isMobile ? 2500 : 2000;
        this.lastSpeechTime = null;
        this.silenceCheckInterval = null;
        
        // Roleplay silence specifications
        this.impatience_threshold = 10000;
        this.hangup_threshold = 15000;
        this.total_silence_start = null;
        this.impatience_triggered = false;
        this.hangupSilenceTimer = null;
        
        this.shouldRestart = false;
        this.wasPausedBySystem = false;
        
        console.log(`🎤 Natural Voice Handler - Mobile: ${this.isMobile}, iOS: ${this.isIOS}`);
        this.init();
    }

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
        console.log('🎤 Initializing Natural Voice Handler...');
        
        this.checkBrowserSupport();
        this.initializeUIElements();
        this.setupEventListeners();
        
        if (this.isSupported) {
            this.initializeSpeechRecognition();
        }
        
        console.log(`✅ Natural Voice Handler initialized. Mobile: ${this.isMobile}, Supported: ${this.isSupported}`);
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
                micButton.title = this.isMobile ? 'Voice recognition ready (Mobile)' : 'Voice recognition ready';
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
        // Microphone button click (works for both mobile and desktop)
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                console.log('🎤 Manual mic button clicked');
                if (this.isListening) {
                    this.stopListening();
                } else {
                    this.forceStartListening(); // Force start, bypassing cooldowns
                }
            });
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
            this.recognition.continuous = this.settings.continuous;
            this.recognition.interimResults = this.settings.interimResults;
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
            this.restartAttempts = 0; // Reset restart attempts on successful start
            this.isInCooldown = false;
            
            // Start silence tracking only if it's user's turn
            if (this.isUserTurn) {
                this.total_silence_start = Date.now();
                this.impatience_triggered = false;
                this.startHangupSilenceDetection();
            }
        };
        
        // Recognition ends
        this.recognition.onend = () => {
            console.log('🛑 Voice recognition ended');
            this.isListening = false;
            this.updateMicrophoneUI(false);
            this.stopSilenceDetection();
            this.stopHangupSilenceDetection();
            
            // SMART RESTART: Intelligent auto-restart with cooldown
            this.handleSmartRestart();
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
            
            // Start checking for silence to detect when user finished
            this.startSilenceDetection();
            
            // Restart hang-up silence tracking
            this.total_silence_start = Date.now();
        };
    }

    // ===== SMART RESTART LOGIC (THE KEY FIX) =====

    handleSmartRestart() {
        // Don't restart if we shouldn't, or if we're in cooldown
        if (!this.shouldRestart || this.isInCooldown || !this.isSupported) {
            return;
        }
        
        // Don't restart if it's not user turn or if AI is speaking
        if (!this.isUserTurn || this.isAudioPlaying) {
            return;
        }
        
        // Check restart attempts and timing
        const now = Date.now();
        const timeSinceLastStart = now - this.lastStartTime;
        
        // MOBILE: Be more conservative with restarts
        if (this.isMobile) {
            // On mobile, only restart if enough time has passed and not too many attempts
            if (timeSinceLastStart < this.restartCooldown || this.restartAttempts >= this.maxRestartAttempts) {
                console.log(`📱 Mobile restart blocked: attempts=${this.restartAttempts}, cooldown=${timeSinceLastStart < this.restartCooldown}`);
                this.enterCooldownMode();
                return;
            }
        }
        
        // Increment restart attempts
        this.restartAttempts++;
        
        // If too many restart attempts, enter cooldown
        if (this.restartAttempts >= this.maxRestartAttempts) {
            console.log('🔄 Too many restart attempts, entering cooldown');
            this.enterCooldownMode();
            return;
        }
        
        // Perform smart restart with delay
        const restartDelay = this.isMobile ? 1000 : 300; // Longer delay on mobile
        
        console.log(`🔄 Smart restart in ${restartDelay}ms (attempt ${this.restartAttempts}/${this.maxRestartAttempts})`);
        
        setTimeout(() => {
            // Double-check conditions before restarting
            if (this.shouldRestart && this.isUserTurn && !this.isAudioPlaying && !this.isListening) {
                this.startListening(this.isAutoListening);
            }
        }, restartDelay);
    }

    enterCooldownMode() {
        console.log('❄️ Entering cooldown mode');
        this.isInCooldown = true;
        this.restartAttempts = 0;
        
        // Show user-friendly message
        if (this.isMobile) {
            this.updateTranscript('📱 Your turn - tap microphone if voice recognition stopped');
        } else {
            this.updateTranscript('🎤 Your turn - click microphone if needed');
        }
        
        // Auto-exit cooldown after delay
        setTimeout(() => {
            console.log('❄️ Exiting cooldown mode');
            this.isInCooldown = false;
            this.restartAttempts = 0;
            
            // Try to restart if still needed
            if (this.shouldRestart && this.isUserTurn && !this.isAudioPlaying && !this.isListening) {
                console.log('🔄 Post-cooldown restart attempt');
                this.startListening(this.isAutoListening);
            }
        }, this.restartCooldown * 2); // Double cooldown for exit
    }

    forceStartListening() {
        // Force start, bypassing all cooldowns and restrictions
        console.log('🔧 Force starting listening (user initiated)');
        
        this.isInCooldown = false;
        this.restartAttempts = 0;
        this.lastStartTime = Date.now();
        
        this.startListening(false);
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
            // Network errors: try again after delay
            setTimeout(() => {
                if (this.shouldRestart && this.isUserTurn) {
                    console.log('🔄 Retrying after network error...');
                    this.startListening(this.isAutoListening);
                }
            }, 3000);
        } else if (event.error === 'no-speech') {
            // No speech errors: don't count against restart attempts
            this.restartAttempts = Math.max(0, this.restartAttempts - 1);
        }
    }

    // ===== AUDIO MANAGEMENT =====

    async playAudio(text, isInterruptible = true) {
        console.log(`🔊 Playing audio: "${text.substring(0, 50)}..."`);
        
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
            // Reset restart attempts when it becomes user's turn
            this.restartAttempts = 0;
            this.isInCooldown = false;
            
            if (this.isMobile) {
                this.updateTranscript('📱 Your turn - speak naturally (auto-listening)');
            } else {
                this.updateTranscript('🎤 Your turn - speak naturally...');
            }
        }
    }

    setAITurn(isAITurn) {
        this.isAITurn = isAITurn;
        console.log(`🤖 AI turn: ${isAITurn}`);
        
        if (isAITurn) {
            // Stop listening when AI is speaking
            this.stopListening();
        }
    }

    startAutoListeningForUser() {
        if (this.isUserTurn && !this.isAudioPlaying && !this.isAITurn) {
            console.log('🎤 Starting auto-listening for user turn');
            
            // Small delay for clean transition, longer on mobile
            const delay = this.isMobile ? 800 : 500;
            
            setTimeout(() => {
                if (this.isUserTurn && !this.isAudioPlaying && !this.isAITurn) {
                    this.startAutoListening();
                }
            }, delay);
        }
    }

    // ===== PUBLIC METHODS =====

    startAutoListening() {
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
        
        // Record start time for cooldown management
        this.lastStartTime = Date.now();
        
        console.log(`🎤 Starting listening - Auto mode: ${isAutoMode} (Mobile: ${this.isMobile})`);
        this.isAutoListening = isAutoMode;
        
        try {
            this.shouldRestart = true;
            this.finalTranscript = '';
            this.currentTranscript = '';
            this.lastSpeechTime = null;
            
            this.requestMicrophonePermission().then(() => {
                if (this.recognition && !this.isAudioPlaying) {
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
        }
    }

    // ===== HANG-UP SILENCE DETECTION =====

    startHangupSilenceDetection() {
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
                micButton.title = 'Listening - click to stop';
            } else {
                micButton.classList.remove('listening');
                micButton.style.background = 'rgba(255, 255, 255, 0.1)';
                micButton.title = 'Click to start listening';
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

    pauseListening() {
        if (this.isListening) {
            this.wasPausedBySystem = true;
            this.stopListening();
        }
    }

    resumeListening() {
        if (this.wasPausedBySystem && this.shouldRestart && this.isUserTurn) {
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
            restartAttempts: this.restartAttempts,
            isInCooldown: this.isInCooldown
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
        
        console.log('✅ Voice Handler destroyed');
    }
}

// Export for global access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceHandler;
} else {
    window.VoiceHandler = VoiceHandler;
}

console.log('✅ Natural Mobile Voice Handler loaded successfully');