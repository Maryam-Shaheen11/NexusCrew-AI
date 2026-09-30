import os
import streamlit as st

from crew import run_nexuscrew, get_memory_preview


st.set_page_config(
    page_title="NexusCrew AI",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 NexusCrew AI")
st.caption("Context-Aware Multi-Agent Problem Solver • CrewAI + Gemini/Groq + Persistent Memory")

st.markdown(
    """
NexusCrew uses **four specialized AI agents** to turn a user problem into a structured,
reviewed solution:

**Context Analyst → Research Strategist → Solution Architect → Critical Reviewer**

The crew shares persistent memory, so important project decisions and preferences can
be recalled in later runs.
"""
)

# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    provider = st.selectbox(
        "Primary LLM",
        ["Gemini", "Groq"],
        help="Choose which provider powers the agents.",
    )

    st.divider()
    st.subheader("Memory")
    st.write("Persistent CrewAI memory is stored locally in `.crewai/memory`.")
    if st.button("Refresh memory preview"):
        st.rerun()

    preview = get_memory_preview()
    if preview:
        st.caption("Recent remembered items")
        for item in preview:
            st.write(f"• {item}")
    else:
        st.caption("No memory records yet.")

    st.divider()
    st.caption("API keys are loaded only from Streamlit Secrets.")
    st.caption("Never put real keys in GitHub.")

# -------------------------------------------------------------------
# Main input
# -------------------------------------------------------------------
st.subheader("🎯 What do you want the AI team to solve?")

problem = st.text_area(
    "Your problem / project idea / goal",
    height=180,
    placeholder=(
        "Example: I want to build a free AI project for university students "
        "that helps them understand difficult technical topics and create a study plan."
    ),
)

context = st.text_area(
    "Additional context (optional)",
    height=120,
    placeholder=(
        "Add your constraints, target users, technologies, budget, deadline, "
        "skills, previous decisions, or preferences."
    ),
)

run_button = st.button("🚀 Run NexusCrew", type="primary", use_container_width=True)

if run_button:
    if not problem.strip():
        st.warning("Please enter a problem or project goal first.")
        st.stop()

    with st.status("🤖 NexusCrew agents are collaborating...", expanded=True) as status:
        try:
            st.write("🧩 Building shared context...")
            result = run_nexuscrew(
                problem=problem.strip(),
                additional_context=context.strip(),
                provider=provider,
            )

            status.update(
                label="✅ Multi-agent analysis completed",
                state="complete",
                expanded=False,
            )

        except Exception as exc:
            status.update(
                label="❌ The crew could not complete the run",
                state="error",
                expanded=True,
            )
            st.error(str(exc))
            st.info(
                "Check your Streamlit Secrets, Python version, installed requirements, "
                "and selected provider."
            )
            st.stop()

    st.success("The four-agent pipeline has finished.")

    # ----------------------------------------------------------------
    # Agent outputs
    # ----------------------------------------------------------------
    tabs = st.tabs(
        [
            "🧩 Context",
            "🔎 Research",
            "🏗️ Architecture",
            "🛡️ Critique",
            "📌 Final Synthesis",
        ]
    )

    with tabs[0]:
        st.markdown(result["context_analysis"])

    with tabs[1]:
        st.markdown(result["research_analysis"])

    with tabs[2]:
        st.markdown(result["solution_architecture"])

    with tabs[3]:
        st.markdown(result["critical_review"])

    with tabs[4]:
        st.markdown(result["final_answer"])

    st.download_button(
        "⬇️ Download final result as Markdown",
        data=result["final_answer"],
        file_name="nexuscrew_result.md",
        mime="text/markdown",
    )

    st.caption(
        "Memory was updated from this run. Future runs can recall relevant information."
    )
