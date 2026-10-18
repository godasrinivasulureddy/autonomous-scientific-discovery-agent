# Week 1 — Scientific Discovery Agent Demo

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Organization:** Zaalima Development Pvt. Ltd.  
**Team Lead:** Goda Srinivasulu Reddy  
**Team Members:** Anand Satapara, Krishna  
**Development Branch:** `feature/agent-orchestration`  
**Integrated Branch:** `main`  
**Integration:** Pull Request #8 — Merged  
**Final Verification Date:** October 18, 2026

## 1. Week 1 Objectives

The first week focused on three primary objectives:

1. Build a LangChain-based multi-agent orchestration system.
2. Develop automated ArXiv and PubMed research paper ingestion with Pinecone vector storage.
3. Follow GitHub feature branch management, isolated testing, and pull request review practices.

**Overall Objective Status: COMPLETED**

## 2. Multi-Agent Architecture

The system contains three primary scientific research agents.

### Literature Reviewer Agent

- Processes scientific research text.
- Uses Gemini to generate literature reviews.
- Identifies relevant findings, limitations, and research gaps from available paper content.

### Hypothesis Generator Agent

- Receives the literature review.
- Uses Gemini to generate research hypotheses.
- Produces hypotheses based on the scientific context.

### Code Executor Agent

- Executes approved statistical experiments.
- Validates experiment inputs.
- Supports restricted execution using Docker.
- Rejects unsupported experiments.

The agents are connected through LangChain orchestration.

**Status:** IMPLEMENTED AND TESTED  
**Verification:** Three-agent orchestration and integration tests passed.

## 3. Scientific Paper Ingestion

The ingestion pipeline connects to:

- ArXiv API
- PubMed API

It retrieves scientific paper metadata, including paper IDs, titles, abstracts, authors, publication information, and source URLs.

The project also supports PDF downloading, text extraction using PyMuPDF, and text cleaning.

**Status:** IMPLEMENTED AND LIVE-TESTED

## 4. Pinecone Vector Database Integration

The vector database pipeline uses:

- Gemini embedding model.
- Pinecone vector database.
- Text chunking with overlap.
- Scientific paper metadata.
- Semantic similarity search.
- Duplicate detection using paper IDs.

A separate ChromaDB prototype was developed during initial vector database exploration. Pinecone is used for the integrated research pipeline.

**Status:** IMPLEMENTED AND LIVE-TESTED

## 5. Automated Scheduled Ingestion

The scheduled ingestion pipeline:

1. Searches ArXiv and PubMed.
2. Collects available paper abstracts.
3. Checks whether paper IDs are already stored in Pinecone.
4. Skips previously stored papers.
5. Embeds and stores new papers.
6. Reports stored, skipped, and failed counts.

The GitHub Actions workflow is configured to run daily at **03:00 UTC (08:30 AM IST)** from the repository's default branch, `main`.

**Status:** IMPLEMENTED, MERGED INTO MAIN, AND MANUALLY LIVE-TESTED

### Initial Recorded Live Ingestion Result

```text
STORED: arxiv:2610.22122v1 (2 chunks)
STORED: arxiv:2610.21395v1 (2 chunks)
SKIPPED: pubmed:42887972 — already stored in Pinecone
STORED: pubmed:42887874 (1 chunk)

SUMMARY: stored=3, skipped=1, failed=0
```

This confirms that the initial tested execution stored three new papers and skipped an existing PubMed paper.

### Post-Merge Scheduled Ingestion Verification

The workflow was manually executed after merging the implementation into `main`.

**GitHub Actions Run:** Scheduled Scientific Paper Ingestion #1  
**Result:** PASSED  
**Execution Time:** 58 seconds

```text
SKIPPED: arxiv:2610.22122v1 — already stored in Pinecone
SKIPPED: arxiv:2610.21395v1 — already stored in Pinecone
SKIPPED: pubmed:42887972 — already stored in Pinecone
SKIPPED: pubmed:42887874 — already stored in Pinecone

SUMMARY: stored=0, skipped=4, failed=0
```

This confirms that the post-merge workflow successfully identified previously stored papers and avoided duplicate ingestion.

**Note:** Scheduled ingestion currently stores abstracts. Full PDF ingestion is implemented separately.

**Automatic Schedule Verification:** The daily cron schedule is configured on `main`. Successful execution through the automatic scheduled trigger has not yet been independently verified.

## 6. PDF-to-Pinecone Integration

The PDF pipeline downloads and extracts scientific paper text and stores processed content in Pinecone.

### Recorded Live Test

```text
Testing PDF: arxiv:2610.22372v1

PDF TEXT EXTRACTION PASSED: 86820 characters
PDF TO PINECONE LIVE TEST PASSED
Chunks: 14
```

**Status:** LIVE TEST PASSED

The test confirms successful PDF extraction and Pinecone ingestion. It does not establish that all 86,820 extracted characters were stored in the tested run.

## 7. PubMed-to-Pinecone Integration

### Recorded Live Test

```text
LIVE PUBMED INGESTION PASSED

Paper ID: pubmed:42887972
Title: Discovery of thiol-reactive Staphylococcus aureus sortase A inhibitors from natural products by machine learning and thiocholine mass-shift profiling.
Chunks: 2
```

**Status:** LIVE TEST PASSED

