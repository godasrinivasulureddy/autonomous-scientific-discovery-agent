
import os

from services.paper_fetcher import search_all
from services.vector_store import paper_exists, store_paper


def main():
    topic = os.getenv(
        "INGESTION_TOPIC",
        "machine learning drug discovery",
    )
    max_results = int(
        os.getenv("INGESTION_MAX_RESULTS", "2")
    )

    if max_results < 1 or max_results > 10:
        raise ValueError(
            "INGESTION_MAX_RESULTS must be between 1 and 10."
        )

    papers = search_all(
        topic,
        max_results=max_results,
        peer_reviewed_only=True,
    )

    if not papers:
        raise RuntimeError(
            "No eligible papers were returned from ArXiv or PubMed."
        )

    stored = 0
    skipped = 0
    failed = 0
    seen_ids = set()

    for paper in papers:
        if paper.paper_id in seen_ids:
            print(f"SKIPPED: {paper.paper_id} — duplicate result")
            skipped += 1
            continue

        seen_ids.add(paper.paper_id)

        abstract = paper.abstract.strip()

        if not abstract or abstract == "(no abstract available)":
            print(f"SKIPPED: {paper.paper_id} — no abstract")
            skipped += 1
            continue

        try:
            if paper_exists(paper.paper_id):
                print(
                    f"SKIPPED: {paper.paper_id} "
                    "— already stored in Pinecone"
                )
                skipped += 1
                continue

            result = store_paper(
                paper_id=paper.paper_id,
                title=paper.title,
                text=abstract,
                source=paper.source,
                url=paper.url,
                publication_types=paper.publication_types,
                peer_review_status=paper.peer_review_status,
            )

            stored += 1
            print(
                f"STORED: {paper.paper_id} "
                f"({result['chunk_count']} chunks)"
            )

        except Exception as error:
            failed += 1
            print(f"FAILED: {paper.paper_id} — {error}")

    print(
        f"SUMMARY: stored={stored}, "
        f"skipped={skipped}, failed={failed}"
    )

    if failed:
        raise RuntimeError(
            f"{failed} paper(s) failed ingestion."
        )

    if stored == 0 and skipped == 0:
        raise RuntimeError("No valid papers were processed.")


if __name__ == "__main__":
    main()
