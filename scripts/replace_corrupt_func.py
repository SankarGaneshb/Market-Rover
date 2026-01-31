
import os

def surgical_replace():
    app_path = "C:/Users/bsank/Market-Rover/app.py"
    shadow_path = "C:/Users/bsank/Market-Rover/app_shadow_tab.py"
    
    print(f"Reading {app_path} (utf-8)...")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Identify the start of the corrupted function
    # The corruption started around: st.header("x "  Shadow Tracker (Beta)")
    # But the definition line might be intact: def show_shadow_tracker_tab():
    
    marker = "def show_shadow_tracker_tab():"
    
    if marker in content:
        print("Found Shadow Tracker function. Truncating it.")
        parts = content.split(marker)
        # Keep everything before the marker
        clean_content = parts[0].rstrip()
    else:
        print("Function definition not found. Assuming file ends cleanly or corruption is weird.")
        clean_content = content.rstrip()
        
    # Read clean shadow code
    with open(shadow_path, "r", encoding="utf-8") as f:
        shadow_code = f.read()
        
    # Append
    final_content = clean_content + "\n\n\n" + shadow_code
    
    print("Writing fixed content...")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print("Surgical replacement complete.")

if __name__ == "__main__":
    surgical_replace()
