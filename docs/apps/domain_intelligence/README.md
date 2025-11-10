# Domain Intelligence Dashboard

**Version 2.0** - A modern, modular web application for intelligent site mapping and document discovery.

Built on [Crawl4AI](https://github.com/unclecode/crawl4ai) - the most-starred web crawler on GitHub.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd docs/apps/domain_intelligence
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python server.py
```

### 3. Open Dashboard
Navigate to **http://localhost:8080** in your browser.

---

## ✨ Features

### Site Mapping
- **Intelligent Crawling**: BFS (Breadth-First Search) strategy
- **Real-time Progress**: 8 live metrics updating every 2 seconds
- **Configurable Scope**: Control crawl with max_pages limit
- **Session Persistence**: Resume interrupted crawls

### Document Discovery
- **Multi-format Detection**: PDF, DOC, XLS, PPT, and more
- **Automatic Deduplication**: No duplicate downloads
- **Batch Downloads**: Download all discovered files at once
- **Organized Storage**: Files saved to `E:\filefinder\{domain}\`

### Visualization
- **Interactive Graph**: vis-network powered site structure
- **Depth-based Coloring**: Visual depth indicators
- **Real-time Updates**: Graph builds as crawl progresses
- **Click for Details**: View page information

### Export & Analysis
- **PDF Site Map**: Comprehensive site structure report
- **CSV Export**: Document list with metadata
- **Depth Distribution**: Visual breakdown by crawl depth
- **Document Types**: Categorized file type counts

---

## 🎯 Usage

### Starting a Crawl

1. **Enter URL**: Type the starting URL (e.g., `https://example.com`)
2. **Set Max Pages**: Choose page limit (default: 1000)
   - Use 50-100 for testing
   - Use 1000+ for full site mapping
3. **Select File Types**: Check document types to discover
4. **Click "Start Mapping"**: Crawl begins immediately

### Monitoring Progress

The dashboard shows real-time metrics:
- **Pages Discovered**: Total URLs found
- **Pages Crawled**: Successfully processed pages
- **Pages Failed**: Errors encountered
- **Documents Found**: Files discovered
- **Current Depth**: Level being processed
- **Max Depth**: Deepest level reached
- **Crawl Rate**: Pages per minute
- **Speed**: Pages per second

### Downloading Files

1. Wait for crawl to complete (or stop it manually)
2. Click **"Download Files"** button
3. Files download to `E:\filefinder\{domain}\documents\`
4. Success message shows download stats

### Exporting Data

- **Export PDF**: Site map with summary and statistics
- **Export CSV**: Document list with URLs and metadata

---

## 🏗️ Architecture

### Modular Design (v2.0)

```
docs/apps/domain_intelligence/
├── server.py                 # FastAPI backend
├── dashboard.html            # Main UI (549 lines)
├── static/js/
│   ├── api.js               # API client
│   ├── ui.js                # UI utilities
│   ├── state.js             # State management
│   └── main.js              # App orchestration
└── requirements.txt          # Python dependencies
```

### Technology Stack

**Backend**:
- FastAPI (async web framework)
- Crawl4AI (web crawling engine)
- Playwright (browser automation)
- aiohttp (async HTTP)

**Frontend**:
- Vanilla JavaScript (ES6 modules)
- Tailwind CSS (styling)
- vis-network (graph visualization)
- Font Awesome (icons)

---

## 📊 API Reference

### Start Crawl
```http
POST /api/start-crawl
Content-Type: application/json

{
  "url": "https://example.com",
  "options": {
    "max_depth": 100,
    "max_pages": 1000,
    "file_types": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
  }
}
```

### Get Status
```http
GET /api/crawl-status/{session_id}
```

### Stop Crawl
```http
POST /api/stop-crawl/{session_id}
```

### Download Documents
```http
POST /api/download-documents/{session_id}
```

### Export PDF
```http
GET /api/export-pdf/{session_id}
```

### Export CSV
```http
GET /api/export-csv/{session_id}
```

Full API documentation: **http://localhost:8080/docs**

---

## ⚙️ Configuration

### Crawl Options

- **max_depth**: 1-1000 (default: 100)
  - High value = crawl as deep as needed
  - Limited by max_pages in practice

- **max_pages**: 1-10,000 (default: 1000)
  - Primary scope control
  - Stops crawl when limit reached
  - Only counts successful crawls

- **file_types**: Array of extensions
  - Default: `["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]`
  - Customize for specific file types

### Performance Settings

Built-in (not user-configurable):
- **Concurrent Requests**: 2 (human-like behavior)
- **Delay Between Requests**: 5-8 seconds (randomized)
- **Polling Interval**: 2 seconds (real-time updates)

---

## 🔧 Development

### Project Structure

See [MODULARIZATION_PLAN.md](MODULARIZATION_PLAN.md) for Phase 2 roadmap.

### Running in Development

```bash
# With auto-reload
uvicorn server:app --reload --port 8080

# With debugging
python -m debugpy --listen 5678 server.py
```

### Testing

```bash
# Health check
curl http://localhost:8080/health

# Start test crawl
curl -X POST http://localhost:8080/api/start-crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "options": {"max_pages": 50}}'
```

---

## 📝 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step guide
- **[MODULARIZATION_PLAN.md](MODULARIZATION_PLAN.md)** - Phase 2 roadmap
- **[PHASE_1B_COMPLETE.md](PHASE_1B_COMPLETE.md)** - Modularization details
- **[PROJECT_AUDIT.md](PROJECT_AUDIT.md)** - Cleanup documentation

---

## 🐛 Known Issues

### Browser Context Errors
Some browser context errors may appear at the end of large crawls. These are from Crawl4AI's browser management and don't affect results.

### Limitations
- Pause/resume not fully implemented
- Graph and tables still in legacy code (Phase 2 target)
- No virtual scrolling yet (planned for Phase 2)

---

## 🚀 Roadmap

### Phase 2: Advanced Components
- [ ] Extract graph.js module
- [ ] Extract tables.js with virtual scrolling
- [ ] Extract metrics.js module
- [ ] Reduce dashboard.html to ~450 lines

### Future Enhancements
- [ ] Crawl scheduling
- [ ] Multi-domain support
- [ ] Advanced filtering
- [ ] Export to additional formats
- [ ] Crawl templates

---

## 📄 License

Part of the Crawl4AI ecosystem. See main project LICENSE for details.

---

## 🙏 Credits

Built on [Crawl4AI](https://github.com/unclecode/crawl4ai) by [@unclecode](https://github.com/unclecode).

Dashboard architecture inspired by modern web application best practices.

---

## 💬 Support

For issues, questions, or contributions:
1. Check existing documentation
2. Review [CHANGELOG.md](CHANGELOG.md) for recent changes
3. See [Crawl4AI documentation](https://crawl4ai.com/mkdocs/)

---

**Version**: 2.0.0  
**Last Updated**: November 10, 2025  
**Status**: Production Ready ✅
