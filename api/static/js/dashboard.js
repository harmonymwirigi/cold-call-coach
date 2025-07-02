// ===== FIXED: STATIC/JS/DASHBOARD.JS - CORRECT ROLEPLAY 2 UNLOCK LOGIC =====

class Dashboard {
    constructor() {
        this.userProfile = null;
        this.userStats = null;
        this.roleplayAccess = null;
        this.userProgress = null; // Add this to store progress data
        this.isLoading = false;
        
        this.initialize();
    }

    initialize() {
        console.log('Initializing Dashboard');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load dashboard data
        this.loadDashboard();
        
        // Load progress data
        this.loadDashboardProgress();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDashboard());
        }
        
        // Roleplay card clicks
        document.addEventListener('click', (e) => {
            const roleplayCard = e.target.closest('.roleplay-card');
            if (roleplayCard) {
                const roleplayId = parseInt(roleplayCard.dataset.roleplayId);
                if (roleplayCard.classList.contains('unlocked')) {
                    this.navigateToRoleplay(roleplayId);
                } else {
                    this.showUnlockInfo(roleplayId);
                }
            }
        });
        
        // Stats refresh
        setInterval(() => {
            if (!this.isLoading) {
                this.loadUserStats();
                this.loadDashboardProgress(); // Also refresh progress
            }
        }, 60000); // Refresh stats every minute
    }

    async loadDashboard() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(true);

        try {
            // Load all dashboard data
            await Promise.all([
                this.loadUserProfile(),
                this.loadUserStats(),
                this.loadRoleplayAccess(),
                this.loadRecentSessions(),
                this.loadDashboardProgress() // Make sure progress is loaded
            ]);

            // Update UI
            this.updateUserInfo();
            this.updateStatsDisplay();
            this.updateUsageMeter();
            this.updateRoleplayGrid();
            this.updateRecentSessions();

        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    async loadUserProfile() {
        try {
            const response = await fetch('/api/user/profile', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.userProfile = data.profile;
                this.roleplayAccess = data.roleplay_access;
            } else if (response.status === 401) {
                // Redirect to login if unauthorized
                window.location.href = '/login';
            } else {
                throw new Error('Failed to load user profile');
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            throw error;
        }
    }

    async loadUserStats() {
        try {
            const response = await fetch('/api/user/stats', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
                }
            });

            if (response.ok) {
                this.userStats = await response.json();
            } else {
                throw new Error('Failed to load user stats');
            }
        } catch (error) {
            console.error('Error loading user stats:', error);
            // Don't throw - stats are not critical
        }
    }

    async loadRoleplayAccess() {
        // Access info is loaded with profile
        // Individual roleplay unlock status will be checked when needed
    }

    async loadRecentSessions() {
        try {
            const response = await fetch('/api/user/sessions?limit=5', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.recentSessions = data.sessions || [];
            } else {
                throw new Error('Failed to load recent sessions');
            }
        } catch (error) {
            console.error('Error loading recent sessions:', error);
            this.recentSessions = [];
        }
    }

    updateUserInfo() {
        if (!this.userProfile) return;

        // Update user name
        const nameElement = document.getElementById('user-first-name');
        if (nameElement) {
            nameElement.textContent = this.userProfile.first_name;
        }

        // Update access level badge
        const accessBadge = document.getElementById('access-level-badge');
        const accessText = document.getElementById('access-level-text');
        
        if (accessBadge && accessText) {
            const accessLevel = this.userProfile.access_level;
            const levelNames = {
                'limited_trial': 'Trial',
                'unlimited_basic': 'Basic',
                'unlimited_pro': 'Pro'
            };
            
            accessText.textContent = levelNames[accessLevel] || accessLevel;
            
            // Update badge styling
            accessBadge.className = 'access-level-badge';
            accessBadge.classList.add(`access-level-${accessLevel}`);
        }
    }

    updateStatsDisplay() {
        if (!this.userStats) {
            this.setDefaultStats();
            return;
        }

        const statsGrid = document.getElementById('stats-grid');
        if (!statsGrid) return;

        const stats = [
            {
                icon: 'fas fa-phone',
                number: this.userStats.total_sessions,
                label: 'Total Sessions',
                color: 'primary'
            },
            {
                icon: 'fas fa-clock',
                number: `${Math.floor(this.userStats.total_minutes / 60)}h ${this.userStats.total_minutes % 60}m`,
                label: 'Total Practice',
                color: 'info'
            },
            {
                icon: 'fas fa-chart-line',
                number: `${this.userStats.success_rate}%`,
                label: 'Success Rate',
                color: this.userStats.success_rate >= 70 ? 'success' : this.userStats.success_rate >= 50 ? 'warning' : 'danger'
            },
            {
                icon: 'fas fa-trophy',
                number: this.userStats.successful_sessions,
                label: 'Successful Calls',
                color: 'success'
            },
            {
                icon: 'fas fa-calendar-week',
                number: this.userStats.sessions_this_week,
                label: 'This Week',
                color: 'secondary'
            },
            {
                icon: 'fas fa-star',
                number: this.userStats.favorite_roleplay || 'None yet',
                label: 'Favorite Module',
                color: 'warning'
            }
        ];

        statsGrid.innerHTML = stats.map(stat => `
            <div class="stat-card">
                <div class="stat-icon text-${stat.color}">
                    <i class="${stat.icon}"></i>
                </div>
                <div class="stat-number text-${stat.color}">${stat.number}</div>
                <div class="stat-label">${stat.label}</div>
            </div>
        `).join('');
    }

    setDefaultStats() {
        const statsGrid = document.getElementById('stats-grid');
        if (!statsGrid) return;

        statsGrid.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon text-primary">
                    <i class="fas fa-phone"></i>
                </div>
                <div class="stat-number text-primary">0</div>
                <div class="stat-label">Total Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon text-info">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="stat-number text-info">0m</div>
                <div class="stat-label">Total Practice</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon text-secondary">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="stat-number text-secondary">0%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        `;
    }

    updateUsageMeter() {
        if (!this.userProfile) return;

        const usageText = document.getElementById('usage-text');
        const usageProgress = document.getElementById('usage-progress');
        
        if (!usageText || !usageProgress) return;

        const accessLevel = this.userProfile.access_level;
        const monthlyUsage = this.userProfile.monthly_usage_minutes || 0;
        const lifetimeUsage = this.userProfile.lifetime_usage_minutes || 0;

        let usageInfo = '';
        let percentage = 0;
        let progressClass = 'bg-success';

        if (accessLevel === 'limited_trial') {
            const trialLimit = 180; // 3 hours
            const remaining = Math.max(0, trialLimit - lifetimeUsage);
            percentage = Math.min((lifetimeUsage / trialLimit) * 100, 100);
            
            usageInfo = `${Math.floor(remaining / 60)}h ${remaining % 60}m remaining`;
            
            if (percentage > 80) progressClass = 'bg-danger';
            else if (percentage > 60) progressClass = 'bg-warning';
        } else {
            const monthlyLimit = 3000; // 50 hours
            const remaining = Math.max(0, monthlyLimit - monthlyUsage);
            percentage = Math.min((monthlyUsage / monthlyLimit) * 100, 100);
            
            usageInfo = `${Math.floor(remaining / 60)}h ${remaining % 60}m remaining this month`;
            
            if (percentage > 80) progressClass = 'bg-warning';
            else if (percentage > 90) progressClass = 'bg-danger';
        }

        usageText.textContent = usageInfo;
        usageProgress.style.width = `${percentage}%`;
        usageProgress.className = `progress-bar ${progressClass}`;
    }

    updateRoleplayGrid() {
        const roleplayGrid = document.getElementById('roleplay-grid');
        if (!roleplayGrid) return;

        const roleplays = [
            {
                id: 1,
                name: 'Opener + Early Objections',
                description: 'Master call openings and handle early objections with confidence',
                icon: 'fas fa-phone-alt',
                difficulty: 'Beginner',
                color: 'success'
            },
            {
                id: 2,
                name: 'Pitch + Objections + Close',
                description: 'Perfect your pitch and close more meetings',
                icon: 'fas fa-bullseye',
                difficulty: 'Intermediate',
                color: 'primary'
            },
            {
                id: 3,
                name: 'Warm-up Challenge',
                description: '25 rapid-fire questions to sharpen your skills',
                icon: 'fas fa-fire',
                difficulty: 'Quick',
                color: 'warning'
            },
            {
                id: 4,
                name: 'Full Cold Call Simulation',
                description: 'Complete end-to-end cold call practice',
                icon: 'fas fa-headset',
                difficulty: 'Advanced',
                color: 'info'
            },
            {
                id: 5,
                name: 'Power Hour Challenge',
                description: '10 consecutive calls to test your endurance',
                icon: 'fas fa-bolt',
                difficulty: 'Expert',
                color: 'danger'
            }
        ];

        roleplayGrid.innerHTML = roleplays.map(roleplay => {
            const isUnlocked = this.isRoleplayUnlocked(roleplay.id);
            const unlockInfo = this.getRoleplayUnlockInfo(roleplay.id);
            
            return this.createRoleplayCard(roleplay, isUnlocked, unlockInfo);
        }).join('');
    }

    // FIXED: Updated unlock logic for Roleplay 2
    isRoleplayUnlocked(roleplayId) {
        // Roleplay 1 is always unlocked
        if (roleplayId === 1) return true;
        
        // Roleplay 2 is unlocked when Marathon Mode (1.2) is passed
        if (roleplayId === 2) {
            return this.isMarathonModePassed();
        }
        
        // Roleplay 3 is always unlocked
        if (roleplayId === 3) return true;
        
        // Roleplays 4 and 5 require advanced completion
        if (roleplayId === 4 || roleplayId === 5) {
            return this.isRoleplayTwoPassed();
        }
        
        // Default to checking roleplayAccess
        if (!this.roleplayAccess) return false;
        
        const access = this.roleplayAccess[roleplayId];
        return access ? access.unlocked : false;
    }

    // FIXED: Helper method to check Marathon Mode status
    isMarathonModePassed() {
        if (!this.userProgress) return false;
        
        const marathonProgress = this.userProgress['1.2'];
        if (!marathonProgress) return false;
        
        // Check if marathon was passed (6 out of 10 calls)
        return marathonProgress.marathon_passed === true;
    }

    // Helper method to check if Roleplay 2 is passed
    isRoleplayTwoPassed() {
        if (!this.userProgress) return false;
        
        const rp2Progress = this.userProgress['2.1'];
        if (!rp2Progress) return false;
        
        // Check if score is 70 or above
        return rp2Progress.best_score >= 70;
    }

    getRoleplayUnlockInfo(roleplayId) {
        // FIXED: Updated unlock requirements
        const unlockRequirements = {
            1: { unlocked: true, unlock_condition: 'Always available' },
            2: { 
                unlocked: this.isMarathonModePassed(), 
                unlock_condition: 'Complete Marathon Mode (6/10 calls)'
            },
            3: { unlocked: true, unlock_condition: 'Always available' },
            4: { 
                unlocked: this.isRoleplayTwoPassed(), 
                unlock_condition: 'Pass Post-Pitch Practice (70+ score)'
            },
            5: { 
                unlocked: this.isRoleplayTwoPassed(), 
                unlock_condition: 'Pass Advanced Marathon Mode'
            }
        };
        
        return unlockRequirements[roleplayId] || { unlocked: false, unlock_condition: 'Requirements not met' };
    }

    createRoleplayCard(roleplay, isUnlocked, unlockInfo) {
        const lockIcon = isUnlocked ? 'fas fa-unlock text-success' : 'fas fa-lock text-muted';
        const cardClass = isUnlocked ? 'roleplay-card unlocked' : 'roleplay-card locked';
        
        let statusBadge = '';
        let footer = '';
        
        if (isUnlocked) {
            statusBadge = '<span class="badge bg-success">Unlocked</span>';
            footer = `
                <div class="card-footer">
                    <button class="btn btn-${roleplay.color} w-100">
                        <i class="fas fa-play me-2"></i>Start Training
                    </button>
                </div>
            `;
        } else {
            statusBadge = '<span class="badge bg-secondary">Locked</span>';
            const condition = unlockInfo ? unlockInfo.unlock_condition : 'Complete previous modules';
            footer = `
                <div class="card-footer text-muted">
                    <small><i class="fas fa-info-circle me-1"></i>${condition}</small>
                </div>
            `;
        }

        return `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="${cardClass}" data-roleplay-id="${roleplay.id}">
                    <div class="card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div class="roleplay-icon text-${roleplay.color}">
                                    <i class="${roleplay.icon}"></i>
                                </div>
                                <div class="d-flex flex-column align-items-end">
                                    ${statusBadge}
                                    <i class="${lockIcon} mt-2"></i>
                                </div>
                            </div>
                            <h5 class="card-title">${roleplay.name}</h5>
                            <p class="card-text text-muted">${roleplay.description}</p>
                            <div class="difficulty-badge">
                                <span class="badge bg-light text-dark">${roleplay.difficulty}</span>
                            </div>
                        </div>
                        ${footer}
                    </div>
                </div>
            </div>
        `;
    }

    updateRecentSessions() {
        const sessionsTable = document.getElementById('recent-sessions');
        if (!sessionsTable) return;

        if (!this.recentSessions || this.recentSessions.length === 0) {
            sessionsTable.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        No sessions yet. Start your first roleplay to see your progress!
                    </td>
                </tr>
            `;
            return;
        }

        sessionsTable.innerHTML = this.recentSessions.map(session => {
            const date = new Date(session.completed_at || session.created_at || session.started_at).toLocaleDateString();
            const time = new Date(session.completed_at || session.created_at || session.started_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const duration = session.duration_minutes ? `${session.duration_minutes}m` : 'N/A';
            const resultIcon = session.success ? 
                '<i class="fas fa-check-circle text-success"></i>' : 
                '<i class="fas fa-times-circle text-danger"></i>';
            const resultText = session.success ? 'Pass' : 'Needs Work';
            const score = session.score || 'N/A';
            
            const roleplayNames = {
                '1.1': 'Practice Mode',
                '1.2': 'Marathon Mode', 
                '1.3': 'Legend Mode',
                '2.1': 'Post-Pitch Practice',
                '2.2': 'Advanced Marathon',
                '3': 'Warm-up',
                '4': 'Full Call',
                '5': 'Power Hour'
            };
            
            const roleplayName = roleplayNames[session.roleplay_id] || `Roleplay ${session.roleplay_id}`;
            const mode = session.mode ? session.mode.charAt(0).toUpperCase() + session.mode.slice(1) : 'Practice';

            return `
                <tr>
                    <td>
                        <div>${date}</div>
                        <small class="text-muted">${time}</small>
                    </td>
                    <td>
                        <div>${roleplayName}</div>
                        <small class="text-muted">${mode} Mode</small>
                    </td>
                    <td>
                        <span class="badge bg-primary">${mode}</span>
                    </td>
                    <td>${duration}</td>
                    <td>
                        <div class="d-flex align-items-center">
                            ${resultIcon}
                            <span class="ms-1">${resultText}</span>
                        </div>
                    </td>
                    <td>
                        <span class="fw-medium">${score}</span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    navigateToRoleplay(roleplayId) {
        window.location.href = `/roleplay/${roleplayId}`;
    }

    showUnlockInfo(roleplayId) {
        const unlockInfo = this.getRoleplayUnlockInfo(roleplayId);
        const condition = unlockInfo ? unlockInfo.unlock_condition : 'Complete previous modules to unlock';
        
        alert(`This module is locked.\n\nRequirement: ${condition}`);
    }

    showLoading(show) {
        const elements = ['stats-grid', 'roleplay-grid', 'recent-sessions'];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                if (show) {
                    element.innerHTML = `
                        <div class="text-center py-4">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <div class="mt-2">Loading...</div>
                        </div>
                    `;
                }
            }
        });
    }

    showError(message) {
        // You could implement a toast notification here
        console.error('Dashboard Error:', message);
        
        // For now, show an alert
        alert(`Error: ${message}`);
    }

    // Public methods for external access
    refresh() {
        this.loadDashboard();
    }

    getUserProfile() {
        return this.userProfile;
    }

    getUserStats() {
        return this.userStats;
    }

    // ===== FIXED: PROGRESS TRACKING METHODS =====
    
    async loadDashboardProgress() {
        try {
            console.log('🏆 Loading dashboard progress...');
            
            const response = await fetch('/api/user/roleplay-progress', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.userProgress = data.progress; // FIXED: Store progress data
                this.updateDashboardProgress(data);
                console.log('✅ Dashboard progress loaded successfully');
            } else {
                console.warn(`Failed to load progress data: ${response.status}`);
                // Don't throw error, just log warning
            }
        } catch (error) {
            console.error('Error loading dashboard progress:', error);
            // Don't throw error, dashboard can still work without progress data
        }
    }
    
    updateDashboardProgress(data) {
        const { progress, completion_stats, recommendations } = data;
        
        // Update overview stats
        if (completion_stats) {
            const completionEl = document.getElementById('completion-percentage');
            const avgScoreEl = document.getElementById('average-score');
            const totalAttemptsEl = document.getElementById('total-attempts');
            const currentLevelEl = document.getElementById('current-level');
            
            if (completionEl) completionEl.textContent = Math.round(completion_stats.completion_rate || 0) + '%';
            if (avgScoreEl) avgScoreEl.textContent = Math.round(completion_stats.average_score || 0);
            if (totalAttemptsEl) totalAttemptsEl.textContent = completion_stats.total_sessions || 0;
            if (currentLevelEl) {
                // Determine level based on progress
                const avgScore = completion_stats.average_score || 0;
                let level = 'Beginner';
                if (avgScore >= 85) level = 'Expert';
                else if (avgScore >= 70) level = 'Advanced';
                else if (avgScore >= 50) level = 'Intermediate';
                
                currentLevelEl.textContent = level;
            }
        }
        
        // Update Roleplay progress
        if (progress) {
            this.updateRoleplayProgress('1.1', progress['1.1']);
            this.updateRoleplayProgress('1.2', progress['1.2']);
            this.updateRoleplayProgress('1.3', progress['1.3']);
        }
        
        // Update recommendations
        this.updateRecommendations(recommendations || []);
        
        // FIXED: Update overall status with correct logic
        this.updateRoleplayStatus(progress || {});
    }
    
    updateRoleplayProgress(roleplayId, progressData) {
        if (!progressData) return;
        
        const cleanId = roleplayId.replace('.', '-');
        const scoreElement = document.getElementById(`rp${cleanId}-score`);
        const progressElement = document.getElementById(`rp${cleanId}-progress`);
        
        if (scoreElement && progressData.best_score > 0) {
            if (roleplayId === '1.2' && progressData.marathon_passed) {
                scoreElement.textContent = `Passed (${progressData.marathon_best_run || 6}/10)`;
                scoreElement.className = 'text-success';
            } else {
                scoreElement.textContent = `${progressData.best_score}/100`;
                scoreElement.className = progressData.passed ? 'text-success' : 'text-warning';
            }
        }
        
        if (progressElement) {
            let progressPercent = 0;
            if (roleplayId === '1.2' && progressData.marathon_passed) {
                progressPercent = 100; // Marathon passed = 100%
            } else {
                progressPercent = Math.min(100, progressData.best_score || 0);
            }
            progressElement.style.width = progressPercent + '%';
        }
    }
    
    updateRecommendations(recommendations) {
        const container = document.getElementById('recommendations-list');
        if (!container) return;
        
        if (recommendations.length === 0) {
            // Check if Marathon is passed and suggest Roleplay 2
            if (this.isMarathonModePassed()) {
                container.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-star me-2"></i>
                        Congratulations! You've unlocked <strong>Roleplay 2: Post-Pitch Practice</strong>
                        <a href="/roleplay/2" class="btn btn-sm btn-primary ms-2">Start Now</a>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-lightbulb me-2"></i>
                        Complete Marathon Mode to unlock advanced training modules!
                        <a href="/roleplay/1" class="btn btn-sm btn-primary ms-2">Continue</a>
                    </div>
                `;
            }
            return;
        }
        
        container.innerHTML = recommendations.map(rec => `
            <div class="alert alert-${rec.priority === 'high' ? 'warning' : 'info'}">
                <i class="fas fa-${rec.priority === 'high' ? 'exclamation-triangle' : 'arrow-right'} me-2"></i>
                ${rec.reason || rec.message || 'Continue your training!'}
                ${rec.roleplay_id ? `<a href="/roleplay/${rec.roleplay_id}" class="btn btn-sm btn-outline-primary ms-2">Start</a>` : ''}
            </div>
        `).join('');
    }
    
    // FIXED: Correct status update logic
    updateRoleplayStatus(progress) {
        console.log('Updating roleplay status with progress:', progress);
        
        // Update Roleplay 1 status
        const rp1Status = document.getElementById('rp1-status');
        if (rp1Status) {
            const legendCompleted = progress['1.3']?.legend_completed;
            const marathonPassed = progress['1.2']?.marathon_passed;
            const practiceAttempts = progress['1.1']?.total_attempts || 0;
            
            if (legendCompleted) {
                rp1Status.textContent = 'Mastered';
                rp1Status.className = 'badge bg-success';
            } else if (marathonPassed) {
                rp1Status.textContent = 'Advanced';
                rp1Status.className = 'badge bg-info';
            } else if (practiceAttempts > 0) {
                rp1Status.textContent = 'In Progress';
                rp1Status.className = 'badge bg-warning';
            } else {
                rp1Status.textContent = 'Not Started';
                rp1Status.className = 'badge bg-secondary';
            }
        }
        
        // FIXED: Update Roleplay 2 status - check Marathon Mode, not Legend Mode
        const rp2Status = document.getElementById('rp2-status');
        if (rp2Status) {
            const marathonPassed = progress['1.2']?.marathon_passed;
            const rp2Attempts = progress['2.1']?.total_attempts || 0;
            
            if (marathonPassed) {
                if (rp2Attempts > 0) {
                    rp2Status.textContent = 'In Progress';
                    rp2Status.className = 'badge bg-warning';
                } else {
                    rp2Status.textContent = 'Available';
                    rp2Status.className = 'badge bg-success';
                }
            } else {
                rp2Status.textContent = 'Locked';
                rp2Status.className = 'badge bg-danger';
            }
        }
    }
}

// Initialize dashboard when DOM loads
let dashboard;
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏠 Dashboard DOM loaded, initializing...');
    
    // Initialize dashboard class
    dashboard = new Dashboard();
});

// Export for global access
window.dashboard = dashboard;