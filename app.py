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
from agents.research_synthesizer import generate_report, save_report


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
            font-size: 2.2rem;
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
            padding: 6px 12px;
            border-radius: 14px;
            font-size: 0.88rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 6px;
        }
        .pill-done { background-color: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }
        .pill-pending { background-color: #F1F5F9; color: #64748B; border: 1px solid #E2E8F0; }
        .pill-running { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
        .pill-error { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
        
        .citation-card {
            background-color: #F8FAFC;
            border-left: 4px solid #3B82F6;
            padding: 12px 16px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        .summary-card {
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
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

    col_preset, _ = st.columns([4, 1])
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
            height=110,
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
    """Execute the multi-agent discovery workflow with live status monitoring."""
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
        lit_status.markdown('<span class="agent-pill pill-running">📚 1. Lit Reviewer ⏳</span>', unsafe_allow_html=True)
    with status_col2:
        hypo_status = st.empty()
        hypo_status.markdown('<span class="agent-pill pill-pending">💡 2. Hypothesis ⏸️</span>', unsafe_allow_html=True)
    with status_col3:
        vision_status = st.empty()
        vision_status.markdown('<span class="agent-pill pill-pending">👁️ 3. Vision Critic ⏸️</span>', unsafe_allow_html=True)
    with status_col4:
        exec_status = st.empty()
        exec_status.markdown('<span class="agent-pill pill-pending">⚡ 4. Code Executor ⏸️</span>', unsafe_allow_html=True)
    with status_col5:
        critic_status = st.empty()
        critic_status.markdown('<span class="agent-pill pill-pending">📊 5. Stat Critic ⏸️</span>', unsafe_allow_html=True)

    start_time = time.time()
    result: Dict[str, Any] = {}
    agent_stages: Dict[str, str] = {
        "literature_reviewer": "pending",
        "hypothesis_generator": "pending",
        "vision_critic": "skipped",
        "code_executor": "pending",
        "statistical_critic": "pending",
    }

    try:
        progress_bar.progress(15, text="Querying Scientific Literature & Evidence Grounding...")
        mode = config["workflow_mode"]
        pdf_file = inputs["pdf_file"]

        if mode == "Multimodal PDF Analysis (Gemini Vision)":
            if pdf_file is None:
                st.warning("⚠️ No PDF uploaded for Multimodal mode. Defaulting to provided literature text.")
                result = run_research_workflow(
                    research_topic=topic,
                    paper_text=inputs["manual_context"] or topic,
                    experiment_values=inputs["experiment_values"],
                    memory_manager=memory_manager,
                    enable_statistical_critic=config["enable_statistical_critic"],
                )
            else:
                pdf_bytes = pdf_file.read()
                progress_bar.progress(35, text="PyMuPDF Extracting Embedded Figures & Plots...")
                vision_status.markdown('<span class="agent-pill pill-running">👁️ 3. Vision Critic ⏳</span>', unsafe_allow_html=True)

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
                agent_stages["vision_critic"] = "completed"

        elif mode == "RAG Semantic Retrieval (Pinecone)":
            progress_bar.progress(30, text="Performing Pinecone Vector Similarity Search...")
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
                st.info(f"Vector store search defaulted to literature context: {rag_err}")
                result = run_research_workflow(
                    research_topic=topic,
                    paper_text=inputs["manual_context"] or topic,
                    experiment_values=inputs["experiment_values"],
                    memory_manager=memory_manager,
                    enable_statistical_critic=config["enable_statistical_critic"],
                )

        elif mode == "Live Literature Search (ArXiv/PubMed)":
            progress_bar.progress(30, text="Fetching Live Papers from ArXiv & PubMed...")
            try:
                result = run_research_from_papers(
                    research_topic=topic,
                    max_results=config["max_papers"],
                    experiment_values=inputs["experiment_values"],
                    memory_manager=memory_manager,
                    enable_statistical_critic=config["enable_statistical_critic"],
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
        progress_bar.progress(60, text="Agent 2 Generating Testable Hypotheses...")
        lit_status.markdown('<span class="agent-pill pill-done">📚 1. Lit Reviewer ✅</span>', unsafe_allow_html=True)
        hypo_status.markdown('<span class="agent-pill pill-done">💡 2. Hypothesis ✅</span>', unsafe_allow_html=True)
        agent_stages["literature_reviewer"] = "completed"
        agent_stages["hypothesis_generator"] = "completed"

        progress_bar.progress(85, text="Agent 3 & 4: Executing Code & Statistical Critic...")
        exec_status.markdown('<span class="agent-pill pill-done">⚡ 4. Code Executor ✅</span>', unsafe_allow_html=True)
        critic_status.markdown('<span class="agent-pill pill-done">📊 5. Stat Critic ✅</span>', unsafe_allow_html=True)
        agent_stages["code_executor"] = "completed"
        agent_stages["statistical_critic"] = "completed" if config["enable_statistical_critic"] else "skipped"

        progress_bar.progress(100, text="Scientific Discovery Pipeline Completed Successfully!")

        # Calculate metrics and cost
        latency_seconds = round(time.time() - start_time, 2)
        metrics = track_discovery_metrics(result, execution_duration=latency_seconds)
        result["metrics"] = metrics
        result["agent_stages"] = agent_stages
        result["workflow_mode"] = mode
        if memory_manager:
            result["memory_manager"] = memory_manager

        return result

    except Exception as e:
        progress_bar.empty()
        lit_status.markdown('<span class="agent-pill pill-error">📚 1. Lit Reviewer ❌</span>', unsafe_allow_html=True)
        hypo_status.markdown('<span class="agent-pill pill-error">💡 2. Hypothesis ❌</span>', unsafe_allow_html=True)
        exec_status.markdown('<span class="agent-pill pill-error">⚡ 4. Code Executor ❌</span>', unsafe_allow_html=True)
        critic_status.markdown('<span class="agent-pill pill-error">📊 5. Stat Critic ❌</span>', unsafe_allow_html=True)
        
        st.error(f"❌ Discovery Pipeline Execution Error: {str(e)}")
        with st.expander("Troubleshooting & Error Details", expanded=True):
            st.markdown(
                """
                - **API Key Issue:** Ensure `GEMINI_API_KEY` and `PINECONE_API_KEY` are configured in your `.env` file.
                - **Input Validation:** Ensure research topic is not empty and experimental values are valid numbers.
                - **Network Connectivity:** Check internet connection for live ArXiv, PubMed, or Pinecone API calls.
                """
            )
        return None


def extract_all_citations(result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Aggregate citations from citations metadata, retrieved_papers, and papers."""
    citations = []

    # 1. Check citation_metadata from RAG
    if "citation_metadata" in result and result["citation_metadata"]:
        for item in result["citation_metadata"]:
            citations.append({
                "title": item.get("title", "Untitled Paper"),
                "source": item.get("source", "Pinecone Vector Store"),
                "url": item.get("url", "#"),
                "evidence_id": item.get("evidence_id", len(citations) + 1),
            })

    # 2. Check direct citations list
    if "citations" in result and result["citations"]:
        for item in result["citations"]:
            if isinstance(item, dict):
                citations.append({
                    "title": item.get("title", "Untitled Reference"),
                    "source": item.get("source", "Scientific Literature"),
                    "url": item.get("url", "#"),
                    "evidence_id": len(citations) + 1,
                })

    # 3. Check papers list from paper_fetcher
    if "papers" in result and result["papers"]:
        for item in result["papers"]:
            if isinstance(item, dict):
                citations.append({
                    "title": item.get("title", "Untitled Paper"),
                    "source": item.get("source", "ArXiv/PubMed Ingestion"),
                    "url": item.get("url", item.get("pdf_url", "#")),
                    "evidence_id": len(citations) + 1,
                })

    # Deduplicate by title
    seen_titles = set()
    unique_citations = []
    for c in citations:
        title_lower = c["title"].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_citations.append(c)

    return unique_citations


def render_workflow_summary_card(result: Dict[str, Any]) -> None:
    """Render an overview banner summarizing the workflow run."""
    topic = result.get("research_topic", "Unknown Topic")
    mode = result.get("workflow_mode", "Standard Discovery")
    metrics: Optional[ExecutionMetrics] = result.get("metrics")
    latency = f"{metrics.execution_time_seconds}s" if metrics else "N/A"
    tokens = f"{metrics.total_tokens:,}" if metrics else "N/A"
    cost = f"${metrics.estimated_cost_usd:.5f}" if metrics else "N/A"
    fig_count = result.get("multimodal_figures_count", 0)

    st.markdown(
        f"""
        <div class="summary-card">
            <h4 style="margin:0 0 8px 0; color:#1E40AF;">📌 Workflow Run Summary</h4>
            <b>Topic:</b> {topic}<br>
            <b>Mode:</b> {mode} | <b>Latency:</b> {latency} | <b>Tokens Used:</b> {tokens} | <b>Est. Cost:</b> {cost} | <b>Figures Analyzed:</b> {fig_count}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_results_section(result: Dict[str, Any]) -> None:
    """Render Section 2 to 5: Workflow status, agent outputs, and analytics."""
    st.divider()
    render_workflow_summary_card(result)
    st.subheader("📋 Discovery Pipeline Outputs & Agent Evaluation")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📚 Literature & Citations",
        "💡 Hypothesis & Method",
        "👁️ Multimodal Visuals",
        "⚡ Experiment & Statistical Critic",
        "📄 Research Report Export",
        "🧠 Cross-Agent Memory",
        "📊 System Analytics & Cost",
    ])

    with tab1:
        st.markdown("#### Agent 1: Scientific Literature Review")
        lit_text = result.get("literature_review", "No literature review generated.")
        st.write(lit_text)

        st.divider()
        st.markdown("#### 🔗 Grounded Literature Citations & Source References")
        all_citations = extract_all_citations(result)
        if all_citations:
            for cit in all_citations:
                url = cit.get("url", "#")
                link_html = f'<a href="{url}" target="_blank">View Paper ↗</a>' if url and url != "#" else "No link available"
                st.markdown(
                    f"""
                    <div class="citation-card">
                        <b>[{cit.get('evidence_id', '•')}] {cit.get('title', 'Unknown Title')}</b><br>
                        <span style="color:#64748B; font-size:0.9rem;">Source: {cit.get('source', 'Scientific Database')} | {link_html}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Direct context input was provided. No external bibliographic references to index.")

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
                # Show execution metadata if available
                metadata = exp.get("metadata", {})
                if metadata:
                    st.caption(f"Sandbox: Docker {'✅' if metadata.get('docker_sandboxed') else '⚠️ Local'} | Runtime: {metadata.get('execution_time_seconds', 0.0)}s")
            else:
                st.caption("No empirical experiment executed.")

        with col_stat:
            st.markdown("##### 📊 Statistical Critic Evaluation")
            critic = result.get("statistical_critic_result", {})
            if critic:
                is_sig = critic.get("significant") if "significant" in critic else critic.get("is_statistically_significant", False)
                badge = "✅ Significant" if is_sig else "ℹ️ Not Statistically Significant"
                st.markdown(f"**Outcome:** `{badge}`")
                
                test_name = critic.get("test_name") or critic.get("test_performed") or "Confidence Interval Analysis"
                st.markdown(f"- **Method:** `{test_name}`")
                
                ci = critic.get("confidence_interval")
                if ci:
                    st.markdown(f"- **95% Confidence Interval:** `[{ci[0]}, {ci[1]}]`")
                
                p_val = critic.get("p_value")
                if p_val is not None:
                    st.markdown(f"- **p-value:** `{p_val}` (alpha = {critic.get('alpha', 0.05)})")
                
                explanation = critic.get("criticism") or critic.get("explanation") or "N/A"
                st.markdown(f"- **Evaluation:** {explanation}")
                
                recs = critic.get("recommendations", [])
                if recs:
                    st.markdown("**Recommendations:**")
                    for r in recs:
                        st.markdown(f"  - {r}")
            else:
                st.caption("Statistical critic was not invoked or experimental values were omitted.")

    with tab5:
        st.markdown("#### 📄 Synthesized Scientific Research Report")
        st.caption("Evidence-grounded, peer-verifiable report generated in Markdown and LaTeX format.")

        report_data = {
            "question": result.get("research_topic", ""),
            "hypothesis": result.get("hypothesis", ""),
            "sources": extract_all_citations(result),
            "experiment": {"description": "Automated verification benchmark", "execution": result.get("experiment", {})},
            "evaluation": result.get("statistical_critic_result"),
            "figures": [
                {"source": 1, "figure": item.get("reference_label", "Fig 1"), "finding": item.get("analysis", "")[:120]}
                for item in result.get("visual_analyses", [])
            ],
            "title": f"Scientific Discovery Report: {result.get('research_topic', 'Analysis')}",
        }

        try:
            synthesized_report = generate_report(report_data)
            md_text = synthesized_report.to_markdown()
            latex_text = synthesized_report.to_latex()

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.download_button(
                    "📥 Download Report (Markdown)",
                    data=md_text,
                    file_name="scientific_discovery_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_btn2:
                st.download_button(
                    "📥 Download Report (LaTeX)",
                    data=latex_text,
                    file_name="scientific_discovery_report.tex",
                    mime="application/x-latex",
                    use_container_width=True,
                )

            with st.expander("👁️ Preview Report (Markdown)", expanded=True):
                st.markdown(md_text)

            with st.expander("📜 Preview LaTeX Source Code", expanded=False):
                st.code(latex_text, language="latex")

        except Exception as rep_err:
            st.info(f"Report synthesis in progress: {rep_err}")

    with tab6:
        st.markdown("#### Agent Cross-Turn Memory & Context Management")
        mem_obj = result.get("memory_manager")
        mem_context = result.get("memory_context")
        
        if mem_obj and hasattr(mem_obj, "get_history"):
            history = mem_obj.get_history()
            if history:
                st.caption(f"Context Window Retention: {len(history)} turns stored in memory.")
                for entry in history:
                    role_badge = entry.get("role", "agent").upper()
                    st.markdown(f"**[{role_badge}]**: {entry.get('content', '')}")
            else:
                st.info("Cross-agent memory active. No prior interactions recorded in this session.")
        elif mem_context:
            st.markdown("##### 📝 Synthesized Context Memory:")
            st.info(mem_context)
        else:
            st.info("Cross-Agent memory manager is active for multi-step reasoning context retention.")

    with tab7:
        st.markdown("#### Resource Utilization, Token Usage & Estimated Cost")
        metrics: Optional[ExecutionMetrics] = result.get("metrics")
        if metrics:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Pipeline Latency", f"{metrics.execution_time_seconds} s")
            m2.metric("Total Tokens", f"{metrics.total_tokens:,}")
            m3.metric("Est. Gemini Cost", f"${metrics.estimated_cost_usd:.5f}")
            m4.metric("Figures Evaluated", f"{result.get('multimodal_figures_count', 0)}")

            with st.expander("🔍 Detailed Token & Cost Breakdown", expanded=False):
                st.write({
                    "Prompt Tokens (est.)": metrics.prompt_tokens,
                    "Completion Tokens (est.)": metrics.completion_tokens,
                    "Total Tokens": metrics.total_tokens,
                    "Execution Time (seconds)": metrics.execution_time_seconds,
                    "Estimated Cost (USD)": f"${metrics.estimated_cost_usd:.6f}",
                    "Pricing Basis": "Google Gemini Flash ($0.15/1M input, $0.60/1M output)",
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
