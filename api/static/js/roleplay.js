

// ===== STATIC/JS/ROLEPLAY.JS =====
class RoleplayManager {
    constructor() {
        this.currentSession = null;
        this.voiceHandler = null;
        this.isActive = false;
        this.conversationHistory = [];
        
        this.init();
    }

    init() {
        this.voiceHandler = new VoiceHandler(this);
        this.setupEventListeners();
        this.loadRoleplayData();
    }

    setupEventListeners() {
        // Start roleplay button
        const startButton = document.getElementById('start-roleplay-btn');
        if (startButton) {
            startButton.addEventListener('click', () => {
                this.startRoleplay();
            });
        }

        // End roleplay button
        const endButton = document.getElementById('end-roleplay-btn');
        if (endButton) {
            endButton.addEventListener('click', () => {
                this.endRoleplay();
            });
        }

        // Mode selection
        const modeButtons = document.querySelectorAll('.mode-btn');
        modeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectMode(e.target.dataset.mode);
            });
        });
    }

    loadRoleplayData() {
        // Get roleplay ID from URL or page data
        const roleplayId = this.getRoleplayId();
        if (roleplayId) {
            this.loadRoleplayInfo(roleplayId);
        }
    }

    getRoleplayId() {
        // Extract from URL path
        const pathMatch = window.location.pathname.match(/\/roleplay\/(\d+)/);
        return pathMatch ? parseInt(pathMatch[1]) : null;
    }

    async loadRoleplayInfo(roleplayId) {
        try {
            const response = await window.coldCallingApp.apiCall(`/api/roleplay/info/${roleplayId}`);
            
            if (response.ok) {
                const data = await response.json();
                this.updateRoleplayUI(data);
            }
        } catch (error) {
            console.error('Error loading roleplay info:', error);
        }
    }

    updateRoleplayUI(roleplayData) {
        // Update roleplay title and description
        const titleElement = document.getElementById('roleplay-title');
        if (titleElement) {
            titleElement.textContent = roleplayData.name;
        }

        const descElement = document.getElementById('roleplay-description');
        if (descElement) {
            descElement.textContent = roleplayData.description;
        }

        // Update prospect avatar and info
        this.updateProspectInfo(roleplayData);
    }

    updateProspectInfo(roleplayData) {
        const avatarElement = document.getElementById('prospect-avatar');
        const nameElement = document.getElementById('prospect-name');
        const titleElement = document.getElementById('prospect-title');
        const industryElement = document.getElementById('prospect-industry');

        if (avatarElement) {
            avatarElement.src = `/static/images/prospect-avatars/${roleplayData.industry.toLowerCase()}.jpg`;
            avatarElement.alt = `${roleplayData.job_title} prospect`;
        }

        if (nameElement) {
            nameElement.textContent = this.generateProspectName(roleplayData.job_title);
        }

        if (titleElement) {
            titleElement.textContent = roleplayData.job_title;
        }

        if (industryElement) {
            industryElement.textContent = roleplayData.industry;
        }
    }

    generateProspectName(jobTitle) {
        const names = {
            'CEO': ['Alex Morgan', 'Sarah Chen', 'Michael Rodriguez'],
            'CTO': ['David Kim', 'Jennifer Walsh', 'Robert Singh'],
            'VP of Sales': ['Lisa Thompson', 'Mark Johnson', 'Amanda Garcia'],
            'Marketing Manager': ['Emily Davis', 'Chris Wilson', 'Maria Lopez']
        };

        const nameList = names[jobTitle] || ['Jordan Smith', 'Taylor Brown', 'Casey Jones'];
        return nameList[Math.floor(Math.random() * nameList.length)];
    }

    selectMode(mode) {
        // Update mode selection UI
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        
        // Store selected mode
        this.selectedMode = mode;
        
        // Update start button
        const startButton = document.getElementById('start-roleplay-btn');
        if (startButton) {
            startButton.disabled = false;
            startButton.textContent = `Start ${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode`;
        }
    }

    async startRoleplay() {
        const roleplayId = this.getRoleplayId();
        const mode = this.selectedMode || 'practice';

        if (!roleplayId) {
            window.coldCallingApp.showMessage('Invalid roleplay configuration', 'error');
            return;
        }

        try {
            const response = await window.coldCallingApp.apiCall('/api/roleplay/start', {
                method: 'POST',
                body: JSON.stringify({
                    roleplay_id: roleplayId,
                    mode: mode
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentSession = data;
                this.isActive = true;
                
                // Update UI for active roleplay
                this.updateActiveRoleplayUI();
                
                // Play initial AI response
                if (data.initial_response) {
                    await this.playAIResponse(data.initial_response);
                }
                
                window.coldCallingApp.showMessage('Roleplay started! Speak when ready.', 'success');
            } else {
                const errorData = await response.json();
                window.coldCallingApp.showMessage(errorData.error || 'Failed to start roleplay', 'error');
            }
        } catch (error) {
            console.error('Error starting roleplay:', error);
            window.coldCallingApp.showMessage('Network error. Please try again.', 'error');
        }
    }

    updateActiveRoleplayUI() {
        // Hide start controls, show active controls
        const startSection = document.getElementById('start-section');
        const activeSection = document.getElementById('active-section');
        
        if (startSection) startSection.style.display = 'none';
        if (activeSection) activeSection.style.display = 'block';
        
        // Enable voice controls
        const micButton = document.getElementById('mic-button');
        if (micButton) {
            micButton.disabled = false;
        }
        
        // Clear conversation log
        this.conversationHistory = [];
        this.updateConversationLog();
    }

    async processUserInput(transcript) {
        if (!this.isActive || !this.currentSession) {
            return;
        }

        // Add user message to conversation
        this.addMessageToLog('user', transcript);

        try {
            const response = await window.coldCallingApp.apiCall('/api/roleplay/respond', {
                method: 'POST',
                body: JSON.stringify({
                    user_input: transcript
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Add AI response to conversation
                this.addMessageToLog('ai', data.ai_response);
                
                // Play AI response
                await this.playAIResponse(data.ai_response);
                
                // Check if call should end
                if (!data.call_continues) {
                    await this.endRoleplay(data.success);
                }
            } else {
                const errorData = await response.json();
                window.coldCallingApp.showMessage(errorData.error || 'Failed to process input', 'error');
            }
        } catch (error) {
            console.error('Error processing user input:', error);
            window.coldCallingApp.showMessage('Network error during roleplay', 'error');
        }
    }

    async playAIResponse(text) {
        try {
            // Show that AI is speaking
            this.updateAIStatus('speaking');
            
            const response = await window.coldCallingApp.apiCall('/api/roleplay/tts', {
                method: 'POST',
                body: JSON.stringify({ text: text })
            });

            if (response.ok) {
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                
                audio.onended = () => {
                    this.updateAIStatus('listening');
                    URL.revokeObjectURL(audioUrl);
                };
                
                audio.onerror = () => {
                    console.error('Audio playback error');
                    this.updateAIStatus('listening');
                    URL.revokeObjectURL(audioUrl);
                };
                
                await audio.play();
            } else {
                console.error('TTS failed');
                this.updateAIStatus('listening');
            }
        } catch (error) {
            console.error('Error playing AI response:', error);
            this.updateAIStatus('listening');
        }
    }

    playImpatientPrompt() {
        const prompts = [
            "Hello? Are you still with me?",
            "Can you hear me?",
            "Just checking you're there…",
            "Still on the line?"
        ];
        
        const randomPrompt = prompts[Math.floor(Math.random() * prompts.length)];
        this.playAIResponse(randomPrompt);
    }

    handleSilenceTimeout() {
        window.coldCallingApp.showMessage('Call ended due to silence', 'warning');
        this.endRoleplay(false);
    }

    addMessageToLog(sender, message) {
        this.conversationHistory.push({
            sender: sender,
            message: message,
            timestamp: new Date()
        });
        
        this.updateConversationLog();
    }

    updateConversationLog() {
        const logElement = document.getElementById('conversation-log');
        if (!logElement) return;

        logElement.innerHTML = this.conversationHistory.map(entry => `
            <div class="message ${entry.sender}">
                <div class="message-content">${entry.message}</div>
                <div class="message-time">${entry.timestamp.toLocaleTimeString()}</div>
            </div>
        `).join('');

        // Scroll to bottom
        logElement.scrollTop = logElement.scrollHeight;
    }

    updateAIStatus(status) {
        const statusElement = document.getElementById('ai-status');
        if (statusElement) {
            statusElement.textContent = status === 'speaking' ? 'AI is speaking...' : 'AI is listening...';
            statusElement.className = `ai-status ${status}`;
        }
    }

    async endRoleplay(success = false) {
        if (!this.isActive) return;

        this.isActive = false;
        
        // Stop voice handler
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
        }

        try {
            const response = await window.coldCallingApp.apiCall('/api/roleplay/end', {
                method: 'POST',
                body: JSON.stringify({ success: success })
            });

            if (response.ok) {
                const data = await response.json();
                this.showCoachingFeedback(data.coaching);
            }
        } catch (error) {
            console.error('Error ending roleplay:', error);
        }

        // Update UI
        this.updateEndedRoleplayUI();
    }

    updateEndedRoleplayUI() {
        const startSection = document.getElementById('start-section');
        const activeSection = document.getElementById('active-section');
        
        if (startSection) startSection.style.display = 'block';
        if (activeSection) activeSection.style.display = 'none';
        
        // Disable voice controls
        const micButton = document.getElementById('mic-button');
        if (micButton) {
            micButton.disabled = true;
        }
        
        // Reset mode selection
        this.selectedMode = null;
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }

    showCoachingFeedback(coaching) {
        const feedbackSection = document.getElementById('coaching-feedback');
        if (!feedbackSection || !coaching) return;

        feedbackSection.innerHTML = `
            <h4>Coaching Feedback</h4>
            <div class="coaching-categories">
                ${coaching.coaching.sales ? `<div class="feedback-category sales">
                    <h6><i class="fas fa-chart-line"></i> Sales</h6>
                    <p>${coaching.coaching.sales}</p>
                </div>` : ''}
                
                ${coaching.coaching.grammar ? `<div class="feedback-category grammar">
                    <h6><i class="fas fa-spell-check"></i> Grammar</h6>
                    <p>${coaching.coaching.grammar}</p>
                </div>` : ''}
                
                ${coaching.coaching.vocabulary ? `<div class="feedback-category vocabulary">
                    <h6><i class="fas fa-book"></i> Vocabulary</h6>
                    <p>${coaching.coaching.vocabulary}</p>
                </div>` : ''}
                
                ${coaching.coaching.pronunciation ? `<div class="feedback-category pronunciation">
                    <h6><i class="fas fa-volume-up"></i> Pronunciation</h6>
                    <p>${coaching.coaching.pronunciation}</p>
                </div>` : ''}
                
                ${coaching.coaching.rapport ? `<div class="feedback-category rapport">
                    <h6><i class="fas fa-handshake"></i> Rapport</h6>
                    <p>${coaching.coaching.rapport}</p>
                </div>` : ''}
            </div>
            
            <div class="coaching-summary">
                <div class="score-display">
                    <span class="score-number">${coaching.overall_score}/100</span>
                    <span class="score-label">Overall Score</span>
                </div>
                
                <div class="next-steps">
                    <h6>Next Steps:</h6>
                    <p>${coaching.next_steps}</p>
                </div>
            </div>
        `;
        
        feedbackSection.style.display = 'block';
    }

    destroy() {
        if (this.voiceHandler) {
            this.voiceHandler.destroy();
        }
        
        this.isActive = false;
        this.currentSession = null;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/roleplay/')) {
        window.roleplayManager = new RoleplayManager();
    }
});