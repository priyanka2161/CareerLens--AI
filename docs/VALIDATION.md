# Validation record

Executed in this build environment:

- `RUN_MODEL_TESTS=1 python -m pytest -q`: **53 passed**, one upstream Starlette/AnyIO deprecation warning, 23.28 seconds. Covers aliases, word boundaries, negation, experience interval union, required/preferred extraction, unknowns, session isolation, deletion cascades, malformed/oversized/empty files, DOCX table parsing, archive expansion, chunked request limits, repeated-write upserts, score contributions, ranking, co-occurrence and learning gains.
- Actual pinned MiniLM downloaded and loaded successfully: 384 dimensions.
- Transformer paraphrase-versus-unrelated-text integration test passed.
- Real MiniLM API smoke: 18 authored jobs ranked, 31 learning opportunities, 29.63 seconds including model initialization and a network metadata retry. This is **not** a steady-state performance benchmark. See api-minilm-smoke.json.
- `npm run build`: TypeScript checking and Vite production build succeeded. UI entry ~305 KB uncompressed; lazy Plotly chunk ~4.84 MB uncompressed (~1.47 MB gzip).
- MiniLM and explicit LSA evaluation harnesses produced provisional smoke reports from nine authored pairs. Their metrics do not establish accuracy.
- Evaluation without provisional override correctly reports that no human labels are available.
- SQLAlchemy compiled PostgreSQL DDL for all eight tables.

Not executed / not established:

- Docker/Compose container build or running PostgreSQL integration: Docker/server binaries were unavailable. The database tests above use SQLite; PostgreSQL DDL compilation is not a runtime test.
- Browser visual or interaction QA, mobile screenshots, automated frontend interaction tests, accessibility audit.
- Public deployment, sustained load, penetration tests, malware scanning, backup recovery, rolling upgrades.
- Real human-labeled model accuracy, subgroup fairness, OCR performance or multilingual extraction quality.

The documented boundary matters: this is a runnable portfolio reference implementation with tested engineering paths, not a fully validated production hiring service.

## Test environment

Python 3.12.14, Node v24.19.0. Docker images specify Python 3.12, Node 22 and PostgreSQL 16. Docker CPU PyTorch is pinned to 2.8.0; the local test runtime versions are below.

| Package | Tested version |
|---|---|
| fastapi | 0.116.1 |
| uvicorn | 0.35.0 |
| SQLAlchemy | 2.0.43 |
| psycopg | 3.2.9 |
| pypdf | 5.9.0 |
| python-docx | 1.2.0 |
| numpy | 2.2.6 |
| scikit-learn | 1.7.1 |
| sentence-transformers | 5.1.0 |
| torch | 2.14.0 |
| httpx | 0.28.1 |
| pytest | 8.4.1 |
