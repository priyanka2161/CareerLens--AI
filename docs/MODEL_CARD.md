# Model card and scoring policy

## Intended use

Self-assessment and learning planning for an English-language technical resume portfolio project. Do not use this unvalidated index to automatically reject applicants. No protected characteristics are intentionally used. Heuristic extraction and residual proxy information mean fairness is not established.

## Semantic encoder

Default: sentence-transformers/all-MiniLM-L6-v2, pinned revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf, 384-dimensional normalized representations. It is a compact, general-purpose sentence embedding model suitable for CPU experimentation, not a resume-specific expert model. The official model card describes its sentence/paragraph embedding purpose; a production choice needs domain evaluation against alternatives.

References:
- https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html
- https://www.sbert.net/docs/sentence_transformer/pretrained_models.html
- https://fastapi.tiangolo.com/tutorial/request-files/

Overlapping 100-word chunks with stride 80 reduce truncation of long resumes. The encoder mean-pools chunk embeddings, then renormalizes. A 100-word heuristic is not a token-count guarantee for unusual inputs; tokenizer-aware chunking is a next improvement. Pooling can dilute a decisive requirement. This implementation does not claim a paraphrase implies demonstrated proficiency.

The Encoder protocol isolates model selection from matching. Replace encode(texts) while keeping normalized output and add evaluation/model-version metadata. No private text is sent to an external inference API. Downloading model weights requires outbound access to Hugging Face. Remote model code is disabled.

Explicit alternative: EMBEDDING_BACKEND=lsa-demo fits TF-IDF bigrams and a 12-component truncated SVD on the authored sample job catalog. It is reproducible, entirely local after Python dependencies are installed, and illustrates latent co-occurrence rather than plain keyword matching. It has weak out-of-domain/paraphrase behavior and in-catalog leakage. It is not a replacement for the requested modern semantic model. Unknown vectors return unavailable similarity; there is no silent fallback from MiniLM.

## Score factors

| Factor | Definition | Why it exists |
|---|---|---|
| Skills | Fraction of required normalized skills explicitly detected; if no required skills, use preferred skills | Auditable requirement coverage |
| Semantic | max(0, cosine) between content-focused resume and job vectors | Related responsibilities without exact wording |
| Experience | min(1, detected years / required years); zero required years handled separately | Stated tenure requirement |
| Education | 1 when detected degree meets mandatory degree level, 0 if lower | Explicit degree requirement only, never university rank |
| Projects | max(0, cosine) between project content and job responsibilities | Evidence of relevant applied work |

An unavailable factor is null, not zero and not a perfect match. Remaining factors each get 1/N weight; overall is their mean × 100. Coverage is N/5 × 100. Contributions and actual weights are returned. Explicit missing skills count zero; unknown degree/experience is excluded. Lack of an education requirement excludes education. Preferred overlap remains visible but cannot dilute required-skill coverage. Related taxonomy-category matches are explanation-only; they earn no skill credit.

Equal weights are a neutral starting prior because no trustworthy annotated data supports unequal coefficients. Equal weighting is STILL a policy choice, not an empirical optimum. Correlation between semantic and project factors can double-count similar evidence. A high index at low coverage is less informative and may outrank a better-documented profile; the UI shows coverage alongside rankings. The index is not a probability, percentile, certification or ATS score.

## Calibration plan

Obtain consented, de-identified examples spanning roles, experience, languages and layouts. Have at least two domain reviewers independently label relevance 0–3 and extracted skills, with an adjudication protocol. Split by candidate and employer/template, reserve a time-separated test set, and compare explicit-skills, LSA, MiniLM, and stronger retrieval/reranking baselines. Learn nonnegative factor coefficients on training data with regularization; select hyperparameters only on validation data. Handle missingness explicitly and monitor subgroup error/coverage. Use isotonic/Platt calibration only for a separately defined binary outcome with sufficient labels; never calibrate a similarity index into hiring chance without outcomes. Version coefficients, taxonomy, encoder and annotation rubric together. Report held-out NDCG@k, precision/recall at declared threshold, confidence intervals and error slices. No learned calibration or scientific accuracy claim is shipped.

## Skill gap and learning policy

Missing skill set = catalog skills minus explicit profile skills. For each skill, calculate mean marginal required-skill coverage gain: sum over jobs requiring s of 1/(number of required skills in that job), divided by number of selected jobs. This is the precise counterfactual gain in the skills factor, not the overall score or a guaranteed learning outcome. Required demand fraction sets High (≥30%), Medium (>0), Low (preferred only). Sort by gain, mention frequency, then related-category foundation. The category heuristic is a weak learning-proximity signal, not a prerequisite graph or mastery estimate. Role filtering changes the denominator. No percentages are hard-coded.

## Bias and privacy

Names, contacts and university identifiers are excluded from selected semantic text; university prestige is never scored. Dates are removed before semantic matching, and overlapping intervals are merged for experience. No gender, nationality, religion or marital-status scoring exists. Yet names inside project prose, socioeconomic proxies, employer identity, educational access and language can remain. Employment gaps are not directly scored, but tenure itself can disadvantage nontraditional careers. The degree factor applies only to explicit non-optional requirements; equivalent-experience alternatives are conservatively excluded. No fairness certification is claimed. Counterfactual name-invariance unit tests cover only straightforward cases. Broader redaction and subgroup testing remain necessary.
