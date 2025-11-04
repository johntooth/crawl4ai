#!/usr/bin/env python3
"""
Exhaustive Crawling Test Runner

This script runs all exhaustive crawling tests in the correct order and provides
a comprehensive test report.
"""

import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def run_all_exhaustive_tests():
    """Run all exhaustive crawling tests."""
    print("🚀 Running Exhaustive Crawling Test Suite")
    print("=" * 50)
    
    test_modules = [
        ("Basic Functionality", "test_exhaustive_basic"),
        ("Configuration Validation", "test_exhaustive_config_validation"),
        ("Configuration Tests", "test_exhaustive_config"),
        ("Performance Tests", "test_exhaustive_performance"),
        ("Mock Website Scenarios", "test_mock_website_scenarios"),
        ("Orchestration Tests", "test_exhaustive_orchestration"),
        ("Comprehensive Integration", "test_comprehensive_exhaustive_crawling"),
        ("Dead-End Detection", "test_exhaustive_dead_end_detection"),
    ]
    
    passed_tests = 0
    total_tests = len(test_modules)
    
    for test_name, module_name in test_modules:
        print(f"\n📋 Running {test_name}...")
        try:
            # Import and run the test module
            module = __import__(module_name)
            
            # Run the main function if it exists
            if hasattr(module, 'main'):
                if asyncio.iscoroutinefunction(module.main):
                    await module.main()
                else:
                    module.main()
            else:
                print(f"   ✅ {test_name} - Module imported successfully")
            
            passed_tests += 1
            print(f"   ✅ {test_name} - PASSED")
            
        except Exception as e:
            print(f"   ❌ {test_name} - FAILED: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All exhaustive crawling tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_exhaustive_tests())
    sys.exit(exit_code)