# __init__.py
import warnings

from .async_webcrawler import AsyncWebCrawler, CacheMode
# MODIFIED: Add SeedingConfig and VirtualScrollConfig here
from .async_configs import BrowserConfig, CrawlerRunConfig, HTTPCrawlerConfig, LLMConfig, ProxyConfig, GeolocationConfig, SeedingConfig, VirtualScrollConfig, LinkPreviewConfig, MatchMode
# NEW: Import ExhaustiveCrawlConfig for domain intelligence crawler
from .exhaustive_configs import ExhaustiveCrawlConfig, create_exhaustive_preset_config
# NEW: Import exhaustive strategy configuration functions
from .exhaustive_strategy_config import (
    create_exhaustive_bfs_strategy,
    create_minimal_filter_chain,
    configure_exhaustive_crawler_settings,
    create_exhaustive_strategy_preset
)

from .content_scraping_strategy import (
    ContentScrapingStrategy,
    LXMLWebScrapingStrategy,
    WebScrapingStrategy,  # Backward compatibility alias
)
from .async_logger import (
    AsyncLoggerBase,
    AsyncLogger,
)
from .proxy_strategy import (
    ProxyRotationStrategy,
    RoundRobinProxyStrategy,
)
from .extraction_strategy import (
    ExtractionStrategy,
    LLMExtractionStrategy,
    CosineStrategy,
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
    JsonLxmlExtractionStrategy,
    RegexExtractionStrategy
)
from .chunking_strategy import ChunkingStrategy, RegexChunking
from .markdown_generation_strategy import DefaultMarkdownGenerator
from .table_extraction import (
    TableExtractionStrategy,
    DefaultTableExtraction,
    NoTableExtraction,
    LLMTableExtraction,
)
from .content_filter_strategy import (
    PruningContentFilter,
    BM25ContentFilter,
    LLMContentFilter,
    RelevantContentFilter,
)
from .models import CrawlResult, MarkdownGenerationResult, DisplayMode
from .components.crawler_monitor import CrawlerMonitor
from .link_preview import LinkPreview
from .async_dispatcher import (
    MemoryAdaptiveDispatcher,
    SemaphoreDispatcher,
    RateLimiter,
    BaseDispatcher,
)
from .docker_client import Crawl4aiDockerClient
from .hub import CrawlerHub
from .browser_profiler import BrowserProfiler
from .deep_crawling import (
    DeepCrawlStrategy,
    BFSDeepCrawlStrategy,
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
    URLFilter,
    FilterStats,
    SEOFilter,
    KeywordRelevanceScorer,
    URLScorer,
    CompositeScorer,
    DomainAuthorityScorer,
    FreshnessScorer,
    PathDepthScorer,
    BestFirstCrawlingStrategy,
    DFSDeepCrawlStrategy,
    DeepCrawlDecorator,
)
# NEW: File Discovery Filter
from .file_discovery_filter import (
    FileDiscoveryFilter,
    FileType,
    FileMetadata,
    FileDiscoveryStats,
    create_document_filter,
    create_data_filter,
    create_media_filter,
    create_comprehensive_filter,
)
# NEW: Import AsyncUrlSeeder
from .async_url_seeder import AsyncUrlSeeder
# Adaptive Crawler
from .adaptive_crawler import (
    AdaptiveCrawler,
    AdaptiveConfig,
    CrawlState,
    CrawlStrategy,
    StatisticalStrategy
)

# NEW: Exhaustive Crawling with Dead-End Detection
from .exhaustive_analytics import (
    ExhaustiveAnalytics,
    DeadEndMetrics,
    URLTrackingState
)
from .exhaustive_webcrawler import (
    ExhaustiveAsyncWebCrawler,
    ExhaustiveCrawlConfig,
    create_exhaustive_crawler
)
from .exhaustive_integration import (
    ExhaustiveCrawlIntegration,
    configure_exhaustive_crawler,
    create_dead_end_detector,
    analyze_url_discovery_rate
)

# C4A Script Language Support
from .script import (
    compile as c4a_compile,
    validate as c4a_validate,
    compile_file as c4a_compile_file,
    CompilationResult,
    ValidationResult,
    ErrorDetail
)

# Browser Adapters
from .browser_adapter import (
    BrowserAdapter,
    PlaywrightAdapter,
    UndetectedAdapter
)

from .utils import (
    start_colab_display_server,
    setup_colab_environment,
    hooks_to_string
)

