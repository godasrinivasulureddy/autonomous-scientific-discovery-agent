
# Autonomous-Scientific-Discovery-Agent

An AI-powered scientific research assistant using Gemini LLMs, RAG, and multi-agent architecture to analyze research papers, generate hypotheses, and evaluate experiments.

## Team Members

- Goda Srinivasulu Reddy — Team Lead
- Anand Satapara
- Krishna

## Project Objective

Build a multi-agent research assistant that can retrieve scientific papers, analyze research findings, generate hypotheses, and support approved experimental analysis.

## Technologies

- Python
- Gemini API
- ArXiv API
- PubMed API
- PyMuPDF
- ChromaDB (integration pending)
- GitHub Actions
- Pytest

## Implemented Features

### 1. Research Paper Ingestion
- Search research papers using ArXiv and PubMed.
- Retrieve paper metadata.
- Download and process available research PDFs.
- Extract and clean text, with abstract fallback.
- Remove duplicate papers by paper ID.

### 2. AI Research Agents
- Literature Reviewer Agent powered by Gemini.
- Hypothesis Generator Agent powered by Gemini.
- Orchestrator connecting paper ingestion and research agents.
- Controlled retries for temporary Gemini API errors.

### 3. Approved Experiment Execution
- Descriptive statistics experiment.
- Mean and sample standard deviation calculations.
- Input validation.
- Restriction against arbitrary experiment execution.

## Testing

- Python unit and integration tests: PASSED.
- Live Paper-to-Agent GitHub Actions test: PASSED.
- Live test retrieved 2 papers and generated a literature review and research hypothesis.
- Error-handling and invalid-input tests added.

## Week 1 Progress

### Completed
- GitHub repository and feature branches.
- Gemini API integration.
- Literature Reviewer and Hypothesis Generator.
- Approved Code Executor interface.
- Paper ingestion integration.
- Basic agent orchestration.
- Python tests and live paper-to-agent test.

### Pending
- Integrate Member 3's ChromaDB vector database module.
- Verify document chunking and embedding storage.
- Verify similarity search and source metadata.
- Connect retrieved vector chunks to agent inputs.
- Test the complete RAG-enabled research workflow.
- Complete Week 1 demonstration and handover.

## Current Workflow

Research Topic
    |
    v
ArXiv / PubMed Search
    |
    v
Paper Processing
    |
    v
Gemini Literature Reviewer
    |
    v
Gemini Hypothesis Generator
    |
    v
Research Results

Note: Vector retrieval is planned between paper processing and the AI agents but is not yet integrated.

## Project Status

Week 1 development is in progress. The paper-to-agent workflow has passed live integration testing. Full RAG integration is pending.
