# Exhaustive Crawling Test Suite

This directory contains comprehensive tests for the exhaustive crawling functionality in Crawl4AI. The test suite validates all aspects of the domain intelligence crawler implementation.

## Test Files Overview

### Core Tests
- **`test_exhaustive_basic.py`** - Basic functionality validation and component imports
- **`test_exhaustive_config.py`** - Configuration creation and validation tests
- **`test_exhaustive_config_validation.py`** - Comprehensive configuration validation

### Integration Tests
- **`test_exhaustive_orchestration.py`** - Real exhaustive crawling with HTTP requests
- **`test_comprehensive_exhaustive_crawling.py`** - End-to-end workflow testing
- **`test_exhaustive_dead_end_detection.py`** - Dead-end detection functionality

### Performance & Scenarios
- **`test_exhaustive_performance.py`** - Performance testing for large-scale scenarios
- **`test_mock_website_scenarios.py`** - Mock website patterns and structures

## Running Tests

### Run All Tests
```bash
# Run the complete test suite
python tests/exhaustive/run_all_tests.py

# Or use pytest
python -m pytest tests/exhaustive/ -v
```

### Run Individual Test Categories
```bash
# Basic functionality
python tests/exhaustive/test_exhaustive_basic.py

# Configuration tests
python tests/exhaustive/test_exhaustive_config.py

# Performance tests
python tests/exhaustive/test_exhaustive_performance.py

# Mock scenarios
python tests/exhaustive/test_mock_website_scenarios.py

# Real crawling tests
python tests/exhaustive/test_exhaustive_orchestration.py
```

## Test Coverage

### ✅ Configuration Testing
- ExhaustiveCrawlConfig creation and validation
- Preset configurations (comprehensive, balanced, fast, files_focused, adaptive)
- Parameter validation and boundary testing
- Adaptive crawler integration

### ✅ Dead-End Detection
- Consecutive dead page thresholds
- Revisit ratio calculations
- URL discovery rate analysis
- Stopping condition logic

### ✅ Performance Testing
- Large-scale URL tracking (1000+ URLs)
- Memory usage validation
- Analytics performance
- Configuration creation performance

### ✅ Mock Website Scenarios
- Linear site structures (page1 → page2 → page3)
- Hub-and-spoke patterns
- Deep tree structures
- Cyclic link patterns
- File-rich sites
- Error handling scenarios

### ✅ Integration Testing
- Real HTTP crawling
- Progress tracking
- Analytics integration
- URL queue management
- Batch processing

## Requirements Validation

All tests validate the requirements specified in the domain intelligence crawler specification:

1. **Unit tests for ExhaustiveCrawlConfig and dead-end detection logic** ✅
2. **Integration tests for exhaustive crawling workflow** ✅
3. **Performance tests for large site mapping scenarios** ✅
4. **Mock websites for testing different crawling scenarios** ✅

## Test Data

The test suite uses:
- **Mock CrawlResult objects** for unit testing
- **Simulated website structures** for scenario testing
- **Real HTTP requests** for integration testing
- **Performance benchmarks** for scalability validation

## Expected Results

When all tests pass, you should see:
- ✅ Configuration validation working correctly
- ✅ Dead-end detection stopping crawls appropriately
- ✅ Performance meeting benchmarks (< 2s for 1000 URLs)
- ✅ Mock scenarios covering various site patterns
- ✅ Real crawling working with actual websites

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure you're running from the project root
2. **Network Timeouts**: Some integration tests require internet access
3. **Performance Failures**: May indicate system resource constraints

### Debug Mode
Add `verbose=True` to configuration objects for detailed logging during tests.

## Contributing

When adding new exhaustive crawling features:
1. Add corresponding tests to the appropriate test file
2. Update this README if new test categories are added
3. Ensure all tests pass before submitting changes
4. Follow the existing test patterns and naming conventions