// ===== static/js/roleplay/roleplay-2-1-manager.js =====
// Post-Pitch Practice Mode - Advanced conversation flow

class Roleplay21Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "2.1";
        this.roleplayType = "advanced_practice";
        this.advancedState = null;
        
        // Advanced conversation tracking
        this.aiIsSpeaking = false;
        this.currentAudio = null;
        this.stageTracking = {
            pitch_delivered: false,
            objections_handled: 0,
            questions_handled: 0,
            company_fit_qualified: false,
            meeting_asked: false,
            slots_offered: 0
        };
        
        this.init();
    }

    init() {
        console.log('🎯 Initializing Roleplay 2.1 (Post-Pitch Practice) Manager...');
        super.init();
        
        if (this.voiceHandler) {
            this.voiceHandler.onTranscript = this.processUserInput.bind(this);
            console.log('✅ Voice handler callback connected for Advanced Practice.');
        }
        
        this.enableAdvancedFeatures();
    }

    // ===== CRITICAL: Required method for conversation flow =====
    async playAIResponseAndWaitForUser(text) {
        console.log('🎯 Advanced Practice: Playing AI response (interruptible)...');
        this.aiIsSpeaking = true;
        this.addToConversationHistory('ai', text);
        this.updateTranscript(`🗣️ Prospect: "${text}"`);

        await this.playAIResponse(text);
    }

    async playAIResponse(text) {
        if (this.voiceHandler) {
            await this.voiceHandler.playAudio(text);
        } else {
            console.warn("Voice handler not available, simulating speech time.");
            await this.simulateSpeakingTime(text);
            this.startUserTurn();
        }
    }

    startUserTurn() {
        console.log('👤 Advanced Practice: Starting user turn.');
        if (this.voiceHandler) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        this.updateTranscript('🎤 Your turn... speak now.');
        this.addPulseToMicButton();
    }

    enableAdvancedFeatures() {
        console.log('🎯 Advanced Practice: Enabling advanced conversation features...');
        
        if (this.voiceHandler) {
            this.voiceHandler.enableInterruption();
        }
        
        this.updateUI('advanced-mode-active');
        this.showAdvancedIndicators();
    }

    showAdvancedIndicators() {
        // Show advanced practice indicators in UI
        const modeIndicator = document.getElementById('roleplay-mode-indicator');
        if (modeIndicator) {
            modeIndicator.innerHTML = `
                <div class="advanced-mode-badge">
                    <i class="fas fa-bullhorn me-1"></i>
                    Advanced Practice
                </div>
            `;
            modeIndicator.style.display = 'block';
        }
    }

    handleUserInterruption() {
        console.log('⚡ Advanced Practice: User interrupted AI - switching to user turn');
        
        this.stopCurrentAudio();
        this.aiIsSpeaking = false;
        
        if (this.voiceHandler && !this.voiceHandler.isListening) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        
        this.updateTranscript('⚡ You interrupted - keep speaking...');
    }
    
    stopCurrentAudio() {
        if (this.currentAudio) {
            console.log('🔇 Advanced Practice: Stopping current AI audio');
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
    }

    initializeModeSelection() {
        console.log('🎯 Advanced Practice: Initializing single-mode selection.');
        const modeGrid = document.getElementById('mode-grid');
        
        if (modeGrid) {
            modeGrid.innerHTML = `
                <div class="text-white text-center">
                     <h4 class="mb-3">🎯 Post-Pitch Practice</h4>
                     <p class="lead">Advanced roleplay covering the complete post-pitch conversation flow.</p>
                     
                     <div class="mt-4 p-3 bg-primary bg-opacity-20 rounded">
                         <p class="mb-2"><strong>📋 What You'll Practice:</strong></p>
                         <ul class="text-start">
                             <li><strong>Mini Pitch:</strong> Concise, outcome-focused pitch + discovery question</li>
                             <li><strong>Objections & Questions:</strong> Handle 1-3 objections and 1-3 questions</li>
                             <li><strong>Qualification:</strong> Secure company-fit admission (mandatory)</li>
                             <li><strong>Meeting Ask:</strong> Request meeting with specific time slots</li>
                             <li><strong>Professional Wrap-up:</strong> Confirm details and close naturally</li>
                         </ul>
                     </div>
                     
                     <div class="mt-3 p-2 bg-warning bg-opacity-20 rounded">
                         <small><strong>⚠️ Advanced Level:</strong> Requires completion of Marathon Mode (1.2)</small>
                     </div>
                </div>
            `;
        }
        
        this.selectMode('advanced_practice');
    }

    async startCall() {
        console.log('🎯 Starting Advanced Practice Mode...');
        this.updateStartButton('Starting Advanced Practice...', true);
        
        try {
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST', 
                body: JSON.stringify({ 
                    roleplay_id: this.roleplayId, 
                    mode: this.selectedMode 
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to start advanced practice');
            }

            const data = await response.json();
            console.log('🎯 Advanced practice session started:', data);
            
            this.currentSession = data;
            this.advancedState = data.stage_info;
            this.isActive = true;
            
            // Show advanced UI elements
            this.updateAdvancedUI();
            
            // Start with AI pitch prompt
            await this.startPhoneCallSequence(data.initial_response);

        } catch (error) {
            console.error('❌ Advanced practice start error:', error);
            this.showError(`Could not start Advanced Practice: ${error.message}`);
            this.updateStartButton('Start Advanced Practice', false);
        }
    }

    updateAdvancedUI() {
        // Show advanced tracking elements
        const advancedTracker = document.getElementById('advanced-progress-tracker');
        if (advancedTracker) {
            advancedTracker.innerHTML = `
                <div class="advanced-stage-tracker">
                    <div class="stage-item" id="stage-pitch">
                        <i class="fas fa-bullhorn"></i>
                        <span>Pitch</span>
                    </div>
                    <div class="stage-item" id="stage-objections">
                        <i class="fas fa-comments"></i>
                        <span>Objections</span>
                    </div>
                    <div class="stage-item" id="stage-qualification">
                        <i class="fas fa-check-circle"></i>
                        <span>Qualify</span>
                    </div>
                    <div class="stage-item" id="stage-meeting">
                        <i class="fas fa-calendar"></i>
                        <span>Meeting</span>
                    </div>
                </div>
            `;
            advancedTracker.style.display = 'block';
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || this.isProcessing) {
            console.log('🚫 Advanced Practice: Cannot process input - not active or already processing');
            return;
        }
        
        this.isProcessing = true;
        this.updateTranscript('🧠 Processing advanced input...');
        
        try {
            console.log(`🎯 Advanced Practice: Processing "${transcript}"`);
            
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST', 
                body: JSON.stringify({ user_input: transcript })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get AI response');
            }

            const data = await response.json();
            console.log('🎯 Advanced practice response received:', data);
            
            // Update advanced state tracking
            if (data.stage_info) {
                this.advancedState = data.stage_info;
                this.updateStageProgress(data.stage_info.current_stage);
            }

            // Update conversation tracking
            if (data.evaluation) {
                this.updateConversationTracking(data.evaluation);
            }
            
            // Check if call should continue
            if (!data.call_continues) {
                console.log('🎯 Advanced practice completed!');
                this.endCall(true, data);
            } else {
                // Continue conversation
                await this.playAIResponseAndWaitForUser(data.ai_response);
            }
            
        } catch (error) {
            console.error('❌ Advanced practice processing error:', error);
            this.showError(`Error during advanced practice: ${error.message}`);
            this.startUserTurn(); // Try to recover
        } finally {
            this.isProcessing = false;
        }
    }

    updateStageProgress(currentStage) {
        // Update visual stage progress
        const stages = ['pitch_prompt', 'objections_questions', 'qualification', 'meeting_ask', 'wrap_up'];
        const stageElements = {
            'pitch_prompt': 'stage-pitch',
            'objections_questions': 'stage-objections', 
            'qualification': 'stage-qualification',
            'meeting_ask': 'stage-meeting'
        };
        
        // Clear all active states
        Object.values(stageElements).forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                element.classList.remove('active', 'completed');
            }
        });
        
        // Set current stage as active
        const currentElementId = stageElements[currentStage];
        if (currentElementId) {
            const currentElement = document.getElementById(currentElementId);
            if (currentElement) {
                currentElement.classList.add('active');
            }
        }
        
        // Mark completed stages
        const currentIndex = stages.indexOf(currentStage);
        if (currentIndex > 0) {
            stages.slice(0, currentIndex).forEach(stage => {
                const elementId = stageElements[stage];
                if (elementId) {
                    const element = document.getElementById(elementId);
                    if (element) {
                        element.classList.add('completed');
                    }
                }
            });
        }
    }

    updateConversationTracking(evaluation) {
        // Update internal tracking based on evaluation
        if (evaluation.criteria_met) {
            evaluation.criteria_met.forEach(criterion => {
                switch (criterion) {
                    case 'pitch_delivered':
                        this.stageTracking.pitch_delivered = true;
                        break;
                    case 'objection_handled':
                        this.stageTracking.objections_handled++;
                        break;
                    case 'question_handled':
                        this.stageTracking.questions_handled++;
                        break;
                    case 'company_fit':
                        this.stageTracking.company_fit_qualified = true;
                        break;
                    case 'meeting_ask':
                        this.stageTracking.meeting_asked = true;
                        break;
                }
            });
        }
        
        // Update UI indicators
        this.updateTrackingDisplay();
    }

    updateTrackingDisplay() {
        // Show mini indicators of progress
        const trackingElement = document.getElementById('conversation-tracking');
        if (trackingElement) {
            const indicators = [];
            
            if (this.stageTracking.pitch_delivered) {
                indicators.push('<span class="indicator success">📢 Pitch ✓</span>');
            }
            
            if (this.stageTracking.objections_handled > 0) {
                indicators.push(`<span class="indicator info">💬 Objections: ${this.stageTracking.objections_handled}</span>`);
            }
            
            if (this.stageTracking.company_fit_qualified) {
                indicators.push('<span class="indicator success">✅ Qualified ✓</span>');
            }
            
            if (this.stageTracking.meeting_asked) {
                indicators.push('<span class="indicator success">📅 Meeting ✓</span>');
            }
            
            trackingElement.innerHTML = indicators.join(' ');
        }
    }

    async endCall(isFinishedByApi = false, finalData = null) {
        if (!this.isActive) {
            console.log('🎯 Advanced Practice: Already ended');
            return;
        }
        
        console.log('🎯 Ending Advanced Practice Mode...');
        this.isActive = false;
        
        // Stop timers and voice
        if (this.durationInterval) clearInterval(this.durationInterval);
        if (this.voiceHandler) this.voiceHandler.stopListening();
        
        try {
            let dataToShow = finalData;
            
            // If not finished by API, call end endpoint
            if (!isFinishedByApi) {
                console.log('🎯 Calling end session API...');
                const response = await this.apiCall('/api/roleplay/end', { 
                    method: 'POST', 
                    body: JSON.stringify({ forced_end: true }) 
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to end session');
                }
                
                dataToShow = await response.json();
            }
            
            console.log('📊 Final advanced practice data received:', dataToShow);
            this.showFeedback(dataToShow);
            
        } catch (error) {
            console.error('❌ Error ending advanced practice:', error);
            this.showError('Could not end session properly. Please refresh.');
            
            // Show fallback feedback
            this.showFeedback({
                coaching: { overall: 'Advanced practice completed! Results could not be retrieved.' },
                overall_score: 75,
                advanced_results: { stages_completed: 3 }
            });
        }
    }

    showFeedback(data) {
        console.log('📊 Advanced Practice: Showing feedback');
        
        const { coaching, overall_score = 75, advanced_results } = data;
        
        // Call the base method to handle UI changes
        super.showFeedback(coaching, overall_score);
        
        // Add advanced-specific feedback
        this.populateAdvancedFeedback(data);
    }

    populateAdvancedFeedback(data) {
        const { coaching, overall_score = 75, advanced_results } = data;
        const feedbackContent = document.getElementById('feedback-content');
        
        if (!feedbackContent) {
            console.warn('🎯 No feedback content element found');
            return;
        }
        
        let advancedMessage = '';
        let statusClass = 'info';
        
        if (advanced_results) {
            const {
                pitch_delivered = false,
                objections_handled = 0,
                questions_handled = 0,
                company_fit_qualified = false,
                meeting_asked = false,
                meeting_slots_offered = 0,
                stages_completed = 0
            } = advanced_results;
            
            if (company_fit_qualified && meeting_asked) {
                advancedMessage = `🎉 Excellent! You completed the full post-pitch conversation flow.`;
                statusClass = 'success';
            } else if (stages_completed >= 3) {
                advancedMessage = `Good progress! You completed ${stages_completed} stages of the advanced conversation.`;
                statusClass = 'warning';
            } else {
                advancedMessage = `Practice session completed. Focus on progressing through all conversation stages.`;
                statusClass = 'info';
            }
            
            // Create detailed breakdown
            const breakdown = `
                <div class="advanced-breakdown mt-3">
                    <h6>📊 Conversation Breakdown:</h6>
                    <div class="row">
                        <div class="col-6">
                            <small>
                                • Pitch Delivered: ${pitch_delivered ? '✅' : '❌'}<br>
                                • Objections Handled: ${objections_handled}<br>
                                • Questions Handled: ${questions_handled}
                            </small>
                        </div>
                        <div class="col-6">
                            <small>
                                • Company Fit Qualified: ${company_fit_qualified ? '✅' : '❌'}<br>
                                • Meeting Asked: ${meeting_asked ? '✅' : '❌'}<br>
                                • Time Slots Offered: ${meeting_slots_offered}
                            </small>
                        </div>
                    </div>
                </div>
            `;
            
            advancedMessage += breakdown;
        } else {
            advancedMessage = 'Advanced practice session completed!';
        }
        
        // Create advanced-specific feedback
        const advancedFeedback = `
            <div class="feedback-item advanced-result bg-${statusClass} bg-opacity-20 border-${statusClass}">
                <h5><i class="fas fa-bullhorn me-2"></i>Advanced Practice Results</h5>
                <div>${advancedMessage}</div>
            </div>
        `;
        
        // Add coaching if available
        let coachingFeedback = '';
        if (coaching) {
            const coachingItems = Object.entries(coaching)
                .filter(([key, value]) => typeof value === 'string' && value.trim())
                .map(([key, value]) => {
                    const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    return `
                        <div class="coaching-item mb-2">
                            <h6><i class="fas fa-graduation-cap me-2"></i>${title}</h6>
                            <p class="mb-0">${value}</p>
                        </div>
                    `;
                }).join('');
            
            if (coachingItems) {
                coachingFeedback = `
                    <div class="feedback-item">
                        <h5><i class="fas fa-chalkboard-teacher me-2"></i>Detailed Coaching</h5>
                        ${coachingItems}
                    </div>
                `;
            }
        }
        
        feedbackContent.innerHTML = advancedFeedback + coachingFeedback;
    }

    // Override mode selection to show advanced description
    selectMode(mode) {
        super.selectMode(mode);
        
        // Update start button for advanced practice
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn && mode === 'advanced_practice') {
            startBtn.textContent = 'Start Advanced Practice';
        }
    }

    // Advanced practice specific utilities
    getAdvancedMetrics() {
        return {
            roleplay_type: 'advanced_practice',
            conversation_tracking: this.stageTracking,
            stage_info: this.advancedState,
            total_interactions: this.stageTracking.objections_handled + this.stageTracking.questions_handled
        };
    }

    resetAdvancedState() {
        this.stageTracking = {
            pitch_delivered: false,
            objections_handled: 0,
            questions_handled: 0,
            company_fit_qualified: false,
            meeting_asked: false,
            slots_offered: 0
        };
        
        this.advancedState = null;
        
        // Clear UI indicators
        const trackingElement = document.getElementById('conversation-tracking');
        if (trackingElement) {
            trackingElement.innerHTML = '';
        }
    }

    // Override initialization to reset advanced state
    initializeModeSelection() {
        super.initializeModeSelection();
        this.resetAdvancedState();
    }
}

// Export for global access
window.Roleplay21Manager = Roleplay21Manager;