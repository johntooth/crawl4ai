# Crawl4AI Codebase Guidelines

## Critical: We Have a Complete Crawl4AI Clone

**IMPORTANT**: This workspace contains a complete clone of the Crawl4AI project. You do NOT need to import external libraries or install packages that are already part of the Crawl4AI ecosystem.

## Before Writing Any Code

### 1. Always Check Existing Implementation First
- **MANDATORY**: Before implementing any functionality, search the existing codebase to understand:
  - How similar features are already implemented
  - What libraries and dependencies are already available
  - What patterns and conventions are used
  - What interfaces and base classes exist

### 2. Leverage Existing Infrastructure
- Use existing imports and dependencies that are already in the project
- Follow existing patterns for async operations, logging, configuration, etc.
- Extend existing classes rather than creating new ones when possible
- Use existing utility functions and helper methods

### 3. Check Dependencies Before Adding New Ones
- **DO NOT** add new external dependencies without first checking if:
  - The functionality already exists in the codebase
  - A similar library is already included
  - The feature can be implemented using existing dependencies

## Common Existing Dependencies (Already Available)

### Core Libraries
- `asyncio` - For async operations
- `aiohttp` - For HTTP requests (already used in the project)
- `aiofiles` - For async file operations (already used in the project)
- `playwright` - For browser automation
- `pydantic` - For data models and validation
- `sqlite3`/`aiosqlite` - For database operations

### Crawl4AI Specific Modules
- `crawl4ai.async_webcrawler` - Main crawler class
- `crawl4ai.async_configs` - Configuration classes
- `crawl4ai.async_crawler_strategy` - Browser automation strategies
- `crawl4ai.models` - Data models and response objects
- `crawl4ai.utils` - Utility functions
- `crawl4ai.async_logger` - Logging infrastructure

## Implementation Guidelines

### 1. Extend Existing Classes
```python
# GOOD: Extend existing AsyncWebCrawler
class EnhancedCrawler(AsyncWebCrawler):
    async def new_method(self):
        # Implementation using existing infrastructure
        pass

# AVOID: Creating completely new classes when extensions work
```

### 2. Use Existing Configuration Patterns
```python
# GOOD: Use existing CrawlerRunConfig
config = CrawlerRunConfig(
    user_agent="Custom-Agent",
    proxy_config=proxy_config
)

# AVOID: Creating new configuration systems
```

### 3. Follow Existing Async Patterns
```python
# GOOD: Follow existing async patterns
async def new_feature(self):
    async with self.session as session:
        # Use existing session management
        pass

# AVOID: Creating new async patterns
```

### 4. Use Existing Logging
```python
# GOOD: Use existing logger
self.logger.info(
    message="Operation completed: {operation}",
    tag="FEATURE",
    params={"operation": operation_name}
)

# AVOID: Creating new logging systems
```

## Code Review Checklist

Before submitting any implementation:

- [ ] Searched existing codebase for similar functionality
- [ ] Used existing dependencies and libraries
- [ ] Followed existing patterns and conventions
- [ ] Extended existing classes where appropriate
- [ ] Used existing configuration and logging systems
- [ ] Verified no new external dependencies are needed
- [ ] Tested that existing functionality still works

## File Structure Awareness

### Key Directories
- `crawl4ai/` - Main package with core functionality
- `tests/` - Test suite with examples of usage patterns
- `examples/` - Usage examples showing best practices
- `docs/` - Documentation with API references

### Key Files to Reference
- `crawl4ai/async_webcrawler.py` - Main crawler implementation
- `crawl4ai/async_configs.py` - Configuration classes and patterns
- `crawl4ai/models.py` - Data models and response structures
- `crawl4ai/utils.py` - Utility functions and helpers

## Integration Philosophy

**Principle**: Enhance and extend the existing Crawl4AI ecosystem rather than replacing or duplicating it.

- Build on existing foundations
- Maintain backward compatibility
- Follow established patterns
- Leverage existing infrastructure
- Contribute to the unified codebase