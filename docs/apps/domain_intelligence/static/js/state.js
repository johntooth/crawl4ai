/**
 * State Management for Domain Intelligence Dashboard
 * Handles global state and session persistence
 */

const SESSION_STORAGE_KEY = 'domain_intelligence_session';

// Global state
export const state = {
    sessionId: null,
    status: null,
    crawlUrl: null,
    crawlOptions: null,
    pages: [],
    documents: [],
    progress: {
        pages_discovered: 0,
        pages_crawled: 0,
        pages_failed: 0,
        documents_found: 0,
        current_page: null,
        current_depth: 0,
        max_depth_reached: 0,
        elapsed_seconds: 0,
        pages_per_second: 0,
        errors: []
    },
    pollingInterval: null
};

/**
 * Update state with new data
 * @param {Object} updates - Partial state updates
 */
export function updateState(updates) {
    Object.assign(state, updates);
    
    // Persist session if active
    if (state.sessionId) {
        saveSessionState();
    }
}

/**
 * Reset state to initial values
 */
export function resetState() {
    state.sessionId = null;
    state.status = null;
    state.crawlUrl = null;
    state.crawlOptions = null;
    state.pages = [];
    state.documents = [];
    state.progress = {
        pages_discovered: 0,
        pages_crawled: 0,
        pages_failed: 0,
        documents_found: 0,
        current_page: null,
        current_depth: 0,
        max_depth_reached: 0,
        elapsed_seconds: 0,
        pages_per_second: 0,
        errors: []
    };
    
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
    }
}

/**
 * Save session state to localStorage
 */
export function saveSessionState() {
    const sessionState = {
        session_id: state.sessionId,
        crawl_url: state.crawlUrl,
        crawl_options: state.crawlOptions,
        timestamp: Date.now()
    };
    
    try {
        localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessionState));
    } catch (e) {
        console.error('Failed to save session state:', e);
    }
}

/**
 * Load session state from localStorage
 * @returns {Object|null} - Saved session state or null
 */
export function loadSessionState() {
    try {
        const saved = localStorage.getItem(SESSION_STORAGE_KEY);
        if (!saved) return null;
        
        const sessionState = JSON.parse(saved);
        
        // Check if session is recent (within 24 hours)
        const age = Date.now() - sessionState.timestamp;
        if (age > 24 * 60 * 60 * 1000) {
            clearSessionState();
            return null;
        }
        
        return sessionState;
    } catch (e) {
        console.error('Failed to load session state:', e);
        return null;
    }
}

/**
 * Clear session state from localStorage
 */
export function clearSessionState() {
    try {
        localStorage.removeItem(SESSION_STORAGE_KEY);
    } catch (e) {
        console.error('Failed to clear session state:', e);
    }
}

/**
 * Check if there's an active session
 * @returns {boolean}
 */
export function hasActiveSession() {
    return state.sessionId !== null && state.status !== 'completed' && state.status !== 'failed';
}

/**
 * Get selected file types from checkboxes
 * @returns {Array<string>} - Array of selected file extensions
 */
export function getSelectedFileTypes() {
    const fileTypes = [];
    const checkboxes = [
        { id: 'fileTypePdf', value: 'pdf' },
        { id: 'fileTypeDoc', value: 'doc' },
        { id: 'fileTypeDocx', value: 'docx' },
        { id: 'fileTypeXls', value: 'xls' },
        { id: 'fileTypeXlsx', value: 'xlsx' },
        { id: 'fileTypePpt', value: 'ppt' },
        { id: 'fileTypePptx', value: 'pptx' }
    ];
    
    checkboxes.forEach(({ id, value }) => {
        const checkbox = document.getElementById(id);
        if (checkbox && checkbox.checked) {
            fileTypes.push(value);
        }
    });
    
    return fileTypes;
}

/**
 * Set file type checkboxes
 * @param {Array<string>} fileTypes - Array of file extensions to check
 */
export function setSelectedFileTypes(fileTypes) {
    const checkboxMap = {
        'pdf': 'fileTypePdf',
        'doc': 'fileTypeDoc',
        'docx': 'fileTypeDocx',
        'xls': 'fileTypeXls',
        'xlsx': 'fileTypeXlsx',
        'ppt': 'fileTypePpt',
        'pptx': 'fileTypePptx'
    };
    
    // Uncheck all first
    Object.values(checkboxMap).forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) checkbox.checked = false;
    });
    
    // Check selected ones
    fileTypes.forEach(type => {
        const id = checkboxMap[type];
        if (id) {
            const checkbox = document.getElementById(id);
            if (checkbox) checkbox.checked = true;
        }
    });
}
