"""
TrialSense AI - Interactive Demo

Streamlit application showcasing the multi-agent clinical trial intelligence system.
"""

import streamlit as st
import asyncio
from datetime import datetime

from trialsense.agents.orchestrator import TrialSenseOrchestrator
from trialsense.config import get_settings
from trialsense.utils.logging import setup_logging

# Page config
st.set_page_config(
    page_title="TrialSense AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        border-radius: 1rem;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .outcome-badge {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .site-badge {
        background-color: #f3e5f5;
        color: #7b1fa2;
    }
    .reasoning-box {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_orchestrator():
    """Initialize and cache the orchestrator."""
    setup_logging()
    return TrialSenseOrchestrator()


def display_header():
    """Display application header."""
    st.markdown('<div class="main-header">🧬 TrialSense AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Agentic AI System for Clinical Trial Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    **Powered by LangGraph Multi-Agent System**

    This system uses specialized AI agents to:
    - 🎯 **Predict trial outcomes** using ML models and historical data
    - 🏥 **Match optimal trial sites** based on performance and capabilities
    - 📊 **Provide evidence-based insights** with explainable AI
    """)


def display_sidebar():
    """Display sidebar with information and settings."""
    st.sidebar.header("About")

    st.sidebar.markdown("""
    ### Multi-Agent Architecture

    <span class="agent-badge outcome-badge">Outcome Agent</span>

    Predicts trial success using XGBoost + SHAP explanations

    <span class="agent-badge site-badge">Site Matching Agent</span>

    Recommends optimal sites based on multi-dimensional analysis

    ### Features
    - 🔍 Semantic search over 400K+ trials
    - 🤖 LangGraph agent orchestration
    - 📈 ML-powered predictions
    - 💡 Explainable AI with SHAP
    - 🔗 RAG for evidence retrieval
    """, unsafe_allow_html=True)

    st.sidebar.header("Example Queries")
    example_queries = [
        "Predict outcome for NCT04567890",
        "Recommend sites for a Phase 3 lung cancer immunotherapy trial",
        "Analyze trial NCT03842513 comprehensively",
        "Find similar trials to NCT02576431",
    ]

    for query in example_queries:
        if st.sidebar.button(query, key=query, use_container_width=True):
            st.session_state.example_query = query

    st.sidebar.divider()
    st.sidebar.caption("Built with LangGraph, LangChain, XGBoost, ChromaDB")


def display_query_interface():
    """Display the main query interface."""
    # Check for example query
    default_query = ""
    if hasattr(st.session_state, "example_query"):
        default_query = st.session_state.example_query
        delattr(st.session_state, "example_query")

    # Query input
    query = st.text_area(
        "Enter your query:",
        value=default_query,
        height=100,
        placeholder="e.g., 'Predict outcome for NCT04567890' or 'Recommend sites for lung cancer trial'"
    )

    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        analyze_button = st.button("🚀 Analyze", type="primary", use_container_width=True)

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    return query, analyze_button


def display_results(result: dict):
    """Display analysis results."""
    st.divider()

    # Task type badge
    task_type = result.get("task_type", "unknown")
    task_badges = {
        "outcome_prediction": ("🎯", "Outcome Prediction", "#e3f2fd"),
        "site_matching": ("🏥", "Site Matching", "#f3e5f5"),
        "comprehensive": ("📊", "Comprehensive Analysis", "#e8f5e9"),
        "chat": ("💬", "Chat", "#fff3e0"),
    }

    emoji, label, color = task_badges.get(task_type, ("❓", "Unknown", "#f5f5f5"))

    st.markdown(f"""
    <div style="background-color: {color}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <h3>{emoji} {label}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Main response
    st.markdown("### Analysis Results")
    st.markdown(result["response"])

    # Reasoning trace in expander
    if result.get("reasoning_trace"):
        with st.expander("🔍 View Reasoning Trace", expanded=False):
            st.markdown('<div class="reasoning-box">', unsafe_allow_html=True)
            for i, step in enumerate(result["reasoning_trace"], 1):
                st.markdown(f"**Step {i}:** {step}")
            st.markdown('</div>', unsafe_allow_html=True)


def display_demo_mode():
    """Display demo mode when no API keys are configured."""
    st.warning("⚠️ API keys not configured. Running in demo mode with mock data.")

    st.markdown("""
    To use the live system, configure your API keys in `.env`:

    ```bash
    OPENAI_API_KEY=your-key
    # or
    ANTHROPIC_API_KEY=your-key
    ```

    ### System Capabilities

    Even without API keys, you can explore:
    - 📂 Complete source code in the repository
    - 🧪 Unit tests demonstrating functionality
    - 📖 Documentation on architecture and design
    - 🏗️ LangGraph workflow implementation
    """)


def main():
    """Main application function."""
    display_header()
    display_sidebar()

    # Check for API keys
    settings = get_settings()
    has_keys = settings.has_openai_key() or settings.has_anthropic_key()

    if not has_keys:
        display_demo_mode()
        return

    # Main interface
    query, analyze_button = display_query_interface()

    # Process query
    if analyze_button and query.strip():
        with st.spinner("🤖 Agents are analyzing..."):
            try:
                orchestrator = get_orchestrator()

                # Run analysis
                result = orchestrator.run(query)

                # Store in session state
                st.session_state.last_result = result

                # Display results
                display_results(result)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                with st.expander("Error Details"):
                    st.exception(e)

    # Display previous results if available
    elif hasattr(st.session_state, "last_result"):
        display_results(st.session_state.last_result)

    # Footer
    st.divider()
    st.caption(f"TrialSense AI v0.1.0 | {datetime.now().year}")


if __name__ == "__main__":
    main()
