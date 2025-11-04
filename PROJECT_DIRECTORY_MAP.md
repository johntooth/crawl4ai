# 🗺️ Crawl4AI Project Directory Map

## 📁 Root Directory Structure

```
crawl4ai/                                    # 🏠 PROJECT ROOT
├── 📂 .github/                             # GitHub workflows and templates
├── 📂 .kiro/                               # Kiro IDE configuration and specs
│   ├── 📂 settings/                        # IDE settings
│   ├── 📂 specs/                           # Project specifications
│   │   └── 📂 domain-intelligence-crawler/ # Domain intelligence spec
│   └── 📂 steering/                        # Development guidelines
├── 📂 crawl4ai/                            # 🧠 CORE PACKAGE
│   ├── 📄 __init__.py                      # Package exports and public API
│   ├── 📄 async_webcrawler.py              # Main AsyncWebCrawler class
│   ├── 📄 async_configs.py                 # Configuration classes
│   ├── 📄 async_database.py                # Database operations (SQLite)
│   ├── 📄 models.py                        # Pydantic data models
│   ├── 📄 utils.py                         # Utility functions
│   │
│   ├── 🎯 DOMAIN INTELLIGENCE COMPONENTS   # New exhaustive crawling system
│   ├── 📄 exhaustive_webcrawler.py         # Exhaustive crawler extension
│   ├── 📄 exhaustive_configs.py            # Exhaustive crawling configuration
│   ├── 📄 exhaustive_analytics.py          # Dead-end detection & analytics
│   ├── 📄 exhaustive_strategy_config.py    # Strategy configuration helpers
│   ├── 📄 exhaustive_integration.py        # Integration utilities
│   ├── 📄 exhaustive_monitoring.py         # Event-based monitoring
│   ├── 📄 exhaustive_analytics_reporting.py # Comprehensive reporting
│   ├── 📄 exhaustive_file_integration.py   # File discovery integration
│   ├── 📄 site_graph_db.py                 # Site graph database extension
│   ├── 📄 file_discovery_filter.py         # Multi-format file detection
│   │
│   ├── 🔧 EXISTING CORE MODULES            # Original Crawl4AI components
│   ├── 📄 async_crawler_strategy.py        # Browser automation strategies
│   ├── 📄 async_dispatcher.py              # Concurrent crawling management
│   ├── 📄 async_logger.py                  # Logging infrastructure
│   ├── 📄 browser_manager.py               # Browser lifecycle management
│   ├── 📄 cache_context.py                 # Caching system
│   ├── 📄 cli.py                           # Command-line interface
│   ├── 📄 config.py                        # Global configuration
│   │
│   ├── 📂 extraction_strategy/             # Content extraction strategies
│   ├── 📂 chunking_strategy/               # Text chunking algorithms
│   ├── 📂 content_scraping_strategy/       # HTML parsing strategies
│   ├── 📂 markdown_generation_strategy/    # Markdown conversion
│   ├── 📂 content_filter_strategy/         # Content filtering
│   ├── 📂 deep_crawling/                   # Multi-page crawling
│   └── 📂 components/                       # Reusable components
│
├── 📂 tests/                               # 🧪 TEST SUITE
│   ├── 📂 exhaustive/                      # Domain intelligence tests
│   │   ├── 📄 __init__.py                  # Test package initialization
│   │   ├── 📄 run_all_tests.py             # Comprehensive test runner
│   │   ├── 📄 test_exhaustive_basic.py     # Basic functionality tests
│   │   ├── 📄 test_exhaustive_config*.py   # Configuration validation tests
│   │   ├── 📄 test_exhaustive_performance.py # Performance benchmarks
│   │   ├── 📄 test_mock_website_scenarios.py # Mock site pattern tests
│   │   ├── 📄 test_exhaustive_orchestration.py # Real crawling integration
│   │   ├── 📄 test_comprehensive_exhaustive_crawling.py # End-to-end tests
│   │   └── 📄 test_exhaustive_dead_end_detection.py # Dead-end detection tests
│   │
│   ├── 📂 async/                           # Async functionality tests
│   ├── 📂 browser/                         # Browser automation tests
│   ├── 📂 general/                         # General functionality tests
│   ├── 📂 docker/                          # Docker deployment tests
│   └── 📄 test_*.py                        # Individual test files
│
├── 📂 examples/                            # 📚 USAGE EXAMPLES
│   ├── 🎯 DOMAIN INTELLIGENCE EXAMPLES     # New exhaustive crawling examples
│   ├── 📄 exhaustive_crawling_example.py   # Basic exhaustive crawling
│   ├── 📄 exhaustive_config_example.py     # Configuration examples
│   ├── 📄 exhaustive_dead_end_detection_example.py # Dead-end detection
│   ├── 📄 exhaustive_orchestration_example.py # Orchestration workflow
│   ├── 📄 exhaustive_monitoring_example.py # Monitoring and events
│   ├── 📄 exhaustive_analytics_reporting_example.py # Analytics & reporting
│   ├── 📄 exhaustive_file_discovery_example.py # File discovery
│   ├── 📄 site_graph_example.py            # Site graph database
│   ├── 📄 file_discovery_filter_example.py # File filtering
│   ├── 📄 adownload_file_example.py        # File downloading
│   │
│   └── 📄 *.py                             # Other usage examples
│
├── 📂 docs/                                # 📖 DOCUMENTATION
│   ├── 📂 customisations/                  # Custom component documentation
│   │   ├── 📄 DOMAIN_INTELLIGENCE_COMPONENTS.md # Component breakdown
│   │   ├── 📄 EXHAUSTIVE_TESTING.md        # Testing documentation
│   │   ├── 📄 CLEANUP_SUMMARY.md           # Project cleanup summary
│   │   └── 📄 INDEX.md                     # Documentation index
│   │
│   ├── 📂 blog/                            # Release notes and updates
│   ├── 📂 examples/                        # Documentation examples
│   └── 📄 *.md                             # Various documentation files
│
├── 📂 scripts/                             # 🔧 UTILITY SCRIPTS
│   └── 📄 cleanup.py                       # Project cleanup automation
│
├── 📂 deploy/                              # 🚀 DEPLOYMENT
│   └── 📂 docker/                          # Docker configurations
│
├── 📂 prompts/                             # 🤖 AI PROMPTS
│   └── 📄 *.md                             # LLM prompts and templates
│
├── 📄 PROJECT_DIRECTORY_MAP.md             # 🗺️ This file
├── 📄 README.md                            # Main project documentation
├── 📄 pyproject.toml                       # Python project configuration
├── 📄 requirements.txt                     # Python dependencies
├── 📄 docker-compose.yml                   # Docker deployment
├── 📄 Dockerfile                           # Docker image configuration
└── 📄 *.md                                 # Various project documentation
```

