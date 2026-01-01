
from PIL import Image, ImageDraw, ImageFont
import os

# Ensure directory exists
ASSETS_DIR = r"C:\Users\bsank\Market-Rover\assets\logos"
os.makedirs(ASSETS_DIR, exist_ok=True)

# Company Config: Name, Width, Height, BgColor, TextColor, SubtitleColor
COMPANIES = [
    # Reliance (Already done, but Good to refresh) - Blue
    ("RELIANCE", 800, 400, "#004b8d", "white", "#ffcc00"), 
    # TCS - Tata Blue - Wide
    ("TCS", 800, 400, "#292929", "white", "#58a8e8"), 
    # HDFC Bank - Red/Blue - Square-ish
    ("HDFCBANK", 800, 600, "#004c8f", "white", "#ed232a"),
    # Infosys - Cyan Blue - Standard
    ("INFY", 800, 500, "#007cc3", "white", "#333333"),
    # ICICI - Orange - Wide
    ("ICICIBANK", 800, 300, "#f37e20", "white", "#053c6d"),
    # SBI - SBI Blue - Circular/Square vibe
    ("SBIN", 600, 600, "#280071", "white", "#42d4f4"),
]

def generate_card(ticker, w, h, bg_color, text_color, sub_color):
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Subtle Grid Pattern
    grid_color = "white" if bg_color != "white" else "#eee"
    grid_opacity = 30 # out of 255
    
    # Create a separate layer for grid to handle transparency if needed, 
    # but for simple lines, just drawing with reduced alpha color code is hard in RGB mode without conversion.
    # We'll just draw solid lines that are slightly off-color.
    
    line_fill = "#ffffff40" # Hex with alpha doesn't work in RGB.
    # Simple trick: Draw playfield lines
    step = 50
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=bg_color, width=1) # trick: drawing same color? no.
        # Let's just draw darker/lighter lines
        # Actually simplest is just simple lines
        pass

    # Draw Text
    text = ticker
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
        
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    tw, th = right - left, bottom - top
    
    cx, cy = w / 2, h / 2
    draw.text((cx - tw/2, cy - th/2 - 20), text, fill=text_color, font=font)
    
    # Subtitle
    sub = "NIFTY 50"
    try:
        sfont = ImageFont.truetype("arial.ttf", 30)
    except:
        sfont = ImageFont.load_default()
        
    left, top, right, bottom = draw.textbbox((0, 0), sub, font=sfont)
    sw, sh = right - left, bottom - top
    
    draw.text((cx - sw/2, cy + th/2 + 10), sub, fill=sub_color, font=sfont)
    
    # Border
    draw.rectangle([0, 0, w-1, h-1], outline=text_color, width=4)

    save_path = os.path.join(ASSETS_DIR, f"{ticker}.png")
    img.save(save_path)
    print(f"✅ Generated {ticker} ({w}x{h})")

for conf in COMPANIES:
    generate_card(*conf)
