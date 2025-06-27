// ===== FIXED: static/js/roleplay/roleplay-1-2-manager.js =====

class Roleplay12Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        // 1. Call the parent constructor FIRST. This is mandatory.
        super(options); 
        
        // 2. Now, it's safe to use 'this' to set up child-specific properties.
        this.roleplayId = "1.2";
        this.marathonState = null;
        this.marathonProgressElement = document.getElementById('marathon-progress');
        this.config = {
            TOTAL_CALLS: 10,
            CALLS_TO_PASS: 6
        };

        // 3. Finally, call the init() method to run the setup sequence.
        this.init();
    }


    initializeModeSelection() {
        console.log('🏁 Marathon Mode: Initializing single-mode selection.');
        const modeGrid = document.getElementById('mode-grid');
        
        if (modeGrid) {
            modeGrid.innerHTML = `
                <div class="text-white text-center">
                    <p class="lead">You are about to start a 10-call marathon.</p>
                    <p>You must successfully complete <strong>${this.config.CALLS_TO_PASS} out of ${this.config.TOTAL_CALLS}</strong> calls to pass.</p>
                    <p class="mt-3">Ready to begin?</p>
                </div>
            `;
        }
        
        // This will find the button and enable it.
        this.selectMode('marathon');
    }
    async startCall() {
        console.log('🏁 Starting Marathon Mode call...');
        this.updateStartButton('Starting Marathon...', true);
        
        try {
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST',
                body: JSON.stringify({ roleplay_id: this.roleplayId, mode: this.selectedMode })
            });

            if (!response.ok) {
                 const errorData = await response.json();
                 throw new Error(errorData.error || 'Failed to start marathon');
            }

            const data = await response.json();
            this.currentSession = data;
            this.marathonState = data.marathon_status || data.roleplay_info?.marathon_state;
            this.isActive = true;
            
            this.updateMarathonUI();
            await this.startPhoneCallSequence(data.initial_response);
        } catch (error) {
            console.error('Error starting Marathon Mode:', error);
            this.showError('Could not start Marathon Mode. Please try again.');
            this.updateStartButton('Start Marathon', false);
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || this.isProcessing) return;
        this.isProcessing = true;
        this.updateTranscript('🧠 Processing...');

        try {
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST',
                body: JSON.stringify({ user_input: transcript })
            });

            if (!response.ok) {
                 const errorData = await response.json();
                 throw new Error(errorData.error || 'Failed to get AI response');
            }

            const data = await response.json();
            if (data.marathon_status) {
                this.marathonState = data.marathon_status;
                this.updateMarathonUI();
            }

            if (data.new_call_started) {
                this.updateTranscript(`📞 ${data.transition_message || 'Starting next call...'}`);
                await this.delay(2000);
            }
            
            if (!data.call_continues) {
                this.endCall(data);
            } else {
                await this.playAIResponse(data.ai_response);
            }
        } catch (error) {
            this.showError(`Error during marathon call: ${error.message}`);
            this.startUserTurn();
        } finally {
            this.isProcessing = false;
        }
    }

    updateMarathonUI() {
        if (!this.marathonState || !this.marathonProgressElement) return;

        this.marathonProgressElement.style.display = 'block';
        this.marathonProgressElement.innerHTML = `
            <div class="marathon-stats">
                <span>Call: <strong>${this.marathonState.current_call_number || 1}/${this.config.TOTAL_CALLS}</strong></span>
                <span style="color: #10b981;">Passed: <strong>${this.marathonState.calls_passed || 0}</strong></span>
                <span style="color: #ef4444;">Failed: <strong>${this.marathonState.calls_failed || 0}</strong></span>
                <span>Target: <strong>${this.config.CALLS_TO_PASS}</strong></span>
            </div>
        `;
    }
    
    endCall(data) {
        super.endCall(data);
        if (this.marathonProgressElement) {
            this.marathonProgressElement.style.display = 'none';
        }
        this.showFeedback(data.coaching, data.overall_score, data.marathon_results);
    }
    
    showFeedback(coaching, score, marathonResults) {
        super.showFeedback(coaching, score);
        if (!marathonResults) return;
        
        const feedbackContent = document.getElementById('feedback-content');
        let message = '';

        if(marathonResults.marathon_passed) {
            message = `<div class="feedback-item" style="background: #10b98120; border-left-color: #10b981;">
                <h5>🎉 Marathon Passed!</h5>
                <p>Nice work—you passed ${marathonResults.calls_passed} out of 10! You've unlocked the next modules and earned one shot at Legend Mode.</p>
            </div>`;
        } else {
            message = `<div class="feedback-item" style="background: #f59e0b20; border-left-color: #f59e0b;">
                <h5>Marathon Complete</h5>
                <p>You completed all 10 calls and scored ${marathonResults.calls_passed}/10. Keep practising—the more reps you get, the easier it becomes.</p>
            </div>`;
        }
        feedbackContent.insertAdjacentHTML('afterbegin', message);
    }
}