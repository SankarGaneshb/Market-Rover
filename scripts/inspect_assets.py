
from PIL import Image
import os

ASSETS_DIR = os.path.join(os.getcwd(), "assets", "logos")

print("Checking assets in:", ASSETS_DIR)
for f in os.listdir(ASSETS_DIR):
    if f.endswith(".png"):
        try:
            path = os.path.join(ASSETS_DIR, f)
            img = Image.open(path)
            print(f"{f}: {img.size}")
        except Exception as e:
            print(f"Error reading {f}: {e}")
