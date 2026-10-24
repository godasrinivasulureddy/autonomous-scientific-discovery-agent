# Autonomous Scientific Discovery Agent

An AI-powered scientific research assistant that retrieves scientific papers, processes research content, generates literature reviews and hypotheses, and supports controlled scientific experiments.

## Team Members

- **Goda Srinivasulu Reddy** — Team Lead, Agent Orchestration and Integration
- **Anand Satapara** — Scientific Paper Ingestion and PDF Processing
- **Krishna** — Vector Database Module

## Week 2 Objective & Status

Implement literature-grounded RAG, secure Docker execution, and an RL-based debugging feedback loop across all 3 team sub-modules.

**Week 2 Status: Completed 100% — October 24, 2026**

All three feature branches (eature/week2-docker-security, eature/week2-rag-grounding, and eature/week2-rl-feedback) were validated via comprehensive unit tests (221/221 passing) and GitHub Actions CI runs, and successfully merged into main.

Detailed reports & demos:
- [Week 2 Development Handover Report](reports/week2-handover.md)
- [Week 2 Integration Demo Walkthrough](docs/week2-demo.md)
- [Week 2 Docker Security Guide](docs/week2-docker-security.md)

## Week 1 Objective

Build a foundation for scientific discovery using LangChain multi-agent orchestration, automated ArXiv/PubMed ingestion, and vector-based research paper retrieval.

**Week 1 Status: Completed — October 18, 2026**

The Week 1 implementation was integrated and merged into the `main` branch through Pull Request #8. Post-merge unit testing and live integration testing have been successfully completed.

## Technologies

Python, LangChain, Gemini API, ArXiv API, PubMed API, PyMuPDF, Pinecone, ChromaDB prototype, Docker, GitHub Actions, and Pytest.

## Implemented Features

### 1. Scientific Paper Ingestion

- Search scientific papers using ArXiv and PubMed.
- Retrieve titles, abstracts, authors, source URLs, and publication metadata.
- Download and extract PDF text when available.
- Use abstracts as fallback when full PDF text is unavailable.
- Identify duplicate papers using paper IDs.
- Store paper content in Pinecone using Gemini embeddings.
- Schedule automated abstract ingestion through GitHub Actions.

### 2. Multi-Agent Orchestration

- Literature Reviewer Agent.
- Hypothesis Generator Agent.
- Code Executor Agent.
- LangChain-based workflow connecting these agents.
- Gemini-powered literature analysis and hypothesis generation.
- Gemini model fallback handling for quota exhaustion and temporary service unavailability.

### 3. Vector Database and RAG

- Text chunking with overlap.
- Gemini embedding generation.
- Pinecone vector storage.
- Semantic similarity search.
- Retrieval-augmented research workflow connecting Pinecone results to the agents.
- Separate ChromaDB prototype developed during initial vector database work.

### 4. Controlled Experiment Execution

- Approved descriptive statistics experiments.
- Input validation.
- Restricted Docker execution.
- Experimental feedback and reward calculation.

### 5. Gemini Model Fallback

The Gemini integration supports a primary model and a configured fallback model.

- **Primary model:** `gemini-3.8-flash`
- **Fallback model:** `gemini-3.5-flash-lite`
- Handles `429 RESOURCE_EXHAUSTED` errors by attempting the fallback model.
- Handles unsupported or unavailable configured models where applicable.
- Retries temporary connection errors and HTTP 503 service errors.
- Reports a failure if all configured models are unsuccessful.

**Live verification:** Both the RAG Pipeline Live Test and Live Paper-to-Agent Test demonstrated successful model switching after the primary model encountered quota exhaustion.

Model fallback does not bypass Google API quotas. Each configured model must be available to the API project and have sufficient quota.

## Automated Ingestion

The scheduled workflow searches ArXiv and PubMed, processes available abstracts, checks for previously stored paper IDs, and stores new content in Pinecone.

**Important:** The scheduled ingestion path currently stores abstracts. PDF extraction and PDF-to-Pinecone ingestion are implemented through separate workflows.

### Scheduled Workflow Configuration

- **Workflow:** Scheduled Scientific Paper Ingestion
- **Schedule:** Daily at 03:00 UTC (08:30 AM IST).
- **Manual execution:** Supported through GitHub Actions.
- **Target database:** Pinecone.
- **Duplicate handling:** Previously stored paper IDs are skipped.

### Post-Merge Execution Result

A manual execution of the scheduled ingestion workflow after merging into `main` completed successfully:

```text
SKIPPED: arxiv:2610.22122v1 — already stored in Pinecone
SKIPPED: arxiv:2610.21395v1 — already stored in Pinecone
SKIPPED: pubmed:42887972 — already stored in Pinecone
SKIPPED: pubmed:42887874 — already stored in Pinecone

SUMMARY: stored=0, skipped=4, failed=0
```

This verifies that the workflow executed successfully and correctly avoided storing duplicate papers.

