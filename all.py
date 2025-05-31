import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ========== Configuration & Setup ==========
CATALOG_URL = ""                      #CATELOG URL
OUTPUT_DIR = "catalog_images"
URL_LIST_FILENAME = "image_urls_found.txt"

# Selenium options for headless Browse
options = Options()
options.add_argument("--headless") # Run browser in the background
options.add_argument("--no-sandbox") # Bypass OS security model, necessary in some environments
options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
options.add_argument("--window-size=1920,1080") # Set a larger window size to ensure elements are rendered
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") # Set a user-agent to mimic a real browser

# Dynamic scrolling parameters
INITIAL_WAIT_TIME = 15 # Increased initial wait for a very dynamic page to load fully
SCROLL_PAUSE_TIME = 5 # Increased pause after each scroll to ensure content loads
MAX_STABLE_CHECKS = 15 # Number of times height and unique image count must be stable before stopping

# Request headers for downloading images (to mimic a browser request)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
DOWNLOAD_TIMEOUT = 25 # Increased timeout in seconds for individual image downloads

# Specific CDN domains to target for image URLs
TARGET_CDN_DOMAINS = ["cdnx.in", "clevup.in"] # Based on image_urls_found.txt [cite: 1]

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== Initialize Selenium Driver ==========
print("🚀 Initializing Chrome driver...")
try:
    # Uses ChromeDriverManager to automatically handle chromedriver installation
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("✅ Driver initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing driver: {e}")
    print("Please ensure Google Chrome is installed and accessible, or try updating webdriver_manager (pip install --upgrade webdriver-manager).")
    exit() # Exit if the driver can't be initialized

# ========== Scraping Phase: Load All Images with Robust Scrolling ==========
print(f"🌐 Navigating to {CATALOG_URL}...")
driver.get(CATALOG_URL)
print(f"Waiting {INITIAL_WAIT_TIME} seconds for initial page content to load...")
time.sleep(INITIAL_WAIT_TIME)

# List to store ALL image URLs found (this list WILL contain duplicates if the same URL appears multiple times)
all_image_urls_for_download = []
# Set to track UNIQUE URLs found so far. This is crucial for the stopping condition logic
# to determine if truly new content (new unique images) is still being loaded by scrolling.
processed_unique_urls_set = set()

last_scroll_height = driver.execute_script("return document.body.scrollHeight")
last_total_unique_images_count = 0
stable_checks_count = 0

print("⏳ Initiating dynamic scrolling to load all content. This process may take some time...")

