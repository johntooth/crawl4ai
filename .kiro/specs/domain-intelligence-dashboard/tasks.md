# Implementation Plan

## Overview
This implementation plan builds the Domain Intelligence Dashboard with the correct data flow: **URL Input → Live Crawl → Real-time Updates → Incremental Graph Building → Export**. The dashboard connects to Crawl4AI's existing crawling infrastructure and displays results as they're discovered in real-time.

## Critical Path: Core Workflow (Phase 1)

- [x] 1. Set up dashboard foundation and template adaptation




  - Copy LinkedIn graph template to `docs/apps/domain_intelligence/dashboard.html`
  - Remove AI chat drawer, settings modal, and OpenAI integration code
  - Remove company/employee specific UI (company list, org charts, decision makers)
  - Update page title and branding to "Domain Intelligence Dashboard"
  - Keep vis.js network, Split.js panels, and core layout structure
  - _Requirements: 1.1, 1.5_

- [x] 2. Create backend crawl integration endpoint




  - [x] 2.1 Build Flask/FastAPI server for dashboard


    - Create `docs/apps/domain_intelligence/server.py` with basic Flask app
    - Add route to serve dashboard.html at root path
    - Add `/api/start-crawl` POST endpoint accepting URL and options
    - Add `/api/crawl-status/<session_id>` GET endpoint for progress polling
    - Use existing AsyncWebCrawler from crawl4ai for actual crawling
    - _Requirements: 7.1, 7.2_
  
  - [x] 2.2 Implement crawl session management


    - Create in-memory dict to track active crawl sessions by ID
    - Store CrawlResult data, progress metrics, and discovered pages per session
    - Implement background thread/task to run AsyncWebCrawler.arun()
    - Update session data as pages are discovered during crawl
    - _Requirements: 7.2, 7.3_

- [x] 3. Build URL input form and crawl starter





  - [x] 3.1 Create input form UI


    - Replace company search with URL input field and validation
    - Add max depth dropdown (1-5 levels, default 3)
    - Add file types checkboxes (PDF, DOC, XLS, PPT, ZIP)
    - Add "Start Mapping" button with loading state
    - Style form with existing dark theme
    - _Requirements: 7.1_
  
  - [x] 3.2 Implement crawl start functionality


    - Create `startCrawl()` JavaScript function to POST to `/api/start-crawl`
    - Validate URL format before submitting
    - Receive session_id from backend response
    - Store session_id in JavaScript variable for polling
    - Disable form and show progress panel when crawl starts
    - _Requirements: 7.1, 7.2_

- [x] 4. Implement real-time progress tracking




  - [x] 4.1 Create progress display UI

    - Replace company count area with progress panel
    - Add progress bar showing percentage complete
    - Display counters: Pages Discovered, Pages Crawled, Documents Found
    - Show current page being processed
    - Add elapsed time display
    - _Requirements: 3.2, 7.2, 7.4_
  
  - [x] 4.2 Implement progress polling mechanism

    - Create `pollCrawlStatus()` function to GET `/api/crawl-status/<session_id>`
    - Poll every 1-2 seconds while crawl is active
    - Update progress UI with latest counts and status
    - Stop polling when crawl completes or fails
    - _Requirements: 3.2, 7.2_
  
  - [x] 4.3 Add crawl control buttons

    - Add Pause and Stop buttons to progress panel
    - Implement `/api/pause-crawl/<session_id>` endpoint
    - Implement `/api/stop-crawl/<session_id>` endpoint
    - Update button states based on crawl status (running/paused/stopped)
    - _Requirements: 7.3_

- [x] 5. Build incremental graph visualization







  - [x] 5.1 Create live graph data structure





    - Initialize empty vis.js DataSet for nodes and edges
    - Create `addPage()` function to add discovered pages as nodes
    - Create `addLink()` function to add page relationships as edges
    - Color nodes by status: gray (pending), blue (crawled), red (failed)
    - Size nodes by depth level (larger = closer to root)


    - _Requirements: 1.1, 1.2, 3.3_
  
  - [x] 5.2 Implement incremental graph updates





    - Parse pages array from `/api/crawl-status` response
    - Add new pages to graph as they're discovered
    - Update existing node colors when page status changes


    - Use hierarchical layout to show site structure
    - Disable physics after initial layout for stability
    - _Requirements: 1.1, 1.2, 3.2_
  
  - [x] 5.3 Add graph interaction handlers





    - Implement node click to select page and show details
    - Add hover tooltips showing page title and URL
    - Keep existing zoom/pan/reset controls from template
    - Highlight connected pages when node is selected
    - _Requirements: 1.3, 1.4, 1.5, 5.5_

- [x] 6. Implement basic export functionality






  - [x] 6.1 Add export button panel

    - Create export section below progress panel
    - Add "Export Site Map (PDF)" button
    - Add "Export Document List (CSV)" button
    - Add "Download All Documents (ZIP)" button
    - _Requirements: 6.1, 6.2, 6.3, 8.1_
  

  - [x] 6.2 Implement site map PDF export

    - Add `/api/export-pdf/<session_id>` endpoint
    - Use html2canvas or similar to capture graph visualization
    - Generate PDF with graph image and page count summary
    - Return PDF file for browser download
    - _Requirements: 6.1, 6.2, 8.1_
  

  - [x] 6.3 Implement document CSV export

    - Add `/api/export-csv/<session_id>` endpoint
    - Generate CSV with columns: URL, Filename, Type, Size, Status, Source Page
    - Include all discovered documents from crawl session
    - Return CSV file for browser download
    - _Requirements: 6.3, 8.2_

- [x] 7. Add document tracking interface




  - [x] 7.1 Create document list in details panel


    - Add documents section showing files found on selected page
    - Display filename, type, size, and download status
    - Show download progress for files being acquired
    - _Requirements: 4.4, 5.4_


- [x] 8. Add session persistence





  - [x] 8.1 Implement session save


    - Save active session_id to localStorage
    - Store last crawl URL and options
    - Persist graph view position and zoom level
    - _Requirements: 2.4_
  

  - [x] 8.2 Add session restore prompt

    - Check for saved session on page load
    - Show "Resume last crawl?" prompt if session exists
    - Restore graph and progress if user confirms
    - _Requirements: 2.4_

- [x] 9. Optimize for large sites




  - [x] 9.1 Add virtual scrolling for page list


    - Implement windowed rendering for lists with 500+ pages
    - Load and render pages in batches
    - Maintain smooth scrolling performance
    - _Requirements: 5.2_
