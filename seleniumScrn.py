import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# === Setup ===
URL = " "
OUTPUT_DIR = "earingsss"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup headless browser
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,3000")  # Large height to cover more of the page
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open the page and wait for it to fully load
driver.get(URL)
time.sleep(20)  # Long wait to let everything load

# Scroll to the very bottom
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(20)

# Grab all image tags (no filtering)
img_tags = driver.find_elements(By.TAG_NAME, "img")
print(f"🖼️ Found {len(img_tags)} <img> tags.")

# Download all of them, even if they are duplicates
count = 0
for idx, tag in enumerate(img_tags, 1):
    src = tag.get_attribute("src") or tag.get_attribute("data-src")
    if src and src.startswith("http"):
        try:
            ext = src.split('.')[-1].split("?")[0]
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            img_data = requests.get(src, timeout=15).content
            file_path = os.path.join(OUTPUT_DIR, f"img_{idx}.{ext}")
            with open(file_path, 'wb') as f:
                f.write(img_data)
            print(f"✅ Saved img_{idx}.{ext}")
            count += 1
        except Exception as e:
            print(f"❌ Failed to download image #{idx}: {e}")

driver.quit()
print(f"\n🎉 Downloaded {count} images to '{OUTPUT_DIR}'.")
