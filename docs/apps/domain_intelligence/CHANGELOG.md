# Changelog

All notable changes to the Domain Intelligence Dashboard project.

---

## [2.0.0] - 2025-11-10 - Phase 1B Complete: Modularization

### 🎉 Major Achievement
- **77% code reduction** in main dashboard file (2375 → 549 lines)
- Successfully modularized monolithic codebase into focused modules

### ✨ Added
- **Modular JavaScript Architecture**
  - `static/js/api.js` - API client (150 lines)
  - `static/js/ui.js` - UI utilities (200 lines)
  - `static/js/state.js` - State management (180 lines)
  - `static/js/main.js` - App orchestration (350 lines)

- **Real-time Metrics Dashboard**
  - 8 live metrics: pages discovered, crawled, failed, documents found
  - Current depth, max depth reached, crawl rate, pages/second
  - Depth distribution chart
  - Document type breakdown

- **Improved Controls**
  - Removed max_depth dropdown (simplified UX)
  - Max_pages as primary crawl control (default: 1000)
  - Clean, focused interface

### 🐛 Fixed
- Stop crawl no longer crashes server (graceful task cancellation)
- Max_pages configuration now available in UI
- Dashboard updates in real-time during crawl
- Download button ID mismatch resolved
- Server validation accepts high max_depth values (up to 1000)

### 🔧 Changed
- Switched from batch to streaming mode for real-time updates
- Default max_depth = 100 (effectively unlimited)
- Max_pages is now the primary scope control
- Simplified form: URL + max_pages + file types only

### 🗑️ Removed
- 15 outdated documentation files
- Backup files and demo data
- Python cache directories
- Maximum depth dropdown from UI

---

## [1.0.0] - 2025-11-09 - Initial Production Release

### ✨ Features
- **Site Mapping & Crawling**
  - BFS (Breadth-First Search) crawling strategy
  - Configurable depth and page limits
  - Real-time progress tracking
  - Session persistence and restore

- **Document Discovery**
  - Multi-format file detection (PDF, DOC, XLS, PPT, etc.)
  - Automatic deduplication
  - Source page tracking
  - Download status monitoring

- **File Downloads**
  - Batch document downloading
  - Organized by domain and file type
  - Download to `E:\filefinder\{domain}\`
  - Progress reporting

- **Visualization**
  - Interactive graph visualization (vis-network)
  - Page relationship mapping
  - Depth-based coloring
  - Click to view details

- **Export Capabilities**
  - PDF site map export
  - CSV document list export
  - Comprehensive metadata

### 🏗️ Architecture
- **Backend**: FastAPI server with async operations
- **Frontend**: Single-page dashboard with Tailwind CSS
- **Browser Automation**: Playwright for web crawling
- **Database**: SQLite with aiosqlite for async operations

### 🔧 Configuration
- Configurable crawl depth (1-10 levels)
- Page limits (1-10,000 pages)
- File type selection (7 common formats)
- Human-like delays (5-8 seconds between requests)
- Concurrent request limits (2 simultaneous)

---

## Development Milestones

### Phase 1A: Core Functionality
- ✅ Basic crawling with BFS strategy
- ✅ Document discovery and tracking
- ✅ File download system
- ✅ Graph visualization
- ✅ Export features

### Phase 1B: Modularization (COMPLETED)
- ✅ Extract API layer
- ✅ Extract UI utilities
- ✅ Extract state management
- ✅ Create main orchestration module
- ✅ Reduce dashboard.html to 549 lines

### Phase 2: Advanced Components (PLANNED)
- ⏳ Extract graph.js (~300 lines)
- ⏳ Extract tables.js with virtual scrolling (~400 lines)
- ⏳ Extract metrics.js (~200 lines)
- ⏳ Final dashboard.html reduction to ~450 lines

---

## Technical Improvements

### Performance
- Streaming mode for real-time updates (no batch delay)
- Efficient deduplication (seen_doc_urls set)
- Optimized polling (2-second intervals)
- Graceful task cancellation (no server restarts)

### Code Quality
- ES6 modules with proper imports/exports
- Separation of concerns (API, UI, State, Main)
- Reusable components
- Better error handling
- Comprehensive logging

### User Experience
- Simplified form (removed confusing max_depth)
- Real-time metrics (8 live indicators)
- Visual feedback (loading states, toasts)
- Session restore on page reload
- Clean, modern interface

---

## Known Issues & Limitations

### Current
- Graph and tables still in legacy code (Phase 2 target)
- Pause/resume not fully implemented
- Some browser context errors at end of large crawls (Crawl4AI issue)

### Future Enhancements
- Virtual scrolling for large datasets
- Advanced filtering and search
- Crawl scheduling
- Multi-domain support
- Export to additional formats

---

## Dependencies

### Core
- Python 3.10+
- FastAPI
- Crawl4AI (with Playwright)
- aiohttp, aiofiles
- pydantic

### Frontend
- Tailwind CSS (CDN)
- vis-network (graph visualization)
- Font Awesome (icons)

---

## Credits

Built on top of [Crawl4AI](https://github.com/unclecode/crawl4ai) - the most-starred web crawler on GitHub.

---

## License

[Your License Here]
