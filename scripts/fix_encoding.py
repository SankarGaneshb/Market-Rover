
import os

def fix_app():
    path = "C:/Users/bsank/Market-Rover/app.py"
    snippet_path = "C:/Users/bsank/Market-Rover/app.py_snippet"
    
    print(f"Reading {path}...")
    with open(path, "rb") as f:
        content_bytes = f.read()
        
    # Decode with ignore/replace to salvage content
    content_str = content_bytes.decode("utf-8", errors="ignore")
    
    # We suspect the end is corrupted where we appended.
    # Let's simple truncate before the appended part if it exists, or just ensure the encoding is valid
    # and re-append the snippet cleanly.
    
    # Check if show_shadow_tracker_tab is already there (maybe corrupted)
    if "def show_shadow_tracker_tab" in content_str:
        print("Found existing (possibly corrupted) shadow tracker function. Removing it to re-add cleanly.")
        # Split and keep the part before
        parts = content_str.split("def show_shadow_tracker_tab")
        content_str = parts[0]
        
    # Clean up trailing whitespace/newlines
    content_str = content_str.rstrip()
    
    # Read the clean snippet
    if os.path.exists(snippet_path):
        print(f"Reading snippet {snippet_path}...")
        with open(snippet_path, "r", encoding="utf-8") as f:
            snippet = f.read()
            
        # Append cleanly
        new_content = content_str + "\n\n" + snippet
        
        # Write back to app.py with UTF-8 enforcement
        print(f"Writing fixed content to {path}...")
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print("Success! File repaired.")
    else:
        print("Snippet not found. Just saving cleaned file.")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content_str)

if __name__ == "__main__":
    fix_app()
