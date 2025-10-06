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

# Read all channel links from save.csv (skip header, only valid links)
channel_links = []
print("📊 Reading channel links from save.csv...")
try:
    with open('save.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].startswith('http'):
                channel_links.append(row[0])
    print(f"✅ Found {len(channel_links)} valid channel links")
except Exception as e:
    print(f"❌ Error reading save.csv: {e}")
    exit(1)

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

def worker(links, below_writer, between_writer, above_writer, below_lock, between_lock, above_lock, f_below, f_between, f_above, worker_id):
    """Worker function for processing channel links"""
    print(f"🚀 Worker {worker_id} starting with {len(links)} channels")
    driver = setup_driver()
    
    try:
        for i, link in enumerate(links):
            try:
                print(f"🔄 Worker {worker_id} processing {i+1}/{len(links)}: {link}")
                count_text = get_subscriber_count(driver, link)
                count_num = parse_subscriber_number(count_text)
                
                # Categorize and save
                if count_num < 1000:
                    with below_lock:
                        below_writer.writerow([link, count_text, count_num])
                        f_below.flush()
                    print(f"📉 Below 1K: {link} | {count_text}")
                elif 1000 <= count_num <= 10000:
                    with between_lock:
                        between_writer.writerow([link, count_text, count_num])
                        f_between.flush()
                    print(f"📊 1K-10K: {link} | {count_text}")
                else:
                    with above_lock:
                        above_writer.writerow([link, count_text, count_num])
                        f_above.flush()
                    print(f"📈 Above 10K: {link} | {count_text}")
                    
            except Exception as e:
                print(f"❌ Error processing {link}: {e}")
                with above_lock:
                    above_writer.writerow([link, 'ERROR', 0])
                    f_above.flush()
                    
    finally:
        driver.quit()
        print(f"✅ Worker {worker_id} completed")

def main():
    """Main function to process all channel links"""
    print(f"🎯 Starting subscriber count extraction for {len(channel_links)} channels")
    
    # Ask user for number of windows/threads
    try:
        user_input = input("How many Chrome windows do you want to open? (default 3, max 20): ").strip()
        if user_input == "":
            num_windows = 3  # Default value
        else:
            num_windows = int(user_input)
            if num_windows < 1:
                print("❌ Number must be at least 1. Using default 3.")
                num_windows = 3
            elif num_windows > 20:
                print("❌ Maximum 20 windows allowed for system stability. Using 20.")
                num_windows = 20
    except ValueError:
        print("❌ Invalid input. Using default 3 windows.")
        num_windows = 3
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        return
    except Exception as e:
        print(f"❌ Error with input: {e}. Using default 3 windows.")
        num_windows = 3

    print(f"🚀 Using {num_windows} Chrome windows")
    
    # Split channel_links into chunks
    chunk_size = max(1, (len(channel_links) + num_windows - 1) // num_windows)
    threads = []
    
    # Thread locks for file writing
    below_lock = threading.Lock()
    between_lock = threading.Lock()
    above_lock = threading.Lock()
    
    # Open CSV files for writing
    print("📝 Creating output CSV files...")
    with open('below_1k.csv', 'w', encoding='utf-8', newline='') as f_below, \
         open('1k_10k.csv', 'w', encoding='utf-8', newline='') as f_between, \
         open('above_10k.csv', 'w', encoding='utf-8', newline='') as f_above:
        
        below_writer = csv.writer(f_below)
        between_writer = csv.writer(f_between)
        above_writer = csv.writer(f_above)
        
        # Write headers
        headers = ['Channel Link', 'Subscriber Text', 'Subscriber Count']
        below_writer.writerow(headers)
        between_writer.writerow(headers)
        above_writer.writerow(headers)
        
        # Start threads
        for i in range(num_windows):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(channel_links))
            chunk = channel_links[start_idx:end_idx]
            
            if chunk:
                print(f"🔄 Starting worker {i+1} with {len(chunk)} channels (indices {start_idx}-{end_idx-1})")
                t = threading.Thread(
                    target=worker, 
                    args=(chunk, below_writer, between_writer, above_writer, 
                          below_lock, between_lock, above_lock, 
                          f_below, f_between, f_above, i+1)
                )
                t.start()
                threads.append(t)
        
        # Wait for all threads to complete
        print("⏳ Waiting for all workers to complete...")
        for i, t in enumerate(threads):
            t.join()
            print(f"✅ Worker {i+1} finished")
    
    print("🎉 Done! All subscriber counts saved to:")
    print("   📉 below_1k.csv - Channels with < 1,000 subscribers")
    print("   📊 1k_10k.csv - Channels with 1,000-10,000 subscribers") 
    print("   📈 above_10k.csv - Channels with > 10,000 subscribers")

if __name__ == "__main__":
    main()