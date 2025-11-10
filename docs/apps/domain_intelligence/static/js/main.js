/**
 * Main Application Entry Point
 * Coordinates all modules and initializes the dashboard
 */

import * as API from './api.js';
import * as UI from './ui.js';
import * as State from './state.js';

// Make modules available globally for inline event handlers
window.API = API;
window.UI = UI;
window.State = State;

// Global variables for graph and network
let network = null;
let siteGraphData = { nodes: [], edges: [] };

/**
 * Initialize the application
 */
export async function initApp() {
    try {
        console.log('Initializing Domain Intelligence Dashboard...');
        
        // Check for saved session
        await checkForSavedSession();
        
        // Initialize graph
        initializeGraph();
        
        // Setup event listeners
        setupEventListeners();
        
        console.log('Dashboard ready - event listeners attached');
    } catch (error) {
        console.error('Failed to initialize app:', error);
    }
}

/**
 * Check for saved session and prompt to restore
 */
async function checkForSavedSession() {
    const savedSession = State.loadSessionState();
    
    if (savedSession) {
        try {
            // Validate session exists on server
            const response = await fetch(`/api/crawl-status/${savedSession.session_id}`);
            if (response.ok) {
                showSessionRestoreModal(savedSession);
            } else {
                console.log('Saved session no longer exists on server, clearing...');
                State.clearSessionState();
            }
        } catch (error) {
            console.error('Error checking saved session:', error);
            State.clearSessionState();
        }
    }
}

/**
 * Show session restore modal
 */
function showSessionRestoreModal(sessionState) {
    const modal = document.getElementById('sessionRestoreModal');
    const detailsDiv = document.getElementById('sessionRestoreDetails');
    
    const timeAgo = UI.formatTimeAgo(sessionState.timestamp);
    const fileTypesStr = sessionState.crawl_options.file_types.join(', ').toUpperCase() || 'None';
    
    detailsDiv.innerHTML = `
        <div class="space-y-2">
            <div class="flex justify-between">
                <span class="text-neutral-400">URL:</span>
                <span class="text-neutral-200 truncate ml-2 max-w-xs">${sessionState.crawl_url}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-neutral-400">Max Pages:</span>
                <span class="text-neutral-200">${sessionState.crawl_options.max_pages || 1000} pages</span>
            </div>
            <div class="flex justify-between">
                <span class="text-neutral-400">File Types:</span>
                <span class="text-neutral-200">${fileTypesStr}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-neutral-400">Started:</span>
                <span class="text-neutral-200">${timeAgo}</span>
            </div>
        </div>
    `;
    
    UI.showModal('sessionRestoreModal');
    
    document.getElementById('resumeSessionBtn').onclick = () => {
        UI.hideModal('sessionRestoreModal');
        resumeSession(sessionState);
    };
    
    document.getElementById('discardSessionBtn').onclick = () => {
        UI.hideModal('sessionRestoreModal');
        State.clearSessionState();
    };
}

/**
 * Resume a saved session
 */
async function resumeSession(sessionState) {
    console.log('Resuming session:', sessionState);
    
    // Restore form values
    document.getElementById('crawlUrlInput').value = sessionState.crawl_url;
    document.getElementById('maxPagesInput').value = sessionState.crawl_options.max_pages || 1000;
    State.setSelectedFileTypes(sessionState.crawl_options.file_types);
    
    // Restore session state
    State.updateState({
        sessionId: sessionState.session_id,
        crawlUrl: sessionState.crawl_url,
        crawlOptions: sessionState.crawl_options
    });
    
    // Start polling for status
    startPolling(sessionState.session_id);
    
    UI.showToast('Session resumed', 2000);
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Start crawl button
    const startBtn = document.getElementById('startMappingBtn');
    if (startBtn) {
        startBtn.addEventListener('click', handleStartCrawl);
    }
    
    // Stop crawl button
    const stopBtn = document.getElementById('stopCrawlBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', handleStopCrawl);
    }
    
    // Download documents button
    const downloadBtn = document.getElementById('downloadAllBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', handleDownloadDocuments);
    } else {
        console.warn('Download button not found (id: downloadAllBtn)');
    }
    
    // Export buttons
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', () => handleExport('pdf'));
    }
    
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => handleExport('csv'));
    }
}

/**
 * Handle start crawl
 */
