// ===== COMPLETE FIXED STATIC/JS/ROLEPLAY.JS =====
class RoleplayManager {
    constructor() {
        this.currentSession = null;
        this.voiceHandler = null;
        this.isActive = false;
        this.conversationHistory = [];
        this.selectedMode = null;
        this.isProcessing = false;
        this.lastRequestTime = 0;
        this.aiIsSpeaking = false;
        
        this.init();
    }

    init() {
        console.log('Initializing RoleplayManager...');
        
        // Initialize voice handler only if VoiceHandler is available
        if (typeof VoiceHandler !== 'undefined') {
            this.voiceHandler = new VoiceHandler(this);
            console.log('Voice handler initialized');
        } else {
            console.warn('VoiceHandler not available');
        }
        
        this.setupEventListeners();
        this.loadRoleplayData();
        
        console.log('RoleplayManager initialized successfully');
    }

    setupEventListeners() {
        // Start roleplay button (prevent double-clicks)
        const startButton = document.getElementById('start-training-btn');
        if (startButton) {
            startButton.addEventListener('click', (e) => {
                e.preventDefault();
                if (!this.isProcessing) {
                    console.log('Start button clicked');
                    this.startRoleplay();
                }
            });
        }

        // End roleplay button
        const endButton = document.getElementById('end-training-btn');
        if (endButton) {
            endButton.addEventListener('click', (e) => {
                e.preventDefault();
                if (!this.isProcessing) {
                    console.log('End button clicked');
                    this.endRoleplay();
                }
            });
        }

        // Mode selection (prevent rapid clicks)
        const modeButtons = document.querySelectorAll('.mode-btn');
        modeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const mode = e.currentTarget.dataset.mode;
                console.log('Mode selected:', mode);
                this.selectMode(mode);
            });
        });

        // Abort session
        const abortButton = document.getElementById('abort-training-btn');
        if (abortButton) {
            abortButton.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Abort button clicked');
                this.abortSession();
            });
        }
    }

    loadRoleplayData() {
        const roleplayId = this.getRoleplayId();
        console.log('Loading roleplay data for ID:', roleplayId);
        if (roleplayId) {
            this.loadRoleplayInfo(roleplayId);
        }
    }

    getRoleplayId() {
        const pathMatch = window.location.pathname.match(/\/roleplay\/(\d+)/);
        return pathMatch ? parseInt(pathMatch[1]) : null;
    }

    async loadRoleplayInfo(roleplayId) {
        try {
            console.log('Fetching roleplay info for ID:', roleplayId);
            const response = await this.apiCall(`/api/roleplay/info/${roleplayId}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Roleplay info loaded:', data);
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
            const industryImages = {
                'technology': 'tech-cto.jpg',
                'finance': 'finance-vp.jpg', 
                'healthcare': 'healthcare-director.jpg',
                'manufacturing': 'manufacturing-manager.jpg',
                'education': 'education-principal.jpg'
            };
            
            const imageFile = industryImages[roleplayData.industry.toLowerCase()] || 'tech-cto.jpg';
            avatarElement.src = `/static/images/prospect-avatars/${imageFile}`;
            avatarElement.alt = `${roleplayData.job_title} prospect`;
            
            avatarElement.onerror = function() {
                this.src = 'https://via.placeholder.com/100x100/6c757d/ffffff?text=👤';
                this.onerror = null;
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
        if (!mode || this.isProcessing) return;
        
        console.log('Selecting mode:', mode);
        
        // Update mode selection UI
        const modeButtons = document.querySelectorAll('.mode-btn');
        modeButtons.forEach(btn => {
            btn.classList.remove('active', 'btn-primary', 'btn-warning', 'btn-danger');
            btn.classList.add('btn-outline-primary', 'btn-outline-warning', 'btn-outline-danger');
        });
        
        const selectedButton = document.querySelector(`[data-mode="${mode}"]`);
        if (selectedButton) {
            selectedButton.classList.remove('btn-outline-primary', 'btn-outline-warning', 'btn-outline-danger');
            const colorClass = this.getButtonColor(mode);
            selectedButton.classList.add(`btn-${colorClass}`);
        }
        
        // Store selected mode
        this.selectedMode = mode;
        
        // Update start button
        const startButton = document.getElementById('start-training-btn');
        if (startButton) {
            startButton.disabled = false;
            startButton.innerHTML = `<i class="fas fa-rocket me-2"></i>Start ${this.capitalizeFirst(mode)} Mode`;
        }
    }

    getButtonColor(mode) {
        const colors = {
            'practice': 'primary',
            'marathon': 'warning', 
            'legend': 'danger'
        };
        return colors[mode] || 'primary';
    }

    async startRoleplay() {
        if (this.isProcessing) {
            console.log('Already processing, ignoring duplicate request');
            return;
        }

        const roleplayId = this.getRoleplayId();
        const mode = this.selectedMode || 'practice';

        console.log('Starting roleplay:', { roleplayId, mode });

        if (!roleplayId) {
            this.showMessage('Invalid roleplay configuration', 'error');
            return;
        }

        // Prevent duplicate requests
        const now = Date.now();
        if (now - this.lastRequestTime < 2000) {
            console.log('Request too soon, ignoring');
            return;
        }

        this.isProcessing = true;
        this.lastRequestTime = now;
        
        // Update button state immediately
        const startButton = document.getElementById('start-training-btn');
        if (startButton) {
            startButton.disabled = true;
            startButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Starting...';
        }

        try {
            console.log('Making API call to start roleplay...');
            const response = await this.apiCall('/api/roleplay/start', {
                method: 'POST',
                body: JSON.stringify({
                    roleplay_id: roleplayId,
                    mode: mode
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Roleplay started successfully:', data);
                
                this.currentSession = data;
                this.isActive = true;
                
                // Update UI for active roleplay
                this.updateActiveRoleplayUI();
                
                // Show natural flow message
                this.updateTranscript('📞 Phone is ringing... The prospect is answering...');
                this.updateAIStatus('answering');
                
                // Auto-play initial AI response (prospect answers phone)
                if (data.initial_response) {
                    console.log('Playing initial AI response:', data.initial_response);
                    await this.playAIResponseAndWaitForUser(data.initial_response);
                } else {
                    console.log('No initial response, prompting user');
                    this.promptUserToSpeak('The prospect answered. Make your opening!');
                }
                
                this.showMessage('📞 Call connected! Listen to the prospect, then respond.', 'success');
            } else {
                const errorData = await response.json();
                console.error('Failed to start roleplay:', errorData);
                this.showMessage(errorData.error || 'Failed to start roleplay', 'error');
            }
        } catch (error) {
            console.error('Error starting roleplay:', error);
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            this.isProcessing = false;
            // Reset button if not started successfully
            if (!this.isActive && startButton) {
                startButton.disabled = false;
                startButton.innerHTML = `<i class="fas fa-rocket me-2"></i>Start ${this.capitalizeFirst(mode)} Mode`;
            }
        }
    }

    updateActiveRoleplayUI() {
        console.log('Updating UI for active roleplay');
        
        // Hide start controls, show active controls
        const modeSection = document.getElementById('mode-selection-section');
        const activeSection = document.getElementById('active-training-section');
        
        if (modeSection) modeSection.style.display = 'none';
        if (activeSection) activeSection.style.display = 'block';
        
        // Keep microphone DISABLED until AI finishes speaking
        const micButton = document.getElementById('mic-button');
        if (micButton) {
            micButton.disabled = true;
            micButton.innerHTML = '<i class="fas fa-clock"></i>';
            micButton.title = 'Wait for the prospect to finish speaking...';
        }
        
        // Clear conversation log
        this.conversationHistory = [];
        this.updateConversationLog();
    }

    async playAIResponseAndWaitForUser(text) {
        try {
            console.log('Playing AI response:', text);
            
            // Show that AI is speaking
            this.updateAIStatus('speaking');
            this.updateTranscript(`🎯 Prospect: "${text}"`);
            this.addMessageToLog('ai', text);
            this.aiIsSpeaking = true;

            // Try to play audio
            try {
                console.log('Requesting TTS for:', text.substring(0, 50));
                const response = await this.apiCall('/api/roleplay/tts', {
                    method: 'POST',
                    body: JSON.stringify({ text: text })
                });

                if (response.ok) {
                    console.log('TTS request successful');
                    const audioBlob = await response.blob();
                    
                    // Play audio if available
                    if (audioBlob.size > 100) {
                        console.log('Playing audio blob, size:', audioBlob.size);
                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audio = new Audio(audioUrl);
                        
                        // Wait for audio to finish playing
                        await new Promise((resolve) => {
                            audio.onended = () => {
                                console.log('Audio playback finished');
                                URL.revokeObjectURL(audioUrl);
                                resolve();
                            };
                            
                            audio.onerror = () => {
                                console.log('Audio playback failed, continuing silently');
                                URL.revokeObjectURL(audioUrl);
                                resolve();
                            };
                            
                            audio.play().catch((playError) => {
                                console.log('Audio play failed:', playError);
                                resolve();
                            });
                        });
                    } else {
                        console.log('Audio blob too small, simulating speaking time');
                        await this.simulateSpeakingTime(text);
                    }
                } else {
                    console.log('TTS request failed, simulating speaking time');
                    await this.simulateSpeakingTime(text);
                }
            } catch (ttsError) {
                console.log('TTS error:', ttsError);
                await this.simulateSpeakingTime(text);
            }

            // AI finished speaking - now prompt user
            this.aiIsSpeaking = false;
            console.log('AI finished speaking, prompting user to respond');
            this.promptUserToSpeak('Your turn! Click the microphone to respond...');
            
        } catch (error) {
            console.error('Error playing AI response:', error);
            this.aiIsSpeaking = false;
            await this.simulateSpeakingTime(text);
            this.promptUserToSpeak('Your turn! Click the microphone to respond...');
        }
    }

    async simulateSpeakingTime(text) {
        // Simulate realistic speaking time based on text length
        const wordsPerMinute = 150;
        const words = text.split(' ').length;
        const speakingTimeMs = (words / wordsPerMinute) * 60 * 1000;
        const minTime = 1000; // Minimum 1 second
        const maxTime = 5000; // Maximum 5 seconds
        
        const delay = Math.max(minTime, Math.min(maxTime, speakingTimeMs));
        
        console.log(`Simulating speaking time: ${delay}ms for ${words} words`);
        return new Promise(resolve => setTimeout(resolve, delay));
    }

    promptUserToSpeak(message) {
        console.log('Prompting user to speak:', message);
        
        // Update UI to show it's user's turn
        this.updateAIStatus('listening');
        this.updateTranscript(message);
        
        // Enable microphone
        const micButton = document.getElementById('mic-button');
        if (micButton) {
            micButton.disabled = false;
            micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            micButton.title = 'Click to speak (Ctrl+Space)';
            
            // Add visual pulse to draw attention
            micButton.classList.add('pulse-animation');
            setTimeout(() => {
                if (micButton.classList) {
                    micButton.classList.remove('pulse-animation');
                }
            }, 3000);
        }
        
        // Auto-start voice recognition if available
        if (this.voiceHandler && !this.voiceHandler.isListening) {
            console.log('Auto-starting voice recognition...');
            setTimeout(() => {
                this.voiceHandler.startListening();
            }, 500);
        }
    }

    async processUserInput(transcript) {
        if (!this.isActive || !this.currentSession || this.isProcessing || this.aiIsSpeaking) {
            console.log('Cannot process user input - invalid state');
            return;
        }

        console.log('Processing user input:', transcript);

        this.isProcessing = true;

        // Stop voice recognition while processing
        if (this.voiceHandler) {
            this.voiceHandler.stopListening();
        }

        // Update UI
        this.updateTranscript('Processing your response...');
        const micButton = document.getElementById('mic-button');
        if (micButton) {
            micButton.disabled = true;
            micButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }

        // Add user message to conversation
        this.addMessageToLog('user', transcript);

        try {
            console.log('Sending user input to API...');
            const response = await this.apiCall('/api/roleplay/respond', {
                method: 'POST',
                body: JSON.stringify({
                    user_input: transcript
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('AI response received:', data);
                
                // Check if call should end
                if (!data.call_continues) {
                    console.log('Call should end');
                    await this.endRoleplay(data.success);
                    return;
                }
                
                // Play AI response and wait for user
                await this.playAIResponseAndWaitForUser(data.ai_response);
                
            } else {
                const errorData = await response.json();
                console.error('API error:', errorData);
                this.showMessage(errorData.error || 'Failed to process input', 'error');
                this.promptUserToSpeak('Sorry, please try again...');
            }
        } catch (error) {
            console.error('Error processing user input:', error);
            this.showMessage('Network error during roleplay', 'error');
            this.promptUserToSpeak('Network error, please try again...');
        } finally {
            this.isProcessing = false;
        }
    }

    addMessageToLog(sender, message) {
        console.log('Adding message to log:', { sender, message: message.substring(0, 50) });
        
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
                    <div>Call will begin shortly...</div>
                </div>
            `;
            return;
        }

        logElement.innerHTML = this.conversationHistory.map(entry => `
            <div class="message ${entry.sender}" style="margin-bottom: 1rem; padding: 0.75rem; border-radius: 10px; background: ${entry.sender === 'ai' ? '#f8f9fa' : '#e3f2fd'};">
                <div class="message-content">
                    <strong>${entry.sender === 'ai' ? '📞 Prospect:' : '🎤 You:'}</strong> ${entry.message}
                </div>
                <div class="message-time" style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">
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
            const statusMessages = {
                'answering': '📞 Answering phone...',
                'speaking': '🗣️ Prospect is speaking...',
                'listening': '👂 Prospect is listening...',
                'thinking': '🤔 Thinking...'
            };
            
            statusElement.textContent = statusMessages[status] || 'AI is ready';
            statusElement.className = `ai-status ${status}`;
        }
    }

    updateTranscript(text) {
        const transcriptElement = document.getElementById('live-transcript');
        if (transcriptElement) {
            transcriptElement.textContent = text;
        }
    }

    async endRoleplay(success = false) {
        if (!this.isActive || this.isProcessing) return;

        console.log('Ending roleplay, success:', success);

        this.isProcessing = true;
        this.isActive = false;
        this.aiIsSpeaking = false;
        
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
                console.log('Roleplay ended successfully:', data);
                this.showCoachingFeedback(data.coaching);
                this.showMessage('Session completed successfully!', 'success');
            }
        } catch (error) {
            console.error('Error ending roleplay:', error);
            this.showMessage('Error ending session', 'error');
        } finally {
            this.isProcessing = false;
        }

        // Update UI
        this.updateEndedRoleplayUI();
    }

    async abortSession() {
        if (!this.isActive) return;

        console.log('Aborting session');

        try {
            await this.apiCall('/api/roleplay/session/abort', {
                method: 'POST'
            });
            
            this.isActive = false;
            this.aiIsSpeaking = false;
            
            if (this.voiceHandler) {
                this.voiceHandler.stopListening();
            }
            
            this.updateEndedRoleplayUI();
            this.showMessage('Session aborted', 'info');
        } catch (error) {
            console.error('Error aborting session:', error);
        }
    }

    updateEndedRoleplayUI() {
        console.log('Updating UI for ended roleplay');
        
        const modeSection = document.getElementById('mode-selection-section');
        const activeSection = document.getElementById('active-training-section');
        
        if (modeSection) modeSection.style.display = 'block';
        if (activeSection) activeSection.style.display = 'none';
        
        // Disable voice controls
        const micButton = document.getElementById('mic-button');
        if (micButton) {
            micButton.disabled = true;
            if (micButton.classList) {
                micButton.classList.remove('pulse-animation');
            }
        }
        
        // Reset state
        this.selectedMode = null;
        this.isProcessing = false;
        this.aiIsSpeaking = false;
        
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active', 'btn-primary', 'btn-warning', 'btn-danger');
            btn.classList.add('btn-outline-primary', 'btn-outline-warning', 'btn-outline-danger');
        });
        
        const startButton = document.getElementById('start-training-btn');
        if (startButton) {
            startButton.disabled = true;
            startButton.innerHTML = 'Select a mode to start training';
        }
    }

    showCoachingFeedback(coaching) {
        const feedbackSection = document.getElementById('coaching-feedback-section');
        if (!feedbackSection || !coaching) return;

        const content = document.getElementById('coaching-content');
        if (!content) return;

        console.log('Showing coaching feedback:', coaching);

        content.innerHTML = `
            <div class="coaching-summary mb-4">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h4><i class="fas fa-medal me-2"></i>Session Complete!</h4>
                        <p class="mb-0">Here's your personalized coaching feedback:</p>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="score-display">
                            <span class="score-number h1 text-primary">${coaching.overall_score || 0}</span>
                            <div class="score-label">Overall Score</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="coaching-categories">
                ${coaching.coaching && coaching.coaching.sales_coaching ? `
                <div class="feedback-category sales mb-3 p-3 border-start border-primary border-4">
                    <h6><i class="fas fa-chart-line text-primary me-2"></i>Sales Performance</h6>
                    <p class="mb-0">${coaching.coaching.sales_coaching}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.grammar_coaching ? `
                <div class="feedback-category grammar mb-3 p-3 border-start border-success border-4">
                    <h6><i class="fas fa-spell-check text-success me-2"></i>Grammar & Structure</h6>
                    <p class="mb-0">${coaching.coaching.grammar_coaching}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.vocabulary_coaching ? `
                <div class="feedback-category vocabulary mb-3 p-3 border-start border-info border-4">
                    <h6><i class="fas fa-book text-info me-2"></i>Vocabulary</h6>
                    <p class="mb-0">${coaching.coaching.vocabulary_coaching}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.pronunciation_coaching ? `
                <div class="feedback-category pronunciation mb-3 p-3 border-start border-warning border-4">
                    <h6><i class="fas fa-volume-up text-warning me-2"></i>Pronunciation</h6>
                    <p class="mb-0">${coaching.coaching.pronunciation_coaching}</p>
                </div>` : ''}
                
                ${coaching.coaching && coaching.coaching.rapport_assertiveness ? `
                <div class="feedback-category rapport mb-3 p-3 border-start border-danger border-4">
                    <h6><i class="fas fa-handshake text-danger me-2"></i>Rapport & Confidence</h6>
                    <p class="mb-0">${coaching.coaching.rapport_assertiveness}</p>
                </div>` : ''}
            </div>
        `;
        
        feedbackSection.style.display = 'block';
        feedbackSection.scrollIntoView({ behavior: 'smooth' });
    }

    showMessage(message, type = 'info') {
        console.log('Showing message:', { message, type });
        
        // Use global showAlert if available, otherwise create toast
        if (typeof showAlert === 'function') {
            showAlert(message, type);
        } else {
            this.createToast(message, type);
        }
    }

    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            }
        };

        console.log('Making API call to:', endpoint, options.method || 'GET');

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            console.error('Authentication required, redirecting to login');
            window.location.href = '/login';
            throw new Error('Authentication required');
        }

        return response;
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    destroy() {
        console.log('Destroying RoleplayManager');
        
        if (this.voiceHandler) {
            this.voiceHandler.destroy();
        }
        
        this.isActive = false;
        this.currentSession = null;
        this.isProcessing = false;
        this.aiIsSpeaking = false;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/roleplay/')) {
        console.log('Initializing roleplay on page load');
        window.roleplayManager = new RoleplayManager();
    }
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .pulse-animation {
        animation: pulse 1.5s infinite !important;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .ai-status.speaking {
        color: #dc3545 !important;
        font-weight: bold;
    }
    
    .ai-status.listening {
        color: #28a745 !important;
        font-weight: bold;
    }
    
    .ai-status.answering {
        color: #ffc107 !important;
        font-weight: bold;
    }
`;
document.head.appendChild(style);