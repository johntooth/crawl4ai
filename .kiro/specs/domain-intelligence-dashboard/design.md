# Design Document

## Overview

The Domain Intelligence Dashboard extends the existing LinkedIn graph visualization template (`docs/apps/linkdin/templates/graph_view_template.html`) to create a focused site mapping tool. The design leverages the proven vis.js network visualization and Split.js panel layout while simplifying the data model for a core 4-step workflow: Input → Map → Download → Review. This keeps the implementation lean while providing immediate practical value.

## Architecture

### Core 4-Step Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Domain Intelligence Dashboard                │
├─────────────────────────────────────────────────────────────┤
│ Step 1: INPUT                                               │
│ [URL Input] [Max Depth] [File Types] [Start Mapping]       │
├─────────────────────────────────────────────────────────────┤
│ Step 2: MAP & DOWNLOAD                                      │
│ Progress: [██████ 65%] Pages: 142 | Documents: 23/45       │
│ [Pause] [Stop] [View Current Graph]                         │
├─────────────────────────────────────────────────────────────┤
│ Step 3: REVIEW                                              │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │   Page List     │ │  Site Graph     │ │ Document Panel  ││
│ │   - Search      │ │  - Vis.js       │ │ - File Preview  ││
│ │   - Filter      │ │  - Interactive  │ │ - Download      ││
│ │   - Status      │ │  - Click Pages  │ │ - Status        ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ Step 4: EXPORT                                              │
│ [Site Map PDF] [Document CSV] [Download All] [Share]       │
└─────────────────────────────────────────────────────────────┘
```

### Simplified Data Flow

```
URL Input → Crawl Start → Progress Updates → Graph Render → Export
    ↓           ↓             ↓               ↓            ↓
Start Form → Background   → Live Status  → Vis.js     → PDF/CSV
           → Crawling    → Updates      → Network    → Downloads
           → File DL     → Page Count   → Click      → Reports
                        → Doc Count    → Details
```

## Components and Interfaces

### Essential Components

#### 1. CrawlController
**Purpose:** Manages the core crawling and download workflow
**Key Methods:**
- `startCrawl(url, options)` - Begin site mapping with specified parameters
- `pauseCrawl()` - Pause current crawling operation
- `stopCrawl()` - Stop and cleanup crawling operation
- `getProgress()` - Return current crawl status and metrics

#### 2. SiteGraphRenderer
**Purpose:** Simplified vis.js network for site structure visualization
**Key Methods:**
- `renderGraph(pages, links)` - Display site structure as interactive network
- `updateNodeStatus(pageId, status)` - Update page status (crawled/downloading/failed)
- `highlightPage(pageId)` - Focus on specific page in graph
- `exportGraphImage()` - Generate PNG/SVG of current graph view

#### 3. DocumentManager
**Purpose:** Handles file downloads and document tracking
**Key Methods:**
- `downloadFile(url, metadata)` - Download and store document files
- `getFilePreview(fileId)` - Generate preview for supported file types
- `getDownloadStatus(fileId)` - Check download progress and status
- `exportDocumentList()` - Generate CSV inventory of all documents

#### 4. ReportGenerator
**Purpose:** Creates exportable reports and summaries
**Key Methods:**
- `generateSiteMapPDF()` - Create PDF report with graph and page list
- `generateDocumentInventory()` - Create CSV with all discovered files
- `generateCrawlSummary()` - Create summary report with metrics and status

### Simplified Data Models

#### CrawlSession Model
```typescript
interface CrawlSession {
  id: string;              // Unique session identifier
  start_url: string;       // Starting URL for crawl
  status: 'running' | 'paused' | 'completed' | 'failed';
  start_time: Date;
  end_time?: Date;
  options: CrawlOptions;
  progress: CrawlProgress;
}

interface CrawlOptions {
  max_depth: number;       // Maximum crawl depth (default: 3)
  file_types: string[];    // Target extensions ['pdf', 'doc', 'xls']
  max_pages: number;       // Page limit (default: 1000)
}

interface CrawlProgress {
  pages_discovered: number;
  pages_crawled: number;
  documents_found: number;
  documents_downloaded: number;
  current_page?: string;
  errors: string[];
}

