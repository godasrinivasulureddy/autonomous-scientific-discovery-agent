# Autonomous Scientific Discovery Agent

An AI-powered scientific research assistant that retrieves scientific papers, processes research content, generates literature reviews and hypotheses, and supports controlled scientific experiments.

## Team Members

- **Goda Srinivasulu Reddy** — Team Lead, Agent Orchestration and Integration
- **Anand Satapara** — Scientific Paper Ingestion and PDF Processing
- **Krishna** — Vector Database Module

## Week 1 Objective

Build a foundation for scientific discovery using LangChain multi-agent orchestration, automated ArXiv/PubMed ingestion, and vector-based research paper retrieval.

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

- Literature Reviewer Agent
- Hypothesis Generator Agent
- Code Executor Agent
- LangChain-based workflow connecting these agents
- Gemini-powered literature analysis and hypothesis generation

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

## Automated Ingestion

The scheduled workflow searches ArXiv and PubMed, processes available abstracts, checks for previously stored paper IDs, and stores new content in Pinecone.

**Important:** The scheduled ingestion path currently stores abstracts. PDF extraction and PDF-to-Pinecone ingestion are implemented through separate workflows.

The daily GitHub Actions schedule becomes operational after the workflow is present on the repository's default branch.

## Testing and Verification

- Python test workflow: Passed in PR #8.
- Gemini live API workflow: Passed in PR #8.
- Paper-to-Agent live workflow: Previously passed.
- Additional live workflows exist for Pinecone, RAG, ArXiv, PubMed, PDF ingestion, scheduled ingestion, and Docker.

The remaining live workflows require final run-by-run verification before claiming complete end-to-end validation.

## Week 1 Status

The main implementation is present, including paper ingestion, LangChain agent orchestration, Pinecone storage, semantic retrieval, and automated ingestion configuration.

**Remaining before final merge:**

- Verify live workflow results.
- Confirm ArXiv and PubMed storage in Pinecone.
- Verify duplicate skipping.
- Review teammate contributions.
- Update final testing evidence.
- Complete pull request review and merge.

## Project Limitations

- Some papers provide abstracts but no accessible PDF full text.
- Scheduled ingestion currently processes abstracts rather than full PDF documents.
- Gemini and Pinecone live execution depends on API availability and quotas.
- Generated hypotheses require scientific validation.
- Scheduled GitHub Actions execution depends on the workflow being present on the default branch.

## Project Status

**Week 1: Implementation substantially complete; final integration verification and pull request review in progress.**