## 🎯 Domain Intelligence Components Map

### **Core Implementation Files**
```
crawl4ai/
├── exhaustive_webcrawler.py         # 🕷️  Main exhaustive crawler
├── exhaustive_configs.py            # ⚙️  Configuration system
├── exhaustive_analytics.py          # 📊  Analytics & dead-end detection
├── exhaustive_strategy_config.py    # 🎛️  Strategy configuration
├── exhaustive_integration.py        # 🔗  Integration utilities
├── exhaustive_monitoring.py         # 📡  Event monitoring
├── exhaustive_analytics_reporting.py # 📈  Comprehensive reporting
├── exhaustive_file_integration.py   # 📁  File discovery integration
├── site_graph_db.py                 # 🗄️  Site graph database
└── file_discovery_filter.py         # 🔍  File detection & filtering
```

### **Test Suite Structure**
```
tests/exhaustive/
├── run_all_tests.py                 # 🏃  Test runner
├── test_exhaustive_basic.py         # ✅  Basic functionality
├── test_exhaustive_config*.py       # ⚙️  Configuration tests
├── test_exhaustive_performance.py   # 🚀  Performance benchmarks
├── test_mock_website_scenarios.py   # 🌐  Mock site patterns
├── test_exhaustive_orchestration.py # 🎭  Real crawling tests
├── test_comprehensive_*.py          # 🔄  End-to-end integration
└── test_exhaustive_dead_end_*.py    # 🛑  Dead-end detection
```

