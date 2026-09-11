# Portfolio and interview preparation

## Resume-ready description

**CareerLens AI — Explainable Resume & Job Matching Platform**
Built a Python/FastAPI and React/TypeScript application for document extraction, normalized skill evidence, replaceable sentence embeddings, transparent compatibility scoring, job ranking, and counterfactual learning recommendations. Designed a PostgreSQL relational schema, Docker deployment, interactive Plotly skill-demand/co-occurrence analytics, and automated tests for parsing, security boundaries, scoring, and recommendation logic. Created an evaluation harness for ranking and classification metrics while explicitly separating synthetic fixtures from human-validated results.

Use only claims you can personally demonstrate. Do not add fabricated user counts, accuracy percentages, business impact, deployment uptime or “production ML” claims.

## Five strong interview questions

1. Why did you use MiniLM and cosine similarity, and how would you compare it with a cross-encoder reranker on a held-out dataset?
2. How do you distinguish an undetected skill from an explicit lack of a skill, and how do those cases affect your score?
3. Why are your initial weights equal, how does missing-factor renormalization affect rankings, and what labels would you need to calibrate them?
4. How do you prevent leakage when evaluating jobs from the same templates or resumes from the same candidate?
5. How is a skill-learning recommendation derived mathematically, and why is it not a promise of overall score improvement or employment?

## Five technical challenges to explain

1. **Document variability:** multi-column PDFs, table order, OCR limits, section detection and safe parser resource limits. Explain your evidence-preserving extraction and conservative unknowns.
2. **Semantic evidence versus mastery:** paraphrases can match without proving a skill. Explain why related semantic/taxonomy signals do not create new profile skills.
3. **Scoring under missingness:** coverage changes denominators, semantic/project factors correlate, and short resumes can receive deceptively high indices. Explain both the current behavior and a validated missingness-aware successor.
4. **Evaluation and data scarcity:** synthetic labels are smoke checks. Explain dual-human annotation, candidate/employer-disjoint splits, NDCG versus precision/recall, and error analysis.
5. **Operational/privacy trade-offs:** cached models versus repeated embeddings, CPU latency, request limits, deletion cascades, anonymization limits, session token safety, and moving to a queue/vector index for scale.
