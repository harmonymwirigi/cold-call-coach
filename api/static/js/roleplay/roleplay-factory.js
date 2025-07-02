// ===== FIXED: static/js/roleplay/roleplay-factory.js =====

class RoleplayFactory {
    static managerClasses = {};
    static initialized = false;
    
    static initialize() {
        if (this.initialized) return;
        
        try {
            // Register existing managers
            if (typeof Roleplay11Manager !== 'undefined') {
                this.managerClasses["1.1"] = Roleplay11Manager;
                console.log('✅ Registered Roleplay 1.1 Manager');
            }
            
            // FIXED: Ensure Roleplay 1.2 is registered
            if (typeof Roleplay12Manager !== 'undefined') {
                this.managerClasses["1.2"] = Roleplay12Manager;
                console.log('✅ Registered Roleplay 1.2 Manager');
            } else {
                console.warn('⚠️ Roleplay12Manager not found - check script loading order');
            }
            
            // UPDATED: Register all new managers
            if (typeof Roleplay13Manager !== 'undefined') {
                this.managerClasses["1.3"] = Roleplay13Manager;
                console.log('✅ Registered Roleplay 1.3 Manager');
            }
            
            if (typeof Roleplay21Manager !== 'undefined') {
                this.managerClasses["2.1"] = Roleplay21Manager;
                console.log('✅ Registered Roleplay 2.1 Manager');
            }
            
            if (typeof Roleplay22Manager !== 'undefined') {
                this.managerClasses["2.2"] = Roleplay22Manager;
                console.log('✅ Registered Roleplay 2.2 Manager');
            }
            
            if (typeof Roleplay3Manager !== 'undefined') {
                this.managerClasses["3"] = Roleplay3Manager;
                console.log('✅ Registered Roleplay 3 Manager');
            }
            
            if (typeof Roleplay4Manager !== 'undefined') {
                this.managerClasses["4"] = Roleplay4Manager;
                console.log('✅ Registered Roleplay 4 Manager');
            }
            
            if (typeof Roleplay5Manager !== 'undefined') {
                this.managerClasses["5"] = Roleplay5Manager;
                console.log('✅ Registered Roleplay 5 Manager');
            }
            
            console.log('🏭 Roleplay Factory initialized with:', Object.keys(this.managerClasses));
            this.initialized = true;
            
        } catch (error) {
            console.error('❌ Failed to initialize Roleplay Factory:', error);
        }
    }
    
    static createManager(roleplayId, options = {}) {
        this.initialize();
        
        console.log(`🏭 Creating manager for roleplay ID: ${roleplayId}`);
        
        const ManagerClass = this.managerClasses[roleplayId];
        if (!ManagerClass) {
            const available = Object.keys(this.managerClasses);
            console.error(`❌ Unknown roleplay ID: ${roleplayId}. Available: ${available.join(', ')}`);
            
            // Fallback to 1.1 if available
            if (this.managerClasses["1.1"]) {
                console.warn(`🔄 Falling back to Roleplay 1.1 Manager`);
                return new this.managerClasses["1.1"](options);
            }
            
            throw new Error(`No manager found for roleplay ID ${roleplayId}`);
        }
        
        console.log(`✅ Creating ${roleplayId} manager instance`);
        return new ManagerClass(options);
    }
    
    static getAvailableRoleplays() {
        this.initialize();
        return Object.keys(this.managerClasses);
    }
    
    static registerManager(roleplayId, managerClass) {
        this.managerClasses[roleplayId] = managerClass;
        console.log(`🏭 Manually registered manager: ${roleplayId}`);
    }
    
    static getManagerInfo(roleplayId) {
        this.initialize();
        
        const infoMap = {
            "1.1": {
                name: "Practice Mode",
                description: "Single call with detailed CEFR A2 coaching",
                icon: "user-graduate",
                color: "#60a5fa",
                difficulty: "Beginner"
            },
            "1.2": {
                name: "Marathon Mode", 
                description: "10 calls, need 6 to pass",
                icon: "running",
                color: "#fbbf24",
                difficulty: "Intermediate"
            },
            "1.3": {
                name: "Legend Mode",
                description: "6 perfect calls in a row",
                icon: "crown", 
                color: "#ef4444",
                difficulty: "Expert"
            },
            "2.1": {
                name: "Post-Pitch Practice",
                description: "Advanced pitch, objections, and qualification",
                icon: "bullhorn",
                color: "#8b5cf6",
                difficulty: "Advanced"
            },
            "2.2": {
                name: "Advanced Marathon",
                description: "10 advanced calls with complex scenarios",
                icon: "running",
                color: "#06b6d4",
                difficulty: "Expert"
            },
            "3": {
                name: "Warm-up Challenge",
                description: "25 rapid-fire questions for skill sharpening",
                icon: "fire",
                color: "#f59e0b",
                difficulty: "All Levels"
            },
            "4": {
                name: "Full Cold Call Simulation",
                description: "Complete end-to-end call practice",
                icon: "headset",
                color: "#10b981",
                difficulty: "Advanced"
            },
            "5": {
                name: "Power Hour Challenge",
                description: "10 consecutive calls for endurance",
                icon: "bolt",
                color: "#dc2626",
                difficulty: "Expert"
            }
        };
        
        return infoMap[roleplayId] || {
            name: `Roleplay ${roleplayId}`,
            description: "Roleplay training",
            icon: "phone",
            color: "#6b7280",
            difficulty: "Unknown"
        };
    }
    
    static validateManagerAvailability() {
        this.initialize();
        
        const expectedManagers = ["1.1", "1.2"];
        const issues = [];
        
        expectedManagers.forEach(id => {
            if (!this.managerClasses[id]) {
                issues.push(`Missing manager for ${id}`);
            }
        });
        
        if (issues.length > 0) {
            console.warn('⚠️ Manager availability issues:', issues);
        } else {
            console.log('✅ All expected managers are available');
        }
        
        return issues;
    }
}

// Global access
window.RoleplayFactory = RoleplayFactory;

// Auto-initialize on load
document.addEventListener('DOMContentLoaded', () => {
    RoleplayFactory.initialize();
    RoleplayFactory.validateManagerAvailability();
});