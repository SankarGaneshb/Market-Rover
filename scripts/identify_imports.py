
import ast
import os
import sys
import pkg_resources

# Standard library modules to ignore
STD_LIB = sys.stdlib_module_names

# Known mappings for packages where import name != pip name
MAPPING = {
    'PIL': 'pillow',
    'sklearn': 'scikit-learn',
    'fitz': 'pymupdf',
    'dotenv': 'python-dotenv',
    'bs4': 'beautifulsoup4',
    'google.generativeai': 'google-generativeai',
    'google.auth': 'google-auth',
    'googleapiclient': 'google-api-python-client',
    'crewai': 'crewai',
    'crewai_tools': 'crewai-tools',
    'streamlit': 'streamlit',
    'plotly': 'plotly',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'yaml': 'pyyaml',
    'duckduckgo_search': 'duckduckgo-search',
    'yfinance': 'yfinance',
    'requests': 'requests',
    'altair': 'altair',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'networkx': 'networkx',
    'fpdf': 'fpdf2',
    'pypdf': 'pypdf',
    'jose': 'python-jose',
    'jwt': 'pyjwt',
    'authlib': 'authlib',
    'schedule': 'schedule',
    'watchdog': 'watchdog',
     # Add others as discovered
    'backoff': 'backoff',
    'dateutil': 'python-dateutil',
    'openpyxl': 'openpyxl',
    'xlsxwriter': 'xlsxwriter',
    'tabulate': 'tabulate',
    'tqdm': 'tqdm',
    'pdfplumber': 'pdfplumber',
    'newspaper': 'newspaper3k',
    'feedparser': 'feedparser',
    'apscheduler': 'apscheduler',
    'pytz': 'pytz',
    'tzlocal': 'tzlocal',
    'validators': 'validators',
    'streamlit_option_menu': 'streamlit-option-menu',
    'st_aggrid': 'streamlit-aggrid',
    'extra_streamlit_components': 'extra-streamlit-components',
    'streamlit_lottie': 'streamlit-lottie',
    'streamlit_calendar': 'streamlit-calendar',
    'streamlit_authenticator': 'streamlit-authenticator'
}

def get_imports(root_dir):
    imports = set()
    for subdir, _, files in os.walk(root_dir):
        if 'venv' in subdir or '.git' in subdir:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(subdir, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.add(alias.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.add(node.module.split('.')[0])
                    except Exception as e:
                        print(f"Error parsing {path}: {e}")
    return imports

def main():
    root = os.getcwd()
    raw_imports = get_imports(root)
    
    # Filter standard library
    third_party = {i for i in raw_imports if i not in STD_LIB and i not in sys.builtin_module_names}
    
    # Filter local modules (naive check: if folder exists)
    local_modules = {d for d in os.listdir(root) if os.path.isdir(d)}
    true_third_party = {i for i in third_party if i not in local_modules}
    
    # Remove known local utils
    true_third_party.discard('utils')
    true_third_party.discard('rover_tools')
    true_third_party.discard('config')
    true_third_party.discard('agents')
    true_third_party.discard('tasks')
    true_third_party.discard('crew_engine')
    true_third_party.discard('tabs')
    
    print("\n--- Detected Direct Imports ---")
    
    final_reqs = set()
    for imp in sorted(true_third_party):
        pkg = MAPPING.get(imp, imp)
        # Try to match with installed packages to get correct dash/underscore naming
        try:
            # simple verify if it basically exists in current environment
            # This helps correct cases like "pkg_resources" -> "setuptools"
            dist = pkg_resources.get_distribution(pkg)
            final_reqs.add(dist.project_name)
            print(f"  {imp} -> {dist.project_name} ({dist.version})")
        except pkg_resources.DistributionNotFound:
            # Fallback to mapping or raw name
            final_reqs.add(pkg)
            print(f"  {imp} -> {pkg} (Not Found locally or mapped manually)")
            
    print("\n--- Proposed requirements.txt Content (Minimal) ---")
    for req in sorted(final_reqs):
        print(req)

if __name__ == "__main__":
    main()
