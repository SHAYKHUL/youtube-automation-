"""
YouTube Email Discovery for Authenticated Channels
Reads channels from signin_to_see_email.csv and discovers emails after login
"""

import csv
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


class AuthenticatedEmailDiscovery:
    """Discovers emails from channels requiring authentication"""
    
    def __init__(self, manual_debug=True):
        """Initialize the email discovery"""
        self.manual_debug = manual_debug
        self.driver = None
        self.wait = None
        self.discovered_emails = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            print("🌐 Setting up Chrome browser...")
            
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--start-maximized")
            
            if self.manual_debug:
                chrome_options.add_experimental_option("detach", True)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            
            print("✅ Chrome browser initialized")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up browser: {e}")
            return False
    
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Add random human-like delays"""
        time.sleep(random.uniform(min_delay, max_delay))
    
    def human_like_typing(self, element, text, typing_delay=0.05):
        """Type text with human-like delays"""
        element.clear()
        time.sleep(0.2)  # Brief pause after clearing
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.02, typing_delay))  # Faster minimum delay
    
    def login_to_youtube(self, email, password):
        """Login to YouTube with robust error handling"""
        try:
            print(f"\n🔐 Logging into YouTube with: {email}")
            
            # Navigate to YouTube
            self.driver.get("https://www.youtube.com")
            self.human_like_delay(2, 4)
            
            # Click Sign In
            print("Clicking Sign In...")
            sign_in_selectors = [
                "//a[@aria-label='Sign in']",
                "//a[contains(text(), 'Sign in')]",
                "//yt-button-shape//a[contains(@href, 'accounts.google.com')]"
            ]
            
            for selector in sign_in_selectors:
                try:
                    sign_in_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    sign_in_btn.click()
                    break
                except:
                    continue
            
            self.human_like_delay(2, 4)
            
            # Enter email - try multiple selectors
            print("Entering email...")
            email_field = None
            email_selectors = [
                (By.ID, "identifierId"),
                (By.NAME, "identifier"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.XPATH, "//input[@type='email']")
            ]
            
            for selector_type, selector_value in email_selectors:
                try:
                    email_field = self.wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    print(f"✓ Found email field")
                    break
                except:
                    continue
            
            if not email_field:
                print("❌ Could not find email field")
                if self.manual_debug:
                    input("Please enter email manually and press Enter...")
                    self.human_like_delay(3, 5)
                else:
                    return False
            else:
                self.human_like_typing(email_field, email, 0.1)
                self.human_like_delay(1, 2)
                
                # Click next button
                try:
                    next_button = self.wait.until(EC.element_to_be_clickable((By.ID, "identifierNext")))
                    next_button.click()
                except:
                    email_field.send_keys(Keys.RETURN)
                
                self.human_like_delay(3, 5)
            
            # Enter password - try multiple selectors
            print("Entering password...")
            password_field = None
            password_selectors = [
                (By.NAME, "password"),
                (By.NAME, "Passwd"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@type='password']"),
                (By.ID, "password")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    print(f"✓ Found password field")
                    break
                except:
                    continue
            
            if not password_field:
                print("❌ Could not find password field")
                print(f"Current URL: {self.driver.current_url}")
                if self.manual_debug:
                    input("Please enter password manually and press Enter...")
                    self.human_like_delay(3, 5)
                else:
                    return False
            else:
                self.human_like_typing(password_field, password, 0.05)  # Faster typing
                self.human_like_delay(0.5, 1)  # Shorter delay
                
                # Click next button
                try:
                    next_button = self.wait.until(EC.element_to_be_clickable((By.ID, "passwordNext")))
                    next_button.click()
                except:
                    password_field.send_keys(Keys.RETURN)
                
                print("Waiting for login to complete...")
                self.human_like_delay(3, 5)  # Shorter wait
            
            # Check for login success
            if "youtube.com" in self.driver.current_url:
                print("✅ Login successful!")
                return True
            
            print("⚠️  Login status unclear")
            if self.manual_debug:
                input("Press Enter after completing login manually...")
            return True
            
        except Exception as e:
            print(f"❌ Error during login: {e}")
            print(f"Current URL: {self.driver.current_url if self.driver else 'N/A'}")
            if self.manual_debug:
                print("Please complete login manually")
                input("Press Enter after completing login...")
                return True
            return False
    
    def extract_email_from_about(self, channel_url):
        """Navigate to channel About page and extract email with CAPTCHA handling"""
        try:
            print(f"\n🔍 Visiting: {channel_url}")
            
            # Go to About page
            about_url = channel_url.rstrip('/') + '/about'
            self.driver.get(about_url)
            self.human_like_delay(3, 5)
            
            found_emails = []
            
            # Method 1: Click "View email address" button and handle CAPTCHA
            try:
                print("Looking for 'View email address' button...")
                
                # Try multiple selectors for the email button
                email_button_selectors = [
                    "//button[contains(@aria-label, 'View email address')]",
                    "//button[contains(., 'View email address')]",
                    "#view-email-button-container button",
                    "yt-button-view-model button"
                ]
                
                email_button = None
                for selector in email_button_selectors:
                    try:
                        if selector.startswith("//"):
                            email_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        else:
                            email_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        print(f"✓ Found email button")
                        break
                    except:
                        continue
                
                if email_button:
                    print("Clicking 'View email address' button...")
                    email_button.click()
                    self.human_like_delay(2, 3)
                    
                    # Check for reCAPTCHA checkbox
                    captcha_solved = False
                    try:
                        print("Checking for reCAPTCHA...")
                        # Wait for reCAPTCHA iframe
                        time.sleep(2)
                        # Switch to reCAPTCHA iframe
                        captcha_iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
                        self.driver.switch_to.frame(captcha_iframe)
                        # Click the checkbox
                        print("Clicking reCAPTCHA checkbox...")
                        checkbox = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".recaptcha-checkbox-border")))
                        checkbox.click()
                        # Wait for the checkmark to appear (CAPTCHA solved)
                        try:
                            self.wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".recaptcha-checkbox-checked"))
                            )
                            print("✅ reCAPTCHA checkmark detected! CAPTCHA solved.")
                            captcha_solved = True
                        except TimeoutException:
                            print("⚠️  reCAPTCHA checkmark not detected. Manual solve may be required.")
                            captcha_solved = False
                        # Switch back to main content
                        self.driver.switch_to.default_content()
                        # If not solved, check for challenge iframe (bframe = challenge with images)
                        if not captcha_solved:
                            try:
                                challenge_iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='bframe']")
                                if challenge_iframes and len(challenge_iframes) > 0 and challenge_iframes[0].is_displayed():
                                    print("⚠️  reCAPTCHA IMAGE CHALLENGE detected!")
                                    print("You need to solve the image challenge manually")
                                    if self.manual_debug:
                                        input("Please solve the CAPTCHA challenge and press Enter when done...")
                                        captcha_solved = True
                                else:
                                    print("✅ reCAPTCHA auto-solved (no visible challenge)!")
                                    captcha_solved = True
                            except:
                                print("✅ reCAPTCHA auto-solved!")
                                captcha_solved = True
                        
                    except Exception as e:
                        print(f"CAPTCHA handling: {e}")
                        # Assume no CAPTCHA or already handled
                        captcha_solved = True
                    
                    # Click Submit button after CAPTCHA
                    if captcha_solved:
                        try:
                            print("Looking for Submit button...")
                            time.sleep(2)
                            
                            submit_selectors = [
                                "#submit-btn",
                                "//button[contains(., 'Submit')]",
                                "//span[contains(text(), 'Submit')]/ancestor::button"
                            ]
                            
                            for selector in submit_selectors:
                                try:
                                    if selector.startswith("//"):
                                        submit_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                                    else:
                                        submit_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                                    print("✓ Found Submit button, clicking...")
                                    submit_btn.click()
                                    break
                                except:
                                    continue
                            
                            self.human_like_delay(2, 3)
                            
                        except Exception as e:
                            print(f"Submit button not found: {e}")
                    
                    # Extract email from the modal
                    try:
                        print("Extracting email from modal...")
                        
                        # Try direct email link selector
                        email_link = self.driver.find_element(By.CSS_SELECTOR, "a#email")
                        email_address = email_link.text.strip()
                        if email_address and '@' in email_address:
                            found_emails.append(email_address)
                            print(f"✅ Found email: {email_address}")
                        
                    except:
                        # Try alternative selectors
                        try:
                            email_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
                            for link in email_links:
                                email = link.text.strip() or link.get_attribute('href').replace('mailto:', '')
                                if email and '@' in email and email not in found_emails:
                                    found_emails.append(email)
                                    print(f"✅ Found email: {email}")
                        except:
                            pass
                    
                    # Also check page text for emails
                    try:
                        page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                        import re
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, page_text)
                        
                        for email in emails:
                            if (email not in found_emails and 
                                '@gmail.com' not in email.lower() and 
                                '@youtube.com' not in email.lower() and
                                '@google.com' not in email.lower()):
                                found_emails.append(email)
                                print(f"✅ Found email in text: {email}")
                    except:
                        pass
            
            except Exception as e:
                print(f"Method 1 failed: {e}")
            
            # Method 2: Check if email is already visible on page (no button needed)
            if not found_emails:
                try:
                    print("Checking for visible emails on page...")
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    import re
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, page_text)
                    
                    for email in emails:
                        if (email not in found_emails and 
                            '@gmail.com' not in email.lower() and 
                            '@youtube.com' not in email.lower() and
                            '@google.com' not in email.lower()):
                            found_emails.append(email)
                            print(f"✅ Found visible email: {email}")
                
                except Exception as e:
                    print(f"Method 2 failed: {e}")
            
            if not found_emails:
                print("❌ No email found")
            
            return found_emails
            
        except Exception as e:
            print(f"❌ Error extracting email: {e}")
            return []
    
    def check_for_captcha(self):
        """Check if CAPTCHA is present"""
        try:
            captcha_indicators = [
                "recaptcha",
                "captcha",
                "I'm not a robot"
            ]
            
            page_source = self.driver.page_source.lower()
            for indicator in captcha_indicators:
                if indicator in page_source:
                    return True
            return False
            
        except:
            return False
    
    def close(self):
        """Close browser"""
        try:
            if self.driver and not self.manual_debug:
                self.driver.quit()
                print("Browser closed")
        except Exception as e:
            print(f"Error closing browser: {e}")


def main():
    """Main function to discover emails from signin_to_see_email.csv"""
    print("="*70)
    print("YOUTUBE EMAIL DISCOVERY - Authenticated Channel Emails")
    print("="*70)
    print()
    
    # File paths - prefer local file first, then parent directory
    local_path = "signin_to_see_email.csv"
    parent_path = os.path.join("..", "signin_to_see_email.csv")
    gmail_csv = "gmail_accounts.csv"
    output_csv = "discovered_emails_authenticated.csv"

    # Prefer local file to avoid accidentally using a parent-directory file
    if os.path.exists(local_path):
        signin_csv = local_path
    elif os.path.exists(parent_path):
        signin_csv = parent_path
    else:
        print(f"❌ File not found: signin_to_see_email.csv")
        print(f"   Looking in: {os.path.abspath('.')} and parent: {os.path.abspath('..')}")
        return
    
    if not os.path.exists(gmail_csv):
        print(f"❌ Gmail accounts file not found: {gmail_csv}")
        print("Please create gmail_accounts.csv with columns: email,password")
        return
    
    # Read Gmail credentials from CSV
    print(f"📧 Reading Gmail credentials from: {gmail_csv}")
    gmail_email = None
    gmail_password = None
    
    try:
        with open(gmail_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('email') and row.get('password'):
                    gmail_email = row['email'].strip()
                    gmail_password = row['password'].strip()
                    print(f"✅ Using Gmail account: {gmail_email}")
                    break
    except Exception as e:
        print(f"❌ Error reading Gmail CSV: {e}")
        return
    
    if not gmail_email or not gmail_password:
        print("❌ No valid Gmail credentials found in gmail_accounts.csv")
        print("CSV format should be: email,password")
        return
    
    # Read channel links from signin_to_see_email.csv
    print(f"\n📋 Reading channels from: {signin_csv}")
    channels = []

    try:
        # First attempt: use DictReader and look for a 'Channel Link' column (common header)
        with open(signin_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Normalize fieldnames in case of BOM or trailing spaces
            if reader.fieldnames:
                normalized = [h.strip() if h else h for h in reader.fieldnames]
                # Map original to normalized
                field_map = {orig: norm for orig, norm in zip(reader.fieldnames, normalized)}
            else:
                field_map = {}

            for row in reader:
                # Try common header first
                # Use case-insensitive match for 'Channel Link'
                link = None
                for key in row.keys():
                    if key and key.strip().lower() == 'channel link':
                        link = row.get(key)
                        break
                if link and link.strip():
                    channels.append(link.strip())

        # Fallback: if nothing found, try plain reader and take first column values that look like URLs
        if not channels:
            with open(signin_csv, 'r', encoding='utf-8-sig') as f:
                plain = csv.reader(f)
                for r in plain:
                    if not r:
                        continue
                    first = r[0].strip()
                    if first.lower().startswith('http'):
                        channels.append(first)
    except Exception as e:
        print(f"❌ Error reading signin CSV: {e}")
        return
    
    if not channels:
        print("❌ No channel links found in signin_to_see_email.csv")
        return
    
    print(f"✅ Found {len(channels)} channel(s) to process")
    
    # Ask user confirmation
    print(f"\nWill process {len(channels)} channels using account: {gmail_email}")
    choice = input("Continue? (y/n): ").strip().lower()
    if choice != 'y':
        print("Cancelled")
        return
    
    # Initialize discoverer
    discoverer = AuthenticatedEmailDiscovery(manual_debug=True)
    
    if not discoverer.setup_driver():
        print("Failed to setup browser")
        return
    
    # Login to YouTube
    if not discoverer.login_to_youtube(gmail_email, gmail_password):
        print("Failed to login")
        discoverer.close()
        return
    
    # Process each channel
    results = []
    for i, channel_url in enumerate(channels, 1):
        print(f"\n{'='*70}")
        print(f"Channel {i}/{len(channels)}")
        print(f"{'='*70}")
        
        emails = discoverer.extract_email_from_about(channel_url)
        
        results.append({
            'channel_url': channel_url,
            'emails': emails,
            'status': 'Found' if emails else 'Not Found'
        })
        
        # Add delay between channels
        if i < len(channels):
            delay = random.uniform(3, 6)
            print(f"Waiting {delay:.1f}s before next channel...")
            time.sleep(delay)
    
    # Save results
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print(f"{'='*70}")
    
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Channel URL', 'Discovered Emails', 'Status'])
            
            for result in results:
                writer.writerow([
                    result['channel_url'],
                    '; '.join(result['emails']) if result['emails'] else '',
                    result['status']
                ])
        
        print(f"✅ Results saved to: {output_csv}")
        
        # Summary
        found_count = sum(1 for r in results if r['emails'])
        print(f"\n📊 Summary:")
        print(f"   Total channels: {len(results)}")
        print(f"   Emails found: {found_count}")
        print(f"   Not found: {len(results) - found_count}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    # Keep browser open in debug mode
    if discoverer.manual_debug:
        print("\n🔍 Manual debug mode: Browser will stay open")
        input("Press Enter to close browser...")
    
    discoverer.close()
    print("\n✅ Email discovery completed!")


if __name__ == "__main__":
    main()
