#!/usr/bin/env python3
"""
Automated test for enhanced video description extraction
"""

import sys
import os
from selenium import webdriver
from email_finder import get_latest_video_description, extract_emails_and_socials

def test_enhanced_video_description():
    """Test the enhanced video description extraction automatically"""
    
    # Test channels - using more direct links
    test_channels = [
        "https://www.youtube.com/@TEDx",
        "https://www.youtube.com/@TheTechLead"
    ]
    
    print("🧪 Automated Video Description Test")
    print("="*50)
    
    # Setup webdriver
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        for i, channel in enumerate(test_channels, 1):
            print(f"\n🔍 Testing Channel {i}: {channel}")
            print("-" * 40)
            
            try:
                # Step 1: Get video description
                print("📹 Extracting latest video description...")
                desc_text = get_latest_video_description(driver, channel)
                
                if desc_text:
                    print(f"✅ Description extracted! Length: {len(desc_text)} characters")
                    print(f"📝 First 200 chars: {desc_text[:200]}...")
                    
                    # Step 2: Extract emails and socials from description
                    print("🔍 Searching for emails and social links in description...")
                    emails, socials, usernames = extract_emails_and_socials(desc_text)
                    
                    print(f"📧 Emails found: {len(emails)}")
                    for email in emails:
                        print(f"   - {email}")
                    
                    print(f"🔗 Social links found: {len(socials)}")  
                    for platform, links in socials.items():
                        print(f"   {platform}: {', '.join(links)}")
                        
                    print(f"👤 Usernames found: {len(usernames)}")
                    for username in usernames:
                        print(f"   - {username}")
                else:
                    print("❌ No description text extracted")
                    
            except Exception as e:
                print(f"❌ Error testing {channel}: {str(e)}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "="*50)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_enhanced_video_description()
    print("\n✅ Automated test completed!")
