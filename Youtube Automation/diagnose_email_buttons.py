#!/usr/bin/env python3
"""
Diagnose what email buttons actually exist on YouTube channels
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def diagnose_email_buttons():
    """Check what email-related elements exist on channels"""
    
    # Test a channel known to have business contact info
    channel = "https://www.youtube.com/@mkbhd"
    
    print("🔍 Diagnosing Email Button Elements")
    print("="*50)
    
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        # Go to about page
        about_url = channel.rstrip('/') + '/about'
        driver.get(about_url)
        time.sleep(5)
        
        print(f"📋 Current URL: {driver.current_url}")
        print(f"📋 Page title: {driver.title}")
        
        # Check all button-like elements
        selectors_to_check = [
            "//button",
            "//a[contains(@role, 'button')]", 
            "//*[contains(text(), 'email')]",
            "//*[contains(text(), 'Email')]",
            "//*[contains(text(), 'contact')]",
            "//*[contains(text(), 'Contact')]",
            "//*[contains(text(), 'business')]",
            "//*[contains(text(), 'Business')]",
            "//button[contains(@aria-label, 'View')]",
            "//yt-button-shape"
        ]
        
        for selector in selectors_to_check:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"\n📋 Selector: {selector}")
                print(f"Found {len(elements)} elements")
                
                for i, elem in enumerate(elements[:3]):  # Show first 3
                    try:
                        text = elem.text.strip()
                        aria_label = elem.get_attribute('aria-label') or ''
                        href = elem.get_attribute('href') or ''
                        tag = elem.tag_name
                        
                        if text or aria_label:
                            print(f"  [{i+1}] {tag}: '{text}' | aria-label: '{aria_label}' | href: '{href[:50]}...'")
                    except:
                        continue
                        
            except Exception as e:
                print(f"❌ Error with selector {selector}: {e}")
        
        # Check page source for email-related content
        page_source = driver.page_source.lower()
        keywords = ['view email', 'business inquiries', 'contact', 'sign in to see']
        
        print("\n📄 Page source analysis:")
        for keyword in keywords:
            count = page_source.count(keyword)
            print(f"  '{keyword}': {count} occurrences")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    diagnose_email_buttons()
    print("\n✅ Email button diagnosis completed!")
