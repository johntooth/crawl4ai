# Technology Stack & Build System

## CRITICAL: Complete Crawl4AI Codebase Available

**IMPORTANT**: This workspace contains the complete Crawl4AI project. All dependencies, libraries, and infrastructure are already available. DO NOT import external packages that are already part of the ecosystem.

**MANDATORY**: Always check existing codebase before writing new code:
- Search for existing implementations
- Use existing dependencies (aiohttp, aiofiles, playwright, etc.)
- Follow existing patterns and conventions
- Extend existing classes rather than creating new ones

## Core Technologies

- **Language**: Python 3.10+ (modern async/await patterns)
- **Web Automation**: Playwright (primary), Selenium (legacy sync support)
- **Browser Support**: Chromium, Firefox, WebKit, Undetected Chrome
- **Async Framework**: asyncio with aiohttp for HTTP operations
- **Database**: SQLite with aiosqlite for async operations
- **Packaging**: setuptools with pyproject.toml (PEP 621 compliant)

## Key Dependencies

- **Browser Control**: playwright>=1.49.0, patchright>=1.49.0
- **LLM Integration**: litellm>=1.53.1 (supports all major LLM providers)
- **Content Processing**: lxml, beautifulsoup4, rank-bm25, nltk
- **Data Handling**: pydantic>=2.10, numpy, pillow
- **CLI**: click>=8.1.7, rich>=13.9.4 for enhanced terminal output
- **Docker**: FastAPI server with JWT authentication

## Architecture Patterns

- **Async-First**: All core operations use async/await patterns
- **Strategy Pattern**: Pluggable extraction, chunking, and markdown generation strategies
- **Configuration Objects**: Typed configs (BrowserConfig, CrawlerRunConfig, LLMConfig)
- **Context Managers**: Resource management with async context managers
- **Dependency Injection**: Strategy injection for customizable behavior

## Common Commands

### Development Setup
```bash
# Clone and install in development mode
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .

# Install with optional features
pip install -e ".[all]"  # All features
pip install -e ".[torch]"  # PyTorch features
pip install -e ".[transformer]"  # Transformer features
```

### Installation & Setup
```bash
# Standard installation
pip install crawl4ai
crawl4ai-setup  # Setup browsers

# Pre-release versions
pip install crawl4ai --pre

# Manual browser setup if needed
python -m playwright install chromium
```

### CLI Usage
```bash
# Basic crawling
crwl https://example.com -o markdown

# Deep crawling with BFS strategy
crwl https://docs.site.com --deep-crawl bfs --max-pages 10

# LLM extraction
crwl https://example.com -q "Extract product prices"
```

### Docker Deployment
```bash
# Pull and run latest
docker pull unclecode/crawl4ai:latest
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g unclecode/crawl4ai:latest

# Using docker-compose
docker-compose up -d
```

### Testing
```bash
# Run diagnostics
crawl4ai-doctor

# Test installation
python -c "import crawl4ai; print('OK')"
```

## Build Configuration

- **pyproject.toml**: Modern Python packaging with dynamic versioning
- **setup.py**: Backward compatibility wrapper
- **requirements.txt**: Development dependencies
- **Dockerfile**: Multi-stage build with Python 3.12 slim base
- **docker-compose.yml**: Production deployment configuration