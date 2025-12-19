# GitHub Pre-Push Checklist

Before pushing to GitHub, ensure:

## 1. Environment Files
- [ ] `.env` file is NOT committed (check .gitignore)
- [ ] `.env.example` is updated with all variables
- [ ] API keys are removed from code

## 2. Generated Files
- [ ] `reports/` folder is empty or gitignored
- [ ] `uploads/` folder is empty or gitignored
- [ ] `__pycache__/` folders are gitignored

## 3. Dependencies
- [ ] `requirements.txt` is up to date
- [ ] All imports work: `python -c "import crew, config, utils"`

## 4. Tests
- [ ] Mock tests pass: `python test_mock_data.py`
- [ ] No syntax errors: `python -m py_compile *.py`

## 5. Documentation
- [ ] README.md is updated
- [ ] .env.example has all variables
- [ ] Comments are clear

## 6. Git Commands

```bash
# Initialize git (if not already)
git init

# Add files
git add .

# Check what will be committed
git status

# Commit with meaningful message
git commit -m "feat: Market-Rover 2.0 - Add web UI, visualizations, and parallel execution"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/Market-Rover.git

# Push to GitHub
git push -u origin main
```

## 7. Post-Push
- [ ] GitHub Actions CI runs successfully
- [ ] All badges are green
- [ ] README displays correctly on GitHub

## Quick Validation Commands

```bash
# Test mock data
python test_mock_data.py

# Check linting
flake8 . --count --select=E9,F63,F7,F82 --show-source

# Test imports
python -c "from crew import create_crew; print('OK')"
python -c "from utils.mock_data import mock_generator; print('OK')"
python -c "from utils.report_visualizer import ReportVisualizer; print('OK')"
```
