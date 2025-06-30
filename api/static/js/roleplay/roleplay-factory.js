// ===== static/js/roleplay/roleplay-factory.js (Complete Implementation) =====

class RoleplayFactory {
    static managerClasses = {};
    static initialized = false;
    
    static initialize() {
        if (this.initialized) return;
        
        try {
            if (typeof Roleplay11Manager !== 'undefined') {
                this.managerClasses["1.1"] = Roleplay11Manager;
            }
            if (typeof Roleplay12Manager !== 'undefined') { // <--- ADD THIS BLOCK
                this.managerClasses["1.2"] = Roleplay12Manager;
            }
            // Add Roleplay13Manager here when it's created
            
            console.log('🏭 Roleplay Factory initialized with:', Object.keys(this.managerClasses));
            this.initialized = true;
            
        } catch (error) {
            console.error('❌ Failed to initialize Roleplay Factory:', error);
        }
    }
    
    
    static createManager(roleplayId, options = {}) {
        this.initialize();
        
        const ManagerClass = this.managerClasses[roleplayId];
        if (!ManagerClass) {
            const available = Object.keys(this.managerClasses);
            console.error(`Unknown roleplay ID: ${roleplayId}. Available managers: ${available.join(', ')}`);
            // Fallback to a default manager or show an error
            if (this.managerClasses["1.1"]) {
                console.warn(`Falling back to Roleplay11Manager.`);
                return new Roleplay11Manager(options);
            }
            throw new Error(`No manager found for roleplay ID ${roleplayId} and no fallback is available.`);
        }
        
        console.log(`🏭 Creating ${roleplayId} manager`);
        return new ManagerClass(options);
    }
    
    static getAvailableRoleplays() {
        this.initialize();
        return Object.keys(this.managerClasses);
    }
    
    static registerManager(roleplayId, managerClass) {
        this.managerClasses[roleplayId] = managerClass;
        console.log(`🏭 Registered new manager: ${roleplayId}`);
    }
    
    static getManagerInfo(roleplayId) {
        this.initialize();
        
        const infoMap = {
            "1.1": {
                name: "Practice Mode",
                description: "Single call with detailed CEFR A2 coaching",
                icon: "user-graduate",
                color: "#60a5fa"
            },
            "1.2": {
                name: "Marathon Mode", 
                description: "10 calls, need 6 to pass",
                icon: "running",
                color: "#fbbf24"
            }
        };
        
        return infoMap[roleplayId] || {
            name: `Roleplay ${roleplayId}`,
            description: "Roleplay training",
            icon: "phone",
            color: "#6b7280"
        };
    }
}

// Export for global access
window.RoleplayFactory = RoleplayFactory;