

// static/js/roleplay/roleplay-1-2-manager.js
class Roleplay12Manager extends BaseRoleplayManager {
    constructor(containerId) {
        super(containerId);
        this.marathonState = {
            currentCall: 1,
            totalCalls: 10,
            callsPassed: 0,
            callsFailed: 0,
            isComplete: false
        };
    }
    
    async startCall() {
        // Marathon-specific call start logic
        console.log('🏃 Starting Marathon Mode call...');
        
        // Implementation similar to Roleplay 1.1 but with marathon tracking
        const response = await this.apiCall('/api/roleplay/start', {
            method: 'POST',
            body: JSON.stringify({
                roleplay_id: '1.2',
                mode: this.selectedMode
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.currentSession = data;
            this.marathonState = data.marathon_status || this.marathonState;
            
            await this.startPhoneCallSequence(data.initial_response);
        }
    }
    
    async processUserInput(transcript) {
        console.log('🏃 Processing Marathon input:', transcript);
        
        const response = await this.apiCall('/api/roleplay/respond', {
            method: 'POST',
            body: JSON.stringify({
                user_input: transcript
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Update marathon state
            if (data.marathon_status) {
                this.marathonState = data.marathon_status;
                this.updateMarathonUI();
            }
            
            // Handle marathon completion
            if (data.marathon_complete) {
                this.handleMarathonComplete(data);
                return;
            }
            
            // Handle new call started
            if (data.new_call_started) {
                this.handleNewCallStarted(data);
                return;
            }
            
            // Normal response handling
            if (data.call_continues) {
                await this.playAIResponseAndWaitForUser(data.ai_response);
            } else {
                this.endCall(data.call_result === 'passed');
            }
        }
    }
    
    handleNewCallStarted(data) {
        console.log(`🔄 Starting call ${this.marathonState.currentCall}/${this.marathonState.totalCalls}`);
        
        // Show transition UI
        this.updateTranscript(`📞 Starting call ${this.marathonState.currentCall}/${this.marathonState.totalCalls}...`);
        
        setTimeout(async () => {
            await this.playAIResponseAndWaitForUser(data.ai_response);
        }, 1000);
    }
    
    handleMarathonComplete(data) {
        console.log('🏁 Marathon complete!', data.marathon_status);
        
        setTimeout(() => {
            this.showMarathonResults(data);
        }, 2000);
    }
    
    updateMarathonUI() {
        // Update progress indicators
        const progressElement = document.getElementById('marathon-progress');
        if (progressElement) {
            progressElement.innerHTML = `
                <div class="marathon-stats">
                    <span>Call ${this.marathonState.currentCall}/${this.marathonState.totalCalls}</span>
                    <span>Passed: ${this.marathonState.callsPassed}</span>
                    <span>Failed: ${this.marathonState.callsFailed}</span>
                    <span>Need: ${this.marathonState.callsToPass}</span>
                </div>
            `;
        }
    }
    
    showMarathonResults(data) {
        console.log('📊 Showing Marathon results');
        
        document.getElementById('call-interface').style.display = 'none';
        document.getElementById('feedback-section').style.display = 'flex';
        
        const marathonResults = data.marathon_status;
        const passed = marathonResults.is_passed;
        
        // Show results
        const content = document.getElementById('feedback-content');
        content.innerHTML = `
            <div class="marathon-results">
                <h3>${passed ? '🎉 Marathon Passed!' : '📈 Marathon Complete'}</h3>
                <div class="results-grid">
                    <div class="result-item">
                        <strong>Calls Passed:</strong> ${marathonResults.callsPassed}/${marathonResults.totalCalls}
                    </div>
                    <div class="result-item">
                        <strong>Target:</strong> ${marathonResults.callsToPass} calls
                    </div>
                    <div class="result-item">
                        <strong>Success Rate:</strong> ${Math.round((marathonResults.callsPassed / marathonResults.totalCalls) * 100)}%
                    </div>
                </div>
                
                ${passed ? 
                    '<p>🔓 You\'ve unlocked modules 2.1 & 2.2 for 24 hours and earned one Legend Mode attempt!</p>' :
                    '<p>Keep practicing! The more reps you get, the easier it becomes. Ready to try Marathon again?</p>'
                }
            </div>
        `;
        
        // Show coaching if available
        if (data.coaching) {
            this.populateMarathonCoaching(data.coaching);
        }
    }
    
    populateMarathonCoaching(coaching) {
        const content = document.getElementById('feedback-content');
        
        const coachingHTML = `
            <div class="marathon-coaching">
                <h4>📝 Marathon Coaching</h4>
                <div class="coaching-grid">
                    <div class="coaching-item">
                        <h6>🎯 Sales Performance</h6>
                        <p>${coaching.sales_coaching || 'Good job on completing the marathon!'}</p>
                    </div>
                    <div class="coaching-item">
                        <h6>📝 Grammar</h6>
                        <p>${coaching.grammar_coaching || 'Focus on using natural contractions.'}</p>
                    </div>
                    <div class="coaching-item">
                        <h6>📖 Vocabulary</h6>
                        <p>${coaching.vocabulary_coaching || 'Use simple, outcome-focused language.'}</p>
                    </div>
                    <div class="coaching-item">
                        <h6>🎤 Pronunciation</h6>
                        <p>${coaching.pronunciation_coaching || 'Practice speaking clearly and consistently.'}</p>
                    </div>
                    <div class="coaching-item">
                        <h6>🤝 Rapport & Confidence</h6>
                        <p>${coaching.rapport_assertiveness || 'Show empathy first, then be confident.'}</p>
                    </div>
                </div>
            </div>
        `;
        
        content.innerHTML += coachingHTML;
    }
    
    showFeedback(coaching, score = 75) {
        // Marathon uses different feedback display
        this.showMarathonResults({
            marathon_status: this.marathonState,
            coaching: coaching
        });
    }
}

// Export for global access
window.Roleplay12Manager = Roleplay12Manager;