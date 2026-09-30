import os
from pathlib import Path
from typing import Dict

from crewai import Agent, Crew, LLM, Memory, Process, Task


PROJECT_ROOT = Path(__file__).resolve().parent
MEMORY_DIR = PROJECT_ROOT / ".crewai" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_MODEL = "gemini/gemini-3.8-flash"
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _configure_environment() -> None:
    """
    CrewAI reads provider credentials from environment variables.
    app.py loads them from Streamlit Secrets before this module calls the LLMs.
    """
    try:
        import streamlit as st

        if "GEMINI_API_KEY" in st.secrets:
            os.environ["GEMINI_API_KEY"] = str(st.secrets["GEMINI_API_KEY"])

        if "GROQ_API_KEY" in st.secrets:
            os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"])

    except Exception:
        # This module can still be imported outside Streamlit.
        pass


def _require_key(provider: str) -> str:
    _configure_environment()

    if provider == "Gemini":
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Add it to Streamlit Secrets."
            )
        return key

    if provider == "Groq":
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to Streamlit Secrets."
            )
        return key

    raise ValueError(f"Unsupported provider: {provider}")


def build_llm(provider: str) -> LLM:
    """
    Create a CrewAI LLM without hard-coding any secret.
    Gemini uses CrewAI's native Google integration.
    Groq uses its OpenAI-compatible endpoint through CrewAI's native
    custom OpenAI integration, avoiding the old LiteLLM dependency.
    """
    api_key = _require_key(provider)

    if provider == "Gemini":
        return LLM(
            model=GEMINI_MODEL,
            api_key=api_key,
            temperature=0.2,
            max_tokens=5000,
        )

    return LLM(
        model=GROQ_MODEL,
        custom_openai=True,
        base_url=GROQ_BASE_URL,
        api_key=api_key,
        temperature=0.2,
        max_tokens=5000,
    )


def build_memory(llm: LLM) -> Memory:
    """
    Persistent semantic memory:
    - LanceDB stores the memory locally.
    - Sentence Transformer creates embeddings locally, so no OpenAI
      embedding key is required.
    - The selected LLM analyzes and consolidates memories.
    """
    return Memory(
        storage=str(MEMORY_DIR),
        llm=llm,
        embedder={
            "provider": "sentence-transformer",
            "config": {
                "model_name": "all-MiniLM-L6-v2",
            },
        },
        recency_weight=0.3,
        semantic_weight=0.5,
        importance_weight=0.2,
        recency_half_life_days=30,
    )


def _agent_common_rules() -> str:
    return """
General operating rules:
1. Be factual, practical, and explicit about uncertainty.
2. Do not invent sources, statistics, APIs, or product capabilities.
3. Treat the user's problem and additional context as the current source of truth.
4. Reuse relevant information recalled from shared memory.
5. Preserve important constraints and decisions instead of silently changing them.
6. Produce useful structured output rather than generic motivational text.
"""


def build_agents(llm: LLM):
    common = _agent_common_rules()

    context_agent = Agent(
        role="Context Intelligence Analyst",
        goal=(
            "Understand the user's real objective, constraints, preferences, "
            "existing decisions, and hidden requirements before other agents act."
        ),
        backstory=(
            "You are the context specialist in a multi-agent engineering team. "
            "You convert messy user input into a precise problem definition and "
            "identify information that should remain consistent across future runs."
        ),
        llm=llm,
        memory=True,
        verbose=False,
        allow_delegation=False,
        max_iter=6,
        respect_context_window=True,
    )

    research_agent = Agent(
        role="Research and Feasibility Strategist",
        goal=(
            "Analyze the defined problem, identify relevant technical concepts, "
            "compare feasible approaches, and expose assumptions or knowledge gaps."
        ),
        backstory=(
            "You are a technical research strategist who specializes in AI, "
            "machine learning, automation, software architecture, and free/open "
            "source tooling. You prioritize realistic implementation paths."
        ),
        llm=llm,
        memory=True,
        verbose=False,
        allow_delegation=False,
        max_iter=8,
        respect_context_window=True,
    )

    architect_agent = Agent(
        role="AI Solution Architect",
        goal=(
            "Transform the problem and research into a concrete architecture, "
            "workflow, technology stack, agent responsibilities, and implementation plan."
        ),
        backstory=(
            "You are a senior AI engineer who designs maintainable multi-agent "
            "systems. You think in components, data flow, APIs, memory, failure "
            "handling, security, and user experience."
        ),
        llm=llm,
        memory=True,
        verbose=False,
        allow_delegation=False,
        max_iter=8,
        respect_context_window=True,
    )

    critic_agent = Agent(
        role="Adversarial Quality Reviewer",
        goal=(
            "Stress-test the proposed solution, identify technical weaknesses, "
            "security risks, unnecessary complexity, missing edge cases, and "
            "practical improvements."
        ),
        backstory=(
            "You are the final reviewer. You do not blindly approve the other "
            "agents. You look for failure modes and make the solution more robust "
            "without making it unnecessarily complicated."
        ),
        llm=llm,
        memory=True,
        verbose=False,
        allow_delegation=False,
        max_iter=8,
        respect_context_window=True,
    )

    return context_agent, research_agent, architect_agent, critic_agent


