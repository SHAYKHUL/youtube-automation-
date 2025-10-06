import csv
import time
import threading
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """Setup Chrome driver with optimized options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def get_subscriber_count(driver, channel_url):
    """Extract subscriber count from YouTube channel"""
    try:
        print(f"🔍 Getting subscriber count for: {channel_url}")
        driver.get(channel_url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)  # Additional wait for dynamic content
        
        # Try multiple strategies to find subscriber count
        strategies = [
            "//span[contains(text(), 'subscriber')]",
            "//*[contains(text(), 'subscriber')]",
            "//yt-formatted-string[contains(text(), 'subscriber')]",
            "//div[@id='subscriber-count']",
            "//span[@id='subscriber-count']"
        ]
        
        for strategy in strategies:
            try:
                elements = driver.find_elements(By.XPATH, strategy)
                for el in elements:
                    text = el.text.strip()
                    if 'subscriber' in text.lower():
                        # Extract number from text like "1.2K subscribers"
                        match = re.search(r'(\d+(?:\.\d+)?[KMB]?)\s*subscriber', text, re.IGNORECASE)
                        if match:
                            result = match.group(1)
                            print(f"✅ Found subscriber count: {result}")
                            return result
            except Exception:
                continue
        
        # Fallback: Get page source and search for subscriber info
        page_source = driver.page_source
        matches = re.findall(r'(\d+(?:\.\d+)?[KMB]?)\s*subscriber', page_source, re.IGNORECASE)
        if matches:
            result = matches[0]
            print(f"✅ Found subscriber count in source: {result}")
            return result
            
        print(f"❌ No subscriber count found for {channel_url}")
        return "N/A"
        
    except Exception as e:
        print(f"❌ Error getting subscriber count for {channel_url}: {e}")
        return "N/A"

def parse_subscriber_number(subs_text):
    """Convert subscriber text to number (e.g., '1.2K' -> 1200)"""
    if not subs_text or subs_text == 'N/A':
        return 0
    
    # Clean the text
    subs_text = subs_text.replace(',', '').strip()
    
    # Extract number and suffix
    match = re.search(r'(\d+(?:\.\d+)?)\s*([KMB]?)', subs_text, re.IGNORECASE)
    if not match:
        return 0
    
    try:
        num = float(match.group(1))
        suffix = match.group(2).upper()
        
        if suffix == 'K':
            num *= 1000
        elif suffix == 'M':
            num *= 1000000
        elif suffix == 'B':
            num *= 1000000000
            
        return int(num)
    except Exception:
        return 0

def test_sample_channels():
    """Test with first 3 channels from save.csv"""
    # Read first 3 channels from save.csv
    test_channels = []
    with open('save.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        count = 0
        for row in reader:
            if row and row[0].startswith('http'):
                test_channels.append(row[0])
                count += 1
                if count >= 3:  # Only test 3 channels
                    break
    
    print(f"🧪 Testing with {len(test_channels)} channels")
    
    # Create CSV files for results
    with open('test_below_1k.csv', 'w', encoding='utf-8', newline='') as f_below, \
         open('test_1k_10k.csv', 'w', encoding='utf-8', newline='') as f_between, \
         open('test_above_10k.csv', 'w', encoding='utf-8', newline='') as f_above:
        
        below_writer = csv.writer(f_below)
        between_writer = csv.writer(f_between)
        above_writer = csv.writer(f_above)
        
        # Write headers
        headers = ['Channel Link', 'Subscriber Text', 'Subscriber Count']
        below_writer.writerow(headers)
        between_writer.writerow(headers)
        above_writer.writerow(headers)
        
        driver = setup_driver()
        try:
            for i, channel_url in enumerate(test_channels):
                print(f"\n🔄 Processing {i+1}/{len(test_channels)}: {channel_url}")
                
                count_text = get_subscriber_count(driver, channel_url)
                count_num = parse_subscriber_number(count_text)
                
                # Categorize and save
                if count_num < 1000:
                    below_writer.writerow([channel_url, count_text, count_num])
                    f_below.flush()
                    print(f"📉 Below 1K: {count_text} ({count_num:,})")
                elif 1000 <= count_num <= 10000:
                    between_writer.writerow([channel_url, count_text, count_num])
                    f_between.flush()
                    print(f"📊 1K-10K: {count_text} ({count_num:,})")
                else:
                    above_writer.writerow([channel_url, count_text, count_num])
                    f_above.flush()
                    print(f"📈 Above 10K: {count_text} ({count_num:,})")
                    
        finally:
            driver.quit()
    
    print("\n✅ Test completed! Check test_*.csv files for results.")

if __name__ == "__main__":
    test_sample_channels()
