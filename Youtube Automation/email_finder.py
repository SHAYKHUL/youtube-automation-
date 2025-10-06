import csv
import re
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_emails_and_socials(text):
    """Enhanced extraction of emails and social media info"""
    import urllib.parse
    
    if not text:
        return [], {}, []
    
    # URL decode the text to handle encoded URLs in redirects
    try:
        decoded_text = urllib.parse.unquote(text)
        # Use both original and decoded text for better coverage
        text_to_search = text + " " + decoded_text
    except:
        text_to_search = text
    
    text_to_search = text_to_search.lower()
    
    # Enhanced email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text_to_search, re.IGNORECASE)
    
    # Enhanced social media patterns - capture full URLs
    social_patterns = {
        'facebook': [
            r'(https?://(?:www\.)?facebook\.com/[^\s\)\"&]+)',
            r'(https?://(?:www\.)?fb\.com/[^\s\)\"&]+)',
            r'facebook\.com/([A-Za-z0-9._/-]+(?:\?[^\s\)\"&]*)?)',
            r'fb\.com/([A-Za-z0-9._/-]+(?:\?[^\s\)\"&]*)?)',
            r'facebook:\s*([A-Za-z0-9._-]+)',
            r'fb:\s*([A-Za-z0-9._-]+)'
        ],
        'instagram': [
            r'(https?://(?:www\.)?instagram\.com/[^\s\)\"&]+)',
            r'(https?://(?:www\.)?instagr\.am/[^\s\)\"&]+)',
            r'instagram\.com/([A-Za-z0-9._-]+)',
            r'instagram:\s*@?([A-Za-z0-9._-]+)',
            r'ig:\s*@?([A-Za-z0-9._-]+)',
            r'insta:\s*@?([A-Za-z0-9._-]+)'
        ],
        'twitter': [
            r'(https?://(?:www\.)?twitter\.com/[^\s\)\"&]+)',
            r'(https?://(?:www\.)?x\.com/[^\s\)\"&]+)',
            r'twitter\.com/([A-Za-z0-9._-]+)',
            r'x\.com/([A-Za-z0-9._-]+)',
            r'twitter:\s*@?([A-Za-z0-9._-]+)',
            r'x:\s*@?([A-Za-z0-9._-]+)'
        ],
        'tiktok': [
            r'(https?://(?:www\.)?tiktok\.com/@[^\s\)\"&]+)',
            r'tiktok\.com/@([A-Za-z0-9._-]+)',
            r'tiktok:\s*@?([A-Za-z0-9._-]+)',
            r'tt:\s*@?([A-Za-z0-9._-]+)'
        ],
        'youtube': [
            r'(https?://(?:www\.)?youtube\.com/[^\s\)\"&]+)',
            r'youtube\.com/([A-Za-z0-9._-]+)',
            r'youtu\.be/([A-Za-z0-9._-]+)'
        ],
        'linkedin': [
            r'(https?://(?:www\.)?linkedin\.com/[^\s\)\"&]+)',
            r'linkedin\.com/([A-Za-z0-9._-]+)',
            r'linkedin:\s*([A-Za-z0-9._-]+)'
        ],
        'website': [
            r'https?://(?:www\.)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            r'www\.([A-Za-z0-9.-]+\.[A-Za-z]{2,})'
        ]
    }
    
    socials = {}
    all_usernames = []
    
    for platform, patterns in social_patterns.items():
        found_links = []
        for pattern in patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if match and len(match.strip()) > 1:
                    if platform == 'website':
                        if not any(social in match.lower() for social in ['facebook', 'instagram', 'twitter', 'tiktok', 'youtube', 'linkedin']):
                            found_links.append(f"https://{match}")
                    else:
                        # Handle full URLs vs partial paths
                        clean_match = match.strip()
                        if clean_match.startswith('http'):
                            # Already a full URL
                            found_links.append(clean_match)
                            # Extract username for @ collection
                            try:
                                username = clean_match.split('/')[-1].split('?')[0]
                                if username and not username.startswith('http'):
                                    all_usernames.append(f"@{username}")
                            except:
                                pass
                        else:
                            # Partial path - reconstruct full URL
                            if platform == 'facebook':
                                if clean_match.startswith('profile.php'):
                                    found_links.append(f"https://www.facebook.com/{clean_match}")
                                else:
                                    found_links.append(f"https://www.facebook.com/{clean_match}")
                            elif platform == 'instagram':
                                found_links.append(f"https://www.instagram.com/{clean_match}")
                            elif platform == 'twitter':
                                found_links.append(f"https://www.twitter.com/{clean_match}")
                            elif platform == 'tiktok':
                                if not clean_match.startswith('@'):
                                    clean_match = f"@{clean_match}"
                                found_links.append(f"https://www.tiktok.com/{clean_match}")
                            elif platform == 'linkedin':
                                found_links.append(f"https://www.linkedin.com/{clean_match}")
                            elif platform == 'youtube':
                                found_links.append(f"https://www.youtube.com/{clean_match}")
                            
                            # Collect usernames for @ extraction
                            username = clean_match.split('/')[0].split('?')[0]
                            if username and not username.startswith('http'):
                                all_usernames.append(f"@{username}")
        
        if found_links:
            socials[platform] = list(set(found_links))  # Remove duplicates
    
    # Extract additional @usernames that aren't part of URLs
    additional_usernames = re.findall(r'(?<![\w@])@([A-Za-z0-9_\.]+)', text_to_search)
    all_usernames.extend([f"@{u}" for u in additional_usernames if len(u) > 1])
    
    # Remove duplicates from usernames
    unique_usernames = list(set(all_usernames))
    
    return list(set(emails)), socials, unique_usernames

