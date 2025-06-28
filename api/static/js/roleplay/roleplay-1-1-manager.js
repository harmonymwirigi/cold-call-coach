// ===== FIXED: static/js/roleplay/roleplay-1-1-manager.js =====

class Roleplay11Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "1.1";
        this.roleplayType = "practice";
        this.aiIsSpeaking = false; // Add this property
        this.currentAudio = null; // Add this property
        this.init();
    }

    init() {
        console.log('🚀 Initializing Roleplay 1.1 (Practice) Manager...');
        super.init();
        if (this.voiceHandler) {
            this.voiceHandler.onTranscript = this.processUserInput.bind(this);
            console.log('✅ Voice handler callback connected for Practice Mode.');
        }
    }
    async playAIResponseAndWaitForUser(text) {
        console.log('ðŸŽ­ Practice Mode: Playing AI response (interruptible)...');
        this.aiIsSpeaking = true;
        this.addToConversationHistory('ai', text);
        this.updateTranscript(`ðŸ—£ï¸  Prospect: "${text}"`);

        // This now correctly calls the method from the base class
        await this.playAIResponse(text);
    }
    initializeModeSelection() {
        const modeGrid = document.getElementById('mode-grid');
        if (modeGrid) {
            modeGrid.innerHTML = `
                <div class="text-white text-center">
                     <p class="lead">Starting a single practice call.</p>
                     <p>You will receive detailed feedback after the call.</p>
                </div>
            `;
        }
        this.selectMode('practice');
    }
    createModeSelectionUI(modes) {
        const modeGrid = document.getElementById('mode-grid');
        if (!modeGrid) return;
    
        if (modes.length === 1 && modes[0].id === 'practice') {
             modeGrid.innerHTML = `
                <div class="text-white text-center">
                     <p class="lead">Starting a single practice call.</p>
                     <p>You will receive detailed feedback after the call.</p>
                </div>
            `;
            return;
        }

        modeGrid.innerHTML = modes.map(mode => `
            <div class="mode-card" data-mode="${mode.id}">
                <div class="mode-icon"><i class="fas fa-${mode.icon}"></i></div>
                <h5>${mode.name}</h5>
                <small>${mode.description}</small>
            </div>
        `).join('');

        // Re-bind events if needed, though this is simple enough not to require it
    }
    
    setupPracticeSpecificFeatures() {
        console.log('Practice mode features are being set up.');
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
        this.updateStartButton('Connecting...', true);
        try {
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST', body: JSON.stringify({ roleplay_id: this.roleplayId, mode: this.selectedMode })
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to start');
            const data = await response.json();
            this.currentSession = data;
            this.isActive = true;
            await this.startPhoneCallSequence(data.initial_response);
        } catch (error) {
            this.showError(`Could not start Practice Mode: ${error.message}`);
            this.updateStartButton('Start Practice', false);
        }
    }
    async endCall(isFinishedByApi = false, finalData = null) {
        if (!this.isActive) return;
        this.isActive = false;
        if (this.durationInterval) clearInterval(this.durationInterval);
        if (this.voiceHandler) this.voiceHandler.stopListening();
    
        try {
            let data_to_show = finalData;
            if (!isFinishedByApi) {
                const response = await this.apiCall('/api/roleplay/end', { method: 'POST', body: JSON.stringify({ forced_end: true }) });
                if (!response.ok) throw new Error((await response.json()).error || 'Failed to end session');
                data_to_show = await response.json();
            }
            console.log('📊 Final practice session data received:', data_to_show);
            // Directly call the method to display feedback
            this.showFeedback(data_to_show.coaching, data_to_show.overall_score);
        } catch (error) {
            console.error('Error ending practice call:', error);
            this.showError('Could not end session. Please refresh.');
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || this.isProcessing) return;
        this.isProcessing = true;
        this.updateTranscript('ðŸ§  Processing...');
        try {
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST', body: JSON.stringify({ user_input: transcript })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to get AI response');
            
            if (!data.call_continues) {
                this.endCall(true, data);
            } else {
                await this.playAIResponseAndWaitForUser(data.ai_response);
            }
        } catch (error) {
            this.showError(`Error during practice call: ${error.message}`);
            this.startUserTurn();
        } finally {
            this.isProcessing = false;
        }
    }
    async playAIResponse(text) {
        if (this.voiceHandler) {
             // Let the voice handler manage playing audio and starting the next user turn
            await this.voiceHandler.playAudio(text);
        } else {
            // Fallback if voice handler isn't ready
            console.warn("Voice handler not available, simulating speech time.");
            await this.simulateSpeakingTime(text);
            this.startUserTurn();
        }
    }
    
    startUserTurn() {
        console.log('ðŸ‘¤ Starting user turn.');
        if (this.voiceHandler) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        this.updateTranscript('ðŸŽ¤ Your turn... speak now.');
        // The original file was missing this call, which makes the mic button pulse.
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
        // Call the base method to handle the UI changes
        super.showFeedback(coaching, score); 
        // You can add practice-specific feedback UI updates here if needed
        this.populatePracticeCoaching(coaching);
    }
    
    populatePracticeCoaching(coaching) {
        const content = document.getElementById('feedback-content');
        if (!content) return;
        content.innerHTML = '';
        if (coaching) {
            const feedbackItems = [
                { key: 'sales_coaching', icon: 'chart-line', title: 'Sales Performance' },
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
                        </div>`;
                }
            });
        } else {
            content.innerHTML = `<div class="feedback-item"><p>Practice complete. Great job!</p></div>`;
        }
    }
}

// Export for global access
window.Roleplay11Manager = Roleplay11Manager;