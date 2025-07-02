// ===== static/js/roleplay/roleplay-4-manager.js =====
// Full Cold Call Simulation - Complete end-to-end conversation

class Roleplay4Manager extends BaseRoleplayManager {
    constructor(options = {}) {
        super(options);
        this.roleplayId = "4";
        this.roleplayType = "simulation";
        this.simulationState = {
            prospectPersonality: null,
            companyScenario: null,
            trustLevel: 0,
            interestLevel: 0,
            conversationDepth: 0,
            stagesCompleted: [],
            discoveryPoints: [],
            valuePropositions: [],
            qualificationData: {}
        };
        
        // Simulation UI elements
        this.relationshipMeter = null;
        this.stageTracker = null;
        this.simulationTimer = null;
        
        this.init();
    }

    init() {
        console.log('🎯 Initializing Roleplay 4 (Full Cold Call Simulation) Manager...');
        super.init();
        
        if (this.voiceHandler) {
            this.voiceHandler.onTranscript = this.processUserInput.bind(this);
            console.log('✅ Voice handler callback connected for Simulation Mode.');
        }
        
        this.enableSimulationFeatures();
    }

    // ===== CRITICAL: Required method for conversation flow =====
    async playAIResponseAndWaitForUser(text) {
        console.log('🎯 Simulation: Playing AI response (realistic conversation)...');
        this.addToConversationHistory('ai', text);
        this.updateTranscript(`🗣️ Prospect: "${text}"`);

        await this.playAIResponse(text);
    }

    async playAIResponse(text) {
        if (this.voiceHandler) {
            await this.voiceHandler.playAudio(text);
        } else {
            console.warn("Voice handler not available, simulating realistic speech time.");
            await this.simulateSpeakingTime(text);
            this.startUserTurn();
        }
    }

    startUserTurn() {
        console.log('👤 Simulation: Starting user turn.');
        if (this.voiceHandler) {
            this.voiceHandler.setUserTurn(true);
            this.voiceHandler.startAutoListening();
        }
        this.updateTranscript('🎤 Your turn... speak naturally.');
        this.addPulseToMicButton();
    }

    enableSimulationFeatures() {
        console.log('🎯 Simulation: Enabling complete conversation features...');
        
        if (this.voiceHandler) {
            this.voiceHandler.enableInterruption();
        }
        
        this.updateUI('simulation-mode-active');
        this.showSimulationIndicators();
    }

    showSimulationIndicators() {
        // Show simulation mode indicators in UI
        const modeIndicator = document.getElementById('roleplay-mode-indicator');
        if (modeIndicator) {
            modeIndicator.innerHTML = `
                <div class="simulation-mode-badge">
                    <i class="fas fa-headset me-1"></i>
                    Full Simulation
                </div>
            `;
            modeIndicator.style.display = 'block';
        }
    }

    initializeModeSelection() {
        console.log('🎯 Simulation: Initializing simulation mode selection.');
        const modeGrid = document.getElementById('mode-grid');
        
        if (modeGrid) {
            modeGrid.innerHTML = `
                <div class="text-white text-center">
                     <h4 class="mb-3">🎯 Full Cold Call Simulation</h4>
                     <p class="lead">Experience a complete, realistic cold call from start to finish.</p>
                     
                     <div class="mt-4 p-3 bg-success bg-opacity-20 rounded">
                         <p class="mb-2"><strong>🌟 Complete Experience:</strong></p>
                         <ul class="text-start">
                             <li><strong>Realistic Prospects:</strong> AI personalities that react naturally</li>
                             <li><strong>Full Conversation:</strong> Phone pickup → Discovery → Value → Close</li>
                             <li><strong>Relationship Building:</strong> Trust and rapport development</li>
                             <li><strong>Industry Scenarios:</strong> Context-specific challenges</li>
                             <li><strong>Advanced Coaching:</strong> Comprehensive skill assessment</li>
                         </ul>
                     </div>
                     
                     <div class="mt-3 p-2 bg-warning bg-opacity-20 rounded">
                         <small><strong>🎯 Advanced Level:</strong> Complete Post-Pitch Practice first to unlock</small>
                     </div>
                </div>
            `;
        }
        
        this.selectMode('simulation');
    }

    async startCall() {
        console.log('🎯 Starting Full Cold Call Simulation...');
        this.updateStartButton('Starting Simulation...', true);
        
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
                throw new Error(errorData.error || 'Failed to start simulation');
            }

            const data = await response.json();
            console.log('🎯 Simulation session started:', data);
            
            this.currentSession = data;
            this.isActive = true;
            
