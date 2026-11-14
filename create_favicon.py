# Run this Python script ONCE to create the favicon:
# Save as create_favicon.py in project root, run: python create_favicon.py

from PIL import Image, ImageDraw
import os

os.makedirs('static/images', exist_ok=True)

# Create a 32x32 blue favicon
img  = Image.new('RGB', (32, 32), color='#2563EB')
draw = ImageDraw.Draw(img)
draw.rectangle([8, 8, 24, 24], fill='white')
draw.rectangle([12, 12, 20, 20], fill='#2563EB')
img.save('static/images/favicon.ico', format='ICO')
print("Favicon created!")