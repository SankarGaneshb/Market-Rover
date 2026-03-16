# Pledge Rover

**"The signal institutions had. Now yours."**

Pledge Rover is an institutional-grade module within the Market Rover intelligence suite designed to track, score, and evaluate Promoter Pledging ("Skin in the Game") in the Indian stock market. It goes beyond simple data scraping by deploying a multi-agent AI pipeline to interpret filings and gauge actual Contagion Risk and Promoter Intent.

## Overview

Unlike the US markets where pledging is rare, Promoter Pledging in India is a major corporate funding mechanism. Identifying the nuances between "Growth Pledging" (expanding infrastructure) and "Survival Pledging" (to avoid margin calls) is critical. Pledge Rover acts as your automated research desk for exactly this problem.

## System Architecture 

Pledge Rover has three main tiers, mimicking the battle-tested architecture of InvestBrand and perfectly suited for **Google Cloud Run**:

### 1. The Multi-Agent Council (Backend AI)
Built using Python (FastAPI/LangGraph/CrewAI), this is an AI pipeline consisting of four specialized agents:
- **The Harvester**: Extracts deterministic numbers (LTV, percentage encumbered) from Regulation 31 SAST and LODR XBRL filings.
- **The Genealogist**: Traces "Shadow Entities" by matching Pledgees (lenders) against MCA/LEI databases to expose obscure NBFC loops.
- **The Actuary**: Runs the math. Computes margin call trigger prices and calculates proximity to Contagion thresholds.
- **The Skeptic**: Evaluates the narrative. It challenges the Actuary by parsing Annual Reports (MD&A) and issues a Final Synthesis on true intent.

### 2. The API Layer (Backend Integration)
The application leverages a `FastAPI` server configured specifically to deploy seamlessly onto Google Cloud Run. It mimics the familiar `src/routes`, `src/config`, and `src/data` folder structures you used in InvestBrand. 

### 3. The Front-End Experience
A React (Vite) + Tailwind CSS application featuring a "Trust & Speed" design aesthetic—deep navy corporate blues with fast electric cyan highlights. It provides the **Market Dashboard** and the **Target Intelligence Profile** which visualizes the Agentic debate log explicitly.

## Development Setup

### Backend (FastAPI / Python)
```bash
cd pledge_rover/backend
pip install -r requirements.txt
uvicorn src.server:app --reload --port 8080
```
This requires Python 3.10+. If deploying to Cloud Run, simply wrap this in a Dockerfile with `uvicorn src.server:app --host 0.0.0.0 --port $PORT`.

### Frontend (React / Vite)
```bash
cd pledge_rover/frontend
npm install
npm run dev
```

For a comprehensive guide on exactly how the module functions, evaluates risk, and operates on a functional level, see the [User Guide](USER_GUIDE.md).
