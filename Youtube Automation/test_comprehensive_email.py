#!/usr/bin/env python3
"""
Test comprehensive email detection scenarios
"""

from selenium import webdriver
from email_finder import check_more_info_section

def test_comprehensive_scenarios():
    """Test various email detection scenarios"""
    
    test_cases = [
        {
            "name": "Channel with visible business email",
            "channel": "https://www.youtube.com/@mkbhd",
            "expected": "visible_email"
        },
        {
            "name": "Large channel likely requiring sign-in", 
            "channel": "https://www.youtube.com/@tseries",
            "expected": "sign_in_required"
        },
        {
            "name": "Small tech channel",
            "channel": "https://www.youtube.com/@TechLinked", 
            "expected": "mixed"
        }
    ]
    
    print("📧 Comprehensive Email Detection Test")
    print("="*60)
    
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['name']}")
            print("-" * 50)
            print(f"Channel: {test_case['channel']}")
            
            # Clear cache between tests
            driver.delete_all_cookies()
            
            sign_in_required, more_info_text = check_more_info_section(driver, test_case['channel'])
            
            print(f"📊 Results:")
            print(f"   Sign-in required: {sign_in_required}")
            print(f"   Contact info found: {'Yes' if more_info_text else 'No'}")
            if more_info_text:
                print(f"   Details: {more_info_text[:100]}...")
            
            # Analysis
            if sign_in_required and not more_info_text:
                print("✅ RESULT: Sign-in required (no visible emails)")
            elif more_info_text and not sign_in_required:
                print("✅ RESULT: Visible contact information found")
            elif more_info_text and sign_in_required:
                print("✅ RESULT: Mixed - visible emails + additional sign-in required")
            else:
                print("❌ RESULT: No contact information available")
            
            print("="*60)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_comprehensive_scenarios()
    print("\n✅ Comprehensive test completed!")
