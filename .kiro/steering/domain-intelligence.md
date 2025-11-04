# Domain Intelligence Architecture

## CRITICAL: Working with Crawl4AI Codebase

**MANDATORY FIRST STEP**: This workspace contains a complete Crawl4AI clone. Before implementing ANY functionality:

1. **Search the existing codebase** for similar features, patterns, and dependencies
2. **Use existing libraries** - aiohttp, aiofiles, playwright, etc. are already available
3. **Extend existing classes** rather than creating new ones
4. **Follow existing patterns** for async operations, logging, configuration
5. **Check existing imports** - do NOT add external dependencies unnecessarily

## Critical Gaps & Implementation Strategy

### 1. Adaptive Intelligence Infrastructure

**Current State**: Basic adaptive_crawler.py exists but lacks concrete learning mechanisms
**Needed**: Intelligent pattern recognition and strategy adaptation

```python
# Target Architecture
class DomainIntelligenceStrategy:
    async def learn_site_patterns(self, crawl_results: List[CrawlResult]) -> SitePatterns
    async def predict_relevant_paths(self, domain: str) -> List[str]
    async def adjust_crawl_strategy(self, real_time_metrics: Dict) -> CrawlerRunConfig
    async def score_content_relevance(self, content: str, query: str) -> float
```

**Implementation Approach**:
- Extend existing LLMExtractionStrategy for pattern learning
- Use existing LLMConfig infrastructure for domain analysis
- Build on async_database.py for pattern persistence
- Leverage existing BM25ContentFilter for relevance scoring

### 2. Site Mapping & Graph Persistence

**Current State**: Basic deep crawling with BFS/DFS strategies
**Needed**: Comprehensive site structure mapping and persistence

```python
# New Module Structure
site_mapping/
├── site_graph_builder.py      # Build site relationship graphs
├── url_relationship_tracker.py # Track parent-child URL relationships
├── completeness_analyzer.py    # Measure crawl completeness
├── sitemap_exporter.py        # Export to XML, JSON, GraphML
└── crawl_resume_manager.py    # Resume interrupted crawls
```

**Integration Points**:
- Extend existing async_database.py for graph storage
- Build on deep_crawling/ strategies
- Use existing cache_context.py for state management
- Leverage async_dispatcher.py for concurrent mapping

### 3. File Discovery & Content Intelligence

**Current State**: HTML-focused content extraction
**Needed**: Multi-format file detection and extraction

```python
# New Capabilities
file_discovery/
├── file_type_detector.py       # Detect .pdf, .doc, .xls, etc.
├── download_manager.py         # Async file downloading
├── file_content_extractor.py   # Extract text from files
└── file_metadata_preserver.py  # Preserve file metadata
```

**Architecture Alignment**:
- Follow existing ContentScrapingStrategy pattern
- Use async patterns from async_webcrawler.py
- Extend existing models.py for file metadata
- Build on browser_manager.py for file downloads

## Implementation Patterns

### Configuration Extension
```python
# Extend existing CrawlerRunConfig
@dataclass
class DomainIntelligentConfig(CrawlerRunConfig):
    enable_site_mapping: bool = True
    file_extensions_target: List[str] = field(default_factory=list)
    max_site_depth: int = 10
    domain_learning_enabled: bool = True
    completeness_threshold: float = 0.95
    resume_interrupted_crawls: bool = True
```

### Strategy Pattern Usage
```python
# Follow existing strategy patterns
class DomainLearningStrategy(ExtractionStrategy):
    async def extract(self, content: str) -> DomainPatterns:
        # Learn site structure and content patterns
        pass

class FileDiscoveryStrategy(ContentFilterStrategy):
    async def filter(self, urls: List[str]) -> List[FileMetadata]:
        # Identify and prioritize file downloads
        pass

class SiteCompletenessStrategy(ChunkingStrategy):
    async def chunk(self, urls: List[str]) -> List[CrawlBatch]:
        # Organize crawling for maximum completeness
        pass
```

### Core Class Extensions
```python
# Extend AsyncWebCrawler for domain intelligence
class DomainIntelligentCrawler(AsyncWebCrawler):
    async def arun_exhaustive(self, url: str, 
                             domain_config: DomainIntelligentConfig) -> SiteMapResult:
        # Build comprehensive site map
        pass
    
    async def arun_resume(self, crawl_id: str) -> SiteMapResult:
        # Resume interrupted domain crawl
        pass
    
    async def analyze_domain_patterns(self, domain: str) -> DomainAnalysis:
        # Learn domain-specific patterns
        pass
```

## Integration Guidelines

### Leverage Existing Infrastructure
- **LLM Integration**: Use existing LLMConfig for pattern analysis
- **Async Operations**: Follow async_webcrawler.py patterns
- **Database**: Extend async_database.py for graph storage
- **Caching**: Use cache_context.py for state persistence
- **Configuration**: Follow async_configs.py patterns

### Maintain API Consistency
- **Method Naming**: Follow arun() pattern (arun_exhaustive, arun_resume)
- **Configuration**: Extend existing config classes
- **Results**: Follow CrawlResult model patterns
- **Error Handling**: Use existing error handling patterns

### Performance Considerations
- **Memory Management**: Follow existing memory monitoring patterns
- **Concurrency**: Use async_dispatcher.py for parallel operations
- **Resource Cleanup**: Follow context manager patterns
- **Progress Tracking**: Extend existing logging infrastructure

## Priority Implementation Order

1. **Site Graph Builder**: Core infrastructure for relationship tracking
2. **Domain Learning Strategy**: Pattern recognition and adaptation
3. **File Discovery System**: Multi-format content extraction
4. **Completeness Analyzer**: Crawl quality metrics
5. **Resume Manager**: Interrupted crawl recovery