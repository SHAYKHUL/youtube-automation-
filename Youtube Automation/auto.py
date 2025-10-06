from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import pandas as pd
import openpyxl # For creating Excel files
import os

def setup_driver():
    """Sets up and returns a Chrome WebDriver instance."""
    # If chromedriver is not in your PATH, specify the path here:
    # service = Service('/path/to/chromedriver')
    # driver = webdriver.Chrome(service=service)
    driver = webdriver.Chrome()
    driver.maximize_window()
    return driver

def go_to_youtube(driver):
    """Navigates to YouTube.com."""
    driver.get("https://www.youtube.com")
    print("Navigated to YouTube.com")
    time.sleep(3) # Give time for the page to load

def search_topic(driver, topic):
    """Searches for a given topic on YouTube."""
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "search_query"))
        )
        search_box.send_keys(topic)
        search_box.send_keys(Keys.RETURN)
        print(f"Searched for: {topic}")
        time.sleep(5) # Give time for search results to load
    except Exception as e:
        print(f"Error searching for topic: {e}")

def apply_advanced_filters(driver, filters):
    """
    Applies a list of filters (in order) to the YouTube search results page.
    Each filter is a string, e.g., 'Today', 'Video', '4K', 'Upload date', 'View count', 'HD', 'Under 4 minutes', '4-20 minutes', 'Over 20 minutes'.
    """
    try:
        # Scroll to top to avoid sticky header covering the filter button
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        # Try to close overlays/popups if present
        try:
            # Close sign-in popup if present
            signin_close = driver.find_elements(By.XPATH, "//yt-icon-button[@id='close-button']")
            if signin_close:
                signin_close[0].click()
                time.sleep(1)
        except Exception:
            pass
        try:
            # Close cookie consent if present
            cookie_button = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept all') or contains(text(), 'I agree') or contains(text(), 'Accept')]" )
            if cookie_button:
                cookie_button[0].click()
                time.sleep(1)
        except Exception:
            pass

        # Click the Filters button
        filter_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "filter-button"))
        )
        filter_button.click()
        time.sleep(2)

        for f in filters:
            # Try to find the filter option by its text
            try:
                option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//yt-formatted-string[contains(text(), '{f}') or contains(text(), '{f.lower()}') or contains(text(), '{f.upper()}') or contains(text(), '{f.title()}')]"))
                )
                option.click()
                time.sleep(2)
            except Exception as e:
                print(f"Could not apply filter '{f}': {e}")
        print(f"Applied filters: {filters}")
        time.sleep(5) # Wait for filtered results to load
    except Exception as e:
        print(f"Error applying filters: {e}")

def scroll_down_for_videos(driver, num_scrolls=5):
    """Scrolls down the page to load more videos."""
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    for _ in range(num_scrolls):
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(3) # Give time for new content to load
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    print(f"Scrolled down {_+1} times to load more videos.")

def scroll_down_to_end(driver, max_waits=10):
    """Scrolls down the page until no more new videos are loaded or max_waits is reached."""
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    wait_count = 0
    # For live saving
    seen_channel_links_live = set()
    # Write header to save.csv at the start
    with open("save.csv", "w", encoding="utf-8") as f:
        f.write("Channel Link\n")
    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(3)
        # Extract and save new links after each scroll
        video_details = get_video_details(driver)
        for item in video_details:
            link = item.get("Channel Link", "N/A")
            views = item.get("Views", 0)
            if (
                0 <= views < 10000
                and link != "N/A"
                and ("/channel/" in link or "/@" in link)
                and link not in seen_channel_links_live
            ):
                with open("save.csv", "a", encoding="utf-8") as f:
                    f.write(link + "\n")
                seen_channel_links_live.add(link)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            wait_count += 1
            if wait_count >= max_waits:
                break
        else:
            wait_count = 0
        last_height = new_height
    print("Scrolled to end of results and live-saved channel links.")

