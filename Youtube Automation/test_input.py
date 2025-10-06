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

# Read channel links from save.csv for testing
channel_links = []
print("📊 Reading channel links from save.csv...")
try:
    with open('save.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        count = 0
        for row in reader:
            if row and row[0].startswith('http'):
                channel_links.append(row[0])
                count += 1
                if count >= 6:  # Only take first 6 for testing
                    break
    print(f"✅ Found {len(channel_links)} channels for testing")
except Exception as e:
    print(f"❌ Error reading save.csv: {e}")
    exit(1)

def main():
    """Test the input functionality"""
    print(f"🎯 Testing custom window input with {len(channel_links)} channels")
    
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
    print(f"📊 Will process {len(channel_links)} channels")
    
    # Calculate chunks
    chunk_size = max(1, (len(channel_links) + num_windows - 1) // num_windows)
    print(f"📦 Each window will process approximately {chunk_size} channels")
    
    for i in range(num_windows):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(channel_links))
        chunk = channel_links[start_idx:end_idx]
        if chunk:
            print(f"🔄 Window {i+1}: {len(chunk)} channels (indices {start_idx}-{end_idx-1})")
    
    print("✅ Input test completed successfully!")

if __name__ == "__main__":
    main()
