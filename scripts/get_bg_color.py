
import os
import sys
from PIL import Image

# Path to image
img_path = r"c:\Users\victor.senisse.GRUPOSTUDIO\Desktop\Plataforma BI\studio-automation-core\images\mock_unidades_weekly.png"

def main():
    try:
        img = Image.open(img_path)
        # Sample top-left pixel (usually background)
        pixel = img.getpixel((0, 0))
        print(f"Background Color Sampled: {pixel}")
        
        # Also sample a bit inward in case of border
        pixel_in = img.getpixel((20, 20))
        print(f"Background Color Inner: {pixel_in}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
