#!/usr/bin/env python3
"""
Test the enhanced 'Sign in to see email' detection
"""

from selenium import webdriver
from email_finder import check_more_info_section

def test_sign_in_detection():
    """Test channels that require sign-in to see email"""
    
    # Test channels that likely require sign-in for email
    test_channels = [
        "https://www.youtube.com/@MrBeast",
        "https://www.youtube.com/@PewDiePie",
        "https://www.youtube.com/@tseries",
        "https://www.youtube.com/@YouTubeCreators"
    ]
    
    print("🔐 Testing Sign-in Required Detection")
    print("="*50)
    
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        for i, channel in enumerate(test_channels, 1):
            print(f"\n🔍 Testing Channel {i}: {channel}")
            print("-" * 40)
            
            try:
                # Check more info section for sign-in requirement
                sign_in_required, more_info_text = check_more_info_section(driver, channel)
                
                if sign_in_required:
                    print("✅ DETECTED: Sign in required to see email")
                else:
                    print("❌ No sign-in requirement detected")
                    if more_info_text:
                        print(f"📝 More info found: {more_info_text[:200]}...")
                    else:
                        print("📝 No additional info found")
                        
            except Exception as e:
                print(f"❌ Error testing {channel}: {str(e)}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "="*50)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_sign_in_detection()
    print("\n✅ Sign-in detection test completed!")
