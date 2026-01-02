"""
Automated Audit Script for Market Rover
Enforces the "Global Agent Rules" defined in AI_AGENTS.md.

Run this script monthly or before major deployments:
    python scripts/run_audit.py
"""
import os
import sys
import re
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

ROOT_DIR = Path(__file__).parent.parent

def check_python_version():
    """Rule 5: Production Path Rule - Python Version Check"""
    required_major = 3
    required_minor = 11 # Minimum, preferably 3.13
    
    current = sys.version_info
    print(f"checking Python version... {current.major}.{current.minor}")
    
    if current.major == required_major and current.minor >= required_minor:
        return True, "Python version OK"
    return False, f"Python version obsolete: {current.major}.{current.minor} (Req: 3.11+)"

def check_secrets_exposure():
    """Rule 3: Ironclad Security Rule"""
    suspicious_patterns = [
        r"AIza[0-9A-Za-z-_]{35}", # Google API Key regex
        r"sk-[a-zA-Z0-9]{20,}",   # OpenAI style (just in case)
        r"GOOGLE_API_KEY\s*=\s*['\"]AIza", # Hardcoded assignment
    ]
    
    exposed_files = []
    
    for root, dirs, files in os.walk(ROOT_DIR):
        if ".git" in dirs: dirs.remove(".git")
        if "__pycache__" in dirs: dirs.remove("__pycache__")
        if ".venv" in dirs: dirs.remove(".venv")
        
        for file in files:
            if file.endswith((".py", ".md", ".txt")) and file != ".env" and file != ".env.example":
                path = Path(root) / file
                try:
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    for pattern in suspicious_patterns:
                        if re.search(pattern, content):
                            exposed_files.append(f"{file} (Possible Key Leak)")
                except Exception:
                    pass
                    
    if exposed_files:
        return False, f"Potential Secrets Exposed in: {exposed_files}"
    return True, "No hardcoded secrets found."

def check_versioning_rule():
    """Rule 6: No Versioning Rule"""
    forbidden_strings = ["Market-Rover 2.0", "Market Rover 2.0", "V2.0", "V3.0"]
    violations = []
    
    # Check app.py specifically for UI titles
    app_path = ROOT_DIR / "app.py"
    if app_path.exists():
        content = app_path.read_text(encoding='utf-8')
        for s in forbidden_strings:
            if s in content:
                violations.append(f"app.py contains '{s}'")
                
    if violations:
        return False, f"Versioning Violations found: {violations}"
    return True, "Versioning naming convention OK."

def check_batch_tools_usage():
    """Rule 1: Batch Imperative"""
    agents_path = ROOT_DIR / "agents.py"
    if not agents_path.exists():
        return False, "agents.py missing"
        
    content = agents_path.read_text(encoding='utf-8')
    
    required_tools = ["batch_scrape_news", "batch_get_stock_data"]
    missing = [t for t in required_tools if t not in content]
    
    if missing:
        return False, f"Agents might not be using batch tools. Missing usage of: {missing}"
    return True, "Batch tools implementation detected in agents.py"

def run_audit():
    print(f"\n🔍 {GREEN}Starting Market Rover System Audit{RESET}\n")
    
    checks = [
        ("Python Environment", check_python_version),
        ("Security Scan", check_secrets_exposure),
        ("Naming Conventions", check_versioning_rule),
        ("Performance Rules", check_batch_tools_usage),
    ]
    
    score = 0
    total = len(checks)
    
    for name, func in checks:
        passed, msg = func()
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"[{status}] {name}: {msg}")
        if passed:
            score += 1
            
    print(f"\nCompliance Score: {score}/{total}")
    
    if score == total:
        print(f"\n✅ {GREEN}SYSTEM HEALTHY. READY FOR DEPLOYMENT.{RESET}")
    else:
        print(f"\n⚠️ {YELLOW}ISSUES FOUND. PLEASE FIX BEFORE DEPLOYMENT.{RESET}")

if __name__ == "__main__":
    run_audit()