def merge_socials(target_socials, source_socials):
    """Merge social media dictionaries, combining lists for each platform"""
    for platform, links in source_socials.items():
        if platform in target_socials:
            target_socials[platform].extend(links)
            target_socials[platform] = list(set(target_socials[platform]))  # Remove duplicates
        else:
            target_socials[platform] = links.copy() if isinstance(links, list) else [links]

def get_about_section(driver, channel_url):
    """Enhanced About section extraction"""
    try:
        about_url = channel_url.rstrip('/') + '/about'
        driver.get(about_url)
        time.sleep(3)
        
        about_text = ""
        
        # Get channel description
        try:
            description_elements = driver.find_elements(By.XPATH, "//yt-formatted-string[@id='description']")
            for elem in description_elements:
                about_text += elem.text + " "
        except Exception:
            pass
        
        # Get details section
        try:
            details_elements = driver.find_elements(By.XPATH, "//div[@id='details']//yt-formatted-string")
            for elem in details_elements:
                about_text += elem.text + " "
        except Exception:
            pass
        
        # Get links section
        try:
            links_elements = driver.find_elements(By.XPATH, "//div[@id='links']//a")
            for elem in links_elements:
                href = elem.get_attribute('href')
                text = elem.text
                if href:
                    about_text += f"{text} {href} "
        except Exception:
            pass
        
        # Fallback to body text if specific elements not found
        if not about_text.strip():
            try:
                about_text = driver.find_element(By.TAG_NAME, 'body').text
            except Exception:
                about_text = ""
        
        return about_text
        
    except Exception as e:
        print(f"Error getting about section for {channel_url}: {e}")
        return ""

def check_more_info_section(driver, channel_url):
    """Enhanced check for additional contact info with improved sign-in detection"""
    try:
        # Should already be on about page
        if '/about' not in driver.current_url:
            about_url = channel_url.rstrip('/') + '/about'
            driver.get(about_url)
            time.sleep(3)
        
        sign_in_required = False
        more_info_text = ""
        
        # Method 1: Look for visible emails FIRST using regex
        try:
            # Get all text content from the about page
            about_text = driver.find_element(By.TAG_NAME, 'body').text
            
            # Extract emails using regex
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, about_text)
            
            if emails:
                for email in emails:
                    if email not in more_info_text:
                        print(f"✅ Found email in About section: {email}")
                        more_info_text += f"Email: {email} "
        except Exception:
            pass
        
        # Method 2: Check for "Sign in to see email address" text (can coexist with visible emails)
        try:
            sign_in_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Sign in to see email')]")
            if sign_in_elements:
                if not more_info_text:  # Only return sign-in required if NO emails found
                    print("🔐 Sign in required to see email address (no visible emails)")
                    sign_in_required = True
                    return True, ""
                else:
                    print("🔐 Sign in required for additional email (but visible emails found)")
        except Exception:
            pass
        
        # Method 3: Look for business contact information in description
        try:
            business_keywords = ['business@', 'contact@', 'info@', 'hello@', 'mail@']
            page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
            
            for keyword in business_keywords:
                if keyword in page_text:
                    # Extract the line containing the business email
                    lines = page_text.split('\n')
                    for line in lines:
                        if keyword in line.lower():
                            more_info_text += f"Business contact: {line.strip()} "
                            break
        except Exception:
            pass
        
        # Method 4: Check for social media links in about section
        try:
            social_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'instagram.com') or contains(@href, 'twitter.com') or contains(@href, 'facebook.com') or contains(@href, 'linkedin.com')]")
            for link in social_links[:3]:  # Limit to first 3
                href = link.get_attribute('href')
                if href and 'youtube.com' not in href:  # Exclude YouTube's own links
                    more_info_text += f"Social: {href} "
        except Exception:
            pass
        
        return sign_in_required, more_info_text
        
    except Exception as e:
        print(f"❌ Error checking more info section: {e}")
        return False, ""