#### SiteGraph Model
```typescript
interface SiteGraph {
  session_id: string;
  pages: SitePage[];       // Simplified from nodes
  links: SiteLink[];       // Simplified from edges
  documents: SiteDocument[];
}

interface SitePage {
  id: string;           // URL hash or identifier
  url: string;          // Full page URL
  title: string;        // Page title
  depth: number;        // Distance from root
  status: 'pending' | 'crawled' | 'failed';
  parent_id?: string;   // Parent page ID
}

interface SiteLink {
  from: string;         // Source page ID
  to: string;           // Target page ID
  anchor_text?: string; // Link text
}

interface SiteDocument {
  id: string;           // Document identifier
  url: string;          // Download URL
  filename: string;     // Original filename
  file_type: string;    // Extension (pdf, doc, etc.)
  file_size: number;    // Size in bytes
  source_page: string;  // Page where document was found
  download_status: 'pending' | 'downloading' | 'completed' | 'failed';
  local_path?: string;  // Path to downloaded file
}
```

#### Simple Metrics Model
```typescript
interface CrawlMetrics {
  pages_total: number;
  pages_crawled: number;
  documents_total: number;
  documents_downloaded: number;
  total_size_mb: number;
  file_types: {
    [extension: string]: number;  // Count by file type
  };
  errors: number;
  duration_minutes: number;
}
```

## Error Handling

### Client-Side Error Management
- **JSON Parsing Errors:** Display user-friendly messages with format requirements
- **Network Failures:** Implement retry logic with exponential backoff
- **Visualization Errors:** Graceful degradation with simplified graph rendering
- **AI Service Errors:** Fallback to cached responses and offline analysis

### Data Validation
- **Site Graph Validation:** Ensure required fields (nodes, edges) exist
- **URL Validation:** Verify node URLs are properly formatted
- **Relationship Integrity:** Check that all edge references point to valid nodes
- **File Size Limits:** Prevent loading of excessively large graph files

## Testing Strategy

### Unit Testing
- **Data Processing:** Test JSON parsing, validation, and transformation functions
- **Graph Calculations:** Verify metrics computation (depth, connectivity, clustering)
- **UI Components:** Test individual component rendering and event handling
- **AI Context Building:** Validate context preparation for chat queries

### Integration Testing  
- **End-to-End Workflows:** Test complete user journeys from file load to analysis
- **Cross-Browser Compatibility:** Ensure consistent behavior across modern browsers
- **Performance Testing:** Validate smooth operation with large site graphs (1000+ nodes)
- **Data Persistence:** Test localStorage functionality and session recovery

### Visual Testing
- **Graph Rendering:** Verify correct node positioning and edge drawing
- **Responsive Design:** Test layout adaptation across different screen sizes
- **Color Schemes:** Validate accessibility and contrast in dark theme
- **Animation Performance:** Ensure smooth transitions and interactions

## Implementation Approach

### Phase 1: Core Template Adaptation
1. Copy LinkedIn graph template to new dashboard location
2. Simplify data model from company/employee to page/document structure
3. Remove AI chat interface and complex analytics
4. Implement basic URL input form and crawl start functionality

### Phase 2: Essential Workflow
1. Add progress tracking display with live updates
2. Implement basic site graph visualization with vis.js
3. Create document list and download status tracking
4. Add pause/stop controls for crawl operations

### Phase 3: Review and Export
1. Implement page details panel with click interactions
2. Add basic search and filter functionality for pages/documents
3. Create PDF export for site map visualization
4. Add CSV export for document inventory

### Phase 4: Polish and Optimization
1. Add file preview capabilities for common document types
2. Implement download all functionality for acquired documents
3. Add session persistence and resume capabilities
4. Optimize performance for large site graphs (1000+ pages)

## Technical Considerations

### Performance Optimization
- **Large Graph Handling:** Use vis.js clustering for sites with 500+ pages
- **Memory Management:** Clean up unused DOM elements and event listeners
- **Progress Updates:** Use efficient polling or WebSocket for live status updates
- **File Downloads:** Implement chunked downloads for large documents

### Browser Compatibility
- **Modern Browser Support:** Target Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **File API:** Use modern File API for document downloads and previews
- **Canvas Rendering:** Leverage vis.js canvas mode for better performance
- **Local Storage:** Use localStorage for session persistence and settings

### Integration with Crawl4AI
- **Existing Infrastructure:** Leverage existing AsyncWebCrawler and file handling
- **Data Format:** Use existing site graph JSON format from sites/ directory
- **Configuration:** Extend existing CrawlerRunConfig for dashboard options
- **Error Handling:** Use existing error patterns and logging infrastructure