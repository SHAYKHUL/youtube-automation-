#!/usr/bin/env python3
"""
Test the enhanced signin_to_see_email.csv functionality with social media
"""

from selenium import webdriver
from email_finder import get_latest_video_description, get_about_section, extract_emails_and_socials, check_more_info_section

def test_signin_with_social():
    """Test channels that require sign-in but have social media"""
    
    # Test a channel that likely has "sign in to see email" but also social media
    test_channel = "https://www.youtube.com/@amyslittleadventures3207"  # From the signin_to_see_email.csv
    
    print("🔐 Testing Sign-in + Social Media Logic")
    print("="*60)
    
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        print(f"Testing: {test_channel}")
        print("-" * 50)
        
        all_emails = []
        all_socials = {}
        all_usernames = []
        
        # Step 1: Video Description
        print("📹 Step 1: Video Description")
        desc_text = get_latest_video_description(driver, test_channel)
        if desc_text:
            video_emails, video_socials, video_usernames = extract_emails_and_socials(desc_text)
            print(f"   Video emails: {len(video_emails)}")
            print(f"   Video social platforms: {list(video_socials.keys())}")
            print(f"   Video usernames: {len(video_usernames)}")
            
            # Merge socials function
            def merge_socials(target, source):
                for platform, links in source.items():
                    if platform not in target:
                        target[platform] = []
                    target[platform].extend(links)
            
            merge_socials(all_socials, video_socials)
            all_usernames.extend(video_usernames)
        
        # Step 2: About Section  
        print("📄 Step 2: About Section")
        about_text = get_about_section(driver, test_channel)
        if about_text:
            about_emails, about_socials, about_usernames = extract_emails_and_socials(about_text)
            print(f"   About emails: {len(about_emails)}")
            print(f"   About social platforms: {list(about_socials.keys())}")
            print(f"   About usernames: {len(about_usernames)}")
            
            def merge_socials(target, source):
                for platform, links in source.items():
                    if platform not in target:
                        target[platform] = []
                    target[platform].extend(links)
            
            merge_socials(all_socials, about_socials)
            all_usernames.extend(about_usernames)
        
        # Step 3: More Info Section
        print("🔐 Step 3: More Info Section")
        sign_in_required, more_info_text = check_more_info_section(driver, test_channel)
        print(f"   Sign-in required: {sign_in_required}")
        print(f"   More info text length: {len(more_info_text) if more_info_text else 0}")
        
        # Check final social media status
        has_social = any([
            all_socials.get('facebook'),
            all_socials.get('instagram'), 
            all_socials.get('twitter'),
            all_socials.get('tiktok'),
            all_socials.get('youtube'),
            all_socials.get('linkedin'),
            all_socials.get('website'),
            all_usernames
        ])
        
        print("\n📊 FINAL ANALYSIS:")
        print(f"   Sign-in required: {sign_in_required}")
        print(f"   Has social media: {has_social}")
        print(f"   Social platforms found: {list(all_socials.keys())}")
        print(f"   Total usernames: {len(all_usernames)}")
        
        # Simulate the new logic
        if sign_in_required and has_social:
            print("\n✅ RESULT: Would save to signin_to_see_email.csv WITH social media info")
            print("Row would be:")
            row = [
                test_channel,
                '; '.join(all_socials.get('facebook', [])),
                '; '.join(all_socials.get('instagram', [])),
                '; '.join(all_socials.get('twitter', [])),
                '; '.join(all_socials.get('tiktok', [])),
                '; '.join(all_socials.get('youtube', [])),
                '; '.join(all_socials.get('linkedin', [])),
                '; '.join(all_socials.get('website', [])),
                '; '.join(all_usernames)
            ]
            print(f"   {row}")
        elif sign_in_required:
            print("\n✅ RESULT: Would save to signin_to_see_email.csv WITHOUT social media")
        else:
            print("\n✅ RESULT: No sign-in required")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_signin_with_social()
    print("\n✅ Test completed!")
