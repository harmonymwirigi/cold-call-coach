// ===== FIXED STATIC/JS/ROLEPLAY.JS =====
class RoleplayManager {
    constructor() {
        this.currentSession = null;
        this.voiceHandler = null;
        this.isActive = false;
        this.conversationHistory = [];
        this.selectedMode = null;
        
        this.init();
    }

    init() {
        // Initialize voice handler only if VoiceHandler is available
        if (typeof VoiceHandler !== 'undefined') {
            this.voiceHandler = new VoiceHandler(this);
        }
        this.setupEventListeners();
        this.loadRoleplayData();
    }

    setupEventListeners() {
        // Start roleplay button
        const startButton = document.getElementById('start-training-btn');
        if (startButton) {
            startButton.addEventListener('click', () => {
                this.startRoleplay();
            });
        }

        // End roleplay button
        const endButton = document.getElementById('end-training-btn');
        if (endButton) {
            endButton.addEventListener('click', () => {
                this.endRoleplay();
            });
        }

        // Mode selection
        const modeButtons = document.querySelectorAll('.mode-btn');
        modeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = e.currentTarget.dataset.mode; // Use currentTarget instead of target
                this.selectMode(mode);
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
            const response = await this.apiCall(`/api/roleplay/info/${roleplayId}`);
            
            if (response.ok) {
                const data = await response.json();
                this.updateRoleplayUI(data);
            } else {
                console.error('Failed to load roleplay info');
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

        if (avatarElement && roleplayData.industry) {
            avatarElement.src = `/static/images/prospect-avatars/${roleplayData.industry.toLowerCase()}.jpg`;
            avatarElement.alt = `${roleplayData.job_title} prospect`;
            
            // Add error handler for missing images
            avatarElement.onerror = function() {
                this.src = '/static/images/prospect-avatars/default.jpg';
                this.onerror = null; // Prevent infinite loop
            };
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
            'Marketing Manager': ['Emily Davis', 'Chris Wilson', 'Maria Lopez'],
            'Director': ['Patricia Williams', 'James Davis', 'Linda Miller'],
            'Operations Manager': ['Robert Taylor', 'Mary Anderson', 'John Wilson']
        };

        const nameList = names[jobTitle] || ['Jordan Smith', 'Taylor Brown', 'Casey Jones'];
        return nameList[Math.floor(Math.random() * nameList.length)];
    }

    selectMode(mode) {
        if (!mode) return;
        
        // Update mode selection UI
        const modeButtons = document.querySelectorAll('.mode-btn');
        modeButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        
        const selectedButton = document.querySelector(`[data-mode="${mode}"]`);
        if (selectedButton) {
            selectedButton.classList.add('active');
        }
        
        // Store selected mode
        this.selectedMode = mode;
        
        // Update start button
        const startButton = document.getElementById('start-training-btn');
        if (startButton) {
            startButton.disabled = false;
            startButton.textContent = `Start ${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode`;
        }
    }

    async startRoleplay() {
        const roleplayId = this.getRoleplayId();
        const mode = this.selectedMode || 'practice';

        if (!roleplayId) {
            this.showMessage('Invalid roleplay configuration', 'error');
            return;
        }

        try {
            const response = await this.apiCall('/api/roleplay/start', {
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
                
                this.showMessage('Roleplay started! Speak when ready.', 'success');
            } else {
                const errorData = await response.json();
                this.showMessage(errorData.error || 'Failed to start roleplay', 'error');
            }
        } catch (error) {
            console.error('Error starting roleplay:', error);
            this.showMessage('Network error. Please try again.', 'error');
        }
    }

    updateActiveRoleplayUI() {
        // Hide start controls, show active controls
        const modeSection = document.getElementById('mode-selection-section');
        const activeSection = document.getElementById('active-training-section');
        
        if (modeSection) modeSection.style.display = 'none';
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
            const response = await this.apiCall('/api/roleplay/respond', {
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
                this.showMessage(errorData.error || 'Failed to process input', 'error');
            }
        } catch (error) {
            console.error('Error processing user input:', error);
            this.showMessage('Network error during roleplay', 'error');
        }
    }

    async playAIResponse(text) {
        try {
            // Show that AI is speaking
            this.updateAIStatus('speaking');
            
            const response = await this.apiCall('/api/roleplay/tts', {
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

        if (this.conversationHistory.length === 0) {
            logElement.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="fas fa-phone-alt fa-2x mb-2 opacity-50"></i>
                    <div>Start the roleplay to begin conversation</div>
                </div>
            `;
            return;
        }

        logElement.innerHTML = this.conversationHistory.map(entry => `
            <div class="message ${entry.sender}" style="margin-bottom: 1rem; padding: 0.5rem;">
                <div class="message-content" style="font-weight: ${entry.sender === 'ai' ? 'bold' : 'normal'}">
                    <strong>${entry.sender === 'ai' ? 'AI:' : 'You:'}</strong> ${entry.message}
                </div>
                <div class="message-time" style="font-size: 0.8rem; color: #666;">
                    ${entry.timestamp.toLocaleTimeString()}
                </div>
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
            const response = await this.apiCall('/api/roleplay/end', {
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
        const modeSection = document.getElementById('mode-selection-section');
        const activeSection = document.getElementById('active-training-section');
        
        if (modeSection) modeSection.style.display = 'block';
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
        
        const startButton = document.getElementById('start-training-btn');
        if (startButton) {
            startButton.disabled = true;
            startButton.textContent = 'Select a mode to start training';
        }
    }

    showCoachingFeedback(coaching) {
        const feedbackSection = document.getElementById('coaching-feedback-section');
        if (!feedbackSection || !coaching) return;

        const content = document.getElementById('coaching-content');
        if (!content) return;

        content.innerHTML = `
            <h4>Coaching Feedback</h4>
            <div class="coaching-categories">
                ${coaching.coaching && coaching.coaching.sales ? `<div class="feedback-category sales mb-3">
                    <h6><i class="fas fa-chart-line"></i> Sales</h6>
                    <p>${coaching.coaching.sales}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.grammar ? `<div class="feedback-category grammar mb-3">
                    <h6><i class="fas fa-spell-check"></i> Grammar</h6>
                    <p>${coaching.coaching.grammar}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.vocabulary ? `<div class="feedback-category vocabulary mb-3">
                    <h6><i class="fas fa-book"></i> Vocabulary</h6>
                    <p>${coaching.coaching.vocabulary}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.pronunciation ? `<div class="feedback-category pronunciation mb-3">
                    <h6><i class="fas fa-volume-up"></i> Pronunciation</h6>
                    <p>${coaching.coaching.pronunciation}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.rapport ? `<div class="feedback-category rapport mb-3">
                    <h6><i class="fas fa-handshake"></i> Rapport</h6>
                    <p>${coaching.coaching.rapport}</p>
                </div>` : ''}
            </div>
            
            <div class="coaching-summary">
                <div class="score-display text-center mb-3">
                    <span class="score-number h2">${coaching.overall_score || 0}/100</span>
                    <div class="score-label">Overall Score</div>
                </div>
                
                <div class="next-steps">
                    <h6>Next Steps:</h6>
                    <p>${coaching.next_steps || 'Keep practicing to improve your skills!'}</p>
                </div>
            </div>
        `;
        
        feedbackSection.style.display = 'block';
    }

    showMessage(message, type = 'info') {
        // Use global showAlert if available, otherwise fallback to console
        if (typeof showAlert === 'function') {
            showAlert(message, type);
        } else if (window.coldCallingApp && typeof window.coldCallingApp.showMessage === 'function') {
            window.coldCallingApp.showMessage(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
            alert(message); // Fallback to alert
        }
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            }
        };

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            // Redirect to login if unauthorized
            window.location.href = '/login';
            throw new Error('Authentication required');
        }

        return response;
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