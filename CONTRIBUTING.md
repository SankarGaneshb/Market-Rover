# Contributing to Market-Rover

Welcome! We love contributions. Here’s how to set up your local environment and ship code safely.

## 🚀 Getting Started

1.  **Clone & Environment**
    ```bash
    git clone https://github.com/SankarGaneshb/Market-Rover.git
    cd Market-Rover
    python -m venv .venv
    # Windows:
    .\.venv\Scripts\activate
    # Mac/Linux:
    source .venv/bin/activate
    ```

2.  **Install Dependencies**
    ```bash
    # Install Prod + Dev dependencies
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

3.  **Configure Secrets**
    - Copy `.env.example` to `.env`
    - Fill in `GOOGLE_API_KEY` (Required for AI features).

## 📦 Dependency Management
We strict separation to keep production fast and Linux-compatible.

### 1. Production (`requirements.txt`)
**Rule:** Only libraries that are *imported* by the app.
**Examples:** `streamlit`, `pandas`, `crewai`.

### 2. Development (`requirements-dev.txt`)
**Rule:** Tools for testing/safety only.
**Examples:** `pytest`, `flake8`, `black`.

*> **Note:** Do NOT add `pywin32` or `jupyter` to `requirements.txt`.*

## 🧪 Testing & Quality
Before pushing, run the "Safety Trio":

1.  **Linting**: Ensure no syntax errors.
    ```bash
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    ```
2.  **Testing**: Run the suite.
    ```bash
    pytest
    ```

## 📝 Pull Request Process
1.  **Branch**: Create a feature branch (`feat/new-persona`). Don't push to `main` directly.
2.  **Commit**: Use descriptive messages.
3.  **Review**: Ensure CI checks (Test/Code Quality) pass on GitHub.

Happy Coding! 🕵️‍♂️
