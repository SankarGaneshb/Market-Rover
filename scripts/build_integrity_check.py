#!/usr/bin/env python3
import sys
import os
import yaml
import subprocess
from pathlib import Path

def check_yaml_syntax():
    """Verify all GitHub workflow files are valid YAML."""
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        return True

    success = True
    for yml in workflows_dir.glob("*.yml"):
        try:
            with open(yml, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"[PASS] YAML Syntax: {yml.name} is valid.")
        except Exception as e:
            print(f"[FAIL] YAML Syntax: {yml.name} is INVALID: {e}")
            success = False
    return success

def check_python_syntax():
    """Run a quick compile check on all Python files."""
    success = True
    for root, _, files in os.walk("."):
        if ".venv" in root or "node_modules" in root: continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    subprocess.check_call([sys.executable, "-m", "py_compile", path],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    print(f"[FAIL] Syntax Error: {path}")
                    success = False
    if success:
        print("[PASS] Python Syntax: All files compiled successfully.")
    return success

def check_utf8_compliance():
    """Ensure no hidden non-UTF8 bytes in critical infrastructure files."""
    critical_files = [".github/workflows/ci.yml", "Dockerfile", "requirements.txt"]
    success = True
    for file in critical_files:
        if not os.path.exists(file): continue
        try:
            with open(file, 'rb') as f:
                content = f.read().decode('utf-8')
            print(f"[PASS] UTF-8 Integrity: {file} is clean.")
        except UnicodeDecodeError:
            print(f"[FAIL] UTF-8 Error: {file} contains invalid characters.")
            success = False
    return success

def main():
    print("[SAFEGUARD] Market-Rover Pre-Flight Build Integrity Check")
    print("="*50)

    v_yaml = check_yaml_syntax()
    v_py = check_python_syntax()
    v_utf = check_utf8_compliance()

    if all([v_yaml, v_py, v_utf]):
        print("\n[SUCCESS] BUILD INTEGRITY VERIFIED. SAFE TO PUSH.")
        sys.exit(0)
    else:
        print("\n[FAILURE] BUILD INTEGRITY FAILED. DO NOT PUSH.")
        sys.exit(1)

if __name__ == "__main__":
    main()
