/**
 * API Client for Domain Intelligence Dashboard
 * Handles all communication with the backend server
 */

const API_BASE = '';  // Same origin

/**
 * Start a new crawl session
 * @param {string} url - Starting URL
 * @param {Object} options - Crawl options (max_depth, max_pages, file_types)
 * @returns {Promise<Object>} - { session_id, status, message }
 */
export async function startCrawl(url, options) {
    const response = await fetch(`${API_BASE}/api/start-crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, options })
    });
    
    if (!response.ok) {
        let errorMessage = 'Failed to start crawl';
        try {
            const error = await response.json();
            // Handle both string and object error details
            if (typeof error.detail === 'string') {
                errorMessage = error.detail;
            } else if (error.detail && error.detail.message) {
                errorMessage = error.detail.message;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = JSON.stringify(error);
            }
        } catch (e) {
            errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
    }
    
    return await response.json();
}

/**
 * Get current crawl status and progress
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} - Full crawl status with pages, documents, progress
 */
export async function getCrawlStatus(sessionId) {
    const response = await fetch(`${API_BASE}/api/crawl-status/${sessionId}`);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get crawl status');
    }
    
    return await response.json();
}

/**
 * Stop a running crawl
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} - { message, status }
 */
export async function stopCrawl(sessionId) {
    const response = await fetch(`${API_BASE}/api/stop-crawl/${sessionId}`, {
        method: 'POST'
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to stop crawl');
    }
    
    return await response.json();
}

/**
 * Pause/resume a crawl (limited support)
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} - { message, status }
 */
export async function pauseCrawl(sessionId) {
    const response = await fetch(`${API_BASE}/api/pause-crawl/${sessionId}`, {
        method: 'POST'
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to pause crawl');
    }
    
    return await response.json();
}

/**
 * Download all discovered documents
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} - Download stats
 */
export async function downloadDocuments(sessionId) {
    const response = await fetch(`${API_BASE}/api/download-documents/${sessionId}`, {
        method: 'POST'
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to download documents');
    }
    
    return await response.json();
}

/**
 * Export site map as PDF
 * @param {string} sessionId - Session ID
 * @returns {Promise<Blob>} - PDF file blob
 */
export async function exportPDF(sessionId) {
    const response = await fetch(`${API_BASE}/api/export-pdf/${sessionId}`);
    
    if (!response.ok) {
        throw new Error('Failed to export PDF');
    }
    
    return await response.blob();
}

/**
 * Export document list as CSV
 * @param {string} sessionId - Session ID
 * @returns {Promise<Blob>} - CSV file blob
 */
export async function exportCSV(sessionId) {
    const response = await fetch(`${API_BASE}/api/export-csv/${sessionId}`);
    
    if (!response.ok) {
        throw new Error('Failed to export CSV');
    }
    
    return await response.blob();
}

/**
 * Check server health
 * @returns {Promise<Object>} - { status, active_sessions, running_crawls }
 */
export async function healthCheck() {
    const response = await fetch(`${API_BASE}/health`);
    
    if (!response.ok) {
        throw new Error('Health check failed');
    }
    
    return await response.json();
}