### **Example Files Structure**
```
examples/
├── exhaustive_crawling_example.py          # 🎯  Basic usage
├── exhaustive_config_example.py            # ⚙️  Configuration
├── exhaustive_dead_end_detection_example.py # 🛑  Dead-end detection
├── exhaustive_orchestration_example.py     # 🎭  Workflow orchestration
├── exhaustive_monitoring_example.py        # 📡  Monitoring & events
├── exhaustive_analytics_reporting_example.py # 📈  Analytics & reporting
├── exhaustive_file_discovery_example.py    # 📁  File discovery
├── site_graph_example.py                   # 🗄️  Database operations
├── file_discovery_filter_example.py        # 🔍  File filtering
└── adownload_file_example.py               # ⬇️  File downloading
```

## 🏗️ Architecture Layers

### **Layer 1: Core Extensions**
- `exhaustive_webcrawler.py` - Main crawler extension
- `exhaustive_configs.py` - Configuration system
- `exhaustive_analytics.py` - Analytics engine

### **Layer 2: Specialized Components**
- `site_graph_db.py` - Database persistence
- `file_discovery_filter.py` - File detection
- `exhaustive_monitoring.py` - Event system

### **Layer 3: Integration & Reporting**
- `exhaustive_integration.py` - Integration utilities
- `exhaustive_analytics_reporting.py` - Reporting system
- `exhaustive_file_integration.py` - File workflow

### **Layer 4: Strategy & Configuration**
- `exhaustive_strategy_config.py` - Strategy helpers
- Preset configurations and validation
- Performance optimization settings

## 🔄 Data Flow Architecture

```
📥 Input URL
    ↓
⚙️ ExhaustiveCrawlConfig
    ↓
🕷️ ExhaustiveAsyncWebCrawler
    ↓
📊 ExhaustiveAnalytics (Dead-end Detection)
    ↓
🗄️ SiteGraphDatabaseManager (Persistence)
    ↓
🔍 FileDiscoveryFilter (File Detection)
    ↓
📈 ExhaustiveAnalyticsReporter (Reporting)
    ↓
📤 Comprehensive Results
```

## 🧪 Testing Architecture

### **Test Categories**
1. **Unit Tests** - Individual component validation
2. **Integration Tests** - Component interaction testing
3. **Performance Tests** - Scalability and speed benchmarks
4. **Mock Scenarios** - Various site structure patterns
5. **End-to-End Tests** - Complete workflow validation

### **Test Coverage**
- ✅ Configuration validation and presets
- ✅ Dead-end detection algorithms
- ✅ Database operations and persistence
- ✅ File discovery and downloading
- ✅ Analytics and reporting
- ✅ Performance benchmarks (1000+ URLs)
- ✅ Mock website scenarios (linear, hub-spoke, tree, cyclic)
- ✅ Real-world crawling integration

## 📊 Database Schema

### **Core Tables**
- `site_urls` - URL tracking and metadata
- `discovered_files` - File discovery and download status
- `site_stats` - Site-level statistics and metrics
- `crawl_sessions` - Session tracking and analytics

### **Technology Stack**
- **Database**: SQLite with async support (`aiosqlite`)
- **Connection Management**: Connection pooling
- **Schema Management**: Version control and migrations
- **Data Integrity**: Atomic transactions and constraints

This comprehensive directory map provides a complete overview of the Domain Intelligence Crawler implementation within the Crawl4AI ecosystem.