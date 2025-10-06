from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from email_finder import get_latest_video_description, extract_emails_and_socials
import time

def test_video_description_extraction():
    """Test video description extraction with a real channel"""
    print("🎥 Testing Video Description Extraction")
    print("=" * 50)
    
    # Setup Chrome with options for better stability
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    
    try:
        # Test with a channel URL (you can change this)
        test_channel = input("Enter a YouTube channel URL to test (or press Enter for default): ").strip()
        if not test_channel:
            test_channel = "https://www.youtube.com/@mkbhd"  # Default test channel
        
        print(f"🚀 Testing channel: {test_channel}")
        
        # Test the video description extraction
        description_text = get_latest_video_description(driver, test_channel)
        
        if description_text:
            print(f"\n📝 Extracted description:")
            print("-" * 40)
            print(description_text[:500] + "..." if len(description_text) > 500 else description_text)
            print("-" * 40)
            
            # Test email and social extraction
            emails, socials, usernames = extract_emails_and_socials(description_text)
            
            print(f"\n🔍 Extraction results:")
            print(f"📧 Emails found: {emails}")
            print(f"📱 Social media found: {socials}")
            print(f"👤 Usernames found: {usernames}")
            
            if emails or socials or usernames:
                print("✅ Contact information found in video description!")
            else:
                print("❌ No contact information found in video description")
        else:
            print("❌ No description text extracted")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        driver.quit()
        print("🔚 Test completed")

def test_multiple_channels():
    """Test video description extraction with multiple channels"""
    print("🎥 Testing Multiple Channels")
    print("=" * 40)
    
    # Setup Chrome
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    
    # Test channels (you can modify this list)
    test_channels = [
        "https://www.youtube.com/@mkbhd",
        "https://www.youtube.com/@veritasium", 
        "https://www.youtube.com/@3blue1brown"
    ]
    
    try:
        for i, channel in enumerate(test_channels, 1):
            print(f"\n🔍 Test {i}: {channel}")
            
            description_text = get_latest_video_description(driver, channel)
            
            if description_text:
                emails, socials, usernames = extract_emails_and_socials(description_text)
                
                print(f"📝 Description length: {len(description_text)} chars")
                print(f"📧 Emails: {len(emails)} found")
                print(f"📱 Social: {len(socials)} platforms found") 
                print(f"👤 Usernames: {len(usernames)} found")
                
                if emails:
                    print(f"   📧 {emails}")
                if socials:
                    print(f"   📱 {socials}")
                if usernames:
                    print(f"   👤 {usernames}")
            else:
                print("❌ No description extracted")
            
            time.sleep(2)  # Delay between channels
            
    except Exception as e:
        print(f"❌ Error during multi-channel test: {e}")
    finally:
        driver.quit()
        print("🔚 Multi-channel test completed")

def main():
    print("🧪 Video Description Extraction Test Suite")
    print("=" * 50)
    
    choice = input("Choose test:\n1. Single channel test\n2. Multiple channels test\nEnter choice (1 or 2): ")
    
    if choice == "1":
        test_video_description_extraction()
    elif choice == "2":
        test_multiple_channels()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
