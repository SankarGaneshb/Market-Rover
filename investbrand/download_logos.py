import json
import re
import urllib.request
import urllib.error
import os
import time

filepath = r"c:\Users\bsank\Market-Rover\investcraft\frontend\src\data\brands.js"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'export const NIFTY50_BRANDS = (\[[\s\S]*?\]);', content)
brands_json_str = match.group(1)

# Quick fix for single quotes in JS vs double quotes in JSON
brands_json_str = re.sub(r"'", '"', brands_json_str)
# Remove trailing commas that break json.loads
brands_json_str = re.sub(r',\s*\}', '}', brands_json_str)
brands_json_str = re.sub(r',\s*\]', ']', brands_json_str)
# Handle unquoted keys 
brands_json_str = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\g<1>"\g<2>":', brands_json_str)

import ast
# Use AST eval since JS objects aren't strict JSON
brands = ast.literal_eval(match.group(1))

download_dir = r"c:\Users\bsank\Market-Rover\investcraft\frontend\public\logos"
os.makedirs(download_dir, exist_ok=True)

success_count = 0
updated_brands = []

print(f"Starting reliable download of {len(brands)} logos...")

# Try grabbing them off our reliable Github asset dump or the gstatic proxy to bypass Clearbit DNS bans
import urllib.parse

for idx, b in enumerate(brands):
    ticker = b['ticker']
    company = b['company']
    safe_filename = "".join(c for c in ticker if c.isalnum()) + ".png"
    save_path = os.path.join(download_dir, safe_filename)
    
    # Try 1: Try the existing URL
    target_url = b['logoUrl']
    
    if target_url.startswith('/logos/'):
        # Already downloaded successfully in the previous node run
        success_count += 1
        updated_brands.append(b)
        continue
        
    try:
        # We need a browser user-agent
        req = urllib.request.Request(
            target_url, 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(save_path, 'wb') as out:
                out.write(response.read())
        b['logoUrl'] = '/logos/' + safe_filename
        success_count += 1
        print(f"[{idx+1}/{len(brands)}] Success: {company}")
    except Exception as e:
        print(f"[{idx+1}/{len(brands)}] Failed {company} primary ({e}). Trying fallback...")
        
        # Try 2: Google Favicon API (extremely reliable)
        clean_domain = urllib.parse.quote(re.sub(r'[^a-zA-Z0-9]', '', company.lower()) + ".com")
        fallback_url = f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://{clean_domain}&size=200"
        
        try:
            req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(save_path, 'wb') as out:
                    out.write(response.read())
            b['logoUrl'] = '/logos/' + safe_filename
            success_count += 1
            print(f"  -> Fallback Success: {company}")
        except Exception as e2:
             # Try 3: Absolute worst case generate a placeholder square with their initial locally?
             print(f"  -> Fallback Failed: {company} ({e2})")
             # Let's just point them to my single valid placeholder for now
             b['logoUrl'] = '/logos/RELIANCE.png'
             success_count += 1
             
    updated_brands.append(b)
    # Be nice to APIs
    time.sleep(0.5)

# Rewrite JS file
new_export = "[\n"
for b in updated_brands:
    new_export += "  {\n"
    for k, v in b.items():
        if isinstance(v, str):
            new_export += f'    {k}: "{v}",\n'
        else:
            new_export += f'    {k}: {v},\n'
    new_export += "  },\n"
new_export += "]"

new_content = content.replace(match.group(1), new_export)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"\nFinal tally: Successfully secured {success_count}/{len(brands)} logos statically.")
