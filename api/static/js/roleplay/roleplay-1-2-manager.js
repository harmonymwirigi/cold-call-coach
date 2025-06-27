// static/js/roleplay/roleplay-1-2-manager.js
class Roleplay12Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "1.2";
        this.marathonState = null;
        this.marathonProgressElement = document.getElementById('marathon-progress');
    }

    async startCall() {
        console.log('🏁 Starting Marathon Mode call...');
        this.updateStartButton('Starting Marathon...', true);
        
        try {
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST',
                body: JSON.stringify({ roleplay_id: this.roleplayId, mode: 'marathon' })
            });

            if (!response.ok) throw new Error('Failed to start marathon');

            const data = await response.json();
            this.currentSession = data;
            this.marathonState = data.marathon_status;
            this.isActive = true;
            
            this.updateMarathonUI();
            await this.startPhoneCallSequence(data.initial_response);
        } catch (error) {
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
                body: JSON.stringify({ user_input: transcript, session_id: this.currentSession.session_id })
            });

            if (!response.ok) throw new Error('Failed to get AI response');

            const data = await response.json();
            this.marathonState = data.marathon_status;
            this.updateMarathonUI();

            if (data.new_call_started) {
                this.updateTranscript(`📞 ${data.transition_message || 'Starting next call...'}`);
                await this.delay(2000); // Pause before the next call starts
            }
            
            if (!data.call_continues) {
                this.endCall(data);
            } else {
                await this.playAIResponse(data.ai_response);
            }
        } catch (error) {
            this.showError('Error during marathon call. Try speaking again.');
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
                <span>Call: <strong>${this.marathonState.current_call_number}/${this.config.TOTAL_CALLS}</strong></span>
                <span style="color: #10b981;">Passed: <strong>${this.marathonState.calls_passed}</strong></span>
                <span style="color: #ef4444;">Failed: <strong>${this.marathonState.calls_failed}</strong></span>
                <span>Target: <strong>${this.config.CALLS_TO_PASS}</strong></span>
            </div>
        `;
    }
    
    endCall(data) {
        // The marathon ends via the backend `end_session` call, 
        // which gives a final result package.
        super.endCall(data);
        this.marathonProgressElement.style.display = 'none';
        this.showFeedback(data.coaching, data.overall_score, data.marathon_results);
    }
    
    showFeedback(coaching, score, marathonResults) {
        // Override to show marathon-specific messages
        super.showFeedback(coaching, score);
        
        const feedbackContent = document.getElementById('feedback-content');
        let message = '';

        if(marathonResults.marathon_passed) {
            message = `<div class="feedback-item" style="background: #10b98120; border-left-color: #10b981;">
                <h5>🎉 Marathon Passed!</h5>
                <p>Nice work—you passed ${marathonResults.calls_passed} out of 10! You've unlocked the next modules and earned one shot at Legend Mode.</p>
            </div>`;
        } else {
            message = `<div class="feedback-item" style="background: #f59e0b20; border-left-color: #f59e0b;">
                <h5> Marathon Complete</h5>
                <p>You completed all 10 calls and scored ${marathonResults.calls_passed}/10. Keep practising—the more reps you get, the easier it becomes.</p>
            </div>`;
        }
        feedbackContent.insertAdjacentHTML('afterbegin', message);
    }
}