async function handleStartCrawl() {
    const urlInput = document.getElementById('crawlUrlInput');
    const url = urlInput.value.trim();
    const urlError = document.getElementById('urlError');
    
    // Validate URL
    const validation = UI.validateUrl(url);
    if (!validation.valid) {
        urlError.textContent = validation.error;
        urlError.classList.remove('hidden');
        urlInput.classList.add('border-red-500');
        return;
    }
    
    urlError.classList.add('hidden');
    urlInput.classList.remove('border-red-500');
    
    // Get options
    const maxPages = parseInt(document.getElementById('maxPagesInput').value) || 1000;
    const fileTypes = State.getSelectedFileTypes();
    
    const options = {
        max_depth: 100,  // High default - let max_pages control the crawl scope
        max_pages: maxPages,
        file_types: fileTypes
    };
    
    // Show loading state
    UI.setButtonLoading('startMappingBtn', true, 'Starting...');
    
    try {
        const result = await API.startCrawl(url, options);
        
        // Update state
        State.updateState({
            sessionId: result.session_id,
            status: result.status,
            crawlUrl: url,
            crawlOptions: options
        });
        
        // Start polling
        startPolling(result.session_id);
        
        UI.showToast('Crawl started successfully', 3000);
        
        // Hide input panel and show metrics dashboard
        const inputPanel = document.getElementById('crawlInputPanel');
        const metricsDashboard = document.getElementById('metricsDashboard');
        
        if (inputPanel) inputPanel.classList.add('hidden');
        if (metricsDashboard) metricsDashboard.classList.remove('hidden');
        
    } catch (error) {
        console.error('Failed to start crawl:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            error: error
        });
        UI.showToast('Failed to start crawl: ' + error.message, 5000);
    } finally {
        UI.setButtonLoading('startMappingBtn', false);
    }
}

/**
 * Handle stop crawl
 */
async function handleStopCrawl() {
    if (!State.state.sessionId) {
        UI.showToast('No active crawl to stop', 3000);
        return;
    }
    
    UI.setButtonLoading('stopCrawlBtn', true, 'Stopping...');
    
    try {
        await API.stopCrawl(State.state.sessionId);
        
        // Stop polling
        if (State.state.pollingInterval) {
            clearInterval(State.state.pollingInterval);
            State.state.pollingInterval = null;
        }
        
        UI.showToast('Crawl stopped', 3000);
        
    } catch (error) {
        console.error('Failed to stop crawl:', error);
        UI.showToast('Failed to stop crawl: ' + error.message, 5000);
    } finally {
        UI.setButtonLoading('stopCrawlBtn', false);
    }
}

/**
 * Handle download documents
 */
async function handleDownloadDocuments() {
    if (!State.state.sessionId) {
        UI.showToast('No active session', 3000);
        return;
    }
    
    UI.setButtonLoading('downloadAllBtn', true, 'Downloading...');
    
    try {
        const result = await API.downloadDocuments(State.state.sessionId);
        
        const message = `Downloaded ${result.stats.successful} documents (${result.stats.failed} failed)`;
        UI.showToast(message, 5000);
        
    } catch (error) {
        console.error('Failed to download documents:', error);
        UI.showToast('Failed to download documents: ' + error.message, 5000);
    } finally {
        UI.setButtonLoading('downloadAllBtn', false);
    }
}

/**
 * Handle export (PDF or CSV)
 */
async function handleExport(format) {
    if (!State.state.sessionId) {
        UI.showToast('No active session', 3000);
        return;
    }
    
    try {
        let blob;
        let filename;
        
        if (format === 'pdf') {
            blob = await API.exportPDF(State.state.sessionId);
            filename = `site-map-${State.state.sessionId}.pdf`;
        } else {
            blob = await API.exportCSV(State.state.sessionId);
            filename = `documents-${State.state.sessionId}.csv`;
        }
        
        UI.downloadBlob(blob, filename);
        UI.showToast(`${format.toUpperCase()} exported successfully`, 3000);
        
    } catch (error) {
        console.error(`Failed to export ${format}:`, error);
        UI.showToast(`Failed to export ${format}: ` + error.message, 5000);
    }
}

/**
 * Start polling for crawl status
 */
function startPolling(sessionId) {
    console.log('Starting polling for session:', sessionId);
    
    // Clear any existing interval
    if (State.state.pollingInterval) {
        clearInterval(State.state.pollingInterval);
    }
    
    // Poll every 2 seconds
    State.state.pollingInterval = setInterval(async () => {
        try {
            const status = await API.getCrawlStatus(sessionId);
            console.log('Poll update:', {
                pages: status.pages.length,
                documents: status.documents.length,
                status: status.status
            });
            updateDashboard(status);
            
            // Stop polling if completed or failed
            if (status.status === 'completed' || status.status === 'failed') {
                console.log('Crawl finished, stopping polling');
                clearInterval(State.state.pollingInterval);
                State.state.pollingInterval = null;
            }
        } catch (error) {
            console.error('Failed to get crawl status:', error);
        }
    }, 2000);
    
    // Do initial fetch immediately
    console.log('Doing initial status fetch...');
    API.getCrawlStatus(sessionId)
        .then(status => {
            console.log('Initial status:', {
                pages: status.pages.length,
                documents: status.documents.length,
                status: status.status
            });
            updateDashboard(status);
        })
        .catch(console.error);
}

/**
 * Update dashboard with crawl status
 */