def get_latest_video_description(driver, channel_url):
    """Enhanced video description extraction with better expand handling"""
    try:
        videos_url = channel_url.rstrip('/') + '/videos'
        driver.get(videos_url)
        time.sleep(3)
        
        # Try multiple selectors for the first video
        video_link = None
        xpaths = [
            "//a[contains(@href, '/watch?v=')]",  # Most reliable - any video link
            "//ytd-rich-grid-media//a[contains(@href, '/watch?v=')]",
            "//ytd-grid-video-renderer//a[contains(@href, '/watch?v=')]", 
            "//ytd-rich-item-renderer//a[contains(@href, '/watch?v=')]",
            "//ytd-video-renderer//a[contains(@href, '/watch?v=')]"
        ]
        
        for xp in xpaths:
            try:
                video_elements = driver.find_elements(By.XPATH, xp)
                if video_elements:
                    # Filter out shorts and get a regular video
                    for element in video_elements:
                        href = element.get_attribute('href')
                        if href and '/watch?v=' in href and '/shorts/' not in href:
                            video_link = href
                            print(f"🎥 Found video: {video_link}")
                            break
                    if video_link:
                        break
            except Exception:
                continue

        if not video_link:
            print("❌ No videos found on channel")
            return ''

        # Navigate to the video
        driver.get(video_link)
        time.sleep(4)
        
        # Scroll to description area
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(2)
        
        description_text = ''
        
        # Method 1: Try multiple expand button selectors
        expand_selectors = [
            "//tp-yt-paper-button[@id='expand']",
            "//button[@id='expand']", 
            "//yt-button-shape[@id='expand']",
            "//*[@id='expand']",
            "//button[contains(@aria-label, 'Show more') or contains(text(), 'Show more')]",
            "//tp-yt-paper-button[contains(@aria-label, 'Show more')]",
            "//button[contains(@class, 'expand')]"
        ]
        
        expanded = False
        for selector in expand_selectors:
            try:
                expand_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expand_btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", expand_btn)
                time.sleep(2)
                print("✅ Expanded description successfully")
                expanded = True
                break
            except Exception:
                continue
        
        if not expanded:
            print("⚠️ Could not find expand button, trying alternative methods")
        
        # Method 2: Try multiple description selectors
        description_selectors = [
            "//div[@id='description']//yt-formatted-string",
            "//div[@id='description']",
            "//ytd-video-secondary-info-renderer//yt-formatted-string[@id='content']",
            "//yt-formatted-string[@id='content']",
            "//div[@id='snippet']",
            "//ytd-expandable-video-description-body-renderer//yt-formatted-string",
            "//yt-formatted-string[contains(@class, 'content')]",
            "//div[contains(@class, 'description')]//yt-formatted-string"
        ]
        
        for selector in description_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 10:  # Filter out very short text
                            description_text += text + " "
                    if description_text.strip():
                        print(f"✅ Found description using selector: {selector}")
                        break
            except Exception as e:
                continue
        
        # Method 3: Look for links in description area
        if description_text:
            try:
                link_elements = driver.find_elements(By.XPATH, "//div[@id='description']//a")
                for link_elem in link_elements:
                    href = link_elem.get_attribute('href')
                    text = link_elem.text
                    if href:
                        description_text += f" {text} {href} "
            except Exception:
                pass
        
        # Method 4: Fallback to broader search if no description found
        if not description_text.strip():
            try:
                # Look in the entire video info area
                info_elements = driver.find_elements(By.XPATH, "//ytd-video-secondary-info-renderer//*[contains(text(), '@') or contains(text(), '.com') or contains(text(), 'http')]")
                for elem in info_elements:
                    text = elem.text.strip()
                    if text and ('mail' in text.lower() or '@' in text or '.com' in text or 'http' in text):
                        description_text += text + " "
            except Exception:
                pass
        
        # Method 5: Last resort - check comments area for pinned comment with contact info
        if not description_text.strip():
            try:
                driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(2)
                pinned_comment = driver.find_elements(By.XPATH, "//ytd-comment-thread-renderer[1]//yt-formatted-string[@id='content-text']")
                if pinned_comment:
                    comment_text = pinned_comment[0].text
                    if 'mail' in comment_text.lower() or '@' in comment_text or 'contact' in comment_text.lower():
                        description_text += comment_text + " "
                        print("✅ Found contact info in pinned comment")
            except Exception:
                pass
        
        if description_text.strip():
            print(f"📝 Description length: {len(description_text)} characters")
            return description_text.strip()
        else:
            print("❌ No description text found")
            return ''
            
    except Exception as e:
        print(f"❌ Error getting video description for {channel_url}: {e}")
        return ''

