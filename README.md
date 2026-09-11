# CareerLens AI

An explainable resume and job matching portfolio application built with Python, FastAPI, PostgreSQL, React/TypeScript, sentence embeddings and Plotly.

**What is implemented:** PDF/DOCX resume upload, pasted resumes, PDF/DOCX/TXT job upload, conservative structured extraction, skill aliases/evidence, required/preferred separation, five-factor compatibility scoring, explanations, job ranking, counterfactual learning suggestions, interactive catalog analytics, light/dark mode, device sessions, data deletion, automated tests and Docker configuration.

**What is not claimed:** validated hiring accuracy, production certification, live job-market data, OCR for scanned files, universal resume extraction, causal salary effects, or established fairness. The catalog contains 18 fictional postings. Human relevance labels are not available. See [self-review](docs/SELF_REVIEW.md).

## 1. Quick start with Docker

Install Python 3.12+ and Docker with Compose, start Docker, extract this project, and open a terminal in the `careerlens-ai` folder:

```bash
python scripts/bootstrap.py
```

This creates `.env` with a random database password if it does not exist, then builds and starts PostgreSQL, the FastAPI backend and the frontend. It does not overwrite an existing `.env`.

Open **http://localhost:3000**. Click **Explore with a sample**, or upload your own selectable-text PDF/DOCX. On first comparison MiniLM downloads its pinned public model weights and initializes on CPU; that may take several minutes depending on your connection. Dependencies also require network access during the first build. No external inference API or API key is needed. Do not upload sensitive documents to a shared/untrusted computer.

To pre-download the model into the Docker cache:

```bash
docker compose exec backend python scripts/download_model.py
```

If you cannot download weights, explicitly set `EMBEDDING_BACKEND=lsa-demo` in `.env`, then restart the backend:

```bash
docker compose up -d --force-recreate backend
```

LSA is a limited offline teaching baseline fitted to the sample catalog; the UI marks it clearly. It is not equivalent to MiniLM or a validated general semantic matcher. The UI never silently substitutes it.

Inspect logs or stop services:

```bash
docker compose logs -f backend
docker compose down
```

PostgreSQL and model-cache volumes persist after `down`. The browser's Delete session data action deletes that session's database records. Deleting Docker volumes is a separate destructive operation; do not do it if you want to retain data.

## 2. Manual setup (no Docker)

Python 3.12 and Node 22+ are recommended. The tested runtime versions are recorded in `docs/VALIDATION.md`. Use a virtual environment rather than a global install.

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell, instead:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/download_model.py
python scripts/seed.py
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

By default manual mode uses a local SQLite file for convenience. PostgreSQL is the intended deployment database and is what Compose configures. `.env` is automatically read by Docker Compose, **not by the manual Python commands**. Export the variables below in your terminal if you want to override defaults.

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. Vite forwards `/api` to the backend at `127.0.0.1:8000`. The frontend never computes matching scores itself. The backend OpenAPI docs are at **http://localhost:8000/docs**, or **http://localhost:3000/api/docs** in Docker.

For offline baseline mode before starting Python commands:

```bash
# macOS / Linux
export EMBEDDING_BACKEND=lsa-demo
# Windows PowerShell
# $env:EMBEDDING_BACKEND='lsa-demo'
```

Build the frontend:

```bash
cd frontend
npm run build
```

`npm run preview` serves only compiled UI assets and does not provide the dev API proxy. Use the Docker Nginx configuration to serve a complete production-style build, or configure your own `/api` reverse proxy.

## 3. Environment variables

| Variable | Default / purpose |
|---|---|
| POSTGRES_PASSWORD | Required for Compose; bootstrap generates a URL-safe random password |
| DATABASE_URL | Manual default `sqlite:///./careerlens.db`; Compose sets PostgreSQL automatically |
| EMBEDDING_BACKEND | `minilm`; explicit alternative `lsa-demo` |
| MODEL_NAME | `sentence-transformers/all-MiniLM-L6-v2` |
| MODEL_REVISION | `c9745ed1d9f207416be6d2e6f8de32d1f16199bf` |
| CORS_ORIGINS | Comma-separated exact frontend origins |
| AUTO_CREATE_SCHEMA | `true` for initial local schema; use explicit migrations for deployed upgrades |
| API_ROOT_PATH | Empty in manual mode; `/api` behind the Docker reverse proxy |
| HF_HOME | Optional model-cache directory; Docker supplies a persistent cache volume |
| VITE_API_BASE | Optional frontend API prefix, default `/api`; configured at build time |

Never commit `.env`, uploaded resumes, databases or model-cache contents. Session tokens are random bearer secrets, stored hashed in the database. Only the token and theme persist in browser local storage. There is no login recovery: clearing browser storage loses the ability to access that anonymous session.

## 4. PostgreSQL setup

Compose creates the `careerlens` database and role. For an existing PostgreSQL server, create an application database and restricted application role, then export a URL:

```bash
export DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/careerlens'
python scripts/seed.py
```

