# Week 1 — Scientific Discovery Agent Demo

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Organization:** Zaalima Development Pvt. Ltd.  
**Team Lead:** Goda Srinivasulu Reddy  
**Team Members:** Anand Satapara, Krishna  
**Development Branch:** `feature/agent-orchestration`

## 1. Week 1 Objectives

The first week focuses on three primary objectives:

1. Build a LangChain-based multi-agent orchestration system.
2. Develop automated ArXiv and PubMed research paper ingestion with Pinecone vector storage.
3. Follow GitHub feature branch management, isolated testing, and pull request review practices.

## 2. Multi-Agent Architecture

The system contains three primary scientific research agents.

### Literature Reviewer Agent

- Processes scientific research text.
- Uses Gemini to generate literature reviews.
- Identifies relevant findings from available paper content.

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

**Status:** IMPLEMENTED  
**Verification:** Agent orchestration tests reported successful.

## 3. Scientific Paper Ingestion

The ingestion pipeline connects to:

- ArXiv API
- PubMed API

It retrieves scientific paper metadata, including paper IDs, titles, abstracts, authors, publication information, and source URLs.

The project also supports PDF downloading, text extraction using PyMuPDF, and text cleaning.

**Status:** IMPLEMENTED

## 4. Pinecone Vector Database Integration

The vector database pipeline uses:

- Gemini embedding model
- Pinecone vector database
- Text chunking with overlap
- Scientific paper metadata
- Semantic similarity search
- Duplicate detection using paper IDs

A separate ChromaDB prototype was developed during initial vector database exploration. Pinecone is used for the integrated research pipeline.

**Status:** IMPLEMENTED

## 5. Automated Scheduled Ingestion

The scheduled ingestion pipeline:

1. Searches ArXiv and PubMed.
2. Collects available paper abstracts.
3. Checks whether paper IDs are already stored in Pinecone.
4. Skips previously stored papers.
5. Embeds and stores new papers.
6. Reports stored, skipped, and failed counts.

The GitHub Actions workflow is configured to run daily at 03:00 UTC once it is present on the repository's default branch.

**Status:** IMPLEMENTED AND LIVE-TESTED MANUALLY

### Recorded Scheduled Ingestion Result

```text
STORED: arxiv:2610.22122v1 (2 chunks)
STORED: arxiv:2610.21395v1 (2 chunks)
SKIPPED: pubmed:42887972 — already stored in Pinecone
STORED: pubmed:42887874 (1 chunks)

SUMMARY: stored=3, skipped=1, failed=0
```

This confirms that the tested execution stored new papers and skipped an existing PubMed paper.

**Note:** Scheduled ingestion currently stores abstracts. Full PDF ingestion is implemented separately.

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

**Implementation Status:** IMPLEMENTED  
**Final Live Verification:** Requires confirmation from the corresponding GitHub Actions run.

## 9. GitHub Branch Management

Development was organized using separate feature branches:

- `feature/agent-orchestration` — Multi-agent orchestration, integration, and testing.
- `feature/paper-ingestion` — ArXiv, PubMed, and PDF processing development.
- `feature/vector-database` — Initial vector database development.

The integrated implementation is maintained in `feature/agent-orchestration`.

Pull Request #8 is used for final Week 1 review and integration into `main`.

**Status:** FEATURE DEVELOPMENT AND TESTING COMPLETED; FINAL PR REVIEW IN PROGRESS

## 10. Week 1 Testing Summary

| Component | Result |
|---|---|
| Python tests | PASSED |
| Gemini Live API and Model Availability | PASSED |
| Three-agent LangChain orchestration | PASSED |
| ArXiv ingestion | PASSED in previously reported live testing |
| PubMed ingestion | PASSED |
| PDF extraction and Pinecone storage | PASSED |
| Scheduled ingestion manual execution | PASSED |
| Pinecone duplicate skipping | OBSERVED |
| Full RAG live integration | FINAL VERIFICATION PENDING |
| Daily scheduled execution on `main` | NOT YET VERIFIED |

## 11. Week 1 Conclusion

The project has established the core architecture for an autonomous scientific research system.

The main Week 1 objectives have been implemented:

- Multi-agent orchestration using LangChain.
- Scientific paper retrieval from ArXiv and PubMed.
- Gemini embedding generation and Pinecone vector storage.
- PDF extraction and ingestion.
- Automated ingestion configuration with duplicate detection.
- GitHub feature branch development and automated testing.

The remaining steps are final live-workflow verification, documentation review, and merging the integrated Week 1 implementation into `main`.

**Overall Status: WEEK 1 IMPLEMENTATION SUBSTANTIALLY COMPLETE — FINAL INTEGRATION REVIEW IN PROGRESS.**