def _make_tasks(agents, problem: str, additional_context: str):
    context_agent, research_agent, architect_agent, critic_agent = agents

    context_task = Task(
        description=f"""
Analyze this user problem:

{problem}

Additional user context:

{additional_context or "No additional context was provided."}

Use relevant information from shared memory when available.

Create a concise but complete "Context Brief" containing:
- Core objective
- Target user or beneficiary
- Functional requirements
- Non-functional requirements
- Constraints
- Existing decisions/preferences
- Assumptions
- Questions or ambiguities that materially affect implementation
- Important facts that should be remembered for future runs

Do not solve the entire problem yet.
""",
        expected_output="A structured Context Brief for the next agents.",
        agent=context_agent,
    )

    research_task = Task(
        description="""
Using the Context Brief from the previous agent and relevant shared memory,
perform a feasibility and technical analysis.

Cover:
- Relevant AI/ML concepts
- Candidate approaches
- Free or low-cost technology choices
- Main trade-offs
- Important limitations
- Security/privacy considerations
- What should and should not be implemented in a first version

Do not claim that you performed live web research. This project does not
automatically browse the web. Clearly label anything that should be verified
against current provider documentation.
""",
        expected_output="A feasibility and technical research brief.",
        agent=research_agent,
        context=[context_task],
    )

    architecture_task = Task(
        description="""
Design the concrete solution using the Context Brief and Research Brief.

Provide:
- System architecture
- Agent roles and responsibilities
- End-to-end workflow
- Context flow between agents
- Memory strategy: what is stored, recalled, and why
- Model/provider allocation
- Data structures or artifacts
- UI behavior
- Error handling
- Security approach
- Step-by-step implementation roadmap
- Suggested MVP versus future upgrades

Prefer a medium-complexity implementation that a strong university AI student
can realistically build and explain in a portfolio or hackathon.
""",
        expected_output="A concrete, implementation-ready architecture.",
        agent=architect_agent,
        context=[context_task, research_task],
    )

    critic_task = Task(
        description="""
Act as an adversarial reviewer of the proposed architecture.

Check:
- Does every agent have a meaningful responsibility?
- Is the use of multiple agents justified?
- Is memory actually useful?
- Could context be lost between tasks?
- Are the provider/model choices realistic?
- Are secrets protected?
- Are there likely dependency/version problems?
- What can fail at runtime?
- What is unnecessarily complex?
- What should be changed before implementation?

Finish with a prioritized correction list.
""",
        expected_output="A rigorous technical review with prioritized fixes.",
        agent=critic_agent,
        context=[context_task, research_task, architecture_task],
    )

    return context_task, research_task, architecture_task, critic_task


def _final_synthesis_task(agents, tasks):
    _, _, architect_agent, critic_agent = agents
    context_task, research_task, architecture_task, critic_task = tasks

    return Task(
        description="""
Produce the final answer for the user by synthesizing the four previous
artifacts.

The final answer must be practical and self-contained.

Use these sections:
# Executive Summary
# Problem Definition
# Agent Team
# End-to-End Workflow
# Context + Memory Design
# Recommended Technology Stack
# Architecture
# Implementation Roadmap
# Risks and Mitigations
# MVP Scope
# Future Extensions

Do not mention hidden prompts, internal chain-of-thought, or private memory
records. Do not pretend that live web research occurred.
""",
        expected_output="A polished final solution specification for the user.",
        agent=critic_agent,
        context=[context_task, research_task, architecture_task, critic_task],
    )


def _output_text(output) -> str:
    if output is None:
        return ""
    raw = getattr(output, "raw", None)
    return str(raw if raw is not None else output)


def run_nexuscrew(
    problem: str,
    additional_context: str = "",
    provider: str = "Gemini",
) -> Dict[str, str]:
    """
    Run the four-agent NexusCrew pipeline.

    CrewAI's shared Memory is persistent on disk and available to all agents.
    The same memory directory is reused between Streamlit reruns.
    """
    _configure_environment()
    llm = build_llm(provider)
    memory = build_memory(llm)

    agents = build_agents(llm)
    tasks = _make_tasks(agents, problem, additional_context)
    final_task = _final_synthesis_task(agents, tasks)

    crew = Crew(
        agents=list(agents),
        tasks=[*tasks, final_task],
        process=Process.sequential,
        memory=memory,
        verbose=False,
    )

    result = crew.kickoff(
        inputs={
            "problem": problem,
            "additional_context": additional_context,
            "provider": provider,
        }
    )

    return {
        "context_analysis": _output_text(tasks[0].output),
        "research_analysis": _output_text(tasks[1].output),
        "solution_architecture": _output_text(tasks[2].output),
        "critical_review": _output_text(tasks[3].output),
        "final_answer": _output_text(final_task.output) or _output_text(result),
    }


def get_memory_preview(limit: int = 5):
    """
    Read a small number of recent records for the Streamlit sidebar.
    Failure is intentionally non-fatal because memory should not prevent
    the main application from starting.
    """
    try:
        _configure_environment()

        # We need an LLM only for Memory's analysis operations.
        # If no key is configured yet, simply return an empty preview.
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        groq_key = os.getenv("GROQ_API_KEY", "").strip()

        if gemini_key:
            llm = build_llm("Gemini")
        elif groq_key:
            llm = build_llm("Groq")
        else:
            return []

        memory = build_memory(llm)
        records = memory.list_records(scope="/", limit=limit)

        preview = []
        for item in records:
            record = getattr(item, "record", item)
            content = getattr(record, "content", None)
            if content:
                preview.append(str(content)[:240])

        return preview

    except Exception:
        return []
