# Paper A submission package

**Status:** package prepared; OpenReview submission not executed (human authentication required).

## Venue policy (verified 2026-09-15)

Source: https://www.jmlr.org/tmlr/author-guide.html, https://jmlr.org/tmlr/editorial-policies.html, https://jmlr.org/tmlr/faq.html, https://jmlr.org/tmlr/submissions.html

| Rule | Current TMLR policy | Adaptation |
| --- | --- | --- |
| Review | Double-blind; author names hidden from reviewers | `paper/tmlr/paper.tex` uses the default (non-`preprint`) TMLR style |
| Template | Mandatory official LaTeX stylefile | Vendored from https://github.com/JmlrOrg/tmlr-style-file (do not edit layout) |
| Length | Any length; >12 pages may delay review | Manuscript is written to stay near that budget |
| Supplementary | Up to 100MB, PDF or ZIP, must be anonymized | `paper/submission/anonymous_supplement/` |
| Preprints | Allowed on arXiv with identity | Do **not** put an identified URL in the TMLR PDF |
| License | CC BY 4.0 from submission | Compatible with Apache-2.0 code |
| LLM use | Allowed; first-page footnote required | Title `\thanks{...}` |
| Surveys | Not considered as of 2026-09-01 | Not a survey |
| OpenReview | https://openreview.net/group?id=TMLR | Human login required |

## Scientific conflict vs the master prompt

The prompt assumed a V1 manuscript already existed. Repository inspection found only `docs/PAPER_OUTLINE.md`, a V2 placeholder. Paper A was therefore **written** as a submission blocker, not treated as already present.

## Files to upload

1. Anonymous PDF compiled from `paper/tmlr/paper.tex`.
2. Anonymous supplementary ZIP from `paper/submission/anonymous_supplement/` (build script below).
3. OpenReview fields: authors, conflicts, AE recommendations, IRB (N/A: no human subjects), funding, competing interests.

## Commands

```bash
cd paper/tmlr
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

```bash
python paper/submission/build_anonymous_zip.py
```

## Human boundary

This environment cannot complete OpenReview login, Action Editor recommendations, anonymous.4open.science account creation, or a Zenodo deposition. Those steps are specified, not faked.

After a real submission, record the OpenReview ID in `paper/SUBMISSION_RECEIPT.md`.
