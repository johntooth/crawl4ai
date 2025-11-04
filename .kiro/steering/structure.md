# Project Structure & Organization

## Root Directory Layout

```
crawl4ai/                    # Main package directory
├── __init__.py             # Package exports and public API
├── async_webcrawler.py     # Core AsyncWebCrawler class
├── async_configs.py        # Configuration classes (BrowserConfig, CrawlerRunConfig)
├── async_crawler_strategy.py # Browser automation strategies
├── async_database.py       # SQLite database operations
├── async_dispatcher.py     # Concurrent crawling management
├── async_logger.py         # Logging infrastructure
├── browser_manager.py      # Browser lifecycle management
├── cache_context.py        # Caching system
├── cli.py                  # Command-line interface
├── config.py              # Global configuration and constants
├── models.py              # Pydantic data models
└── utils.py               # Utility functions

docs/                       # Documentation
├── examples/              # Code examples and tutorials
├── blog/                  # Release notes and updates
└── assets/               # Images and media

tests/                     # Test suite
├── async/                # Async functionality tests
├── browser/              # Browser-specific tests
├── cli/                  # CLI tests
└── general/              # General functionality tests

deploy/docker/             # Docker deployment configurations
```

## Core Module Organization

### Strategy Pattern Implementation
- **extraction_strategy.py**: LLM, CSS, XPath, Regex extraction strategies
- **chunking_strategy.py**: Text chunking algorithms (regex, sliding window)
- **content_scraping_strategy.py**: HTML parsing strategies (LXML, BeautifulSoup)
- **markdown_generation_strategy.py**: Markdown conversion strategies
- **content_filter_strategy.py**: Content filtering (BM25, pruning, LLM-based)

### Browser & Automation
- **browser_adapter.py**: Browser abstraction layer
- **browser_profiler.py**: User profile management
- **proxy_strategy.py**: Proxy rotation and management
- **ssl_certificate.py**: SSL/TLS handling

### Data Processing
- **table_extraction.py**: Table detection and extraction
- **link_preview.py**: Link analysis and scoring
- **user_agent_generator.py**: User agent rotation

### Advanced Features
- **adaptive_crawler.py**: Intelligent crawling with learning
- **deep_crawling/**: Multi-page crawling strategies
- **components/**: Reusable components (monitors, profilers)

## Configuration Architecture

### Typed Configuration Classes
- **BrowserConfig**: Browser settings, profiles, proxy configuration
- **CrawlerRunConfig**: Per-crawl settings, strategies, extraction options
- **LLMConfig**: LLM provider settings and API configuration
- **ProxyConfig**: Proxy rotation and authentication
- **SeedingConfig**: URL discovery and filtering

### Environment Configuration
- **.env** files for API keys and secrets
- **config.py** for global constants and provider mappings
- **pyproject.toml** for package metadata and dependencies

## Naming Conventions

### Files & Modules
- **async_*.py**: Async-first implementations
- ***_strategy.py**: Strategy pattern implementations
- ***_config.py**: Configuration classes
- **test_*.py**: Test files

### Classes
- **Async*** prefix for async classes (AsyncWebCrawler, AsyncLogger)
- *****Strategy** suffix for strategy implementations
- *****Config** suffix for configuration classes
- *****Result** suffix for result data classes

### Methods
- **arun()**: Async single URL crawling
- **arun_many()**: Async batch crawling
- **setup()**: Initialization methods
- **warmup()**: Pre-execution preparation

## Import Organization

### Public API (__init__.py)
All user-facing classes and functions are exported from the main package:
- Core classes: AsyncWebCrawler, CacheMode
- Configuration: BrowserConfig, CrawlerRunConfig, LLMConfig
- Strategies: All extraction, chunking, and processing strategies
- Models: CrawlResult, MarkdownGenerationResult

### Internal Imports
- Relative imports within the package
- Strategy classes imported in crawler modules
- Utility functions imported as needed

## Testing Structure

### Test Categories
- **async/**: Async functionality and concurrency
- **browser/**: Browser automation and profiles
- **cli/**: Command-line interface
- **general/**: Core functionality
- **docker/**: Docker deployment testing

### Test Patterns
- Async test methods with proper setup/teardown
- Mock external dependencies (LLM APIs, websites)
- Integration tests for end-to-end workflows
- Performance tests for large-scale operations