# Paper A submission checklist

Every item is `PASS`, `FAIL`, `NOT_APPLICABLE`, or `HUMAN_BOUNDARY`.
Canonical state: `research/state.json`. Receipt: `paper/SUBMISSION_RECEIPT.json`.

| Item | Status | Evidence |
| --- | --- | --- |
| README stale confirmatory phrases absent | PASS | `tests/test_scientific_state.py`; claim-audit scientific_state |
| Canonical scientific state file | PASS | `research/state.json` |
| CPU metrics consistent | PASS | sealed decision CPU 437.59375 s = 0.122 h in `research/runtime.json`; README/paper agree |
| Headline names frozen mechanism | PASS | README + paper abstract |
| EQ-B in Honest Status | PASS | README confirmatory evidence section |
| Hierarchy-only attribution unsupported | PASS | README, C15, CLAIM_MAP A-ATTR, paper threats |
| Moratorium exits only on Paper A submission | PASS | `V1_CONFIRMATORY_MORATORIUM.md`; `paper_a.submitted=false` ⇒ `moratorium.active=true` |
| Commands split active vs frozen | PASS | README Commands |
| V0/V1 wording not causal | PASS | README What changed from V0 |
| CRLF / frozen-hash regression | PASS | `tests/test_scientific_state.py` |
| Pinned dependencies used in CI | PASS | `.github/workflows/ci.yml` installs `requirements.lock.txt` |
| TMLR policy re-verified 2026-09-15 | PASS | `paper/SUBMISSION.md` |
| Manuscript anonymized (source) | PASS | `\author{Anonymous authors}`; no Crizan/belemcrizan in `paper.tex` |
| Anonymous supplementary ZIP | PASS | `paper/submission/anonymous_supplement.zip` SHA-256 `f4cc8bd9e08183316dcd244c6cbf4607d8372ad6d48f4517c6b83344cda3ecb1` (761222 bytes) |
| Default verification command | PASS | `python reproduce_confirmatory.py` |
| Full reproduction command | PASS | `python reproduce_confirmatory.py --full` → `outputs/confirmatory-full` |
| Full replay result match | PASS | primary 0.42112797022616655, state REFUTED, n=1940 |
| Full replay wall-clock | PASS | 403.8 s (4 workers) |
| Full replay decision CPU | PASS | 967.953125 s = 0.269 CPU-h (distinct from sealed 0.122) |
| Seal hashes | PASS | sealed artifacts unchanged |
| Unit tests | PASS | 111 tests |
| V1 integrity / freeze / claim / state audits | PASS | unittest + claim-audit + audit_v1_readiness GO |
| Compiled anonymous PDF | HUMAN_BOUNDARY | `pdflatex` not available in this environment; compile `paper/tmlr/paper.tex` locally |
| PDF metadata scrub | HUMAN_BOUNDARY | after `pdflatex`, check Properties for username |
| anonymous.4open.science mirror | HUMAN_BOUNDARY | requires human account; do not put identified GitHub URL in PDF |
| OpenReview login / CAPTCHA | HUMAN_BOUNDARY | https://openreview.net/group?id=TMLR |
| OpenReview COI / AE / IRB / funding | HUMAN_BOUNDARY | author-only attestation |
| Record submission ID | HUMAN_BOUNDARY | fill `paper/SUBMISSION_RECEIPT.json` only after platform confirms |
| Public Zenodo DOI | NOT_APPLICABLE | delayed until double-blind policy permits |
| Equalization-audit freeze gate | NOT_APPLICABLE | post-submission only |
| Paper B / repo split | NOT_APPLICABLE | post-submission only |

## Human remaining actions

1. Compile `paper/tmlr/paper.tex` with the official TMLR stylefile (`pdflatex` / `bibtex` / `pdflatex` ×2).
2. Inspect PDF properties and page 1 for identity leaks.
3. Log in to OpenReview (TMLR group), complete author profiles, conflicts, AE recommendations, IRB (N/A), funding, competing interests.
4. Upload anonymous PDF + `paper/submission/anonymous_supplement.zip`.
5. Optionally create an anonymous.4open.science mirror of the same commit; do not link an identified repo from the PDF.
6. After OpenReview shows a submission ID, record it in `paper/SUBMISSION_RECEIPT.json` and set `research/state.json` `paper_a.submitted=true`.

Until step 6, `SUBMISSION STATUS = NOT_SUBMITTED`.
