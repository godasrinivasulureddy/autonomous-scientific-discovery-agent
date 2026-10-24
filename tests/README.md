# Automated Tests

This directory contains automated tests for the Autonomous Multimodal Scientific Discovery Agent.

## Test Coverage

- **Paper ingestion:** ArXiv/PubMed retrieval, publication metadata, duplicate handling, and scheduled ingestion.
- **PDF processing:** Download validation, retries, text extraction, cleaning, and abstract fallback.
- **Vector database:** Pinecone retrieval, embedding integration, text chunking, metadata, and peer-review filtering.
- **Gemini service:** API response handling, missing credentials, network retries, and fallback behavior.
- **Agent orchestration:** Literature review, hypothesis generation, LangChain workflow, and evidence citations.
- **RAG pipeline:** Research retrieval, evidence mapping, citation metadata, and input validation.
- **Docker sandbox:** Execution restrictions, timeouts, container cleanup, and error handling.
- **Experiment feedback:** Reward calculation, experiment selection, and persistent learning history.
- **Integration:** Research-paper processing and multi-agent workflow behavior.

## Running the Tests

Run the complete test suite from the project root:

```bash
python -m pytest -v
```

Run a specific test module:

```bash
python -m pytest tests/test_rag_orchestrator.py -v
```

## Team Responsibilities

Each team member tests their assigned modules before submitting changes for integration. The Team Lead reviews contributions and coordinates integration testing.

## Test Reporting

Record the actual test results from the latest run. Do not report a test as passing unless it has been executed successfully.
