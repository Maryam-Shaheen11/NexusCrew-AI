# 🧠 NexusCrew AI

**Context-Aware Multi-Agent Problem Solver**

NexusCrew is a portfolio-ready multi-agent AI application built with:

- **CrewAI 1.15.22**
- **Streamlit 1.64.0**
- **Gemini 3.8 Flash**
- **Groq GPT OSS 120B**
- **CrewAI Unified Memory**
- **Local Sentence Transformer embeddings**
- **GitHub-friendly secret management**

## What makes it multi-agent?

NexusCrew uses four specialized agents:

1. **Context Intelligence Analyst**
   - Understands the user's objective, constraints, preferences, and previous decisions.
   - Creates a reusable context brief.

2. **Research & Feasibility Strategist**
   - Evaluates technical approaches, trade-offs, free/low-cost tools, and risks.

3. **AI Solution Architect**
   - Converts the analysis into a concrete architecture and implementation roadmap.

4. **Adversarial Quality Reviewer**
   - Stress-tests the proposed design and identifies weaknesses before the final answer.

A final synthesis task combines the work into a practical specification.

## Context + Memory

The system uses CrewAI's unified `Memory`.

Memory is persistent on disk under:

```text
.crewai/memory/
```

The repository ignores this folder so local memory is not accidentally committed.

The memory layer uses:

- CrewAI Memory
- LanceDB storage
- `all-MiniLM-L6-v2` local embeddings
- The selected LLM for memory analysis

This means the application does not need an OpenAI API key just for embeddings.

### What gets remembered?

Examples:

- User's project objective
- Important constraints
- Technology choices
- Preferences
- Previous architecture decisions
- Important facts from previous agent outputs

When a later run is relevant, CrewAI can recall useful information and provide it as context to agents.

## Models

### Gemini

Default model:

```text
gemini/gemini-3.8-flash
```



## Important Python version note

CrewAI 1.15.22 requires:

```text
Python >= 3.10 and < 3.14
```

Use **Python 3.13** for this project.

If your computer currently uses Python 3.14, create a Python 3.13 virtual environment instead of trying to force CrewAI into Python 3.14.

## Project structure

```text
NexusCrew-AI/
│
├── app.py
├── crew.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── .streamlit/
    └── secrets.toml.example
```

After first run, CrewAI will create:

```text
.crewai/
└── memory/
```

Do not commit that folder.


### . Start Streamlit

Use:

```powershell
python -m streamlit run app.py
```

Using `python -m streamlit` is recommended because it avoids the common Windows problem where `streamlit` is installed but the command is not on PATH.

## GitHub security

Commit:

```text
app.py
crew.py
requirements.txt
README.md
.gitignore
.streamlit/secrets.toml.example
```

Do NOT commit:

```text
.streamlit/secrets.toml
.crewai/
.venv/
```

If a key is ever accidentally pushed to GitHub, revoke/rotate it immediately.

## Streamlit Community Cloud

After pushing to GitHub:

1. Create a Streamlit Community Cloud app.
2. Select the GitHub repository.
3. Set the main file to `app.py`.
4. Open the app's Secrets settings.
5. Add:

```toml
GEMINI_API_KEY = "your-real-key"
GROQ_API_KEY = "your-real-key"
```

Do not upload `secrets.toml`.

## Architecture

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │  Streamlit  │
                    │     UI      │
                    └──────┬──────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  Shared Memory    │
                 │  recall / store   │
                 └────────┬──────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
   Context Agent    Research Agent   Architecture Agent
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                  Critical Reviewer
                          │
                          ▼
                  Final Synthesis
                          │
                          ▼
                    Streamlit UI
```

The execution is sequential because later agents depend on earlier outputs.

## Future upgrades

Possible next versions:

- Real web-search tool
- PDF/document knowledge base
- Agent-specific tools
- Human approval checkpoints
- Structured JSON outputs
- Evaluation/benchmarking
- Authentication
- SQLite/PostgreSQL user profiles
- Project workspaces
- Agent execution tracing
- CrewAI Flow for more advanced routing

## License

Add the license you want to use before publishing the repository.

## LIVE APP LINK
https://nexuscrew-ai.streamlit.app/