Replace the placeholders locally; keep credentials out of source control. The seed command creates the initial eight-table schema and populates the authored sample catalog idempotently. `docs/schema.sql` shows the PostgreSQL DDL. `create_all` is not a migration system: introduce reviewed Alembic migrations before changing a deployed schema.

Relations, constraints and indexes are documented in [ARCHITECTURE.md](docs/ARCHITECTURE.md). The implementation uses dialect-specific atomic upserts for repeated match/recommendation writes and foreign-key deletion cascades.

## 5. Tests and evaluation

From the project root, with Python dependencies installed:

```bash
python -m pytest -q
# Include the real transformer integration check after its weights are downloaded:
RUN_MODEL_TESTS=1 python -m pytest -q
# Windows PowerShell: set $env:RUN_MODEL_TESTS='1', then run pytest.
python scripts/smoke_minilm.py docs/api-minilm-smoke.json
```

Tests use a disposable SQLite database and explicit LSA baseline for fast deterministic engineering checks. The opt-in transformer test instantiates the actual pinned MiniLM model. Tests never use your resume database.

```bash
# No human labels -> no accuracy claim:
python scripts/evaluate.py
# Exercise metrics on authored smoke expectations only:
EMBEDDING_BACKEND=lsa-demo python scripts/evaluate.py --allow-provisional
# Actual independent annotations, when available:
python scripts/evaluate.py --data your-human-labeled-pairs.json
```

Evaluation supports precision, recall, NDCG@3, clipped cosine quantiles, false positives and false negatives. The shipped nine pairs are tiny synthetic fixtures with **null human labels**. Do not publish their metrics as real-world accuracy. See [EVALUATION.md](docs/EVALUATION.md), the generated smoke reports and [MODEL_CARD.md](docs/MODEL_CARD.md).

## 6. Sample catalog and private imports

```bash
python scripts/seed.py
# In Docker:
docker compose exec backend python scripts/seed.py
```

The seed reads `data/jobs.sample.json`; repeated runs do not duplicate records. Shared seed records must be explicitly fictional (`source=authored_demo`, `is_sample=true`). Import real/private descriptions through the authenticated Job match page or POST `/job/analyze` and `/job/upload`. The backend query layer combines shared demo records with only the current session's private jobs. Replace the seed/API ingestion boundary with a licensed feed when available; preserve provenance and avoid duplicates. No external job API credential is required for this deliverable.

## 7. How to deploy

The full Python transformer + PostgreSQL service needs a container host/VM; it is not a Cloudflare Worker-only application. A beginner can start with a Linux VM running Docker/Compose and sufficient disk/RAM for PyTorch, model weights and PostgreSQL (start around 4 GB RAM and measure your workload). Copy the project, run bootstrap, and keep the provided localhost-only binding while testing. Access via an SSH tunnel first.

Before exposing it publicly, add a TLS reverse proxy, managed authentication with secure HttpOnly sessions, trusted-proxy handling and shared rate limits, database backups/restore checks, reviewed schema migrations, dependency scanning, upload malware defense, monitoring, retention rules and load testing. Keep the database off public ports and configure exact frontend origins. Do not change the port binding to public access without these deployment checks. Never use the self-assessment index to automatically reject candidates.

**Deployment verification limit:** Docker and a running PostgreSQL service were not available in the build environment. Dockerfiles/Compose and PostgreSQL DDL are included, but an actual Docker/PostgreSQL deployment was not exercised here. Python API/model smoke tests and frontend build were exercised; details are in VALIDATION.md. No live deployed URL is claimed.

## 8. Product walkthrough

1. Overview: choose a fictional sample or go to My resume.
2. My resume: upload/paste, select among stored resumes, expand skill evidence and structured JSON.
3. Job match: paste/upload a description or select a catalog posting; inspect required/preferred skills and compare.
4. Explore jobs: filter target role and search the ranked catalog; click a result for its explanations.
5. Market insights: inspect role/location demand, ML/cloud skill families, co-occurrence, fictional salary examples and role distribution. Export charts through Plotly or inspect data tables.
6. Learning plan: prioritize missing skills by hypothetical mean required-skill coverage gain.
7. Delete a resume or the whole session when finished.

“Resume completeness” checks extraction availability, not writing quality. Compatibility is an uncalibrated index with visible factor coverage, not a hiring probability. Unknowns are not evidence of inability.

## 9. Architecture, portfolio and interviews

- [System, folder structure, database and API architecture](docs/ARCHITECTURE.md)
- [Model choice, math, calibration, limitations and responsible AI](docs/MODEL_CARD.md)
- [Self-review: 27 weaknesses, fixes and remaining gaps](docs/SELF_REVIEW.md)
- [Resume-ready description, five interview questions and five technical challenges](docs/INTERVIEW_PREP.md)
- [Engineering validation and runtime limitations](docs/VALIDATION.md)

The project is designed to make its data science assumptions inspectable. Improving it means collecting credible labels and addressing the documented limitations, not merely increasing the displayed score.

