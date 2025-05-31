# THis scarp alll the images based on the scrool and timing
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

# ========== SETUP SELENIUM WITH HEADLESS CHROME ==========
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") # Add a user-agent

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# ========== LOAD PAGE AND SCROLL TO LOAD ALL CONTENT ==========
url = "https://pinakitraditional.store.shoopy.in/categories/100-store-285319"
driver.get(url)

# Give initial content time to load
time.sleep(5)

# Scroll down repeatedly until no new content loads
last_height = driver.execute_script("return document.body.scrollHeight")
scroll_pause_time = 2 # Time to wait after each scroll
scroll_attempts = 0
max_stable_scroll_attempts = 150 # Number of times height must be stable before stopping

print("Initiating scrolling to load all content...")
while True:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(scroll_pause_time)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    
    if new_height == last_height:
        scroll_attempts += 1
        print(f"Page height stable. Attempt {scroll_attempts}/{max_stable_scroll_attempts}")
        if scroll_attempts >= max_stable_scroll_attempts:
            print("Page height has been stable for multiple attempts. Assuming all content loaded or no more content to load.")
            break
    else:
        scroll_attempts = 0 # Reset attempts if new content was loaded
        print(f"Scrolled to {new_height}px. More content loaded.")

    last_height = new_height

# After scrolling, give a final general wait for any last-minute JavaScript rendering
time.sleep(5)

# ========== PARSE HTML ==========
print("Parsing HTML...")
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
driver.quit()

# ========== EXTRACT IMAGES ==========
save_dir = "catalog_images"
os.makedirs(save_dir, exist_ok=True)

image_urls = set()

# Look for image tags with 'src' or 'data-src' attributes
# Inspect the website's HTML to see if images use data-src for lazy loading
product_images = soup.find_all("img", class_="product-card-image") # Adjust class name if needed
if not product_images: # Fallback if specific class not found
    product_images = soup.find_all("img")

for img in product_images:
    src = img.get("src")
    data_src = img.get("data-src") # Check for data-src attribute

    if src and src.startswith("http"):
        image_urls.add(src)
    elif data_src and data_src.startswith("http"):
        image_urls.add(data_src)

print(f"🔍 Found {len(image_urls)} unique image URLs.")

# ========== DOWNLOAD IMAGES ==========
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"} # Use the same user-agent for requests

downloaded_count = 0
for i, img_url in enumerate(list(image_urls)): # Convert set to list for consistent indexing
    try:
        # Extract extension robustly
        ext = 'jpg' # Default extension
        if '.' in img_url:
            potential_ext = img_url.split('.')[-1].split('?')[0].split('#')[0]
            if len(potential_ext) <= 4 and potential_ext.isalnum(): # Basic check for valid extension
                ext = potential_ext

        filename = f"product_{i+1}.{ext}" # Start naming from 1 for better readability
        
        img_data = requests.get(img_url, headers=headers, timeout=10).content # Add timeout
        with open(os.path.join(save_dir, filename), 'wb') as f:
            f.write(img_data)
        print(f"✅ Downloaded: {filename}")
        downloaded_count += 1
    except requests.exceptions.RequestException as req_e:
        print(f"❌ Network error downloading {img_url}: {req_e}")
    except Exception as e:
        print(f"❌ Failed to download {img_url}: {e}")

print(f"\n🎉 Total images downloaded: {downloaded_count} out of {len(image_urls)} found.")