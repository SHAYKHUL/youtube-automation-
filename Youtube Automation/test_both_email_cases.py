#!/usr/bin/env python3
"""
Test both cases: sign-in required vs visible email
"""

from selenium import webdriver
from email_finder import check_more_info_section

def test_both_cases():
    """Test channels with visible emails vs sign-in required"""
    
    print("📧 Testing Both Email Cases")
    print("="*50)
    
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        # Test 1: Channel with visible email
        print("\n🔍 Test 1: Channel with visible email")
        print("-" * 40)
        channel = "https://www.youtube.com/@mkbhd"
        
        sign_in_required, more_info_text = check_more_info_section(driver, channel)
        
        if sign_in_required:
            print("❌ ERROR: Sign-in detected when email should be visible")
        else:
            print("✅ SUCCESS: No sign-in required")
            if more_info_text:
                print(f"📧 Contact info found: {more_info_text}")
            else:
                print("❌ No contact info extracted")
        
        # Test 2: Channel requiring sign-in (use a different large channel)
        print("\n🔍 Test 2: Channel requiring sign-in")
        print("-" * 40)
        
        # Clear browser cache to avoid cached content
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        
        channel = "https://www.youtube.com/@PewDiePie"
        
        sign_in_required, more_info_text = check_more_info_section(driver, channel)
        
        if sign_in_required:
            print("✅ SUCCESS: Sign-in requirement correctly detected")
        else:
            print("❌ ERROR: Sign-in requirement not detected")
            if more_info_text:
                print(f"📧 Contact info found: {more_info_text}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_both_cases()
    print("\n✅ Both cases test completed!")
