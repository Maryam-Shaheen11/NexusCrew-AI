# NexusCrew AI — Architecture

## Agent pipeline

```text
User Goal
   │
   ▼
Context Intelligence Analyst
   │
   ├── recalls relevant persistent memory
   │
   ▼
Research & Feasibility Strategist
   │
   ▼
AI Solution Architect
   │
   ▼
Adversarial Quality Reviewer
   │
   ▼
Final Synthesis
   │
   ▼
Streamlit
```

## Memory lifecycle

```text
Previous runs
     │
     ▼
Persistent CrewAI Memory
     │
     ├── semantic retrieval
     ├── recency weighting
     └── importance weighting
     │
     ▼
Relevant context injected into agents
     │
     ▼
New useful facts extracted from outputs
     │
     ▼
Persistent memory updated
```

## Security

API keys are never stored in Python source code.

Local development:

```text
.streamlit/secrets.toml
```

Deployment:

```text
Streamlit Community Cloud Secrets
```

Git:

```text
.streamlit/secrets.toml → ignored
.crewai/ → ignored
```
