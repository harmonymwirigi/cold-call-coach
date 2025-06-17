# ===== CREATE_FAVICON.PY =====
# Run this script to create a simple favicon.ico file

import os
from pathlib import Path

def create_simple_favicon():
    """Create a simple 16x16 favicon with 'CC' text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a 16x16 image with a blue background
        img = Image.new('RGBA', (16, 16), color=(0, 123, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to draw "CC" text (for Cold Calling)
        try:
            # Use a simple font
            font = ImageFont.load_default()
            # Draw white "CC" text
            draw.text((2, 2), "CC", fill='white', font=font)
        except:
            # If font loading fails, draw a simple circle
            draw.ellipse([4, 4, 12, 12], fill='white')
        
        # Save as favicon.ico
        static_dir = Path('static')
        static_dir.mkdir(exist_ok=True)
        
        img.save(static_dir / 'favicon.ico', format='ICO')
        print("✅ Created simple favicon.ico in static/ directory")
        
    except ImportError:
        print("⚠️  PIL/Pillow not installed. Creating empty favicon.ico file instead.")
        # Create an empty ICO file
        static_dir = Path('static')
        static_dir.mkdir(exist_ok=True)
        
        # Minimal ICO file header (basically empty but valid)
        ico_data = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00\x16\x00\x00\x00'
        ico_data += b'\x00' * (0x468 - len(ico_data))  # Pad to correct size
        
        with open(static_dir / 'favicon.ico', 'wb') as f:
            f.write(ico_data)
        print("✅ Created minimal favicon.ico in static/ directory")

if __name__ == '__main__':
    create_simple_favicon()