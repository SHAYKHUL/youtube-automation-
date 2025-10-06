#!/usr/bin/env python3
"""
Test reprocessing a signin_to_see_email channel with enhanced functionality
"""

import csv
from selenium import webdriver
from email_finder import get_latest_video_description, get_about_section, extract_emails_and_socials, check_more_info_section

def reprocess_signin_channel():
    """Reprocess a channel from signin_to_see_email.csv with enhanced functionality"""
    
    test_channel = "https://www.youtube.com/@amyslittleadventures3207"
    
    print("🔄 Reprocessing Channel with Enhanced Logic")
    print("="*60)
    print(f"Channel: {test_channel}")
    
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        all_emails = []
        all_socials = {}
        all_usernames = []
        
        def merge_socials(target, source):
            for platform, links in source.items():
                if platform not in target:
                    target[platform] = []
                target[platform].extend(links)
        
        # Step 1: Video Description
        print("\n📹 Step 1: Video Description")
        desc_text = get_latest_video_description(driver, test_channel)
        if desc_text:
            video_emails, video_socials, video_usernames = extract_emails_and_socials(desc_text)
            
            if video_emails:
                print(f"✅ Email found in video description: {video_emails}")
                all_emails.extend(video_emails)
            
            merge_socials(all_socials, video_socials)
            all_usernames.extend(video_usernames)
            
            print(f"📱 Video social media found:")
            for platform, links in video_socials.items():
                if links:
                    print(f"   {platform}: {len(links)} links")
        
        # Step 2: About Section
        print("\n📄 Step 2: About Section")
        about_text = get_about_section(driver, test_channel)
        if about_text:
            about_emails, about_socials, about_usernames = extract_emails_and_socials(about_text)
            
            if about_emails:
                print(f"✅ Email found in About section: {about_emails}")
                all_emails.extend(about_emails)
            
            merge_socials(all_socials, about_socials)
            all_usernames.extend(about_usernames)
            
            print(f"📱 About social media found:")
            for platform, links in about_socials.items():
                if links:
                    print(f"   {platform}: {len(links)} links")
        
        # Step 3: More Info Section (only if no emails found)
        if not all_emails:
            print("\n🔐 Step 3: More Info Section")
            sign_in_required, more_info_text = check_more_info_section(driver, test_channel)
            
            if sign_in_required:
                # Check if we have any social media collected
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
                
                if has_social:
                    print("🔐 Sign in required but social media found - SAVING TO signin_to_see_email.csv with social info")
                    
                    # Create the row as it would be saved
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
                    
                    # Actually save to a test file
                    with open('test_signin_enhanced.csv', 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Channel Link', 'Facebook', 'Instagram', 'Twitter', 'TikTok', 'YouTube', 'LinkedIn', 'Website', '@Usernames'])
                        writer.writerow(row)
                    
                    print("✅ Saved enhanced result to test_signin_enhanced.csv")
                    print(f"📊 Summary:")
                    print(f"   Facebook: {len(all_socials.get('facebook', []))}")
                    print(f"   Instagram: {len(all_socials.get('instagram', []))}")
                    print(f"   Twitter: {len(all_socials.get('twitter', []))}")
                    print(f"   TikTok: {len(all_socials.get('tiktok', []))}")
                    print(f"   YouTube: {len(all_socials.get('youtube', []))}")
                    print(f"   LinkedIn: {len(all_socials.get('linkedin', []))}")
                    print(f"   Website: {len(all_socials.get('website', []))}")
                    print(f"   @Usernames: {len(all_usernames)}")
                    
                else:
                    print("🔐 Sign in required - no social media found")
            else:
                print("❌ No sign-in requirement detected")
        else:
            print(f"\n✅ Emails found: {all_emails} - would save to founded_email.csv")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    reprocess_signin_channel()
    print("\n✅ Reprocessing completed!")