def get_video_details(driver):
    """
    Extracts video details including title, video link, views, and channel link.
    Attempts to get subscriber count if readily available on the search page.
    """
    video_elements = driver.find_elements(By.TAG_NAME, "ytd-video-renderer")
    print(f"Found {len(video_elements)} video elements on the page.")
    channel_data = []

    for idx, video in enumerate(video_elements):
        try:
            # Video Title and Link
            title_element = video.find_element(By.ID, "video-title")
            video_title = title_element.text
            video_link = title_element.get_attribute("href")

            # Views
            views_element = video.find_element(By.XPATH, ".//div[@id='metadata-line']/span[1]")
            views_text = views_element.text
            views = 0
            if "views" in views_text:
                views_str = views_text.replace(" views", "").replace(",", "")
                if 'K' in views_str:
                    views = int(float(views_str.replace('K', '')) * 1000)
                elif 'M' in views_str:
                    views = int(float(views_str.replace('M', '')) * 1000000)
                else:
                    views = int(views_str)


            # Advanced channel link extraction
            channel_name = "N/A"
            channel_link = "N/A"
            possible_selectors = [
                ".//ytd-channel-name//a",
                ".//a[@class='yt-simple-endpoint style-scope yt-formatted-string']",
                ".//a[contains(@href, '/channel/') or contains(@href, '/@')]"
            ]
            for selector in possible_selectors:
                try:
                    el = video.find_element(By.XPATH, selector)
                    link = el.get_attribute("href")
                    name = el.text
                    # Validate link is a channel
                    if link and ("/channel/" in link or "/@" in link):
                        channel_link = link
                        channel_name = name
                        break
                except Exception:
                    continue
            # Fallback: regex search in video card HTML
            if channel_link == "N/A":
                try:
                    html = video.get_attribute("outerHTML")
                    import re
                    match = re.search(r'href=\"(https://www.youtube.com/(channel/|@)[^\"]+)', html)
                    if match:
                        channel_link = match.group(1)
                        # Try to extract channel name from HTML (not always possible)
                        name_match = re.search(r'title=\"([^"]+)\"', html)
                        channel_name = name_match.group(1) if name_match else "N/A"
                except Exception:
                    pass
            # (Optional, slowest fallback: visit video page)
            # if channel_link == "N/A":
            #     try:
            #         driver.execute_script("window.open('');")
            #         driver.switch_to.window(driver.window_handles[-1])
            #         driver.get(video_link)
            #         time.sleep(3)
            #         ch_el = driver.find_element(By.XPATH, "//ytd-channel-name//a")
            #         channel_link = ch_el.get_attribute("href")
            #         channel_name = ch_el.text
            #         driver.close()
            #         driver.switch_to.window(driver.window_handles[0])
            #     except Exception:
            #         pass
            if channel_link == "N/A":
                print(f"[Warning] Could not extract channel link for video: {video_title}")

            # Subscriber Count (often not directly visible on search results, might require navigating)
            subscriber_count = "N/A"
            try:
                sub_count_element = video.find_element(By.XPATH, ".//yt-formatted-string[@id='subscriber-count']")
                sub_count_text = sub_count_element.text
                if "subscribers" in sub_count_text:
                    sub_count_str = sub_count_text.replace(" subscribers", "").replace(",", "")
                    if 'K' in sub_count_str:
                        subscriber_count = int(float(sub_count_str.replace('K', '')) * 1000)
                    elif 'M' in sub_count_str:
                        subscriber_count = int(float(sub_count_str.replace('M', '')) * 1000000)
                    else:
                        subscriber_count = int(sub_count_str)
            except:
                pass

            channel_data.append({
                "Video Title": video_title,
                "Video Link": video_link,
                "Views": views,
                "Channel Name": channel_name,
                "Channel Link": channel_link,
                "Subscriber Count": subscriber_count
            })

            if idx < 3:
                print(f"Sample extracted: {channel_data[-1]}")

        except Exception as e:
            print(f"Could not extract all details for a video: {e}")
            continue
    return channel_data

def filter_and_collect(data, filter_desc, seen_channel_links):
    """
    Filters the collected data for low views and low subscribers,
    and returns a list of channel dicts with an added filter description.
    """
    filtered_channels = []
    for item in data:
        views = item.get("Views")
        sub_count = item.get("Subscriber Count")
        channel_link = item.get("Channel Link")
        if views is not None and views < 1000:
            if sub_count != "N/A":
                if sub_count < 1000:
                    if channel_link not in seen_channel_links:
                        filtered_channels.append({
                            "Video Title": item["Video Title"],
                            "Video Link": item["Video Link"],
                            "Views": item["Views"],
                            "Channel Name": item["Channel Name"],
                            "Channel Link": item["Channel Link"],
                            "Subscriber Count": item["Subscriber Count"],
                            "Filter Combination": filter_desc
                        })
                        seen_channel_links.add(channel_link)
            else:
                if channel_link not in seen_channel_links:
                    filtered_channels.append({
                        "Video Title": item["Video Title"],
                        "Video Link": item["Video Link"],
                        "Views": item["Views"],
                        "Channel Name": item["Channel Name"],
                        "Channel Link": item["Channel Link"],
                        "Subscriber Count": item["Subscriber Count"],
                        "Filter Combination": filter_desc
                    })
                    seen_channel_links.add(channel_link)
    return filtered_channels

