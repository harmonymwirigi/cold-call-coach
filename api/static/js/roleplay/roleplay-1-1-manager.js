// ===== FIXED: static/js/roleplay/roleplay-1-1-manager.js =====

class Roleplay11Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "1.1";
        this.roleplayType = "practice";
        this.naturalMode = true;
        this.conversationHistory = [];
        this.currentAudio = null;
        this.aiIsSpeaking = false;
        
    }
    initializeModeSelection() {
        console.log('ðŸŽ¯ Roleplay 1.1: Initializing specific mode selection.');
        
        // Define the modes for this specific roleplay
        const modes = [
            {
                id: 'practice',
                name: 'Practice Mode',
                description: 'A single, detailed call with full AI coaching and feedback.',
                icon: 'user-graduate'
            }
        ];
        
        // Use the helper from the base class to create the UI
        this.createModeSelectionUI(modes);
        
        // Since there's only one mode, auto-select it
        this.selectMode('practice');
    }
    init() {
        console.log('ðŸš€ Initializing Roleplay 1.1 Manager...');
        super.init();
        this.setupPracticeSpecificFeatures();
    }
    
    setupPracticeSpecificFeatures() {
        // Enable natural conversation features
        this.enableNaturalConversation();
        
        // Setup progress tracking
        this.setupProgressTracking();
        
        // Setup interruption handling
        this.setupInterruptionHandling();
    }

    // ===== ADD THESE TWO MISSING METHODS =====
    setupProgressTracking() {
        console.log('ðŸ“Š Practice Mode: Progress tracking setup.');
        // This method makes the conversation quality indicator visible for practice mode.
        const qualityElement = document.getElementById('conversation-quality');
        if (qualityElement) {
            qualityElement.style.display = 'block';
        }
    }

    setupInterruptionHandling() {
        console.log('âš¡ï¸  Practice Mode: Interruption handling setup confirmed.');
        // The core logic is in the voice handler and handleUserInterruption method.
        // This method is here to complete the initialization sequence.
    }
    // ===== END OF ADDED METHODS =====
    
    enableNaturalConversation() {
        console.log('ðŸ¤– Enabling natural conversation features...');
        
        if (this.voiceHandler) {
            this.voiceHandler.enableInterruption();
        }
        
        // Show natural conversation indicators
        this.updateUI('natural-mode-active');
    }
    
    async startCall() {
        console.log('ðŸš€ Starting Practice Mode call...');
        
        if (!this.selectedMode || this.isProcessing) {
            console.log('â Œ Cannot start call: missing mode or already processing');
            return;
        }
        
        this.isProcessing = true;
        this.updateStartButton('Connecting to Practice Mode...', true);
        
        try {
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST',
                body: JSON.stringify({
                    roleplay_id: this.roleplayId,
                    mode: this.selectedMode
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('âœ… Practice Mode started successfully:', data);
                
                this.currentSession = data;
                this.isActive = true;
                
                await this.startPhoneCallSequence(data.initial_response);
                
            } else {
                const errorData = await response.json();
                console.error('â Œ Failed to start Practice Mode:', errorData);
                this.showError(errorData.error || 'Failed to start Practice Mode call');
            }
        } catch (error) {
            console.error('â Œ Error starting Practice Mode:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.isProcessing = false;
            if (!this.isActive) {
                this.updateStartButton(`Start Practice Mode ${this.capitalizeFirst(this.selectedMode)}`, false);
            }
        }
    }
    
    async processUserInput(transcript) {
        if (!this.isActive || !this.currentSession || this.isProcessing) {
            console.log('â Œ Cannot process user input - invalid state');
            return;
        }
        
        console.log('ðŸ’¬ Processing Practice Mode input:', transcript);
        this.isProcessing = true;
        
        this.addToConversationHistory('user', transcript);
        this.updateTranscript('ðŸ¤– Processing your response...');
        
        try {
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST',
                body: JSON.stringify({
                    user_input: transcript
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('âœ… AI response received:', data);
                
                // Update conversation quality indicator
                if (data.conversation_quality !== undefined) {
                    this.updateConversationQuality(data.conversation_quality);
                }
                
                // Check if call should end
                if (!data.call_continues) {
                    console.log('ðŸ“ž Call ending...');
                    this.endCall(); // Let endCall handle the final data
                    return;
                }
                
                // Play AI response and automatically start next user turn
                await this.playAIResponseAndWaitForUser(data.ai_response);
                
            } else {
                const errorData = await response.json();
                console.error('â Œ API error:', errorData);
                this.showError(errorData.error || 'Failed to process input');
                this.startUserTurn(); // Resume user turn on error
            }
        } catch (error) {
            console.error('â Œ Error processing user input:', error);
            this.showError('Network error during call');
            this.startUserTurn(); // Resume user turn on error
        } finally {
            this.isProcessing = false;
        }
    }
    
    async playAIResponseAndWaitForUser(text) {
        try {
            console.log('ðŸŽ­ Playing AI response (interruptible):', text.substring(0, 50) + '...');
            this.aiIsSpeaking = true;
            
            this.addToConversationHistory('ai', text);
            this.updateTranscript(`ðŸ¤– Prospect: "${text}"`);
            
            // Try to play TTS audio (interruptible)
            try {
                const response = await this.apiCall('/api/roleplay/tts', {
                    method: 'POST',
                    body: JSON.stringify({ text: text })
                });
                
                if (response.ok) {
                    const audioBlob = await response.blob();
                    
                    if (audioBlob.size > 100) {
                        console.log('ðŸ”Š Playing interruptible AI audio');
                        const audioUrl = URL.createObjectURL(audioBlob);
                        this.currentAudio = new Audio(audioUrl);
                        
                        // Setup audio event handlers
                        this.currentAudio.onended = () => {
                            console.log('âœ… AI audio finished - starting user turn');
                            URL.revokeObjectURL(audioUrl);
                            this.currentAudio = null;
                            
                            // Only start user turn if AI is still speaking (not interrupted)
                            if (this.aiIsSpeaking) {
                                this.startUserTurn();
                            }
                        };
                        
                        this.currentAudio.onerror = () => {
                            console.log('â Œ AI audio error - starting user turn');
                            URL.revokeObjectURL(audioUrl);
                            this.currentAudio = null;
                            
                            if (this.aiIsSpeaking) {
                                this.startUserTurn();
                            }
                        };
                        
                        // Play the audio
                        await this.currentAudio.play();
                        
                    } else {
                        console.log('ðŸ“¢ Audio too small, simulating speech time');
                        await this.simulateSpeakingTime(text);
                        if (this.aiIsSpeaking) {
                            this.startUserTurn();
                        }
                    }
                } else {
                    console.log('ðŸŽµ TTS failed, simulating speech time');
                    await this.simulateSpeakingTime(text);
                    if (this.aiIsSpeaking) {
                        this.startUserTurn();
                    }
                }
            } catch (ttsError) {
                console.log('ðŸ”Š TTS error:', ttsError);
                await this.simulateSpeakingTime(text);
                if (this.aiIsSpeaking) {
                    this.startUserTurn();
                }
            }
            
        } catch (error) {
            console.error('â Œ Error playing AI response:', error);
            this.aiIsSpeaking = false;
            await this.simulateSpeakingTime(text);
            this.startUserTurn();
        }
    }
    
    startUserTurn() {
        console.log('ðŸ‘¤ Starting user turn - auto-listening activated');
        
        this.aiIsSpeaking = false;
        
        // Start auto-listening for natural conversation
        if (this.voiceHandler) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        
        // Update UI
        this.updateTranscript('ðŸŽ¤ Your turn - speak naturally...');
        this.addPulseToMicButton();
    }
    
    handleUserInterruption() {
        console.log('âš¡ User interrupted AI - switching to user turn');
        
        // Stop AI audio immediately
        this.stopCurrentAudio();
        
        // Mark AI as no longer speaking
        this.aiIsSpeaking = false;
        
        // If voice handler not already listening, start it
        if (this.voiceHandler && !this.voiceHandler.isListening) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        
        // Update UI
        this.updateTranscript('âš¡ You interrupted - keep speaking...');
    }
    
    stopCurrentAudio() {
        if (this.currentAudio) {
            console.log('ðŸ”‡ Stopping current AI audio');
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
    }
    
    updateConversationQuality(quality) {
        const qualityElement = document.getElementById('conversation-quality');
        if (qualityElement) {
            qualityElement.textContent = `${Math.round(quality)}%`;
            qualityElement.className = 'conversation-quality';
            
            if (quality >= 70) {
                qualityElement.classList.add('good');
            } else if (quality >= 40) {
                qualityElement.classList.add('fair');
            } else {
                qualityElement.classList.add('poor');
            }
        }
    }
    
    showFeedback(coaching, score = 75) {
        console.log('ðŸ“Š Showing Practice Mode feedback');
        
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'flex';
        
        const feedbackHeader = document.querySelector('.feedback-header h4');
        if (feedbackHeader) {
            feedbackHeader.textContent = 'Practice Mode Complete!';
        }
        
        if (coaching) {
            this.populatePracticeCoaching(coaching);
        }
        
        this.animateScore(score);
        this.updateScoreCircleColor(score);
    }
    
    populatePracticeCoaching(coaching) {
        const content = document.getElementById('feedback-content');
        if (!content) return;
        
        content.innerHTML = '';
        
        if (coaching) {
            const feedbackItems = [
                { key: 'sales_coaching', icon: 'chart-line', title: 'Sales Performance (Natural Conversation)' },
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
                    <h6><i class="fas fa-info-circle me-2"></i>Practice Mode Complete</h6>
                    <p style="margin: 0; font-size: 14px;">Your natural conversation call is complete. Great job!</p>
                </div>
            `;
        }
    }
}

// Export for global access
window.Roleplay11Manager = Roleplay11Manager;