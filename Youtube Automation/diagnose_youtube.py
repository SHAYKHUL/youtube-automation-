#!/usr/bin/env python3
"""
Diagnostic test for YouTube video detection
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def diagnose_youtube_page():
    """Diagnose what elements are found on YouTube pages"""
    
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        test_channel = "https://www.youtube.com/@TEDx/videos"
        print(f"🔍 Navigating to: {test_channel}")
        
        driver.get(test_channel)
        time.sleep(5)  # Wait longer for page to load
        
        print("\n📋 Page title:", driver.title)
        print("📋 Current URL:", driver.current_url)
        
        # Check if we got redirected or there's a different structure
        print("\n🔍 Looking for video elements...")
        
        # Try to find any links with video-title id
        video_title_links = driver.find_elements(By.XPATH, "//a[@id='video-title']")
        print(f"Found {len(video_title_links)} elements with id='video-title'")
        
        # Try to find any ytd-rich-grid-media elements
        rich_grid = driver.find_elements(By.XPATH, "//ytd-rich-grid-media")
        print(f"Found {len(rich_grid)} ytd-rich-grid-media elements")
        
        # Try to find any video links
        all_video_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/watch?v=')]")
        print(f"Found {len(all_video_links)} links containing '/watch?v='")
        
        if all_video_links:
            print(f"First video link: {all_video_links[0].get_attribute('href')}")
            print(f"First video title: {all_video_links[0].get_attribute('title') or all_video_links[0].text}")
        
        # Check page source for debugging
        page_source_snippet = driver.page_source[:1000]
        print(f"\n📄 Page source snippet (first 1000 chars):\n{page_source_snippet}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    diagnose_youtube_page()
