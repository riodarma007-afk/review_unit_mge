from PIL import Image
import sys

try:
    img = Image.open('GHT generate.png')
    print(f"Size: {img.size}")
except Exception as e:
    print(f"Error: {e}")
