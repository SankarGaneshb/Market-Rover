---
trigger: always_on
---

If the primary Gemini 3 model is unreachable or returns a status error, use the local-ollama MCP server to generate code completions and refactor logic. Prioritize the gemma3:4b model for all local reasoning tasks