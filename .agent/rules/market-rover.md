---
trigger: always_on
---

# 🧠 Gemini & Agent Rules – Market‑Rover

This document defines **how Gemini is used inside the Market‑Rover repository only** – including models, environment configuration, and strict rules for all AI agents. It complements `README.md` (user-facing) and `AI_AGENTS.md` (architecture-facing). [file:2][file:3]

---

## 1. Scope & Purpose

- This file applies **only to the Market‑Rover workspace** (this repository) and is not intended as a global Gemini config for other projects. [file:2]  
- It is the **single source of truth** for:
  - Which Gemini models to use.
  - How agents should reason, respond, and respect data/tool boundaries.
  - Safety, cost, and performance constraints specific to this app. [file:2][file:3]

Whenever `agents.py`, `tasks.py`, or Gemini integration logic changes, update this file together with `AI_AGENTS.md`. [file:3]

---

## 2. Models & API Configuration

### 2.1 Primary model

- **Default LLM:** `google-gemini-2.0-flash` (or the latest equivalent configured via `langchain-google-genai`). [file:2]  
- **Fallback / long-context model:** `google-gemini-1.5-flash` for longer reasoning tasks (e.g., detailed portfolio reports). [file:2]

### 2.2 API keys & environment

- Required env var in `.env` (local): [file:2]
  ```bash
  GOOGLE_API_KEY=your_gemini_api_key_here
