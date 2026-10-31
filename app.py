"""
Streamlit Web Dashboard for Autonomous Multimodal Scientific Discovery Agent.
Author: Goda Srinivasulu Reddy (Team Lead)
Organization: Zaalima Development Pvt. Ltd.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file automatically
load_dotenv()

# Ensure repository root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.memory_manager import AgentMemoryManager
from agents.orchestrator import (
    run_research_workflow,
    run_research_from_papers,
    run_multimodal_research_pipeline,
)
from agents.rag_orchestrator import run_pinecone_rag_research, run_rag_research
from services.cost_tracker import track_discovery_metrics, ExecutionMetrics


def init_page_config() -> None:
    """Initialize Streamlit page settings and visual styling."""
    st.set_page_config(
        page_title="Autonomous Scientific Discovery Agent",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_custom_css() -> None:
    """Inject custom styles for clean professional enterprise look."""
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2.1rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #475569;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background-color: #F8FAFC;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #E2E8F0;
        }
        .agent-pill {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 6px;
        }
        .pill-done { background-color: #DCFCE7; color: #166534; }
        .pill-pending { background-color: #F1F5F9; color: #64748B; }
        .pill-running { background-color: #FEF3C7; color: #92400E; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> Dict[str, Any]:
    """Render sidebar controls, project metadata, and execution settings."""
    with st.sidebar:
        st.markdown("### 🔬 Discovery Agent")
        st.caption("Autonomous Multimodal Scientific Research System")
        st.caption("**Zaalima Development Pvt. Ltd.** | Week 4")

        st.divider()
        st.subheader("⚙️ Configuration")

        workflow_mode = st.selectbox(
            "Workflow Mode",
            options=[
                "RAG Semantic Retrieval (Pinecone)",
                "Live Literature Search (ArXiv/PubMed)",
                "Direct Literature Input / Text Context",
                "Multimodal PDF Analysis (Gemini Vision)",
            ],
            index=0,
            help="Choose how the agent retrieves and processes scientific evidence.",
        )

        enable_statistical_critic = st.checkbox(
            "Enable Statistical Critic (SciPy)",
            value=True,
            help="Perform automated hypothesis testing, p-values, CI, and effect size calculation.",
        )

        enable_memory = st.checkbox(
            "Enable Cross-Agent Context Memory",
            value=True,
            help="Retain and summarize interactions across Literature, Hypothesis, and Execution.",
        )

        with st.expander("🛠️ Advanced Parameters", expanded=False):
            max_papers = st.slider("Max Papers to Search / Retrieve", 1, 10, 3)
            peer_reviewed_only = st.checkbox("Peer-reviewed Papers Only", value=False)
            docker_timeout = st.slider("Docker Sandbox Timeout (s)", 10, 60, 30)

        st.divider()
        st.markdown("### 👥 Project Team")
        st.markdown(
            """
            - **Goda Srinivasulu Reddy** *(Lead: Orchestration & Streamlit)*
            - **Anand Satapara** *(Research Data & Automated Reports)*
            - **Krishna** *(Vector DB, Docker & Testing QA)*
            """
        )

        return {
            "workflow_mode": workflow_mode,
            "enable_statistical_critic": enable_statistical_critic,
            "enable_memory": enable_memory,
            "max_papers": max_papers,
            "peer_reviewed_only": peer_reviewed_only,
            "docker_timeout": docker_timeout,
        }


def render_topic_input_section() -> Dict[str, Any]:
    """Render Section 1: Research Topic & Empirical Inputs."""
    st.markdown('<div class="main-header">Autonomous Scientific Discovery Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Multi-agent orchestration for scientific literature analysis, hypothesis generation, and empirical verification.</div>',
        unsafe_allow_html=True,
    )

    preset_topics = [
        "Custom Topic...",
        "CRISPR-Cas9 off-target cleavage reduction mechanisms",
        "Transformer attention mechanisms for high-throughput protein folding",
        "Solid-state electrolyte lithium dendrite suppression",
        "mRNA vaccine lipid nanoparticle stability under varying pH",
    ]

    col_preset, col_btn = st.columns([4, 1])
    with col_preset:
        selected_preset = st.selectbox("Sample Research Presets", preset_topics, index=1)

    default_topic = (
        "" if selected_preset == "Custom Topic..." else selected_preset
    )

    research_topic = st.text_input(
        "Scientific Research Topic or Objective:",
        value=default_topic,
        placeholder="e.g. CRISPR-Cas9 off-target cleavage reduction mechanisms",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        manual_context = st.text_area(
            "Direct Literature Evidence / Abstract (Optional if using live RAG):",
            value="CRISPR-Cas9 gene editing demonstrates high on-target cleavage efficiency, but off-target activity remains a safety challenge. High-fidelity Cas9 variants engineered with attenuated non-specific DNA interactions reduce non-target cleavage by up to 20-fold while preserving high target locus cleavage efficiency across mammalian cellular models.",
            height=100,
        )

    with col2:
        exp_input_str = st.text_input(
            "Empirical Benchmark Data Points (comma-separated):",
            value="12.4, 14.2, 11.8, 15.1, 13.5, 12.9, 14.0",
            help="Synthetic or measured experimental values for Statistical Critic evaluation.",
        )
        pdf_file = st.file_uploader(
            "Upload Scientific PDF for Multimodal Figure Analysis:",
            type=["pdf"],
            help="Gemini Vision will extract and analyze embedded charts/plots.",
        )

    experiment_values: Optional[List[float]] = None
    if exp_input_str.strip():
        try:
            experiment_values = [float(x.strip()) for x in exp_input_str.split(",") if x.strip()]
        except ValueError:
            st.warning("⚠️ Invalid experimental values format. Please supply comma-separated numbers.")
            experiment_values = None

    return {
        "research_topic": research_topic,
        "manual_context": manual_context,
        "experiment_values": experiment_values,
        "pdf_file": pdf_file,
    }


def execute_pipeline(
    config: Dict[str, Any],
    inputs: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Execute the multi-agent discovery workflow based on user configuration."""
    topic = inputs["research_topic"].strip()
    if not topic:
        st.error("Please enter a research topic before starting discovery.")
        return None

    memory_manager = AgentMemoryManager(max_entries=10) if config["enable_memory"] else None

    # Step-by-step UI progress containers
    progress_bar = st.progress(0, text="Initializing Discovery Pipeline...")
    status_col1, status_col2, status_col3, status_col4, status_col5 = st.columns(5)

    with status_col1:
        lit_status = st.empty()
        lit_status.markdown('<span class="agent-pill pill-running">📚 1. Lit Reviewer</span>', unsafe_allow_html=True)
    with status_col2:
        hypo_status = st.empty()
        hypo_status.markdown('<span class="agent-pill pill-pending">💡 2. Hypothesis</span>', unsafe_allow_html=True)
    with status_col3:
        vision_status = st.empty()
        vision_status.markdown('<span class="agent-pill pill-pending">👁️ 3. Vision Critic</span>', unsafe_allow_html=True)
    with status_col4:
        exec_status = st.empty()
        exec_status.markdown('<span class="agent-pill pill-pending">⚡ 4. Code Executor</span>', unsafe_allow_html=True)
    with status_col5:
        critic_status = st.empty()
        critic_status.markdown('<span class="agent-pill pill-pending">📊 5. Stat Critic</span>', unsafe_allow_html=True)

    start_time = time.time()
    result: Dict[str, Any] = {}

    try:
        progress_bar.progress(15, text="Querying Literature & Grounding Evidence...")

        mode = config["workflow_mode"]
        pdf_file = inputs["pdf_file"]

        if mode == "Multimodal PDF Analysis (Gemini Vision)" and pdf_file is not None:
            pdf_bytes = pdf_file.read()
            progress_bar.progress(35, text="Extracting Charts and Figures with PyMuPDF...")
            vision_status.markdown('<span class="agent-pill pill-running">👁️ 3. Vision Critic</span>', unsafe_allow_html=True)

            result = run_multimodal_research_pipeline(
                research_topic=topic,
                pdf_bytes=pdf_bytes,
                paper_id=pdf_file.name,
                paper_title=topic,
                experiment_values=inputs["experiment_values"],
                memory_manager=memory_manager,
                enable_statistical_critic=config["enable_statistical_critic"],
            )
            vision_status.markdown('<span class="agent-pill pill-done">👁️ 3. Vision Critic ✅</span>', unsafe_allow_html=True)

        elif mode == "RAG Semantic Retrieval (Pinecone)":
            progress_bar.progress(30, text="Performing Pinecone Vector Search...")
            try:
                result = run_pinecone_rag_research(
                    research_topic=topic,
                    top_k=config["max_papers"],
                    peer_reviewed_only=config["peer_reviewed_only"],
                    experiment_values=inputs["experiment_values"],
                    memory_manager=memory_manager,
                    enable_statistical_critic=config["enable_statistical_critic"],
                )
            except Exception as rag_err:
                # If Pinecone lacks network or index in local test, fallback to manual context
                st.info(f"Vector store search defaulted to literature context: {rag_err}")
                result = run_research_workflow(
                    research_topic=topic,
                    paper_text=inputs["manual_context"] or topic,
                    experiment_values=inputs["experiment_values"],
                    memory_manager=memory_manager,
                    enable_statistical_critic=config["enable_statistical_critic"],
                )

        elif mode == "Live Literature Search (ArXiv/PubMed)":
            progress_bar.progress(30, text="Fetching live papers from ArXiv & PubMed...")
            try:
                result = run_research_from_papers(
                    research_topic=topic,
                    max_results=config["max_papers"],
                )
            except Exception as search_err:
                st.info(f"Live search defaulted to provided text: {search_err}")
                result = run_research_workflow(
                    research_topic=topic,
                    paper_text=inputs["manual_context"] or topic,
                    experiment_values=inputs["experiment_values"],
                    memory_manager=memory_manager,
                    enable_statistical_critic=config["enable_statistical_critic"],
                )
        else:
            # Direct Literature Input
            result = run_research_workflow(
                research_topic=topic,
                paper_text=inputs["manual_context"] or topic,
                experiment_values=inputs["experiment_values"],
                memory_manager=memory_manager,
                enable_statistical_critic=config["enable_statistical_critic"],
            )

        # Update pipeline indicators
        progress_bar.progress(60, text="Generating Testable Hypotheses...")
        lit_status.markdown('<span class="agent-pill pill-done">📚 1. Lit Reviewer ✅</span>', unsafe_allow_html=True)
        hypo_status.markdown('<span class="agent-pill pill-done">💡 2. Hypothesis ✅</span>', unsafe_allow_html=True)

        progress_bar.progress(85, text="Running Verification Code & Statistical Critic...")
        exec_status.markdown('<span class="agent-pill pill-done">⚡ 4. Code Executor ✅</span>', unsafe_allow_html=True)
        critic_status.markdown('<span class="agent-pill pill-done">📊 5. Stat Critic ✅</span>', unsafe_allow_html=True)

        progress_bar.progress(100, text="Scientific Discovery Run Complete!")

        # Calculate metrics and cost
        latency_seconds = round(time.time() - start_time, 2)
        metrics = track_discovery_metrics(result, execution_duration=latency_seconds)
        result["metrics"] = metrics

        return result

    except Exception as e:
        progress_bar.empty()
        st.error(f"Pipeline Execution Error: {str(e)}")
        return None


