
# delete all odd iamegs numbered in the folder
import os
import re

# === Change this to your image folder path ===
FOLDER_PATH = "C:\\Users\\Desktop\\earings"

# Supported extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

# Regex to extract number from filenames like "img_1.jpg", "image_3.webp"
pattern = re.compile(r'(\d+)')

deleted_count = 0

for filename in os.listdir(FOLDER_PATH):
    file_path = os.path.join(FOLDER_PATH, filename)
    
    # Check if it's an image file
    if os.path.isfile(file_path) and os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS:
        match = pattern.search(filename)
        if match:
            number = int(match.group(1))
            if number % 2 == 1:  # odd number
                try:
                    os.remove(file_path)
                    print(f"🗑️ Deleted: {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Could not delete {filename}: {e}")

print(f"\n✅ Done. Deleted {deleted_count} odd-numbered image(s) from '{FOLDER_PATH}'.")
