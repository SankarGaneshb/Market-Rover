
def append_safely():
    base = "C:/Users/bsank/Market-Rover/app.py"
    snippet = "C:/Users/bsank/Market-Rover/app_shadow_tab.py"
    
    with open(base, "r", encoding="utf-8") as f:
        existing = f.read()
        
    with open(snippet, "r", encoding="utf-8") as f:
        new_code = f.read()
        
    # Check if we already have it (to avoid double append)
    if "def show_shadow_tracker_tab" in existing:
        print("Function already exists. Skipping append.")
        return
        
    final = existing + "\n\n" + new_code
    
    with open(base, "w", encoding="utf-8") as f:
        f.write(final)
    print("Appended safely.")

if __name__ == "__main__":
    append_safely()
