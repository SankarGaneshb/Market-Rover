
import os

def move_main_to_end():
    path = "C:/Users/bsank/Market-Rover/app.py"
    
    print(f"Reading {path}...")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    new_lines = []
    main_block_found = False
    
    # We look for the standard block. It might span a few lines.
    # We will just skip writing it when we find it, and append it at the end.
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'if __name__ == "__main__":' in line:
            print(f"Found main block at line {i+1}. Removing it from here.")
            # Skip this line and the next one if it is main()
            # Check next line
            if i + 1 < len(lines) and "main()" in lines[i+1]:
                i += 2
                continue
            # Handle empty lines or slight variations
            elif i + 2 < len(lines) and "main()" in lines[i+2]: # empty line in between
                 i += 3
                 continue
            else:
                 # Just skip the if line and let manual cleanup handle rest or just risk it?
                 # safer to just comment it out locally or be precise.
                 # Let's try to be precise.
                 i += 1
                 # consume lines until main() is found or we hit another def
                 while i < len(lines) and "def " not in lines[i]:
                     if "main()" in lines[i]:
                         # consume this line
                         i += 1
                         break
                     i += 1
                 continue
        else:
            new_lines.append(line)
            i += 1
            
    # Append the block at the end
    print("Appending main block to the end.")
    new_lines.append("\n\nif __name__ == \"__main__\":\n")
    new_lines.append("    main()\n")
    
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print("Done.")

if __name__ == "__main__":
    move_main_to_end()