The automatic daily cron trigger remains subject to separate scheduled-run verification.

## Testing and Verification

### 1. Python Unit Tests

- **GitHub Actions workflow:** Python Tests
- **Feature branch:** Passed after the Gemini fallback error-message compatibility fix.
- **Main branch:** Passed in GitHub Actions run #116.
- **Result:** All existing Python unit tests passed.

### 2. Gemini Live API Test

- Gemini model listing completed successfully.
- The API returned 63 model listings.
- Live response generation succeeded.

```text
GEMINI MODEL AVAILABILITY PASSED: 63 models found
Gemini response: Gemini connection successful
LIVE GEMINI API TEST PASSED
```

### 3. RAG Pipeline Live Test

Successfully verified:

- Pinecone vector storage.
- Pinecone semantic retrieval.
- LangChain research agent execution.
- Literature review generation.
- Hypothesis generation.
- Gemini primary-to-fallback model switching.

```text
PINECONE STORAGE PASSED
PINECONE RETRIEVAL PASSED
Gemini model succeeded: gemini-3.8-flash
Quota exhausted for gemini-3.8-flash. Trying next configured model.
Gemini model succeeded: gemini-3.5-flash-lite
LANGCHAIN RAG AGENT PASSED
Literature review generated successfully
Hypothesis generated successfully
COMPLETE RAG PIPELINE PASSED
```

### 4. Live Paper-to-Agent Test

Successfully verified:

- Scientific paper retrieval.
- Processing of two retrieved papers.
- Literature review generation.
- Research hypothesis generation.
- Gemini model fallback during agent execution.

```text
Gemini model succeeded: gemini-3.8-flash
Quota exhausted for gemini-3.8-flash. Trying next configured model.
Gemini model succeeded: gemini-3.5-flash-lite
LIVE PAPER-TO-AGENT TEST PASSED
Papers found: 2
```

### 5. Additional Integration Tests

The following capabilities were also tested during Week 1 development:

- ArXiv paper ingestion.
- PubMed paper ingestion.
- PDF text extraction and Pinecone storage.
- Pinecone live integration.
- Scheduled ingestion and duplicate detection.
- Docker sandbox execution.
- Gemini API connectivity.

These tests provide additional evidence for the individual project components.

## Week 1 Integration and GitHub Workflow

The project followed a feature-branch-based development and integration process.

### Development Branches

- `feature/agent-orchestration` — Agent orchestration and integration.
- `feature/paper-ingestion` — Scientific paper ingestion and PDF processing.
- `feature/vector-database` — Vector database development.

### Pull Request Integration

- **Pull Request:** #8
- **Target branch:** `main`
- **Status:** Merged successfully.
- **Integration review:** Completed.
- **Post-merge Python Tests:** Passed.
- **Post-merge ingestion verification:** Passed.
- **Post-merge Gemini, RAG, and Paper-to-Agent tests:** Passed.

The completed Week 1 implementation is available on the repository's `main` branch.

## Week 1 Achievements

1. Implemented LangChain-based scientific research agent orchestration.
2. Integrated ArXiv and PubMed scientific paper ingestion.
3. Implemented PDF extraction and separate PDF-to-Pinecone ingestion.
4. Integrated Gemini embeddings with Pinecone vector storage.
5. Implemented semantic retrieval and a RAG-based research workflow.
6. Implemented controlled experiment execution with Docker restrictions.
7. Configured automated scientific paper ingestion using GitHub Actions.
8. Verified duplicate detection during post-merge ingestion.
9. Implemented and live-verified Gemini model fallback.
10. Completed GitHub integration, merge, and post-merge testing.

## Project Limitations

- Some scientific papers provide abstracts but no accessible PDF full text.
- Scheduled ingestion currently processes abstracts rather than full PDF documents.
- Gemini and Pinecone live execution depends on API availability, credentials, and usage quotas.
- Gemini fallback models may also experience quota exhaustion or availability restrictions.
- Generated literature reviews and hypotheses require scientific evaluation and validation.
- Restricted Docker execution supports controlled experiments but does not establish a fully general-purpose secure execution environment.
- Automatic GitHub Actions cron execution requires separate verification; successful manual runs alone do not prove scheduled triggering.
- Full production-scale performance, reliability, and scientific accuracy have not yet been established.

## Project Documentation

- [Week 1 Demonstration](docs/week1-demo.md)
- [Reports Overview](reports/README.md)
- [Week 1 Handover Report](reports/week1-handover.md)

## Project Status

**Week 1: COMPLETED — October 18, 2026**

The Week 1 foundation has been implemented, integrated into `main`, and verified through Python unit tests and live GitHub Actions workflows.

The scientific paper ingestion, LangChain agent orchestration, Pinecone retrieval, RAG workflow, Gemini model fallback, and controlled experiment components have demonstrated successful execution.

**Next Phase:** Week 2 planning and development will proceed according to the official internship requirements.