## 8. Retrieval-Augmented Generation (RAG)

The project integrates Pinecone semantic retrieval with Gemini-powered research agents.

The workflow supports:

- Retrieval of relevant scientific paper chunks.
- Passing retrieved content to research agents.
- Generating literature reviews and hypotheses using retrieved context.
- Automatic fallback to a configured Gemini model when the primary model encounters supported quota errors.

### Final RAG Pipeline Live Test

The final live execution successfully completed Pinecone storage, retrieval, and LangChain research generation.

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

**Implementation Status:** IMPLEMENTED  
**Final Live Verification:** PASSED

### Live Paper-to-Agent Integration Test

The integrated Paper-to-Agent workflow retrieved two scientific papers and generated research outputs.

```text
Gemini model succeeded: gemini-3.8-flash
Quota exhausted for gemini-3.8-flash. Trying next configured model.
Gemini model succeeded: gemini-3.5-flash-lite
LIVE PAPER-TO-AGENT TEST PASSED
Papers found: 2
```

The workflow also generated:

- A structured literature review based on the retrieved scientific papers.
- A research hypothesis identifying a gap involving conflicting gradient directions between data-driven and mechanistic consistency objectives in hybrid neural-ODE architectures.

**Status:** LIVE INTEGRATION TEST PASSED

### Gemini API Quota Handling and Model Fallback

During live testing, the Gemini free-tier API returned:

```text
429 RESOURCE_EXHAUSTED
```

The application was updated to handle supported quota errors by attempting a configured fallback model.

**Primary Model:** `gemini-3.8-flash`  
**Fallback Model:** `gemini-3.5-flash-lite`

Final live tests verified successful fallback execution when the primary model reached its request quota.

The Gemini Live API and Model Availability Test also passed:

```text
GEMINI MODEL AVAILABILITY PASSED: 63 models found
Gemini response: Gemini connection successful
LIVE GEMINI API TEST PASSED
```

**Status:** FALLBACK IMPLEMENTED AND LIVE-VERIFIED

**Limitation:** Model fallback does not eliminate API quota limits. Both models remain subject to their respective availability and quota restrictions. The model listing result does not imply that every listed model supports the same operations or free-tier access.

## 9. GitHub Branch Management

Development was organized using separate feature branches:

- `feature/agent-orchestration` — Multi-agent orchestration, integration, and testing.
- `feature/paper-ingestion` — ArXiv, PubMed, and PDF processing development.
- `feature/vector-database` — Initial vector database development.

The integrated Week 1 implementation was developed and validated in `feature/agent-orchestration`.

### Final Integration

**Pull Request:** #8  
**Target Branch:** `main`  
**Merge Status:** MERGED SUCCESSFULLY

Following the merge, the scheduled ingestion workflow was executed successfully from the integrated repository.

Additional Gemini quota-handling improvements were committed and validated using the Python Tests workflow on `main`.

**Status:** FEATURE DEVELOPMENT, INTEGRATION, AND MERGE COMPLETED

## 10. Week 1 Testing Summary

| Component | Final Result |
|---|---|
| Python tests on `main` — Run #116 | PASSED |
| Gemini Live API and Model Availability | PASSED |
| Three-agent LangChain orchestration | PASSED |
| ArXiv ingestion | PASSED |
| PubMed ingestion | PASSED |
| PDF extraction and Pinecone storage | PASSED |
| Scheduled ingestion manual execution | PASSED |
| Post-merge scheduled ingestion — Run #1 | PASSED |
| Pinecone duplicate skipping | VERIFIED |
| Full RAG live integration | PASSED |
| Live Paper-to-Agent integration | PASSED |
| Gemini primary-to-fallback model switching | LIVE-VERIFIED |
| Pull Request #8 merge into `main` | COMPLETED |
| Daily automatic scheduled execution | NOT YET VERIFIED |

### Final Validation Notes

- The Python Tests workflow passed on the integrated `main` branch.
- The Gemini Live API test confirmed successful connectivity and response generation.
- The RAG pipeline passed storage, retrieval, literature review, and hypothesis generation.
- The Paper-to-Agent workflow retrieved two papers and generated research outputs.
- Both integrated live workflows demonstrated successful Gemini fallback behavior.
- Post-merge scheduled ingestion passed with zero failures and correctly skipped four previously stored papers.
- The automatic daily cron trigger remains a separate operational verification item.

## 11. Week 1 Conclusion

The project has established the core architecture for an autonomous scientific research system.

The main Week 1 objectives have been implemented and validated:

- Multi-agent orchestration using LangChain.
- Scientific paper retrieval from ArXiv and PubMed.
- Gemini embedding generation and Pinecone vector storage.
- PDF extraction and ingestion.
- Automated ingestion configuration with duplicate detection.
- RAG-based literature review and hypothesis generation.
- Gemini quota-error handling and successful model fallback.
- GitHub feature branch development, automated testing, and integration through Pull Request #8.
- Successful post-merge execution of the ingestion workflow on `main`.

The implementation has passed the reported unit and live integration tests. Automatic execution of the daily scheduled workflow remains to be confirmed independently.

**Overall Status: WEEK 1 IMPLEMENTATION, INTEGRATION, AND FINAL LIVE VERIFICATION COMPLETED SUCCESSFULLY.**
