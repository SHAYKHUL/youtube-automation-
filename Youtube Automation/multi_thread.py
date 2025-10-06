import threading
from auto import setup_driver, go_to_youtube, search_topic, apply_advanced_filters, get_video_details
import time

# Move views range input to the very top so it is always asked first
if __name__ == "__main__":
    # Ask user for custom views range with a clear prompt
    while True:
        views_range = input("Views range? (e.g. 0-10000, try 0-50000 for better results): ").strip()
        try:
            min_views, max_views = map(int, views_range.split('-'))
            if min_views < 0 or max_views <= min_views:
                raise ValueError
            break
        except Exception:
            print("Invalid input. Please enter a valid range like 0-10000, where min < max.")
else:
    min_views, max_views = 0, 10000  # Increased default range

# List your search topics here

# Prompt user for up to 100 search topics (one per line, empty line to finish)

# Prompt for number of windows (default 3)
try:
    num_windows = input("How many Chrome windows do you want to open? (default 3): ")
    num_windows = int(num_windows) if num_windows.strip() else 3
    if num_windows < 1 or num_windows > 100:
        print("Please enter a number between 1 and 100.")
        exit(1)
except Exception:
    num_windows = 3

# Prompt for that many search topics
print(f"Enter {num_windows} search topics, one per line:")
search_topics = []
while len(search_topics) < num_windows:
    topic = input()
    if not topic.strip():
        print(f"You must enter {num_windows} topics. Please continue:")
        continue
    search_topics.append(topic.strip())


# Define a smaller set of effective filter combinations for better results
    filter_combinations = [
        # Today - most likely to have low-view videos
        ["Today", "Video"],
        ["Today", "Video", "Upload date"],
        ["Today", "Video", "Under 4 minutes"],
        
        # This week - good for finding newer content
        ["This week", "Video"],
        ["This week", "Video", "Upload date"],
        ["This week", "Video", "Under 4 minutes"],
        
        # This month - balance of recency and availability
        ["This month", "Video"],
        ["This month", "Video", "Upload date"],
        ["This month", "Video", "Under 4 minutes"],
        
        # No time filter - gets all videos
        ["Video", "Upload date"],
        ["Video", "Under 4 minutes"],
    ]


# Global lock for file writing
file_lock = threading.Lock()
# Set to True after header is written
header_written = threading.Event()

# Initialize the CSV file with header at the start
def initialize_csv_file():
    with file_lock:
        try:
            with open("save.csv", "w", encoding="utf-8") as f:
                f.write("Channel Link\n")
                f.flush()  # Force write to disk
            header_written.set()
            print("CSV file initialized with header")
        except Exception as e:
            print(f"Error initializing CSV file: {e}")

def scrape_topic(search_topic_query):
    from auto import scroll_down_to_end  # Import here to avoid circular import
    driver = setup_driver()
    try:
        print(f"Starting scraping for topic: {search_topic_query}")
        go_to_youtube(driver)
        search_topic(driver, search_topic_query)
        
        for filter_idx, filters in enumerate(filter_combinations):
            print(f"Applying filter {filter_idx + 1}/{len(filter_combinations)}: {filters} for topic: {search_topic_query}")
            driver.refresh()
            time.sleep(1)
            apply_advanced_filters(driver, filters)
            # Instead of scroll_down_to_end, do live saving here
            last_height = driver.execute_script("return document.documentElement.scrollHeight")
            wait_count = 0
            seen_channel_links_live = set()
            scroll_count = 0
            
            while True:
                scroll_count += 1
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(1)
                
                print(f"Scroll {scroll_count} for filter {filter_idx + 1} - Topic: {search_topic_query}")
                video_details = get_video_details(driver)
                print(f"Found {len(video_details)} video details")
                
                links_found_this_scroll = 0
                for item in video_details:
                    link = item.get("Channel Link", "N/A")
                    views = item.get("Views", 0)
                    
                    print(f"Checking video: Views={views}, Link={link[:50]}...")
                    
                    # When scraping, use min_views and max_views for filtering
                    if (
                        min_views <= views < max_views
                        and link != "N/A"
                        and ("/channel/" in link or "/@" in link)
                        and link not in seen_channel_links_live
                    ):
                        with file_lock:
                            try:
                                with open("save.csv", "a", encoding="utf-8") as f:
                                    f.write(link + "\n")
                                    f.flush()  # Force immediate write to disk
                                print(f"✅ SAVED: {link} (Views: {views}) - Topic: {search_topic_query}")
                                links_found_this_scroll += 1
                            except Exception as e:
                                print(f"❌ Error writing to CSV: {e}")
                        seen_channel_links_live.add(link)
                    else:
                        # Debug why link wasn't saved
                        if link == "N/A":
                            print(f"❌ Skipped: No channel link found")
                        elif not (min_views <= views < max_views):
                            print(f"❌ Skipped: Views {views} not in range {min_views}-{max_views}")
                        elif not ("/channel/" in link or "/@" in link):
                            print(f"❌ Skipped: Invalid channel link format")
                        elif link in seen_channel_links_live:
                            print(f"❌ Skipped: Already seen this channel")
                
                print(f"Links saved this scroll: {links_found_this_scroll}")
                
                new_height = driver.execute_script("return document.documentElement.scrollHeight")
                if new_height == last_height:
                    wait_count += 1
                    print(f"No new content loaded, wait count: {wait_count}/10")
                    if wait_count >= 10:
                        break
                else:
                    wait_count = 0
                last_height = new_height
    except Exception as e:
        print(f"Error in thread for topic '{search_topic_query}': {e}")
    finally:
        driver.quit()
        print(f"Browser closed for topic: {search_topic_query}")

threads = []

# Initialize CSV file before starting threads
initialize_csv_file()
print(f"Using views range: {min_views} - {max_views}")
print(f"Number of topics to search: {len(search_topics)}")
print(f"Topics: {search_topics}")

# Always launch threads for each topic
import itertools
# Launch one window per topic, up to 100
for topic in search_topics:
    t = threading.Thread(target=scrape_topic, args=(topic,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("All threads completed.")
