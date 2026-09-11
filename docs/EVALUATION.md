# Evaluation protocol

The included nine resume/job pairs are synthetic smoke fixtures. `human_relevance` is deliberately null: no human annotators were available in this build. `provisional_rubric_label` is an authored expectation (0 irrelevant, 1 weak, 2 relevant, 3 strong), not human ground truth. This does not satisfy a scientifically valid accuracy study, and we do not claim otherwise.

Run `EMBEDDING_BACKEND=lsa-demo python scripts/evaluate.py` to confirm that no human scores are available. Use `--allow-provisional` only to exercise precision, recall, NDCG@3, clipped cosine distributions, and false-positive/negative reporting. The 60-point positive threshold is illustrative. The generated provisional report is in this folder.

To collect actual labels, copy data/evaluation.json, add independently judged integer human_relevance values from two consented domain reviewers, record reviewer IDs and adjudication externally, expand to diverse candidate/job groups, then run `--data your-labeled-file.json`. Human relevance ≥2 defines a relevant pair for threshold metrics. Missing labels are excluded. Ranking is grouped by profile ID. NDCG groups with no relevant items are excluded and must be tracked in a real study.

The tool does not tune weights on evaluation pairs. Use candidate/employer-disjoint train/validation/test partitions, avoid duplicate templates, and preserve blind human labels. Add bootstrap intervals over profiles and report both confidence and sample sizes before drawing general conclusions. Cosines are clipped for compatibility, so the reported distribution is clipped, not raw transformer cosine. False-positive/negative lists support manual error review.

Automated tests validate invariants and engineering behavior, not model accuracy. The transformer test is opt-in, uses an unrelated contrast, and requires the model download. The included LSA fixtures overlap its training catalog, making their ranking behavior optimistic. No demographic, language, experience-level or disability slice is validated by the tiny dataset.
