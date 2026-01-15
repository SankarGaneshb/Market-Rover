import os
import shutil
import glob
import argparse
from pathlib import Path
from typing import List, Tuple

def get_size(start_path = '.') -> int:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    
    import math
    if size_bytes == 0:
        return "0B"
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def find_cleanup_targets(root_dir: str) -> dict:
    targets = {
        "Python Cache": [],
        "Pytest Cache": [],
        "Coverage": [],
        "Logs": [],
        "Temp Reports": []
    }

    print(f"Scanning {root_dir}...")

    # Pattern based search
    for root, dirs, files in os.walk(root_dir):
        # Python Cache
        if "__pycache__" in dirs:
            targets["Python Cache"].append(os.path.join(root, "__pycache__"))
        
        # Pytest Cache
        if ".pytest_cache" in dirs:
            targets["Pytest Cache"].append(os.path.join(root, ".pytest_cache"))
            
        # HTML Coverage
        if "htmlcov" in dirs:
             targets["Coverage"].append(os.path.join(root, "htmlcov"))

    # File based search
    # Root level logs
    for file in glob.glob(os.path.join(root_dir, "*.log")):
        targets["Logs"].append(file)
    
    # Logs directory
    logs_dir = os.path.join(root_dir, "logs")
    if os.path.exists(logs_dir):
        for root, dirs, files in os.walk(logs_dir):
             for file in files:
                  if file.endswith(".log"):
                       targets["Logs"].append(os.path.join(root, file))

    # Coverage files
    if os.path.exists(os.path.join(root_dir, ".coverage")):
        targets["Coverage"].append(os.path.join(root_dir, ".coverage"))
        
    return targets

def calculate_sizes(targets: dict) -> dict:
    sizes = {}
    for category, paths in targets.items():
        total = 0
        for path in paths:
            if os.path.isfile(path):
                total += os.path.getsize(path)
            elif os.path.isdir(path):
                total += get_size(path)
        sizes[category] = total
    return sizes

def main():
    parser = argparse.ArgumentParser(description="Market-Rover Janitor: Clean up workspace.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without deleting.", default=False)
    parser.add_argument("--force", action="store_true", help="Clean without confirmation.", default=False)
    args = parser.parse_args()

    root_dir = os.getcwd()
    targets = find_cleanup_targets(root_dir)
    sizes = calculate_sizes(targets)
    
    total_reclaimable = sum(sizes.values())
    
    print("\n" + "="*40)
    print("MARKET-ROVER JANITOR REPORT")
    print("="*40)
    
    if total_reclaimable == 0:
        print("Nothing to clean! Workspace is spotless.")
        return

    for category, size in sizes.items():
        count = len(targets[category])
        print(f"{category:.<25} {count:3} items | {format_size(size):>10}")
    
    print("-" * 40)
    print(f"TOTAL RECLAIMABLE:{format_size(total_reclaimable):>22}")
    print("="*40 + "\n")

    if args.dry_run:
        print("[DRY RUN] No files were deleted.")
        return

    # Interactive choice
    if not args.force:
        choice = input("Select category to clean ([A]ll / [P]ython Cache / [L]ogs / [C]overage / [Q]uit): ").strip().upper()
    else:
        choice = "A"

    if choice == "Q":
        print("Operation cancelled.")
        return
    
    cats_to_clean = []
    if choice == "A":
        cats_to_clean = targets.keys()
    elif choice == "P":
        cats_to_clean = ["Python Cache", "Pytest Cache"]
    elif choice == "L":
        cats_to_clean = ["Logs"]
    elif choice == "C":
        cats_to_clean = ["Coverage"]
    else:
        print("Invalid choice.")
        return

    print("\nCleaning...")
    cleaned_bytes = 0
    for cat in cats_to_clean:
        if cat in targets:
            for path in targets[cat]:
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                    cleaned_bytes += sizes[cat] if path in targets[cat] else 0 # Rough estimate logic
                    print(f"Deleted: {path}")
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

    print(f"\nDone! Reclaimed approximately {format_size(cleaned_bytes)}.")

if __name__ == "__main__":
    main()
