import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ========== SETUP SELENIUM WITH HEADLESS CHROME ==========
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Correct way to use ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# ========== LOAD PAGE ==========
url = "  "
driver.get(url)
time.sleep(5)  # wait for JavaScript to load content

# ========== PARSE HTML ==========
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
driver.quit()

# ========== EXTRACT IMAGES ==========
save_dir = "chokerset_images"
os.makedirs(save_dir, exist_ok=True)

image_tags = soup.find_all("img")
image_urls = set()

for img in image_tags:
    src = img.get("src")
    if src and src.startswith("http"):
        image_urls.add(src)

print(f"🔍 Found {len(image_urls)} image URLs.")

# ========== DOWNLOAD IMAGES ==========
headers = {"User-Agent": "Mozilla/5.0"}

for i, img_url in enumerate(image_urls):
    try:
        ext = img_url.split('.')[-1].split('?')[0]
        filename = f"product_{i}.{ext}"
        img_data = requests.get(img_url, headers=headers).content
        with open(os.path.join(save_dir, filename), 'wb') as f:
            f.write(img_data)
        print(f"✅ Downloaded: {filename}")
    except Exception as e:
        print(f"❌ Failed to download {img_url}: {e}")

print(f"\n🎉 Total images downloaded: {len(image_urls)}")
