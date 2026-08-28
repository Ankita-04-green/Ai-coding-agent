# Ai-coding-agent
An AI coding agent that understands your project, analyzes files, searches code for issues, runs Python files, and makes code changes when needed.
The agent follows a tool-based workflow:

                    User Prompt
                         │
                         ▼
                ┌─────────────────┐
                │   AI Agent      │
                └────────┬────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        Search Files  Read Files  Run Python
              │          │          │
              └──────────┼──────────┘
                         ▼
                   Analyze Result
                         │
                         ▼
                  Modify File
                  (if required)
                         │
                         ▼
                  Agent Response

**Tech Stack**
- Python
- Flask
- Google Gemini API
- SQLite
- HTML
- CSS
- JavaScript