function updateDashboard(status) {
    // Update state
    State.updateState({
        status: status.status,
        pages: status.pages,
        documents: status.documents,
        progress: status.progress
    });
    
    // Update metrics
    updateMetrics(status.progress);
    
    // Update depth distribution
    if (status.pages && status.pages.length > 0) {
        updateDepthDistribution(status.pages);
    }
    
    // Update document types
    if (status.documents && status.documents.length > 0) {
        updateDocumentTypes(status.documents);
    }
    
    // Update progress bar
    const percentage = status.progress.pages_discovered > 0
        ? Math.round((status.progress.pages_crawled / status.progress.pages_discovered) * 100)
        : 0;
    UI.updateProgressBar('progressBar', percentage);
    
    // Update current page
    if (status.progress.current_page) {
        const currentPageEl = document.getElementById('currentPage');
        if (currentPageEl) {
            currentPageEl.textContent = UI.truncate(status.progress.current_page, 60);
        }
    }
    
    // Update graph
    updateGraph(status.pages);
    
    // Update tables
    updateTables(status.pages, status.documents);
}

/**
 * Update metrics dashboard
 */
function updateMetrics(progress) {
    document.getElementById('metricPagesDiscovered').textContent = progress.pages_discovered || 0;
    document.getElementById('metricPagesCrawled').textContent = progress.pages_crawled || 0;
    document.getElementById('metricDocumentsFound').textContent = progress.documents_found || 0;
    
    const elapsedMinutes = (progress.elapsed_seconds || 0) / 60;
    const crawlRate = elapsedMinutes > 0 ? Math.round((progress.pages_crawled || 0) / elapsedMinutes) : 0;
    document.getElementById('metricCrawlRate').textContent = crawlRate;
    
    document.getElementById('metricPagesFailed').textContent = progress.pages_failed || 0;
    document.getElementById('metricCurrentDepth').textContent = progress.current_depth || 0;
    document.getElementById('metricMaxDepth').textContent = progress.max_depth_reached || 0;
    document.getElementById('metricPagesPerSecond').textContent = (progress.pages_per_second || 0).toFixed(2);
}

/**
 * Update depth distribution chart
 */
function updateDepthDistribution(pages) {
    const depthCounts = {};
    pages.forEach(page => {
        depthCounts[page.depth] = (depthCounts[page.depth] || 0) + 1;
    });
    
    const depthHtml = Object.keys(depthCounts).sort((a, b) => a - b).map(depth => {
        const count = depthCounts[depth];
        const percentage = Math.round((count / pages.length) * 100);
        return `
            <div class="flex items-center">
                <div class="w-20 text-sm text-neutral-400">Depth ${depth}:</div>
                <div class="flex-1 bg-neutral-700 rounded-full h-6 mx-3">
                    <div class="bg-blue-600 h-6 rounded-full flex items-center justify-end pr-2" style="width: ${percentage}%">
                        <span class="text-xs text-white font-semibold">${count}</span>
                    </div>
                </div>
                <div class="w-12 text-sm text-neutral-400 text-right">${percentage}%</div>
            </div>
        `;
    }).join('');
    
    const depthDiv = document.getElementById('depthDistribution');
    if (depthDiv) {
        depthDiv.innerHTML = depthHtml || '<div class="text-neutral-500 text-sm">No data yet</div>';
    }
}

/**
 * Update document types chart
 */
function updateDocumentTypes(documents) {
    const docTypes = {};
    documents.forEach(doc => {
        const type = doc.file_type.toUpperCase();
        docTypes[type] = (docTypes[type] || 0) + 1;
    });
    
    const typesHtml = Object.entries(docTypes).map(([type, count]) => `
        <div class="bg-neutral-700 rounded-lg p-4 text-center">
            <div class="text-2xl font-bold text-blue-400">${count}</div>
            <div class="text-xs text-neutral-400 mt-1">${type}</div>
        </div>
    `).join('');
    
    const typesDiv = document.getElementById('documentTypes');
    if (typesDiv) {
        typesDiv.innerHTML = typesHtml || '<div class="text-neutral-500 text-sm col-span-4">No documents yet</div>';
    }
}

/**
 * Initialize graph visualization
 */
function initializeGraph() {
    // Graph initialization will be moved to graph.js in Phase 2
    console.log('Graph initialization placeholder');
}

/**
 * Update graph with new pages
 */
function updateGraph(pages) {
    // Call legacy graph update function (will be moved to graph.js in Phase 2)
    if (typeof window.updateGraphData === 'function') {
        window.updateGraphData(pages);
    } else {
        console.log('Graph update:', pages.length, 'pages');
    }
}

/**
 * Update tables with new data
 */
function updateTables(pages, documents) {
    // Call legacy table rendering functions (will be moved to tables.js in Phase 2)
    if (typeof window.renderPagesTable === 'function') {
        window.renderPagesTable(pages);
    }
    if (typeof window.renderDocumentsTable === 'function') {
        window.renderDocumentsTable(documents);
    }
    console.log('Tables updated:', pages.length, 'pages,', documents.length, 'documents');
}

// Initialize app when DOM is ready
console.log('main.js loaded, document.readyState:', document.readyState);
if (document.readyState === 'loading') {
    console.log('Waiting for DOMContentLoaded...');
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOMContentLoaded fired, calling initApp...');
        initApp();
    });
} else {
    console.log('DOM already ready, calling initApp immediately...');
    initApp();
}

// Export for use in other modules
export { network, siteGraphData, updateDashboard, updateMetrics, updateGraph, updateTables };
