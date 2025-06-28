// ===== FIXED: static/js/roleplay/roleplay-1-2-manager.js =====
// Implements the structured, game-like flow for Marathon Mode.

class Roleplay12Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "1.2";
        this.marathonState = null;
        this.marathonProgressElement = document.getElementById('marathon-progress');
        this.config = { TOTAL_CALLS: 10, CALLS_TO_PASS: 6 };
        this.init();
    }

    init() {
        console.log('ðŸš€ Initializing Roleplay 1.2 (Marathon) Manager...');
        super.init();
        if (this.voiceHandler) {
            this.voiceHandler.onTranscript = this.processUserInput.bind(this);
            console.log('âœ… Voice handler callback connected for Marathon Mode.');
        }
    }

    // --- THIS IS THE NEW, REQUIRED METHOD ---
    async playAIResponseAndWaitForUser(text) {
        console.log('Marathon Mode: Playing AI response and starting user turn.');
        this.addToConversationHistory('ai', text);
        this.updateTranscript(`ðŸ—£ï¸  Prospect: "${text}"`);
        await this.playAIResponse(text);
    }

    // --- EXISTING METHODS (Verified and Kept) ---

    initializeModeSelection() {
        console.log('ðŸ   Marathon Mode: Initializing single-mode selection.');
        const modeGrid = document.getElementById('mode-grid');
        if (modeGrid) {
            modeGrid.innerHTML = `
                <div class="text-white text-center">
                    <p class="lead">You are about to start a 10-call marathon.</p>
                    <p>You must successfully complete <strong>${this.config.CALLS_TO_PASS} out of ${this.config.TOTAL_CALLS}</strong> calls to pass.</p>
                </div>
            `;
        }
        this.selectMode('marathon');
    }

    async startCall() {
        console.log('ðŸ   Starting Marathon Mode...');
        this.updateStartButton('Starting Marathon...', true);
        try {
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST', body: JSON.stringify({ roleplay_id: this.roleplayId, mode: this.selectedMode })
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to start');
            
            const data = await response.json();
            this.currentSession = data;
            this.marathonState = data.marathon_status;
            this.isActive = true;
            
            this.updateMarathonUI();
            await this.startPhoneCallSequence(data.initial_response);

        } catch (error) {
            this.showError(`Could not start Marathon: ${error.message}`);
            this.updateStartButton('Start Marathon', false);
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || this.isProcessing) return;
        this.isProcessing = true;
        this.updateTranscript('ðŸ§  Processing...');

        try {
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST', body: JSON.stringify({ user_input: transcript })
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to get response');

            const data = await response.json();
            
            if (data.marathon_status) {
                this.marathonState = data.marathon_status;
                this.updateMarathonUI();
            }

            if (data.new_call_started) {
                this.updateTranscript(`ðŸ“ž ${data.transition_message || 'Starting next call...'}`);
                await this.delay(1500);
            }
            
            if (!data.call_continues) {
                this.endCall(true, data);
            } else {
                await this.playAIResponse(data.ai_response);
            }
        } catch (error) {
            this.showError(`Error during marathon: ${error.message}`);
            this.startUserTurn();
        } finally {
            this.isProcessing = false;
        }
    }

    async endCall(isFinishedByApi = false, finalData = null) {
        // ... (This method remains the same as the previous correct version)
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
            console.log('📊 Final session data received:', data_to_show);
            this.showFeedback(data_to_show);
        } catch (error) {
            console.error('Error ending call:', error);
            this.showError('Could not end session. Please refresh.');
        }
    }

    showFeedback(data) {
        // ... (This method remains the same as the previous correct version)
        super.showFeedback(data);
        
        const { marathon_results, coaching } = data;
        
        if (!marathon_results) {
             console.warn("Marathon results missing in showFeedback data. Displaying overall coaching.");
        }
        
        const feedbackContent = document.getElementById('feedback-content');
        if (feedbackContent && coaching && coaching.overall) {
            const passed = marathon_results ? marathon_results.marathon_passed : false;
            const message = `<div class="feedback-item" style="background: ${passed ? '#10b98120' : '#f59e0b20'}; border-left-color: ${passed ? '#10b981' : '#f59e0b'};">
                <h5>${passed ? 'ðŸŽ‰ Marathon Passed!' : 'Marathon Complete'}</h5>
                <p>${coaching.overall}</p>
            </div>`;
            feedbackContent.innerHTML = message;
        }
    }

    updateMarathonUI() {
        // ... (This method remains the same)
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
}