while True:
    # Scroll to the very bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME) # Give the page time to load new content after scrolling

    # Get the current complete page source HTML
    current_html = driver.page_source
    current_soup = BeautifulSoup(current_html, "html.parser")

    # --- Image Extraction Logic ---
    # We will prioritize images from the known CDN domains
    current_image_tags = [] 
    
    # Function to check if an image URL is from a target CDN
    def is_target_cdn_image(url):
        if not url:
            return False
        for domain in TARGET_CDN_DOMAINS:
            if domain in url:
                return True
        return False

    # Find <img> tags with src or data-src attributes containing target CDN domains
    current_image_tags.extend(current_soup.find_all("img", src=lambda src: src and is_target_cdn_image(src)))
    current_image_tags.extend(current_soup.find_all("img", attrs={"data-src": lambda data_src: data_src and is_target_cdn_image(data_src)}))
    
    # Additionally, include images with class="product-card-image" (if still relevant)
    # Filter to avoid duplicates if they were already added by CDN check
    product_card_images = current_soup.find_all("img", class_="product-card-image")
    for img_tag in product_card_images:
        src_val = img_tag.get('src') or img_tag.get('data-src')
        if src_val and is_target_cdn_image(src_val): # Only add if it's also from a target CDN
            current_image_tags.append(img_tag)

    # Filter out exact duplicate image tags found by different selectors in this *current* iteration
    unique_tags_this_scroll = []
    seen_tag_identifiers = set() 
    for tag in current_image_tags:
        tag_identifier = str(tag) 
        if tag_identifier not in seen_tag_identifiers:
            unique_tags_this_scroll.append(tag)
            seen_tag_identifiers.add(tag_identifier)
    
    current_unique_images_added = 0
    for img_tag in unique_tags_this_scroll:
        src = img_tag.get("src")
        data_src = img_tag.get("data-src") 

        image_url_to_extract = None
        if src and src.startswith("http"):
            image_url_to_extract = src
        elif data_src and data_src.startswith("http"):
            image_url_to_extract = data_src
        
        if image_url_to_extract:
            # Add the URL to our main list. This list collects ALL instances, allowing duplicates.
            all_image_urls_for_download.append(image_url_to_extract)

            # Check if this URL is NEW to our unique set (for the stopping condition)
            if image_url_to_extract not in processed_unique_urls_set:
                processed_unique_urls_set.add(image_url_to_extract)
                current_unique_images_added += 1

    # --- Stopping Condition Logic ---
    new_scroll_height = driver.execute_script("return document.body.scrollHeight")
    current_total_unique_images_count = len(processed_unique_urls_set)

    # Check if neither scroll height nor unique image count has changed significantly
    if new_scroll_height == last_scroll_height and current_total_unique_images_count == last_total_unique_images_count:
        stable_checks_count += 1
        print(f"Page height and unique image count stable. Consecutive stable checks: {stable_checks_count}/{MAX_STABLE_CHECKS}")
        if stable_checks_count >= MAX_STABLE_CHECKS:
            print("🛑 Stopping scroll: Page height and unique image count have been stable for multiple checks. Assuming all content is loaded.")
            break # Exit the scrolling loop
    else:
        stable_checks_count = 0 # Reset stable count if there's any change
        print(f"Progress: Height changed to {new_scroll_height}px, found {current_total_unique_images_count} unique images (added {current_unique_images_added} this scroll).")

    last_scroll_height = new_scroll_height
    last_total_unique_images_count = current_total_unique_images_count

# Close the Selenium browser
driver.quit()
print(f"\n🎉 Scraping complete. Collected {len(all_image_urls_for_download)} image URLs for download (this includes duplicates if found).")
print(f"A total of {len(processed_unique_urls_set)} unique image URLs were identified.")

# ========== Save All Collected URLs to a Text File ==========
url_list_path = os.path.join(OUTPUT_DIR, URL_LIST_FILENAME)
print(f"📝 Saving all collected URLs to '{url_list_path}'...")
try:
    with open(url_list_path, 'w', encoding='utf-8') as f:
        for url in all_image_urls_for_download:
            f.write(url + '\n')
    print("✅ URLs saved successfully.")
except Exception as e:
    print(f"❌ Error saving URLs to file: {e}")

# ========== Download Images from the Collected List ==========
print(f"\n⬇️ Starting image download to '{OUTPUT_DIR}'...")
downloaded_count = 0
for i, img_url in enumerate(all_image_urls_for_download): # Iterate through the list that contains all instances
    try:
        # Robust file extension extraction
        ext = 'jpg' # Default extension if none can be determined
        if '.' in img_url:
            # Split by '.', take last part, then split by '?' and '#' to remove query parameters/fragments
            potential_ext = img_url.split('.')[-1].split('?')[0].split('#')[0]
            # Basic validation: check length and if it's alphanumeric
            if 1 <= len(potential_ext) <= 4 and potential_ext.isalnum():
                ext = potential_ext.lower()
                # Optionally, map to common image types or default if non-standard
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico']:
                    ext = 'jpg' # Fallback for odd/unknown extensions

        # Create a unique filename for each downloaded image
        # Using 'i+1' to start numbering from 1 for better readability
        filename = f"product_{i+1}.{ext}" 
        file_path = os.path.join(OUTPUT_DIR, filename)

        # Download the image content using requests
        img_data = requests.get(img_url, headers=REQUEST_HEADERS, timeout=DOWNLOAD_TIMEOUT).content
        
        with open(file_path, 'wb') as f:
            f.write(img_data)
        print(f"✅ Downloaded: {filename}")
        downloaded_count += 1
    except requests.exceptions.RequestException as req_e:
        print(f"❌ Network error downloading {img_url}: {req_e}")
    except Exception as e:
        print(f"❌ Failed to download {img_url}: {e}")

print(f"\n✨ Total images downloaded: {downloaded_count} out of {len(all_image_urls_for_download)} URLs processed.")
print("Script execution completed.")