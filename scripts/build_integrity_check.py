#!/usr/bin/env python3
import sys
import os
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

import subprocess
from pathlib import Path

def check_yaml_syntax():
    """Verify all GitHub workflow files are valid YAML."""
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        return True

    if not HAS_YAML:
        print("[SKIP] YAML Syntax: 'PyYAML' not installed. Skipping structural check but enforcing UTF-8.")
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

import re

def check_no_emojis():
    """Verify no emojis exist in prohibited files (workflows, Dockerfiles, .env)."""
    prohibited_patterns = [
        ".github/workflows/*.yml",
        "Dockerfile",
        "**/*/Dockerfile",
        ".env",
        ".env.example"
    ]

    # Range covering common emojis and pictographs
    # We allow standard ASCII and some Latin-1, but block specifically identified emojis in rules
    emoji_pattern = re.compile(r'[^\x00-\x7F]')

    success = True
    base_path = Path(".")

    files_to_check = []
    for pattern in prohibited_patterns:
        files_to_check.extend(list(base_path.glob(pattern)))

    for file_path in files_to_check:
        if not file_path.is_file(): continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = emoji_pattern.findall(content)
                if matches:
                    # Filter out non-emoji but non-ASCII characters if necessary,
                    # but for this repo, the rule is strict about standard text markers.
                    print(f"[FAIL] Unicode Rule: {file_path} contains prohibited characters: {' '.join(set(matches))}")
                    success = False
                else:
                    print(f"[PASS] Unicode Rule: {file_path} is emoji-free.")
        except Exception as e:
            print(f"[SKIP] Unicode Rule: Could not read {file_path}: {e}")

    return success

def check_docker_python_version():
    """Ensure all Dockerfiles use Python 3.13."""
    success = True
    base_path = Path(".")
    docker_files = list(base_path.glob("**/Dockerfile")) + list(base_path.glob("Dockerfile"))

    # Requirement: python:3.13...
    version_pattern = re.compile(r'FROM\s+python:(?!3\.13)[\d.]+')

    for df in set(docker_files):
        if not df.is_file(): continue
        try:
            content = df.read_text(encoding='utf-8')
            if "python:" in content and not "python:3.13" in content:
                # Find exactly what version it is using for the error message
                match = version_pattern.search(content)
                current_v = match.group(0) if match else "Unknown"
                print(f"[FAIL] Docker Rule: {df} uses incorrect Python version ({current_v}). MUST remain 3.13.")
                success = True # Set to False once we are ready to enforce strictly, but for audit let's identify all.
                # Actually, rule says strict requirement.
                success = False
            elif "python:3.13" in content:
                print(f"[PASS] Docker Rule: {df} uses Python 3.13.")
        except Exception as e:
            print(f"[SKIP] Docker Rule: Could not read {df}: {e}")

    return success

def check_utf8_compliance():
    """Ensure no hidden non-UTF8 bytes in critical infrastructure files."""
    critical_files = [
        ".github/workflows/ci.yml",
        "Dockerfile",
        "requirements.txt",
        "hil_rover/Dockerfile",
        "hil_rover/backend/requirements.txt",
        "pledge_rover/Dockerfile"
    ]
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

def check_deep_imports():
    """Verify core application entry points can load (detects missing deps/broken paths)."""
    success = True
    repo_root = os.getcwd()

    # 1. Market-Rover Core
    market_path = os.path.join(repo_root, "market_rover", "backend")
    env = os.environ.copy()
    # Use os.pathsep (':' on Linux, ';' on Windows) for cross-platform compatibility
    env["PYTHONPATH"] = f"{market_path}{os.pathsep}{repo_root}"
    try:
        subprocess.check_call([sys.executable, "-c", "import sys; from src.server import app; print('[OK] Market-Rover Server Load')"],
                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print("[PASS] Deep Import: Market-Rover backend entry point is valid.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Deep Import: Market-Rover backend is broken or missing dependencies.")
        if e.stderr:
            print(f"Diagnostics: {e.stderr.decode().strip()}")
        success = False
    except Exception as e:
        print(f"[FAIL] Deep Import: Market-Rover backend check error: {str(e)}")
        success = False

    # 2. Pledge-Rover Core
    pledge_path = os.path.join(repo_root, "pledge_rover", "backend")
    env["PYTHONPATH"] = f"{pledge_path}{os.pathsep}{repo_root}"
    try:
        subprocess.check_call([sys.executable, "-c", "from src.server import app; print('[OK] Pledge-Rover Server Load')"],
                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print("[PASS] Deep Import: Pledge-Rover backend entry point is valid.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Deep Import: Pledge-Rover backend is broken or missing dependencies.")
        if e.stderr:
            print(f"Diagnostics: {e.stderr.decode().strip()}")
        success = False
    except Exception as e:
        print(f"[FAIL] Deep Import: Pledge-Rover backend check error: {str(e)}")
        success = False

    return success

def main():
    print("[SAFEGUARD] Market-Rover Pre-Flight Build Integrity Check")
    print("="*50)

    v_yaml = check_yaml_syntax()
    v_py = check_python_syntax()
    v_utf = check_utf8_compliance()
    v_emoji = check_no_emojis()
    v_docker = check_docker_python_version()
    v_imports = check_deep_imports()

    if all([v_yaml, v_py, v_utf, v_emoji, v_docker, v_imports]):
        print("\n[SUCCESS] BUILD INTEGRITY VERIFIED. SAFE TO PUSH.")
        sys.exit(0)
    else:
        print("\n[FAILURE] BUILD INTEGRITY FAILED. PROHIBITED CHARACTERS OR VERSION MISMATCH DETECTED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
