# Simple script to serve SVG avatars as images
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