def main():
    input_csv = input("Enter the name of the CSV file to scan (e.g. below_1k.csv): ").strip()
    while True:
        try:
            num_windows = int(input("How many Chrome windows to open in parallel? (default 3, max 100): ") or 3)
            num_windows = max(1, min(100, num_windows))
            break
        except ValueError:
            print("Please enter a valid number.")

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        links = [row[0] for row in reader if row and row[0].startswith('http')]

    def chunkify(lst, n):
        return [lst[i::n] for i in range(n)]
    link_chunks = chunkify(links, num_windows)

    csv_lock = threading.Lock()

    def process_links(links_chunk, idx):
        driver = webdriver.Chrome()
        driver.maximize_window()
        with open('founded_email.csv', 'a', encoding='utf-8', newline='') as f_found, \
             open('not_email_but_social.csv', 'a', encoding='utf-8', newline='') as f_social, \
             open('non_founded_email.csv', 'a', encoding='utf-8', newline='') as f_non, \
             open('signin_to_see_email.csv', 'a', encoding='utf-8', newline='') as f_info:

            found_writer = csv.writer(f_found)
            social_writer = csv.writer(f_social)
            non_writer = csv.writer(f_non)
            info_writer = csv.writer(f_info)

            for link in links_chunk:
                print(f"[Thread {idx}] Scanning: {link}")
                
                all_emails = []
                all_socials = {}
                all_usernames = []
                
                # Step 1: Video Description
                desc_text = get_latest_video_description(driver, link)
                video_emails, video_socials, video_usernames = extract_emails_and_socials(desc_text)
                
                if video_emails:
                    print(f"✅ Email found in video description: {video_emails}")
                    all_emails.extend(video_emails)
                    merge_socials(all_socials, video_socials)
                    all_usernames.extend(video_usernames)
                    
                    # Even if email found, check About for more social info
                    about_text = get_about_section(driver, link)
                    _, about_socials, about_usernames = extract_emails_and_socials(about_text)
                    merge_socials(all_socials, about_socials)
                    all_usernames.extend(about_usernames)
                    
                    save_founded(found_writer, link, all_emails, all_socials, all_usernames, csv_lock, f_found)
                    continue
                
                # If only social found in video description, continue to About
                if video_socials or video_usernames:
                    print(f"📱 Social media found in video description, checking About section")
                    merge_socials(all_socials, video_socials)
                    all_usernames.extend(video_usernames)
                
                # Step 2: About Section
                about_text = get_about_section(driver, link)
                about_emails, about_socials, about_usernames = extract_emails_and_socials(about_text)
                merge_socials(all_socials, about_socials)
                all_usernames.extend(about_usernames)
                
                if about_emails:
                    print(f"✅ Email found in About section: {about_emails}")
                    all_emails.extend(about_emails)
                    save_founded(found_writer, link, all_emails, all_socials, all_usernames, csv_lock, f_found)
                    continue
                
                # Step 3: More Info Section
                sign_in_required, more_info_text = check_more_info_section(driver, link)
                
                if sign_in_required:
                    # Check if we have any social media collected from video descriptions or about sections
                    has_social = any([
                        all_socials.get('facebook'),
                        all_socials.get('instagram'),
                        all_socials.get('twitter'),
                        all_socials.get('tiktok'),
                        all_socials.get('youtube'),
                        all_socials.get('linkedin'),
                        all_socials.get('website'),
                        all_usernames
                    ])
                    
                    if has_social:
                        print("🔐 Sign in required but social media found - saving to signin_to_see_email.csv with social info")
                        # Save to signin_to_see_email.csv with social media info
                        with csv_lock:
                            # Format: Channel Link, Facebook, Instagram, Twitter, TikTok, YouTube, LinkedIn, Website, @Usernames
                            row = [
                                link,
                                '; '.join(all_socials.get('facebook', [])),
                                '; '.join(all_socials.get('instagram', [])),
                                '; '.join(all_socials.get('twitter', [])),
                                '; '.join(all_socials.get('tiktok', [])),
                                '; '.join(all_socials.get('youtube', [])),
                                '; '.join(all_socials.get('linkedin', [])),
                                '; '.join(all_socials.get('website', [])),
                                '; '.join(all_usernames)
                            ]
                            info_writer.writerow(row)
                            f_info.flush()
                        continue
                    else:
                        print("🔐 Sign in required - no social media found - saving to signin_to_see_email.csv")
                        with csv_lock:
                            info_writer.writerow([link])
                            f_info.flush()
                        continue
                
                # Check if more info contains emails or additional social
                if more_info_text:
                    more_emails, more_socials, more_usernames = extract_emails_and_socials(more_info_text)
                    if more_emails:
                        print(f"✅ Email found in More Info section: {more_emails}")
                        all_emails.extend(more_emails)
                        merge_socials(all_socials, more_socials)
                        all_usernames.extend(more_usernames)
                        save_founded(found_writer, link, all_emails, all_socials, all_usernames, csv_lock, f_found)
                        continue
                    else:
                        merge_socials(all_socials, more_socials)
                        all_usernames.extend(more_usernames)
                
                # Step 4: Final Decision
                has_social = any([
                    all_socials.get('facebook'),
                    all_socials.get('instagram'),
                    all_socials.get('twitter'),
                    all_socials.get('tiktok'),
                    all_socials.get('youtube'),
                    all_socials.get('linkedin'),
                    all_socials.get('website'),
                    all_usernames
                ])
                
                if has_social:
                    print("📱 Only social media found - saving to not_email_but_social.csv")
                    save_social(social_writer, link, all_socials, all_usernames, csv_lock, f_social)
                else:
                    print("❌ Nothing found - saving to non_founded_email.csv")
                    with csv_lock:
                        non_writer.writerow([link])
                        f_non.flush()
        driver.quit()

    # Helpers
    def save_founded(writer, link, emails, socials, at_usernames, lock, file_obj):
        """Save channel with email found to founded_email.csv"""
        with lock:
            writer.writerow([
                link,
                '; '.join(emails),
                '; '.join(socials.get('facebook', [])),
                '; '.join(socials.get('instagram', [])),
                '; '.join(socials.get('twitter', [])),
                '; '.join(socials.get('tiktok', [])),
                '; '.join(socials.get('youtube', [])),
                '; '.join(socials.get('linkedin', [])),
                '; '.join(socials.get('website', [])),
                '; '.join(list(set(at_usernames)))  # Remove duplicates
            ])
            file_obj.flush()

    def save_social(writer, link, socials, at_usernames, lock, file_obj):
        """Save channel with only social media to not_email_but_social.csv"""
        with lock:
            writer.writerow([
                link,
                '; '.join(socials.get('facebook', [])),
                '; '.join(socials.get('instagram', [])),
                '; '.join(socials.get('twitter', [])),
                '; '.join(socials.get('tiktok', [])),
                '; '.join(socials.get('youtube', [])),
                '; '.join(socials.get('linkedin', [])),
                '; '.join(socials.get('website', [])),
                '; '.join(list(set(at_usernames)))  # Remove duplicates
            ])
            file_obj.flush()

    # Write headers once
    with open('founded_email.csv', 'w', encoding='utf-8', newline='') as f_found, \
         open('not_email_but_social.csv', 'w', encoding='utf-8', newline='') as f_social, \
         open('non_founded_email.csv', 'w', encoding='utf-8', newline='') as f_non, \
         open('signin_to_see_email.csv', 'w', encoding='utf-8', newline='') as f_info:

        found_writer = csv.writer(f_found)
        social_writer = csv.writer(f_social)
        non_writer = csv.writer(f_non)
        info_writer = csv.writer(f_info)

        found_writer.writerow(['Channel Link', 'Email(s)', 'Facebook', 'Instagram', 'Twitter', 'TikTok', 'YouTube', 'LinkedIn', 'Website', '@Usernames'])
        social_writer.writerow(['Channel Link', 'Facebook', 'Instagram', 'Twitter', 'TikTok', 'YouTube', 'LinkedIn', 'Website', '@Usernames'])
        non_writer.writerow(['Channel Link'])
        info_writer.writerow(['Channel Link', 'Facebook', 'Instagram', 'Twitter', 'TikTok', 'YouTube', 'LinkedIn', 'Website', '@Usernames'])

    # Start threads
    threads = []
    for i, chunk in enumerate(link_chunks):
        t = threading.Thread(target=process_links, args=(chunk, i+1))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    print("✅ Done! Results saved to:")
    print("📧 founded_email.csv - Channels with emails found")
    print("📱 not_email_but_social.csv - Channels with only social media")
    print("❌ non_founded_email.csv - Channels with nothing found")
    print("🔐 signin_to_see_email.csv - Channels requiring sign-in")

if __name__ == "__main__":
    main()