            // Initialize simulation state
            if (data.simulation_info) {
                this.simulationState.prospectPersonality = data.simulation_info.prospect_personality;
                this.simulationState.companyScenario = data.simulation_info.company_scenario;
            }
            
            // Show simulation UI
            this.updateSimulationUI();
            
            // Start complete phone call sequence
            await this.startPhoneCallSequence(data.initial_response);

        } catch (error) {
            console.error('❌ Simulation start error:', error);
            this.showError(`Could not start Full Simulation: ${error.message}`);
            this.updateStartButton('Start Simulation', false);
        }
    }

    updateSimulationUI() {
        // Show simulation-specific UI elements
        const simulationTracker = document.getElementById('simulation-tracker');
        if (simulationTracker) {
            simulationTracker.innerHTML = `
                <div class="simulation-dashboard">
                    <!-- Prospect Info -->
                    <div class="prospect-info mb-3">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Prospect Type:</small>
                                <div class="fw-bold" id="prospect-personality">${this.simulationState.prospectPersonality || 'Analyzing...'}</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Industry:</small>
                                <div class="fw-bold" id="company-scenario">${this.simulationState.companyScenario || 'Loading...'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Relationship Meters -->
                    <div class="relationship-meters mb-3">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Trust Level:</small>
                                <div class="progress">
                                    <div class="progress-bar bg-info" id="trust-meter" style="width: 0%"></div>
                                </div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Interest Level:</small>
                                <div class="progress">
                                    <div class="progress-bar bg-success" id="interest-meter" style="width: 0%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Stage Progress -->
                    <div class="stage-progress">
                        <small class="text-muted">Conversation Stages:</small>
                        <div class="stage-indicators d-flex justify-content-between mt-1">
                            <div class="stage-dot" id="stage-opener" title="Opening">📞</div>
                            <div class="stage-dot" id="stage-discovery" title="Discovery">❓</div>
                            <div class="stage-dot" id="stage-value" title="Value Prop">💎</div>
                            <div class="stage-dot" id="stage-qualify" title="Qualification">✅</div>
                            <div class="stage-dot" id="stage-close" title="Next Steps">🤝</div>
                        </div>
                    </div>
                </div>
            `;
            simulationTracker.style.display = 'block';
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || this.isProcessing) {
            console.log('🚫 Simulation: Cannot process input - not active or already processing');
            return;
        }
        
        this.isProcessing = true;
        this.updateTranscript('🧠 Processing conversation...');
        
        try {
            console.log(`🎯 Simulation: Processing "${transcript}"`);
            
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST', 
                body: JSON.stringify({ user_input: transcript })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get AI response');
            }

            const data = await response.json();
            console.log('🎯 Simulation response received:', data);
            
            // Update simulation state
            if (data.simulation_state) {
                this.updateSimulationState(data.simulation_state);
            }

            // Update conversation tracking
            if (data.evaluation) {
                this.updateConversationTracking(data.evaluation);
            }
            
            // Check if call should continue
            if (!data.call_continues) {
                console.log('🎯 Simulation completed!');
                this.endCall(true, data);
            } else {
                // Continue conversation
                await this.playAIResponseAndWaitForUser(data.ai_response);
            }
            
        } catch (error) {
            console.error('❌ Simulation processing error:', error);
            this.showError(`Error during simulation: ${error.message}`);
            this.startUserTurn(); // Try to recover
        } finally {
            this.isProcessing = false;
        }
    }

    updateSimulationState(simulationState) {
        // Update internal state
        this.simulationState.trustLevel = simulationState.trust_level || this.simulationState.trustLevel;
        this.simulationState.interestLevel = simulationState.interest_level || this.simulationState.interestLevel;
        this.simulationState.conversationDepth = simulationState.conversation_depth || this.simulationState.conversationDepth;
        
        // Update current stage
        const currentStage = simulationState.current_stage;
        this.updateStageProgress(currentStage);
        
        // Update relationship meters
        this.updateRelationshipMeters();
    }

    updateStageProgress(currentStage) {
        // Clear all stage indicators
        const stageMapping = {
            'phone_pickup': 'stage-opener',
            'opener_evaluation': 'stage-opener',
            'discovery': 'stage-discovery',
            'value_proposition': 'stage-value',
            'qualification': 'stage-qualify',
            'next_steps': 'stage-close'
        };
        
        // Reset all stages
        Object.values(stageMapping).forEach(stageId => {
            const element = document.getElementById(stageId);
            if (element) {
                element.classList.remove('active', 'completed');
            }
        });
        
        // Mark current stage as active
        const currentStageElement = stageMapping[currentStage];
        if (currentStageElement) {
            const element = document.getElementById(currentStageElement);
            if (element) {
                element.classList.add('active');
            }
        }
        
        // Mark previous stages as completed
        const stageOrder = ['phone_pickup', 'opener_evaluation', 'discovery', 'value_proposition', 'qualification', 'next_steps'];
        const currentIndex = stageOrder.indexOf(currentStage);
        
        if (currentIndex > 0) {
            stageOrder.slice(0, currentIndex).forEach(stage => {
                const elementId = stageMapping[stage];
                if (elementId) {
                    const element = document.getElementById(elementId);
                    if (element) {
                        element.classList.add('completed');
                    }
                }
            });
        }
    }

    updateRelationshipMeters() {
        // Update trust meter
        const trustMeter = document.getElementById('trust-meter');
        if (trustMeter) {
            const trustPercentage = (this.simulationState.trustLevel / 10) * 100;
            trustMeter.style.width = `${trustPercentage}%`;
        }
        
        // Update interest meter
        const interestMeter = document.getElementById('interest-meter');
        if (interestMeter) {
            const interestPercentage = (this.simulationState.interestLevel / 10) * 100;
            interestMeter.style.width = `${interestPercentage}%`;
        }
    }

    updateConversationTracking(evaluation) {
        // Track discovery points
        if (evaluation.criteria_met && evaluation.criteria_met.includes('asks_questions')) {
            this.simulationState.discoveryPoints.push(Date.now());
        }
        
        // Track value propositions
        if (evaluation.criteria_met && evaluation.criteria_met.includes('outcome_focused')) {
            this.simulationState.valuePropositions.push(Date.now());
        }
        
        // Update conversation quality indicator
        this.updateConversationQuality(evaluation.score || 0);
    }

    updateConversationQuality(score) {
        const qualityElement = document.getElementById('conversation-quality');
        if (qualityElement) {
            const qualityPercentage = (score / 4) * 100;
            qualityElement.textContent = `${Math.round(qualityPercentage)}%`;
            qualityElement.style.display = 'block';
            
            qualityElement.className = 'conversation-quality';
            if (qualityPercentage >= 75) {
                qualityElement.classList.add('excellent');
            } else if (qualityPercentage >= 50) {
                qualityElement.classList.add('good');
            } else {
                qualityElement.classList.add('needs-work');
            }
        }
    }

    async endCall(isFinishedByApi = false, finalData = null) {
        if (!this.isActive) {
            console.log('🎯 Simulation: Already ended');
            return;
        }
        
        console.log('🎯 Ending Full Cold Call Simulation...');
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
            
            console.log('📊 Final simulation data received:', dataToShow);
            this.showFeedback(dataToShow);
            
        } catch (error) {
            console.error('❌ Error ending simulation:', error);
            this.showError('Could not end session properly. Please refresh.');
            
            // Show fallback feedback
            this.showFeedback({
                coaching: { overall: 'Full simulation completed! Results could not be retrieved.' },
                overall_score: 75,
                simulation_results: { stages_completed: 3 }
            });
        }
    }

    showFeedback(data) {
        console.log('📊 Simulation: Showing feedback');
        
        const { coaching, overall_score = 75, simulation_results } = data;
        
        // Call the base method to handle UI changes
        super.showFeedback(coaching, overall_score);
        
        // Add simulation-specific feedback
        this.populateSimulationFeedback(data);
    }

    populateSimulationFeedback(data) {
        const { coaching, overall_score = 75, simulation_results } = data;
        const feedbackContent = document.getElementById('feedback-content');
        
        if (!feedbackContent) {
            console.warn('🎯 No feedback content element found');
            return;
        }
        
        let simulationMessage = '';
        let statusClass = 'info';
        
        if (simulation_results) {
            const {
                call_outcome = 'incomplete',
                stages_completed = 0,
                trust_level = 0,
                interest_level = 0,
                conversation_depth = 0,
                qualification_completed = false,
                prospect_personality = 'Unknown'
            } = simulation_results;
            
            if (call_outcome === 'success') {
                simulationMessage = `🎉 Excellent Simulation! You successfully completed a full cold call conversation.`;
                statusClass = 'success';
            } else if (stages_completed >= 4) {
                simulationMessage = `Great progress! You completed ${stages_completed} conversation stages with good depth.`;
                statusClass = 'success';
            } else {
                simulationMessage = `Simulation completed. Focus on progressing through more conversation stages.`;
                statusClass = 'warning';
            }
            
            // Create detailed breakdown
            const breakdown = `
                <div class="simulation-breakdown mt-3">
                    <h6>📊 Simulation Analysis:</h6>
                    <div class="row">
                        <div class="col-6">
                            <small>
                                • Prospect Type: ${prospect_personality}<br>
                                • Stages Completed: ${stages_completed}/7<br>
                                • Call Outcome: ${call_outcome}
                            </small>
                        </div>
                        <div class="col-6">
                            <small>
                                • Trust Built: ${trust_level}/10<br>
                                • Interest Generated: ${interest_level}/10<br>
                                • Conversation Depth: ${conversation_depth}
                            </small>
                        </div>
                    </div>
                    ${qualification_completed ? 
                        '<div class="mt-2"><span class="badge bg-success">✅ Qualification Completed</span></div>' : 
                        '<div class="mt-2"><span class="badge bg-warning">⚠️ More Qualification Needed</span></div>'
                    }
                </div>
            `;
            
            simulationMessage += breakdown;
        } else {
            simulationMessage = 'Full cold call simulation completed!';
        }
        
        // Create simulation-specific feedback
        const simulationFeedback = `
            <div class="feedback-item simulation-result bg-${statusClass} bg-opacity-20 border-${statusClass}">
                <h5><i class="fas fa-headset me-2"></i>Simulation Results</h5>
                <div>${simulationMessage}</div>
            </div>
        `;
        
        // Add comprehensive coaching if available
        let coachingFeedback = '';
        if (coaching) {
            const coachingCategories = [
                { key: 'relationship_building', icon: 'fas fa-heart', title: 'Relationship Building' },
                { key: 'discovery', icon: 'fas fa-search', title: 'Discovery Skills' },
                { key: 'value_proposition', icon: 'fas fa-gem', title: 'Value Communication' },
                { key: 'qualification', icon: 'fas fa-check-circle', title: 'Qualification' },
                { key: 'overall', icon: 'fas fa-star', title: 'Overall Performance' }
            ];
            
            const coachingItems = coachingCategories
                .filter(category => coaching[category.key] && typeof coaching[category.key] === 'string')
                .map(category => `
                    <div class="coaching-item mb-3">
                        <h6><i class="${category.icon} me-2"></i>${category.title}</h6>
                        <p class="mb-0">${coaching[category.key]}</p>
                    </div>
                `).join('');
            
            if (coachingItems) {
                coachingFeedback = `
                    <div class="feedback-item">
                        <h5><i class="fas fa-chalkboard-teacher me-2"></i>Comprehensive Coaching</h5>
                        ${coachingItems}
                    </div>
                `;
            }
        }
        
        feedbackContent.innerHTML = simulationFeedback + coachingFeedback;
    }

    // Override mode selection to show simulation description
    selectMode(mode) {
        super.selectMode(mode);
        
        // Update start button for simulation
        const startBtn = document.getElementById('start-call-btn');
        if (startBtn && mode === 'simulation') {
            startBtn.textContent = 'Start Full Simulation';
        }
    }

    // Simulation-specific utilities
    getSimulationMetrics() {
        return {
            roleplay_type: 'simulation',
            simulation_state: this.simulationState,
            relationship_metrics: {
                trust_level: this.simulationState.trustLevel,
                interest_level: this.simulationState.interestLevel,
                conversation_depth: this.simulationState.conversationDepth
            },
            discovery_effectiveness: this.simulationState.discoveryPoints.length,
            value_communication: this.simulationState.valuePropositions.length
        };
    }

    resetSimulationState() {
        this.simulationState = {
            prospectPersonality: null,
            companyScenario: null,
            trustLevel: 0,
            interestLevel: 0,
            conversationDepth: 0,
            stagesCompleted: [],
            discoveryPoints: [],
            valuePropositions: [],
            qualificationData: {}
        };
    }

    // Override initialization to reset simulation state
    initializeModeSelection() {
        super.initializeModeSelection();
        this.resetSimulationState();
    }

    // Enhanced speaking time for realistic simulation
    async simulateSpeakingTime(text) {
        const words = text ? text.split(' ').length : 0;
        const baseTime = (words / 160) * 60 * 1000; // Realistic speaking pace
        const variability = 0.3; // Add natural variation
        const finalTime = baseTime * (1 + (Math.random() - 0.5) * variability);
        const boundedTime = Math.max(1000, Math.min(6000, finalTime));
        
        console.log(`⏱️ Realistic speaking time: ${boundedTime}ms for ${words} words`);
        
        return new Promise(resolve => setTimeout(resolve, boundedTime));
    }
}

// Export for global access
window.Roleplay4Manager = Roleplay4Manager;