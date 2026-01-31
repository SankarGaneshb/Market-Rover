
import os

def aggressive_clean():
    path = "C:/Users/bsank/Market-Rover/app.py"
    
    print(f"Sanitizing {path}...")
    try:
        with open(path, "rb") as f:
            content = f.read()
            
        print(f"Original size: {len(content)} bytes")
        
        # Remove null bytes
        clean_content = content.replace(b'\x00', b'')
        
        print(f"Cleaned size: {len(clean_content)} bytes")
        
        # Verify it decodes
        text = clean_content.decode('utf-8')
        print("Successfully decoded to UTF-8.")
        
        with open(path, "wb") as f:
            f.write(clean_content)
            
        print("File Saved.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    aggressive_clean()