def render_results_section(result: Dict[str, Any]) -> None:
    """Render Section 2 to 5: Workflow status, agent outputs, and analytics."""
    st.divider()
    st.subheader("📋 Discovery Pipeline Outputs & Agent Evaluation")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Literature & Citations",
        "💡 Hypothesis & Method",
        "👁️ Multimodal Visuals",
        "⚡ Experiment & Statistical Critic",
        "📊 System Analytics & Cost",
    ])

    with tab1:
        st.markdown("#### Agent 1: Scientific Literature Review")
        lit_text = result.get("literature_review", "No literature review generated.")
        st.write(lit_text)

        citations = result.get("citations", [])
        if citations:
            st.markdown("##### 🔗 Retrieved Citations & References")
            for cit in citations:
                st.markdown(f"- **{cit.get('title', 'Unknown Title')}** ({cit.get('source', 'Unknown Source')}) — [Link]({cit.get('url', '#')})")

    with tab2:
        st.markdown("#### Agent 2: Generated Scientific Hypothesis")
        hypo_text = result.get("hypothesis", "No hypothesis generated.")
        st.info(hypo_text)

    with tab3:
        st.markdown("#### Multimodal Analysis: Figures & Visual Data")
        figures_count = result.get("multimodal_figures_count", 0)
        visual_analyses = result.get("visual_analyses", [])

        if visual_analyses:
            st.success(f"Successfully processed {len(visual_analyses)} figures via Gemini Vision.")
            for item in visual_analyses:
                with st.expander(f"📌 {item.get('reference_label', 'Figure')} — {item.get('figure_type', 'Figure')}", expanded=True):
                    st.markdown(item.get("analysis", "No detailed analysis available."))
        else:
            st.info("No figures extracted. To analyze charts, upload a scientific PDF and select 'Multimodal PDF Analysis' mode.")

    with tab4:
        st.markdown("#### Agent 3: Experiment Execution & Statistical Critic")
        col_exec, col_stat = st.columns(2)

        with col_exec:
            st.markdown("##### ⚡ Code Executor Output")
            exp = result.get("experiment", {})
            if exp:
                st.json(exp)
            else:
                st.caption("No empirical experiment executed.")

        with col_stat:
            st.markdown("##### 📊 Statistical Critic Evaluation")
            critic = result.get("statistical_critic_result", {})
            if critic:
                is_sig = critic.get("is_statistically_significant")
                badge = "✅ Significant" if is_sig else "ℹ️ Not Statistically Significant"
                st.markdown(f"**Outcome:** `{badge}`")
                st.markdown(f"- **Method:** `{critic.get('test_performed', 'N/A')}`")
                st.markdown(f"- **p-value:** `{critic.get('p_value', 'N/A')}` (alpha = {critic.get('alpha', 0.05)})")
                st.markdown(f"- **Summary:** {critic.get('explanation', 'N/A')}")
            else:
                st.caption("Statistical critic was not invoked or experimental values were omitted.")

    with tab5:
        st.markdown("#### Resource Utilization, Token Usage & Estimated Cost")
        metrics: Optional[ExecutionMetrics] = result.get("metrics")
        if metrics:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Pipeline Latency", f"{metrics.execution_time_seconds} s")
            m2.metric("Total Tokens", f"{metrics.total_tokens:,}")
            m3.metric("Est. Gemini Cost", f"${metrics.estimated_cost_usd:.5f}")
            m4.metric("Figures Evaluated", f"{result.get('multimodal_figures_count', 0)}")

            with st.expander("🔍 Detailed Token Breakdown", expanded=False):
                st.write({
                    "Prompt Tokens (est.)": metrics.prompt_tokens,
                    "Completion Tokens (est.)": metrics.completion_tokens,
                    "Total Tokens": metrics.total_tokens,
                    "Pricing Basis": "Gemini Flash: $0.15/1M in, $0.60/1M out",
                })
        else:
            st.caption("Metrics unavailable for this execution.")


def main() -> None:
    """Main application loop."""
    init_page_config()
    inject_custom_css()

    config = render_sidebar()
    inputs = render_topic_input_section()

    if st.button("🚀 Run Scientific Discovery Workflow", type="primary", use_container_width=True):
        with st.spinner("Autonomous Agents Collaborating..."):
            pipeline_result = execute_pipeline(config, inputs)
            if pipeline_result:
                st.session_state["pipeline_result"] = pipeline_result

    if "pipeline_result" in st.session_state:
        render_results_section(st.session_state["pipeline_result"])


if __name__ == "__main__":
    main()
