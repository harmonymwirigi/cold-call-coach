// ===== FIXED: static/js/roleplay/roleplay-1-2-manager.js =====
// Marathon Mode with enhanced conversation flow

class Roleplay12Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "1.2";
        this.roleplayType = "marathon";
        this.marathonState = null;
        this.marathonProgressElement = document.getElementById('marathon-progress');
        this.config = { TOTAL_CALLS: 10, CALLS_TO_PASS: 6 };
        
        // Add conversation state tracking like Roleplay 1.1
        this.aiIsSpeaking = false;
        this.currentAudio = null;
        
        this.init();
    }

    init() {
        console.log('🏁 Initializing Roleplay 1.2 (Marathon) Manager...');
        super.init();
        
        if (this.voiceHandler) {
            this.voiceHandler.onTranscript = this.processUserInput.bind(this);
            console.log('✅ Voice handler callback connected for Marathon Mode.');
        }
        
        // Enable natural conversation features like Practice Mode
        this.enableNaturalConversation();
    }

    // ===== CRITICAL: ADD THE MISSING METHOD =====
    async playAIResponseAndWaitForUser(text) {
        console.log('🏁 Marathon Mode: Playing AI response (interruptible)...');
        this.aiIsSpeaking = true;
        this.addToConversationHistory('ai', text);
        this.updateTranscript(`🗣️ Prospect: "${text}"`);

        // Call the enhanced playAIResponse method that handles user turn transition
        await this.playAIResponse(text);
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
        console.log('👤 Marathon: Starting user turn.');
        if (this.voiceHandler) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        this.updateTranscript('🎤 Your turn... speak now.');
        this.addPulseToMicButton();
    }

    enableNaturalConversation() {
        console.log('🤖 Marathon: Enabling natural conversation features...');
        
        if (this.voiceHandler) {
            this.voiceHandler.enableInterruption();
        }
        
        // Show natural conversation indicators
        this.updateUI('natural-mode-active');
    }

    handleUserInterruption() {
        console.log('⚡ Marathon: User interrupted AI - switching to user turn');
        
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
        this.updateTranscript('⚡ You interrupted - keep speaking...');
    }
    
    stopCurrentAudio() {
        if (this.currentAudio) {
            console.log('🔇 Marathon: Stopping current AI audio');
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
    }

    initializeModeSelection() {
        console.log('🏁 Marathon Mode: Initializing single-mode selection.');
        const modeGrid = document.getElementById('mode-grid');
        
        if (modeGrid) {
            modeGrid.innerHTML = `
                <div class="text-white text-center">
                     <h4 class="mb-3">🏃‍♂️ Marathon Mode</h4>
                     <p class="lead">You are about to start a 10-call marathon.</p>
                     <p>You must successfully complete <strong>${this.config.CALLS_TO_PASS} out of ${this.config.TOTAL_CALLS}</strong> calls to pass.</p>
                     <div class="mt-4 p-3 bg-info bg-opacity-20 rounded">
                         <p class="mb-2"><strong>📋 How Marathon Works:</strong></p>
                         <ul class="text-start">
                             <li>10 consecutive cold calls</li>
                             <li>Pass 6 calls to complete the marathon</li>
                             <li>Each call: Opener → Objection → Mini-pitch</li>
                             <li>Enhanced natural conversation flow</li>
                             <li>Detailed coaching after completion</li>
                         </ul>
                     </div>
                </div>
            `;
        }
        
        this.selectMode('marathon');
    }

    async startCall() {
        console.log('🏁 Starting Marathon Mode...');
        this.updateStartButton('Starting Marathon...', true);
        
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
                throw new Error(errorData.error || 'Failed to start marathon');
            }

            const data = await response.json();
            console.log('🏁 Marathon session started:', data);
            
            this.currentSession = data;
            this.marathonState = data.marathon_status;
            this.isActive = true;
            
            // Show marathon progress UI
            this.updateMarathonUI();
            
            // Start the phone call sequence
            await this.startPhoneCallSequence(data.initial_response);

        } catch (error) {
            console.error('❌ Marathon start error:', error);
            this.showError(`Could not start Marathon: ${error.message}`);
            this.updateStartButton('Start Marathon', false);
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || this.isProcessing) {
            console.log('🚫 Marathon: Cannot process input - not active or already processing');
            return;
        }
        
        this.isProcessing = true;
        this.updateTranscript('🧠 Processing...');
        
        try {
            console.log(`🏁 Marathon Call #${this.marathonState?.current_call_number || 'Unknown'}: Processing "${transcript}"`);
            
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST', 
                body: JSON.stringify({ user_input: transcript })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get AI response');
            }

            const data = await response.json();
            console.log('🏁 Marathon response received:', data);
            
            // Update marathon state if provided
            if (data.marathon_status) {
                this.marathonState = data.marathon_status;
                this.updateMarathonUI();
            }

            // Handle new call transitions
            if (data.new_call_started) {
                console.log(`🏁 New call started: Call #${this.marathonState?.current_call_number}`);
                this.updateTranscript(`📞 ${data.transition_message || 'Starting next call...'}`);
                await this.delay(2000); // Brief pause between calls
            }
            
            // Check if marathon is complete
            if (!data.call_continues) {
                console.log('🏁 Marathon completed!');
                this.endCall(true, data);
            } else {
                // Continue conversation
                await this.playAIResponseAndWaitForUser(data.ai_response);
            }
            
        } catch (error) {
            console.error('❌ Marathon processing error:', error);
            this.showError(`Error during marathon: ${error.message}`);
            this.startUserTurn(); // Try to recover
        } finally {
            this.isProcessing = false;
        }
    }

    async endCall(isFinishedByApi = false, finalData = null) {
        if (!this.isActive) {
            console.log('🏁 Marathon: Already ended');
            return;
        }
        
        console.log('🏁 Ending Marathon Mode...');
        this.isActive = false;
        
        // Stop timers and voice
        if (this.durationInterval) clearInterval(this.durationInterval);
        if (this.voiceHandler) this.voiceHandler.stopListening();
        
        try {
            let dataToShow = finalData;
            
            // If not finished by API, call end endpoint
            if (!isFinishedByApi) {
                console.log('🏁 Calling end session API...');
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
            
            console.log('📊 Final marathon data received:', dataToShow);
            this.showFeedback(dataToShow);
            
        } catch (error) {
            console.error('❌ Error ending marathon:', error);
            this.showError('Could not end session properly. Please refresh.');
            
            // Show fallback feedback
            this.showFeedback({
                coaching: { overall: 'Marathon completed! Results could not be retrieved.' },
                overall_score: 75,
                marathon_results: { marathon_passed: false }
            });
        }
    }

    showFeedback(data) {
        console.log('📊 Marathon: Showing feedback');
        
        const { coaching, overall_score = 75, marathon_results } = data;
        
        // Call the base method to handle UI changes
        super.showFeedback(coaching, overall_score);
        
        // Add marathon-specific feedback
        this.populateMarathonFeedback(data);
    }

    populateMarathonFeedback(data) {
        const { coaching, overall_score = 75, marathon_results } = data;
        const feedbackContent = document.getElementById('feedback-content');
        
        if (!feedbackContent) {
            console.warn('🏁 No feedback content element found');
            return;
        }
        
        let marathonMessage = '';
        let statusClass = 'info';
        
        if (marathon_results) {
            const { calls_passed = 0, total_calls = 0, marathon_passed = false } = marathon_results;
            
            if (marathon_passed) {
                marathonMessage = `🎉 Marathon Passed! You successfully completed ${calls_passed} out of ${total_calls} calls.`;
                statusClass = 'success';
            } else {
                marathonMessage = `Marathon Complete. You passed ${calls_passed} out of ${total_calls} calls. Need ${this.config.CALLS_TO_PASS} to pass.`;
                statusClass = 'warning';
            }
        } else {
            marathonMessage = 'Marathon session completed!';
        }
        
        // Create marathon-specific feedback
        const marathonFeedback = `
            <div class="feedback-item marathon-result bg-${statusClass} bg-opacity-20 border-${statusClass}">
                <h5><i class="fas fa-running me-2"></i>Marathon Results</h5>
                <p>${marathonMessage}</p>
                ${marathon_results ? `
                    <div class="mt-2">
                        <small>
                            Pass Rate: ${Math.round((marathon_results.calls_passed / Math.max(marathon_results.total_calls, 1)) * 100)}% 
                            • Score: ${overall_score}/100
                        </small>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Add coaching if available
        let coachingFeedback = '';
        if (coaching && coaching.overall) {
            coachingFeedback = `
                <div class="feedback-item">
                    <h6><i class="fas fa-graduation-cap me-2"></i>Coaching Summary</h6>
                    <p>${coaching.overall}</p>
                </div>
            `;
        }
        
        feedbackContent.innerHTML = marathonFeedback + coachingFeedback;
    }

    updateMarathonUI() {
        if (!this.marathonState || !this.marathonProgressElement) {
            console.log('🏁 No marathon state or progress element');
            return;
        }
        
        const { current_call_number = 1, calls_passed = 0, calls_failed = 0 } = this.marathonState;
        
        this.marathonProgressElement.style.display = 'block';
        this.marathonProgressElement.innerHTML = `
            <div class="marathon-stats">
                <div class="row text-center">
                    <div class="col-3">
                        <div class="stat-item">
                            <div class="stat-number">${current_call_number}</div>
                            <div class="stat-label">Current Call</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="stat-item text-success">
                            <div class="stat-number">${calls_passed}</div>
                            <div class="stat-label">Passed</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="stat-item text-danger">
                            <div class="stat-number">${calls_failed}</div>
                            <div class="stat-label">Failed</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="stat-item text-warning">
                            <div class="stat-number">${this.config.CALLS_TO_PASS}</div>
                            <div class="stat-label">Target</div>
                        </div>
                    </div>
                </div>
                <div class="progress mt-2">
                    <div class="progress-bar bg-success" style="width: ${(calls_passed / this.config.CALLS_TO_PASS) * 100}%"></div>
                </div>
                <small class="text-muted">Need ${Math.max(0, this.config.CALLS_TO_PASS - calls_passed)} more to pass</small>
            </div>
        `;
    }

    // Marathon-specific utility methods
    updateConversationQuality(quality) {
        // Marathon mode can show conversation quality too
        const qualityElement = document.getElementById('conversation-quality');
        if (qualityElement) {
            qualityElement.textContent = `${Math.round(quality)}%`;
            qualityElement.style.display = 'block';
            
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

    // Override mode selection to show marathon description
    selectMode(mode) {
        super.selectMode(mode);
        
        // Update start button for marathon
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn && mode === 'marathon') {
            startBtn.textContent = `Start Marathon (${this.config.TOTAL_CALLS} calls)`;
        }
    }
}

// Export for global access
window.Roleplay12Manager = Roleplay12Manager;