#!/usr/bin/env python3
"""
Test the enhanced Facebook URL extraction
"""

from email_finder import extract_emails_and_socials

def test_facebook_extraction():
    """Test Facebook URL extraction with various formats"""
    
    test_cases = [
        {
            "name": "Facebook profile.php URL",
            "text": "Check out my Facebook https://www.facebook.com/profile.php?id=100088203832962 for updates!",
            "expected_facebook": "https://www.facebook.com/profile.php?id=100088203832962"
        },
        {
            "name": "Facebook username URL", 
            "text": "Follow me on https://www.facebook.com/johnsmith for updates",
            "expected_facebook": "https://www.facebook.com/johnsmith"
        },
        {
            "name": "Facebook redirect URL",
            "text": "redirect?q=https%3a%2f%2fwww.facebook.com%2fprofile.php%3fid%3d100088203832962&v=test",
            "expected_facebook": "https://www.facebook.com/profile.php?id=100088203832962"
        },
        {
            "name": "Partial Facebook URL",
            "text": "facebook.com/profile.php?id=123456789 is my page",
            "expected_facebook": "https://www.facebook.com/profile.php?id=123456789"
        }
    ]
    
    print("🔍 Testing Facebook URL Extraction")
    print("="*60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['text']}")
        
        emails, socials, usernames = extract_emails_and_socials(test_case['text'])
        
        facebook_links = socials.get('facebook', [])
        
        print(f"Facebook links found: {facebook_links}")
        
        if facebook_links:
            if test_case['expected_facebook'] in facebook_links[0]:
                print("✅ SUCCESS: Facebook URL extracted correctly")
            else:
                print("❌ FAILED: Facebook URL not extracted as expected")
                print(f"   Expected: {test_case['expected_facebook']}")
                print(f"   Got: {facebook_links[0]}")
        else:
            print("❌ FAILED: No Facebook links found")
        
        print("-" * 50)

if __name__ == "__main__":
    test_facebook_extraction()
    print("\n✅ Facebook extraction test completed!")
