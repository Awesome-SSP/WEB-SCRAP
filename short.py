import os
import time
import hashlib
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Settings
CATALOG_URL = "  "
OUTPUT_DIR = "jewlerySet"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Browser setup
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print("🌍 Loading site...")
driver.get(CATALOG_URL)
time.sleep(10)

# Unique image tracking using hashes
unique_image_signatures = set()
image_elements_processed = set()
image_count = 0
stable_rounds = 0

print("🌀 Scrolling through content...")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    imgs = driver.find_elements(By.TAG_NAME, 'img')
    new_images_found = 0

    for img in imgs:
        src = img.get_attribute("src") or img.get_attribute("data-src")
        if not src or not any(domain in src for domain in ["cdnx.in", "clevup.in"]):
            continue

        element_id = img.id if hasattr(img, "id") else str(hash(img))
        if element_id in image_elements_processed:
            continue

        image_elements_processed.add(element_id)

        try:
            img_bytes = requests.get(src, timeout=15).content
            img_hash = hashlib.md5(img_bytes).hexdigest()

            if img_hash not in unique_image_signatures:
                unique_image_signatures.add(img_hash)
                ext = src.split('.')[-1].split("?")[0]
                if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = 'jpg'
                file_path = os.path.join(OUTPUT_DIR, f"image_{image_count+1}.{ext}")
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                print(f"✅ Saved image_{image_count+1}.{ext}")
                image_count += 1
                new_images_found += 1

        except Exception as e:
            print(f"❌ Error downloading {src}: {e}")

    if new_images_found == 0:
        stable_rounds += 1
        if stable_rounds > 5:
            print("🛑 No new unique images for several rounds. Ending.")
            break
    else:
        stable_rounds = 0

driver.quit()
print(f"\n🎉 Done. {image_count} unique images downloaded to '{OUTPUT_DIR}'.")
