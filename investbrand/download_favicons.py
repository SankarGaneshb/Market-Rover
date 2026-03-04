import json
import re
import urllib.request
import urllib.parse
import os
import time
import ast

filepath = r"c:\Users\bsank\Market-Rover\investcraft\frontend\src\data\brands.js"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'export const NIFTY50_BRANDS = (\[[\s\S]*?\]);', content)
brands_json_str = match.group(1)

# Quick fix for single quotes in JS vs double quotes in JSON
brands_json_str = re.sub(r'\'', '\"', brands_json_str)
brands_json_str = re.sub(r',\s*\}', '}', brands_json_str)
brands_json_str = re.sub(r',\s*\]', ']', brands_json_str)
brands_json_str = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\g<1>"\g<2>":', brands_json_str)

brands = ast.literal_eval(match.group(1))

download_dir = r"c:\Users\bsank\Market-Rover\investcraft\frontend\public\logos"
os.makedirs(download_dir, exist_ok=True)

success_count = 0
updated_brands = []

print(f"Starting reliable Google Proxy download of {len(brands)} logos...")

for idx, b in enumerate(brands):
    ticker = b['ticker']
    company = b['company']
    safe_filename = "".join(c for c in ticker if c.isalnum()) + ".png"
    save_path = os.path.join(download_dir, safe_filename)
    
    clean_domain = urllib.parse.quote(re.sub(r'[^a-zA-Z0-9]', '', company.lower()) + ".com")
    fallback_url = f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://{clean_domain}&size=512"
    
    try:
        req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(save_path, 'wb') as out:
                out.write(response.read())
        b['logoUrl'] = '/logos/' + safe_filename
        success_count += 1
        print(f"[{idx+1}/{len(brands)}] Success: {company}")
    except Exception as e:
         print(f"[{idx+1}/{len(brands)}] Failed {company} primary ({e}).")
         
    updated_brands.append(b)
    time.sleep(0.2) # Avoid rate limits

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
