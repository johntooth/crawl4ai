# Quick Start Guide - Domain Intelligence Dashboard

## Prerequisites

- Python 3.10 or higher
- Crawl4AI installed (from the main project)

## Installation

1. Navigate to the dashboard directory:
```bash
cd docs/apps/domain_intelligence
```

2. Install server dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the FastAPI server:
```bash
python server.py
```

You should see:
```
Starting Domain Intelligence Dashboard Server...
Dashboard will be available at: http://localhost:8080
API documentation at: http://localhost:8080/docs
INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## Testing the Server

In a new terminal, run the test script:
```bash
python test_server.py
```

This will:
1. Check server health
2. Start a test crawl of example.com
3. Poll for progress updates
4. Display discovered pages and documents

## Using the API

### Start a Crawl

```bash
curl -X POST http://localhost:8080/api/start-crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": {
      "max_depth": 3,
      "max_pages": 100,
      "file_types": ["pdf", "doc", "xls"]
    }
  }'
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Crawl session 550e8400-e29b-41d4-a716-446655440000 started"
}
```

### Check Status

```bash
curl http://localhost:8080/api/crawl-status/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": {
    "pages_discovered": 15,
    "pages_crawled": 12,
    "documents_found": 3,
    "documents_downloaded": 0,
    "current_page": "https://example.com/about",
    "errors": [],
    "elapsed_seconds": 8.5
  },
  "pages": [...],
  "documents": [...]
}
```

### Pause/Resume

```bash
curl -X POST http://localhost:8080/api/pause-crawl/550e8400-e29b-41d4-a716-446655440000
```

Call again to resume.

### Stop

```bash
curl -X POST http://localhost:8080/api/stop-crawl/550e8400-e29b-41d4-a716-446655440000
```

## Accessing the Dashboard

Open your browser to:
```
http://localhost:8080
```

The dashboard HTML will be served (frontend integration coming in Task 3).

## API Documentation

Interactive API documentation is available at:
```
http://localhost:8080/docs
```

This provides:
- Complete API reference
- Interactive testing interface
- Request/response schemas
- Example requests

## Troubleshooting

### Server Won't Start

**Error**: `Address already in use`

**Solution**: Another process is using port 8080. Either:
- Stop the other process
- Change the port in server.py (last line)

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'crawl4ai'`

**Solution**: Install Crawl4AI from the main project:
```bash
cd ../../../  # Go to project root
pip install -e .
```

### Crawl Fails Immediately

**Error**: Crawl status shows "failed" immediately

**Solution**: Check:
- URL is valid and accessible
- No firewall blocking requests
- Server logs for detailed error messages

### Slow Crawling

**Issue**: Crawl is very slow

**Solution**: Adjust options:
```json
{
  "semaphore_count": 20,  // Increase concurrency
  "mean_delay": 0.1       // Reduce delay
}
```

## Next Steps

1. **Frontend Integration** (Task 3): Connect dashboard UI to API
2. **Progress Tracking** (Task 4): Real-time updates in UI
3. **Graph Visualization** (Task 5): Display discovered pages
4. **Export Features** (Task 6): PDF/CSV exports

## Development Mode

For development with auto-reload:
```bash
uvicorn server:app --reload --port 8080
```

## Production Deployment

For production, use:
```bash
uvicorn server:app --host 0.0.0.0 --port 8080 --workers 4
```

Or with gunicorn:
```bash
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review IMPLEMENTATION_NOTES.md for technical details
3. Check server logs for error messages
4. Refer to Crawl4AI documentation for crawler issues
