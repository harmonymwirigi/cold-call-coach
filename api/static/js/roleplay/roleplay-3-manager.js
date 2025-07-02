// ===== static/js/roleplay/roleplay-3-manager.js =====
// Warm-up Challenge - 25 rapid-fire questions

class Roleplay3Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "3";
        this.roleplayType = "challenge";
        this.challengeState = {
            totalQuestions: 25,
            currentQuestion: 0,
            questionsCorrect: 0,
            currentStreak: 0,
            longestStreak: 0,
            startTime: null,
            questionStartTime: null,
            responseTimes: [],
            categoriesCovered: new Set()
        };
        
        // Challenge UI elements
        this.progressBar = null;
        this.statsDisplay = null;
        this.challengeTimer = null;
        
        this.init();
    }

    init() {
        console.log('🔥 Initializing Roleplay 3 (Warm-up Challenge) Manager...');
        super.init();
        
        if (this.voiceHandler) {
            this.voiceHandler.onTranscript = this.processUserInput.bind(this);
            console.log('✅ Voice handler callback connected for Challenge Mode.');
        }
        
        this.enableChallengeFeatures();
    }

    // ===== CRITICAL: Required method for conversation flow =====
    async playAIResponseAndWaitForUser(text) {
        console.log('🔥 Challenge: Playing question (rapid-fire mode)...');
        this.addToConversationHistory('ai', text);
        this.updateTranscript(`🔥 ${text}`);
        
        // Record question start time for response timing
        this.challengeState.questionStartTime = Date.now();
        
        // In challenge mode, we want faster transitions
        await this.playAIResponse(text);
    }

    async playAIResponse(text) {
        if (this.voiceHandler) {
            // Faster audio playback for challenge mode
            await this.voiceHandler.playAudio(text);
        } else {
            console.warn("Voice handler not available, simulating quick speech time.");
            await this.simulateSpeakingTime(text, 0.5); // Faster simulation
            this.startUserTurn();
        }
    }

    startUserTurn() {
        console.log('👤 Challenge: Starting user turn (rapid response).');
        if (this.voiceHandler) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        this.updateTranscript('🎤 Quick! Answer now...');
        this.addPulseToMicButton();
    }

    enableChallengeFeatures() {
        console.log('🔥 Challenge: Enabling rapid-fire features...');
        
        if (this.voiceHandler) {
            this.voiceHandler.enableInterruption();
        }
        
        this.updateUI('challenge-mode-active');
        this.showChallengeIndicators();
    }

    showChallengeIndicators() {
        // Show challenge mode indicators in UI
        const modeIndicator = document.getElementById('roleplay-mode-indicator');
        if (modeIndicator) {
            modeIndicator.innerHTML = `
                <div class="challenge-mode-badge">
                    <i class="fas fa-fire me-1"></i>
                    Rapid-Fire Challenge
                </div>
            `;
            modeIndicator.style.display = 'block';
        }
    }

    initializeModeSelection() {
        console.log('🔥 Challenge: Initializing challenge mode selection.');
        const modeGrid = document.getElementById('mode-grid');
        
        if (modeGrid) {
            modeGrid.innerHTML = `
                <div class="text-white text-center">
                     <h4 class="mb-3">🔥 Warm-up Challenge</h4>
                     <p class="lead">25 rapid-fire questions to sharpen your cold calling skills!</p>
                     
                     <div class="mt-4 p-3 bg-warning bg-opacity-20 rounded">
                         <p class="mb-2"><strong>⚡ How It Works:</strong></p>
                         <ul class="text-start">
                             <li><strong>25 Questions:</strong> Mixed categories covering all skills</li>
                             <li><strong>Rapid-Fire:</strong> Quick thinking, fast responses</li>
                             <li><strong>Categories:</strong> Openers, objections, qualification, closing</li>
                             <li><strong>Goal:</strong> 60%+ accuracy to pass</li>
                             <li><strong>Time:</strong> 5-10 minutes total</li>
                         </ul>
                     </div>
                     
                     <div class="mt-3 p-2 bg-info bg-opacity-20 rounded">
                         <small><strong>💡 Perfect For:</strong> Daily warm-up, skill assessment, quick practice</small>
                     </div>
                </div>
            `;
        }
        
        this.selectMode('challenge');
    }

    async startCall() {
        console.log('🔥 Starting Warm-up Challenge...');
        this.updateStartButton('Starting Challenge...', true);
        
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
                throw new Error(errorData.error || 'Failed to start challenge');
            }

            const data = await response.json();
            console.log('🔥 Challenge session started:', data);
            
            this.currentSession = data;
            this.isActive = true;
            
            // Initialize challenge state
            this.challengeState.startTime = Date.now();
            this.challengeState.totalQuestions = data.challenge_info?.total_questions || 25;
            this.challengeState.currentQuestion = 1;
            
            // Show challenge UI
            this.updateChallengeUI();
            
            // Start with first question - no phone sequence, direct to question
            await this.startChallengeSequence(data.initial_response);

        } catch (error) {
            console.error('❌ Challenge start error:', error);
            this.showError(`Could not start Warm-up Challenge: ${error.message}`);
            this.updateStartButton('Start Challenge', false);
        }
    }

    async startChallengeSequence(firstQuestion) {
        console.log('🔥 Starting challenge sequence...');
        
        // Hide mode selection, show challenge interface
        document.getElementById('mode-selection').style.display = 'none';
        document.getElementById('phone-container').style.display = 'block';
        document.getElementById('call-interface').style.display = 'flex';
        
        // Update call interface for challenge mode
        this.updateCallInterfaceForChallenge();
        
        // Start challenge timer
        this.startChallengeTimer();
        
        // Play first question
        await this.playAIResponseAndWaitForUser(firstQuestion);
    }

    updateCallInterfaceForChallenge() {
        // Modify the call interface for challenge mode
        const callInterface = document.getElementById('call-interface');
        if (callInterface) {
            callInterface.classList.add('challenge-mode');
        }
        
        // Update status text
        const statusText = document.getElementById('call-status-text');
        if (statusText) {
            statusText.textContent = 'Challenge Active';
        }
        
        // Hide avatar or replace with challenge icon
        const avatar = document.getElementById('contact-avatar');
        if (avatar) {
            avatar.style.display = 'none';
        }
        
        // Update contact info for challenge
        const contactName = document.getElementById('contact-name');
        const contactInfo = document.getElementById('contact-info');
        if (contactName) contactName.textContent = 'Warm-up Challenge';
        if (contactInfo) contactInfo.textContent = 'Rapid-Fire Questions';
    }

    updateChallengeUI() {
        // Show challenge progress UI
        const challengeProgress = document.getElementById('challenge-progress');
        if (challengeProgress) {
            challengeProgress.innerHTML = `
                <div class="challenge-stats">
                    <div class="row text-center">
                        <div class="col-3">
                            <div class="stat-item">
                                <div class="stat-number" id="current-question">1</div>
                                <div class="stat-label">Question</div>
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="stat-item text-success">
                                <div class="stat-number" id="questions-correct">0</div>
                                <div class="stat-label">Correct</div>
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="stat-item text-warning">
                                <div class="stat-number" id="current-streak">0</div>
                                <div class="stat-label">Streak</div>
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="stat-item text-info">
                                <div class="stat-number" id="accuracy-percent">0%</div>
                                <div class="stat-label">Accuracy</div>
                            </div>
                        </div>
                    </div>
                    <div class="progress mt-2">
                        <div class="progress-bar bg-warning" id="challenge-progress-bar" style="width: 4%"></div>
                    </div>
                    <small class="text-muted">Question <span id="progress-text">1 of 25</span></small>
                </div>
            `;
            challengeProgress.style.display = 'block';
        }
    }

    startChallengeTimer() {
        this.callStartTime = Date.now();
        this.durationInterval = setInterval(() => {
            const elapsed = Date.now() - this.callStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            const durationElement = document.getElementById('call-duration');
            if (durationElement) {
                durationElement.textContent = 
                    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    async processUserInput(transcript) {
        if (!this.isActive || this.isProcessing) {
            console.log('🚫 Challenge: Cannot process input - not active or already processing');
            return;
        }
        
        this.isProcessing = true;
        this.updateTranscript('🧠 Processing answer...');
        
        // Record response time
        if (this.challengeState.questionStartTime) {
            const responseTime = Date.now() - this.challengeState.questionStartTime;
            this.challengeState.responseTimes.push(responseTime);
        }
        
        try {
            console.log(`🔥 Challenge Q${this.challengeState.currentQuestion}: Processing "${transcript}"`);
            
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST', 
                body: JSON.stringify({ user_input: transcript })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get AI response');
            }

            const data = await response.json();
            console.log('🔥 Challenge response received:', data);
            
            // Update challenge state
            if (data.challenge_info) {
                this.updateChallengeState(data.challenge_info, data.evaluation);
            }
            
            // Check if challenge is complete
            if (data.challenge_complete || !data.call_continues) {
                console.log('🔥 Challenge completed!');
                this.endCall(true, data);
            } else {
                // Continue with next question
                await this.playAIResponseAndWaitForUser(data.ai_response);
            }
            
        } catch (error) {
            console.error('❌ Challenge processing error:', error);
            this.showError(`Error during challenge: ${error.message}`);
            this.startUserTurn(); // Try to recover
        } finally {
            this.isProcessing = false;
        }
    }

    updateChallengeState(challengeInfo, evaluation) {
        // Update internal state
        this.challengeState.currentQuestion = challengeInfo.current_question || this.challengeState.currentQuestion + 1;
        this.challengeState.questionsCorrect = challengeInfo.questions_correct || this.challengeState.questionsCorrect;
        this.challengeState.currentStreak = challengeInfo.current_streak || this.challengeState.currentStreak;
        
        // Update evaluation-based state
        if (evaluation) {
            if (evaluation.passed) {
                this.challengeState.currentStreak++;
                this.challengeState.longestStreak = Math.max(this.challengeState.longestStreak, this.challengeState.currentStreak);
            } else {
                this.challengeState.currentStreak = 0;
            }
            
            if (evaluation.category) {
                this.challengeState.categoriesCovered.add(evaluation.category);
            }
        }
        
        // Update UI
        this.updateChallengeDisplay();
    }

    updateChallengeDisplay() {
        // Update question number
        const currentQuestionEl = document.getElementById('current-question');
        if (currentQuestionEl) {
            currentQuestionEl.textContent = this.challengeState.currentQuestion;
        }
        
        // Update correct count
        const questionsCorrectEl = document.getElementById('questions-correct');
        if (questionsCorrectEl) {
            questionsCorrectEl.textContent = this.challengeState.questionsCorrect;
        }
        
        // Update streak
        const currentStreakEl = document.getElementById('current-streak');
        if (currentStreakEl) {
            currentStreakEl.textContent = this.challengeState.currentStreak;
        }
        
        // Update accuracy
        const accuracyEl = document.getElementById('accuracy-percent');
        if (accuracyEl && this.challengeState.currentQuestion > 1) {
            const accuracy = Math.round((this.challengeState.questionsCorrect / (this.challengeState.currentQuestion - 1)) * 100);
            accuracyEl.textContent = `${accuracy}%`;
        }
        
        // Update progress bar
        const progressBar = document.getElementById('challenge-progress-bar');
        const progressText = document.getElementById('progress-text');
        if (progressBar && progressText) {
            const percentage = (this.challengeState.currentQuestion / this.challengeState.totalQuestions) * 100;
            progressBar.style.width = `${percentage}%`;
            progressText.textContent = `${this.challengeState.currentQuestion} of ${this.challengeState.totalQuestions}`;
        }
    }

    async endCall(isFinishedByApi = false, finalData = null) {
        if (!this.isActive) {
            console.log('🔥 Challenge: Already ended');
            return;
        }
        
        console.log('🔥 Ending Warm-up Challenge...');
        this.isActive = false;
        
        // Stop timers and voice
        if (this.durationInterval) clearInterval(this.durationInterval);
        if (this.voiceHandler) this.voiceHandler.stopListening();
        
        try {
            let dataToShow = finalData;
            
            // If not finished by API, call end endpoint
            if (!isFinishedByApi) {
                console.log('🔥 Calling end session API...');
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
            
            console.log('📊 Final challenge data received:', dataToShow);
            this.showFeedback(dataToShow);
            
        } catch (error) {
            console.error('❌ Error ending challenge:', error);
            this.showError('Could not end session properly. Please refresh.');
            
            // Show fallback feedback
            this.showFeedback({
                coaching: { overall: 'Warm-up challenge completed! Results could not be retrieved.' },
                overall_score: 75,
                challenge_results: { questions_completed: this.challengeState.currentQuestion }
            });
        }
    }

    showFeedback(data) {
        console.log('📊 Challenge: Showing feedback');
        
        const { coaching, overall_score = 75, challenge_results } = data;
        
        // Call the base method to handle UI changes
        super.showFeedback(coaching, overall_score);
        
        // Add challenge-specific feedback
        this.populateChallengeFeedback(data);
    }

    populateChallengeFeedback(data) {
        const { coaching, overall_score = 75, challenge_results } = data;
        const feedbackContent = document.getElementById('feedback-content');
        
        if (!feedbackContent) {
            console.warn('🔥 No feedback content element found');
            return;
        }
        
        let challengeMessage = '';
        let statusClass = 'info';
        
        if (challenge_results) {
            const {
                questions_completed = 0,
                questions_correct = 0,
                accuracy = 0,
                longest_streak = 0,
                categories_covered = 0,
                avg_response_time = 0
            } = challenge_results;
            
            if (accuracy >= 80) {
                challengeMessage = `🔥 Excellent Challenge! ${accuracy.toFixed(1)}% accuracy shows mastery!`;
                statusClass = 'success';
            } else if (accuracy >= 60) {
                challengeMessage = `✅ Good Challenge! ${accuracy.toFixed(1)}% accuracy - you passed!`;
                statusClass = 'success';
            } else {
                challengeMessage = `⚡ Challenge Complete! ${accuracy.toFixed(1)}% accuracy - keep practicing!`;
                statusClass = 'warning';
            }
            
            // Create detailed breakdown
            const breakdown = `
                <div class="challenge-breakdown mt-3">
                    <h6>📊 Challenge Results:</h6>
                    <div class="row">
                        <div class="col-6">
                            <small>
                                • Questions: ${questions_completed}/25<br>
                                • Correct: ${questions_correct}<br>
                                • Accuracy: ${accuracy.toFixed(1)}%
                            </small>
                        </div>
                        <div class="col-6">
                            <small>
                                • Longest Streak: ${longest_streak}<br>
                                • Categories: ${categories_covered}<br>
                                • Avg Time: ${avg_response_time.toFixed(1)}s
                            </small>
                        </div>
                    </div>
                </div>
            `;
            
            challengeMessage += breakdown;
        } else {
            challengeMessage = 'Warm-up challenge completed!';
        }
        
        // Create challenge-specific feedback
        const challengeFeedback = `
            <div class="feedback-item challenge-result bg-${statusClass} bg-opacity-20 border-${statusClass}">
                <h5><i class="fas fa-fire me-2"></i>Challenge Results</h5>
                <div>${challengeMessage}</div>
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
                        <h5><i class="fas fa-chalkboard-teacher me-2"></i>Performance Coaching</h5>
                        ${coachingItems}
                    </div>
                `;
            }
        }
        
        feedbackContent.innerHTML = challengeFeedback + coachingFeedback;
    }

    // Override mode selection to show challenge description
    selectMode(mode) {
        super.selectMode(mode);
        
        // Update start button for challenge
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn && mode === 'challenge') {
            startBtn.textContent = 'Start Challenge';
        }
    }

    // Challenge-specific utilities
    getChallengeMetrics() {
        return {
            roleplay_type: 'challenge',
            challenge_state: this.challengeState,
            total_time: this.challengeState.startTime ? Date.now() - this.challengeState.startTime : 0,
            categories_covered: Array.from(this.challengeState.categoriesCovered)
        };
    }

    resetChallengeState() {
        this.challengeState = {
            totalQuestions: 25,
            currentQuestion: 0,
            questionsCorrect: 0,
            currentStreak: 0,
            longestStreak: 0,
            startTime: null,
            questionStartTime: null,
            responseTimes: [],
            categoriesCovered: new Set()
        };
    }

    // Override initialization to reset challenge state
    initializeModeSelection() {
        super.initializeModeSelection();
        this.resetChallengeState();
    }

    // Faster speaking simulation for challenge mode
    async simulateSpeakingTime(text, speedMultiplier = 1) {
        const words = text ? text.split(' ').length : 0;
        const baseTime = (words / 200) * 60 * 1000; // Faster base rate
        const adjustedTime = Math.max(500, baseTime * speedMultiplier);
        
        console.log(`⏱️ Challenge speaking time: ${adjustedTime}ms for ${words} words`);
        
        return new Promise(resolve => setTimeout(resolve, adjustedTime));
    }
}

// Export for global access
window.Roleplay3Manager = Roleplay3Manager;