__all__ = [
    "AsyncLoggerBase",
    "AsyncLogger",
    "AsyncWebCrawler",
    "BrowserProfiler",
    "LLMConfig",
    "GeolocationConfig",
    # NEW: Add SeedingConfig and VirtualScrollConfig
    "SeedingConfig",
    "VirtualScrollConfig",
    # NEW: Add AsyncUrlSeeder
    "AsyncUrlSeeder",
    # Adaptive Crawler
    "AdaptiveCrawler",
    "AdaptiveConfig", 
    "CrawlState",
    "CrawlStrategy",
    "StatisticalStrategy",
    "DeepCrawlStrategy",
    "BFSDeepCrawlStrategy",
    "BestFirstCrawlingStrategy",
    "DFSDeepCrawlStrategy",
    "FilterChain",
    "URLPatternFilter",
    "ContentTypeFilter",
    "DomainFilter",
    "FilterStats",
    "URLFilter",
    "SEOFilter",
    # NEW: File Discovery Filter exports
    "FileDiscoveryFilter",
    "FileType",
    "FileMetadata", 
    "FileDiscoveryStats",
    "create_document_filter",
    "create_data_filter",
    "create_media_filter",
    "create_comprehensive_filter",
    "KeywordRelevanceScorer",
    "URLScorer",
    "CompositeScorer",
    "DomainAuthorityScorer",
    "FreshnessScorer",
    "PathDepthScorer",
    "DeepCrawlDecorator",
    "CrawlResult",
    "CrawlerHub",
    "CacheMode",
    "MatchMode",
    "ContentScrapingStrategy",
    "WebScrapingStrategy",
    "LXMLWebScrapingStrategy",
    "BrowserConfig",
    "CrawlerRunConfig",
    "ExhaustiveCrawlConfig",
    "create_exhaustive_preset_config",
    "create_exhaustive_bfs_strategy",
    "create_minimal_filter_chain", 
    "configure_exhaustive_crawler_settings",
    "create_exhaustive_strategy_preset",
    "HTTPCrawlerConfig",
    "ExtractionStrategy",
    "LLMExtractionStrategy",
    "CosineStrategy",
    "JsonCssExtractionStrategy",
    "JsonXPathExtractionStrategy",
    "JsonLxmlExtractionStrategy",
    "RegexExtractionStrategy",
    "ChunkingStrategy",
    "RegexChunking",
    "DefaultMarkdownGenerator",
    "TableExtractionStrategy",
    "DefaultTableExtraction",
    "NoTableExtraction",
    "RelevantContentFilter",
    "PruningContentFilter",
    "BM25ContentFilter",
    "LLMContentFilter",
    "BaseDispatcher",
    "MemoryAdaptiveDispatcher",
    "SemaphoreDispatcher",
    "RateLimiter",
    "CrawlerMonitor",
    "LinkPreview",
    "DisplayMode",
    "MarkdownGenerationResult",
    "Crawl4aiDockerClient",
    "ProxyRotationStrategy",
    "RoundRobinProxyStrategy",
    "ProxyConfig",
    "start_colab_display_server",
    "setup_colab_environment",
    "hooks_to_string",
    # C4A Script additions
    "c4a_compile",
    "c4a_validate", 
    "c4a_compile_file",
    "CompilationResult",
    "ValidationResult",
    "ErrorDetail",
    # Browser Adapters
    "BrowserAdapter",
    "PlaywrightAdapter", 
    "UndetectedAdapter",
    "LinkPreviewConfig",
    # NEW: Exhaustive Crawling exports
    "ExhaustiveAnalytics",
    "DeadEndMetrics", 
    "URLTrackingState",
    "ExhaustiveAsyncWebCrawler",
    "ExhaustiveCrawlConfig",
    "create_exhaustive_crawler",
    "ExhaustiveCrawlIntegration",
    "configure_exhaustive_crawler",
    "create_dead_end_detector",
    "analyze_url_discovery_rate"
]


# def is_sync_version_installed():
#     try:
#         import selenium # noqa

#         return True
#     except ImportError:
#         return False


# if is_sync_version_installed():
#     try:
#         from .web_crawler import WebCrawler

#         __all__.append("WebCrawler")
#     except ImportError:
#         print(
#             "Warning: Failed to import WebCrawler even though selenium is installed. This might be due to other missing dependencies."
#         )
# else:
#     WebCrawler = None
#     # import warnings
#     # print("Warning: Synchronous WebCrawler is not available. Install crawl4ai[sync] for synchronous support. However, please note that the synchronous version will be deprecated soon.")

# Disable all Pydantic warnings
warnings.filterwarnings("ignore", module="pydantic")
# pydantic_warnings.filter_warnings()