if __name__ == "__main__":
    search_topic_query = input("Enter the topic you want to search on YouTube: ")

    # Define all filter combinations as lists of filter names
    filter_combinations = [
        # Today
        ["Today", "Video", "Upload date"],
        ["Today", "Video", "4K", "Upload date"],
        ["Today", "Video", "4K", "View count"],
        ["Today", "Video", "View count"],
        ["Today", "Video", "HD", "View count"],
        ["Today", "Video", "HD", "Upload date"],

        ["Today", "Video", "Under 4 minutes", "Upload date"],
        ["Today", "Video", "Under 4 minutes", "4K", "View count"],
        ["Today", "Video", "Under 4 minutes", "4K", "Upload date"],
        ["Today", "Video", "Under 4 minutes", "View count"],
        ["Today", "Video", "Under 4 minutes", "HD", "View count"],
        ["Today", "Video", "Under 4 minutes", "HD", "Upload date"],

        ["Today", "Video", "4-20 minutes", "Upload date"],
        ["Today", "Video", "4-20 minutes", "4K", "View count"],
        ["Today", "Video", "4-20 minutes", "4K", "Upload date"],
        ["Today", "Video", "4-20 minutes", "View count"],
        ["Today", "Video", "4-20 minutes", "HD", "View count"],
        ["Today", "Video", "4-20 minutes", "HD", "Upload date"],

        ["Today", "Video", "Over 20 minutes", "Upload date"],
        ["Today", "Video", "Over 20 minutes", "4K", "View count"],
        ["Today", "Video", "Over 20 minutes", "4K", "Upload date"],
        ["Today", "Video", "Over 20 minutes", "View count"],
        ["Today", "Video", "Over 20 minutes", "HD", "View count"],
        ["Today", "Video", "Over 20 minutes", "HD", "Upload date"],

        # This week
        ["This week", "Video", "Upload date"],
        ["This week", "Video", "4K", "Upload date"],
        ["This week", "Video", "4K", "View count"],
        ["This week", "Video", "View count"],
        ["This week", "Video", "HD", "Upload date"],
        ["This week", "Video", "HD", "View count"],

        ["This week", "Video", "Under 4 minutes", "Upload date"],
        ["This week", "Video", "Under 4 minutes", "4K", "View count"],
        ["This week", "Video", "Under 4 minutes", "4K", "Upload date"],
        ["This week", "Video", "Under 4 minutes", "View count"],
        ["This week", "Video", "Under 4 minutes", "HD", "View count"],
        ["This week", "Video", "Under 4 minutes", "HD", "Upload date"],

        ["This week", "Video", "4-20 minutes", "Upload date"],
        ["This week", "Video", "4-20 minutes", "4K", "View count"],
        ["This week", "Video", "4-20 minutes", "4K", "Upload date"],
        ["This week", "Video", "4-20 minutes", "View count"],
        ["This week", "Video", "4-20 minutes", "HD", "View count"],
        ["This week", "Video", "4-20 minutes", "HD", "Upload date"],

        ["This week", "Video", "Over 20 minutes", "Upload date"],
        ["This week", "Video", "Over 20 minutes", "4K", "View count"],
        ["This week", "Video", "Over 20 minutes", "4K", "Upload date"],
        ["This week", "Video", "Over 20 minutes", "View count"],
        ["This week", "Video", "Over 20 minutes", "HD", "View count"],
        ["This week", "Video", "Over 20 minutes", "HD", "Upload date"],

        # This month
        ["This month", "Video", "Upload date"],
        ["This month", "Video", "4K", "Upload date"],
        ["This month", "Video", "4K", "View count"],
        ["This month", "Video", "View count"],
        ["This month", "Video", "HD", "Upload date"],
        ["This month", "Video", "HD", "View count"],

        ["This month", "Video", "Under 4 minutes", "Upload date"],
        ["This month", "Video", "Under 4 minutes", "4K", "View count"],
        ["This month", "Video", "Under 4 minutes", "4K", "Upload date"],
        ["This month", "Video", "Under 4 minutes", "View count"],
        ["This month", "Video", "Under 4 minutes", "HD", "View count"],
        ["This month", "Video", "Under 4 minutes", "HD", "Upload date"],

        ["This month", "Video", "4-20 minutes", "Upload date"],
        ["This month", "Video", "4-20 minutes", "4K", "View count"],
        ["This month", "Video", "4-20 minutes", "4K", "Upload date"],
        ["This month", "Video", "4-20 minutes", "View count"],
        ["This month", "Video", "4-20 minutes", "HD", "View count"],
        ["This month", "Video", "4-20 minutes", "HD", "Upload date"],

        ["This month", "Video", "Over 20 minutes", "Upload date"],
        ["This month", "Video", "Over 20 minutes", "4K", "View count"],
        ["This month", "Video", "Over 20 minutes", "4K", "Upload date"],
        ["This month", "Video", "Over 20 minutes", "View count"],
        ["This month", "Video", "Over 20 minutes", "HD", "View count"],
        ["This month", "Video", "Over 20 minutes", "HD", "Upload date"],

        # This Year
        ["This year", "Video", "Upload date"],
        ["This year", "Video", "4K", "Upload date"],
        ["This year", "Video", "4K", "View count"],
        ["This year", "Video", "View count"],
        ["This year", "Video", "HD", "Upload date"],
        ["This year", "Video", "HD", "View count"],

        ["This year", "Video", "Under 4 minutes", "Upload date"],
        ["This year", "Video", "Under 4 minutes", "4K", "View count"],
        ["This year", "Video", "Under 4 minutes", "4K", "Upload date"],
        ["This year", "Video", "Under 4 minutes", "View count"],
        ["This year", "Video", "Under 4 minutes", "HD", "View count"],
        ["This year", "Video", "Under 4 minutes", "HD", "Upload date"],

        ["This year", "Video", "4-20 minutes", "Upload date"],
        ["This year", "Video", "4-20 minutes", "4K", "View count"],
        ["This year", "Video", "4-20 minutes", "4K", "Upload date"],
        ["This year", "Video", "4-20 minutes", "View count"],
        ["This year", "Video", "4-20 minutes", "HD", "View count"],
        ["This year", "Video", "4-20 minutes", "HD", "Upload date"],

        ["This year", "Video", "Over 20 minutes", "Upload date"],
        ["This year", "Video", "Over 20 minutes", "4K", "View count"],
        ["This year", "Video", "Over 20 minutes", "4K", "Upload date"],
        ["This year", "Video", "Over 20 minutes", "View count"],
        ["This year", "Video", "Over 20 minutes", "HD", "View count"],
        ["This year", "Video", "Over 20 minutes", "HD", "Upload date"],
    ]

    all_results = []
    seen_channel_links = set()

    driver = setup_driver()
    try:
        go_to_youtube(driver)
        search_topic(driver, search_topic_query)
        for filters in filter_combinations:
            # Refresh search page for each filter set
            driver.refresh()
            time.sleep(3)
            apply_advanced_filters(driver, filters)
            scroll_down_to_end(driver)
            # No need to collect all_results for CSV, as links are saved live


        # Always write headers, even if no results
        df = pd.DataFrame(all_results)
        csv_path = "save.csv"
        df.to_csv(csv_path, index=False)
        if all_results:
            print(f"\nSuccessfully saved {len(all_results)} low view/subscriber channels to {csv_path}")
        else:
            print("\nNo channels found matching the low view/subscriber criteria. CSV file created with headers only.")

        # Save only unique, valid channel links and names for videos with <1000 views
        channel_links = {}
        for item in all_results:
            link = item.get("Channel Link", "N/A")
            name = item.get("Channel Name", "N/A")
            # If name is empty or only whitespace, set to 'N/A'
            if not name or not name.strip():
                name = "N/A"
            if (
                item.get("Views", 0) < 1000
                and link != "N/A"
                and ("/channel/" in link or "/@" in link)
            ):
                channel_links[link] = name
        with open("channel_links.csv", "w", encoding="utf-8") as f:
            for link in sorted(channel_links.keys()):
                f.write(link + "\n")
        print(f"Saved {len(channel_links)} unique channel links (<1000 views) to channel_links.csv")

    except Exception as e:
        print(f"An error occurred during the automation process: {e}")
    finally:
        if driver:
            driver.quit()
            print("Browser closed.")
