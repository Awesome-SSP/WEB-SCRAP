import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===================== CONFIGURATION =====================
BASE_URL = "  "  # Replace with actual category/catalog URL
IMAGE_SELECTOR = "img"  # Update this if the images use a specific class like img.product-image
SAVE_DIR = "store_catalog_images"

# Create folder if not exists
os.makedirs(SAVE_DIR, exist_ok=True)

# Fetch HTML page
headers = {"User-Agent": "Mozilla/5.0"}  # Avoid basic bot detection
response = requests.get(BASE_URL, headers=headers)
if response.status_code != 200:
    print("Failed to load page:", response.status_code)
    exit()

# Parse HTML
soup = BeautifulSoup(response.text, "html.parser")
image_tags = soup.select(IMAGE_SELECTOR)

# Collect and download images
downloaded = 0
for img in image_tags:
    src = img.get("src") or img.get("data-src")
    if not src:
        continue

    # Handle relative URLs
    full_url = urljoin(BASE_URL, src)

    try:
        img_data = requests.get(full_url, headers=headers).content
        ext = full_url.split('.')[-1].split('?')[0]  # get extension, handle ?params
        filename = f"image_{downloaded}.{ext}"
        with open(os.path.join(SAVE_DIR, filename), 'wb') as f:
            f.write(img_data)
        print(f"Downloaded {filename}")
        downloaded += 1
    except Exception as e:
        print(f"Failed to download {full_url}: {e}")

print(f"\n✅ Finished. Total images downloaded: {downloaded}")
