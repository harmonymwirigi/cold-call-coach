# ===== CREATE_PLACEHOLDER_IMAGES.PY =====
"""
Simple script to create placeholder avatar images for the roleplay system.
Run this from the project root directory.
"""

import os
from pathlib import Path

def create_placeholder_images():
    """Create placeholder avatar images to prevent 404 errors"""
    
    # Create the directory if it doesn't exist
    avatar_dir = Path("static/images/prospect-avatars")
    avatar_dir.mkdir(parents=True, exist_ok=True)
    
    # List of images we need
    images_needed = [
        'default.jpg',
        'technology.jpg', 
        'tech.jpg',
        'finance.jpg',
        'healthcare.jpg',
        'manufacturing.jpg',
        'education.jpg',
        'executive.jpg',
        'technical.jpg',
        'manager.jpg'
    ]
    
    # Create simple SVG placeholders
    for image_name in images_needed:
        image_path = avatar_dir / image_name
        
        if not image_path.exists():
            # Get industry/type from filename
            industry = image_name.replace('.jpg', '').replace('_', ' ').title()
            if industry == 'Default':
                industry = 'Person'
            elif industry == 'Tech':
                industry = 'Technology'
            
            # Create SVG content
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background circle -->
  <circle cx="100" cy="100" r="100" fill="url(#grad)" />
  
  <!-- Person icon -->
  <circle cx="100" cy="75" r="25" fill="white" opacity="0.9" />
  <path d="M 60 150 Q 100 120 140 150 L 140 200 L 60 200 Z" fill="white" opacity="0.9" />
  
  <!-- Industry label -->
  <text x="100" y="190" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="12" font-weight="bold" opacity="0.8">
    {industry}
  </text>
</svg>'''
            
            # Write SVG file (we'll use .svg extension but serve as needed)
            svg_path = avatar_dir / f"{image_name.replace('.jpg', '.svg')}"
            with open(svg_path, 'w') as f:
                f.write(svg_content)
            
            print(f"Created placeholder: {svg_path}")
    
    # Also create a simple HTML file to view all avatars
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Avatar Previews</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .avatar { display: inline-block; margin: 10px; text-align: center; }
        .avatar img { width: 100px; height: 100px; border-radius: 50%; }
        .avatar p { margin: 5px 0; }
    </style>
</head>
<body>
    <h1>Prospect Avatars</h1>
    <div>'''
    
    for image_name in images_needed:
        svg_name = image_name.replace('.jpg', '.svg')
        industry = image_name.replace('.jpg', '').replace('_', ' ').title()
        html_content += f'''
        <div class="avatar">
            <img src="{svg_name}" alt="{industry}">
            <p>{industry}</p>
        </div>'''
    
    html_content += '''
    </div>
</body>
</html>'''
    
    # Write preview HTML
    with open(avatar_dir / 'preview.html', 'w') as f:
        f.write(html_content)
    
    print(f"\nCreated {len(images_needed)} placeholder avatars in {avatar_dir}")
    print(f"View them at: {avatar_dir / 'preview.html'}")
    
    # Create a simple Python script to serve the SVGs as JPEGs
    serve_script = '''# Simple script to serve SVG avatars as images
from flask import Flask, send_file, abort
import os
from pathlib import Path

app = Flask(__name__)
AVATAR_DIR = Path("static/images/prospect-avatars")

@app.route('/static/images/prospect-avatars/<filename>')
def serve_avatar(filename):
    """Serve SVG files as images"""
    # Try to find the corresponding SVG file
    svg_filename = filename.replace('.jpg', '.svg').replace('.png', '.svg')
    svg_path = AVATAR_DIR / svg_filename
    
    if svg_path.exists():
        return send_file(svg_path, mimetype='image/svg+xml')
    
    # Fallback to a default SVG
    default_path = AVATAR_DIR / 'default.svg'
    if default_path.exists():
        return send_file(default_path, mimetype='image/svg+xml')
    
    abort(404)

if __name__ == '__main__':
    print("This would serve avatars. Integrate into your main Flask app instead.")
'''
    
    with open(avatar_dir / 'serve_avatars.py', 'w') as f:
        f.write(serve_script)
    
    return avatar_dir

if __name__ == "__main__":
    create_placeholder_images()