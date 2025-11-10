# Dashboard Modularization Plan

## Current Problem
The dashboard.html file is 2600+ lines of monolithic code mixing:
- HTML structure
- CSS styles  
- JavaScript logic
- API calls
- UI state management
- Graph visualization
- Table rendering

This makes it hard to:
- Find and fix bugs
- Add new features
- Maintain code quality
- Test components

## Proposed Structure

```
docs/apps/domain_intelligence/
├── server.py                    # Backend API (already clean)
├── dashboard.html               # Main HTML shell (~100 lines)
├── static/
│   ├── css/
│   │   ├── main.css            # Base styles
│   │   ├── components.css      # Component-specific styles
│   │   └── graph.css           # Graph visualization styles
│   ├── js/
│   │   ├── api.js              # API client (fetch calls)
│   │   ├── state.js            # Global state management
│   │   ├── ui.js               # UI utilities (toast, modals)
│   │   ├── graph.js            # Graph visualization
│   │   ├── tables.js           # Table rendering (pages, docs)
│   │   ├── metrics.js          # Metrics dashboard
│   │   ├── forms.js            # Form handling
│   │   └── main.js             # App initialization
│   └── components/
│       ├── sidebar.html        # Left sidebar component
│       ├── metrics.html        # Metrics dashboard component
│       └── graph.html          # Graph container component
```

## Module Responsibilities

### api.js (~150 lines)
- `startCrawl(url, options)` - POST /api/start-crawl
- `getCrawlStatus(sessionId)` - GET /api/crawl-status/{id}
- `stopCrawl(sessionId)` - POST /api/stop-crawl/{id}
- `downloadDocuments(sessionId)` - POST /api/download-documents/{id}
- `exportPDF(sessionId)` - GET /api/export-pdf/{id}
- `exportCSV(sessionId)` - GET /api/export-csv/{id}

### state.js (~100 lines)
- Global state object
- Session state persistence (localStorage)
- State update notifications
- Session restore logic

### ui.js (~150 lines)
- `showToast(message, duration)`
- `showModal(id)` / `hideModal(id)`
- `updateProgress(progress)`
- `toggleSidebar(side)`
- Form validation helpers

### graph.js (~300 lines)
- Graph initialization
- Node/edge rendering
- Layout algorithms
- Interaction handlers
- Graph updates

### tables.js (~400 lines)
- Virtual scrolling implementation
- Page table rendering
- Document table rendering
- Sorting/filtering
- Row selection

### metrics.js (~200 lines)
- Metrics dashboard updates
- Depth distribution chart
- Document type breakdown
- Real-time metric calculations

### forms.js (~150 lines)
- Form submission handling
- Input validation
- File type selection
- URL validation

### main.js (~100 lines)
- App initialization
- Event listener setup
- Polling loop
- Component coordination

## Benefits

1. **Maintainability**: Each file has single responsibility
2. **Testability**: Can test modules independently
3. **Reusability**: Components can be reused
4. **Performance**: Can lazy-load modules
5. **Collaboration**: Multiple devs can work on different modules
6. **Debugging**: Easier to locate issues

## Migration Strategy

### Phase 1: Extract API Layer (Quick Win)
- Create `static/js/api.js` with all fetch calls
- Update dashboard.html to use API module
- Test all endpoints still work

### Phase 2: Extract State Management
- Create `static/js/state.js` for global state
- Move localStorage logic
- Update components to use state module

### Phase 3: Extract UI Utilities
- Create `static/js/ui.js` for common UI functions
- Move toast, modal, validation logic
- Update all callers

### Phase 4: Extract Large Components
- Create `static/js/graph.js` for graph visualization
- Create `static/js/tables.js` for table rendering
- Create `static/js/metrics.js` for metrics dashboard

### Phase 5: Extract Forms & Main
- Create `static/js/forms.js` for form handling
- Create `static/js/main.js` for initialization
- Clean up dashboard.html to just HTML structure

### Phase 6: Extract CSS
- Create separate CSS files
- Remove inline styles
- Organize by component

## Implementation Notes

### Using ES6 Modules
```html
<script type="module">
  import { startCrawl, getCrawlStatus } from './static/js/api.js';
  import { showToast } from './static/js/ui.js';
  import { initGraph } from './static/js/graph.js';
  
  // App initialization
  initGraph();
</script>
```

### Backward Compatibility
- Keep existing functionality working
- No breaking changes to API
- Gradual migration, test each phase

### File Serving
FastAPI can serve static files:
```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="docs/apps/domain_intelligence/static"), name="static")
```

## Next Steps

1. Create `static/` directory structure
2. Start with Phase 1 (API extraction) - lowest risk, high value
3. Test thoroughly after each phase
4. Update documentation as we go

This modularization will make the codebase much more maintainable while keeping all existing functionality intact.
