#!/usr/bin/env python3
"""
Simple ANAO Site Mapping - Config-Driven Approach

This demonstrates the power of Crawl4AI's configuration system
to map a site with minimal code.
"""

import asyncio
from pathlib import Path
import sys

# Add the parent directory to the path to import crawl4ai
sys.path.append(str(Path(__file__).parent.parent))

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig


async def simple_anao_mapping():
    """Simple ANAO site mapping using just configuration."""
    
    print("🌐 Simple ANAO Site Mapping")
    print("Using Crawl4AI's config-driven approach")
    print("=" * 50)
    
    # Simple browser configuration
    browser_config = BrowserConfig(
        headless=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    # Simple crawler configuration - this is where the power is!
    crawler_config = CrawlerRunConfig(
        # Basic settings
        word_count_threshold=100,
        delay_before_return_html=2.0,
        page_timeout=30000,
        
        # Content extraction
        only_text=False,
        css_selector=None,  # Get everything
        
        # Be respectful to the server
        mean_delay=2.0,
        max_range=3.0,
        
        # Enable link extraction
        exclude_external_links=False,
        exclude_social_media_links=True,
        
        # Screenshot for verification
        screenshot=True
    )
    
    # The magic happens here - just one simple call!
    async with AsyncWebCrawler(browser_config=browser_config, config=crawler_config) as crawler:
        
        print("📄 Crawling ANAO homepage...")
        result = await crawler.arun(url="https://www.anao.gov.au/")
        
        if result.success:
            print("✅ Success!")
            print(f"   📝 Content length: {len(result.cleaned_html):,} characters")
            print(f"   📄 Title: {result.title}")
            
            # Show discovered links
            if hasattr(result, 'links') and result.links:
                internal_links = result.links.get('internal', [])
                external_links = result.links.get('external', [])
                
                print(f"   🔗 Internal links: {len(internal_links)}")
                print(f"   🌐 External links: {len(external_links)}")
                
                # Show some key internal links
                print("\n🎯 Key Internal Links Found:")
                for i, link in enumerate(internal_links[:10]):
                    if isinstance(link, dict):
                        url = link.get('href', '')
                        text = link.get('text', '')[:50]
                        print(f"   {i+1}. {text} -> {url}")
                
                # Look for files
                file_links = []
                for link in internal_links:
                    if isinstance(link, dict):
                        url = link.get('href', '')
                        if any(url.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                            file_links.append(link)
                
                if file_links:
                    print(f"\n📁 Files Discovered: {len(file_links)}")
                    for i, file_link in enumerate(file_links[:5]):
                        url = file_link.get('href', '')
                        text = file_link.get('text', '')[:50]
                        print(f"   {i+1}. {text} -> {Path(url).name}")
                else:
                    print("\n📁 No direct file links found on homepage")
            
            # Show screenshot info
            if result.screenshot:
                print(f"\n📸 Screenshot captured: {len(result.screenshot)} bytes")
            
            print(f"\n📊 Simple Analysis:")
            print(f"   ✅ Site is accessible and crawlable")
            print(f"   📄 Rich content with {len(result.cleaned_html):,} characters")
            print(f"   🔗 Well-connected with {len(internal_links) if 'internal_links' in locals() else 0} internal links")
            print(f"   📁 Potential for file discovery: {'Yes' if 'file_links' in locals() and file_links else 'Limited on homepage'}")
            
            return True
            
        else:
            print("❌ Failed to crawl ANAO homepage")
            print(f"   Error: {result.error_message}")
            return False


async def main():
    """Main function - this is all the code you need!"""
    
    print("🚀 Crawl4AI - Config-Driven Web Crawling")
    print("No complex scripts needed - just configuration!")
    print()
    
    success = await simple_anao_mapping()
    
    if success:
        print("\n🎉 Simple mapping completed!")
        print("\n💡 Key Takeaway:")
        print("   With Crawl4AI, you get powerful web crawling")
        print("   through simple configuration, not complex code!")
        print("\n📚 Next Steps:")
        print("   1. Adjust CrawlerRunConfig for your needs")
        print("   2. Use extraction_strategy for structured data")
        print("   3. Add chunking_strategy for content processing")
        print("   4. Enable deep_crawl_strategy for site mapping")
    else:
        print("\n❌ Mapping failed - check your internet connection")


if __name__ == "__main__":
    asyncio.run(main())