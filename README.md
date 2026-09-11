CareerLens AI

CareerLens AI is a local-first web app that analyzes resumes and matches them against job postings using semantic similarity, giving transparent, explainable scores instead of a black-box match percentage.

Note: This is a portfolio/reference project — not a validated hiring tool or production-certified system.

Features
Resume parsing – extracts sections, skills, dates, and education from PDF, DOCX, and TXT files
Semantic job matching – uses a MiniLM sentence-transformer (with an offline LSA fallback) to compare resumes against job postings
Transparent scoring – every match includes a breakdown across five scoring factors with human-readable explanations
Analytics – skill frequency, co-occurrence, and learning-gain insights across the job catalog
Responsive UI – light/dark themed React frontend with interactive charts
Tech Stack
Layer	Technology
Frontend	React, TypeScript, Vite, Plotly
Backend	FastAPI (Python)
Database	PostgreSQL (Docker) / SQLite (manual setup)
ML	Sentence-Transformers (MiniLM), scikit-learn (LSA fallback)
Containerization	Docker & Docker Compose
Getting Started
Option A: Docker (recommended)

Requirements: Docker Desktop

bash
python scripts/bootstrap.py

This sets up the environment file, builds the containers, and starts Postgres, the backend, and the frontend together. Once running, open http://localhost:3000.

To stop:

bash
docker compose down
Option B: Manual setup (no Docker)

Requirements: Python 3.12+, Node.js 22+

bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # macOS/Linux

# 2. Install backend dependencies
python -m pip install -r requirements.txt

# 3. Download the ML model and seed sample data
python scripts/download_model.py
python scripts/seed.py

# 4. Start the backend
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

# 5. In a new terminal, start the frontend
cd frontend
npm ci
npm run dev

Open http://localhost:5173 in your browser.

Project Structure
careerlens-ai/
  backend/app/       FastAPI backend — parsing, embeddings, scoring, analytics, API routes
  frontend/src/       React frontend — screens, charts, API client
  data/               Sample resumes, sample jobs, skills taxonomy
  scripts/            Bootstrap, model download, seeding, evaluation
  tests/              Backend test suite
  docs/               Architecture, model card, evaluation notes
Testing
bash
pytest
License

Add your preferred license here (e.g. MIT).
