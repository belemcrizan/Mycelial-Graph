# Paper A submission package

**Status:** package prepared; OpenReview submission not executed (human authentication required).
**Scientific state:** `research/state.json` has `paper_a.submitted = false`.
**Receipt:** `paper/SUBMISSION_RECEIPT.json` (do not set `submitted: true` without an OpenReview ID).

## Venue policy (re-verified 2026-09-15)

Source: https://www.jmlr.org/tmlr/author-guide.html, https://jmlr.org/tmlr/editorial-policies.html, https://jmlr.org/tmlr/faq.html, https://jmlr.org/tmlr/submissions.html

| Rule | Current TMLR policy | Adaptation |
| --- | --- | --- |
| Review | Double-blind; author names hidden from reviewers | `paper/tmlr/paper.tex` uses the default (non-`preprint`) TMLR style and `\author{Anonymous authors}` |
| Template | Mandatory official LaTeX stylefile | Vendored from https://github.com/JmlrOrg/tmlr-style-file (do not edit layout) |
| Length | Any length; >12 pages may delay review | Manuscript is written to stay near that budget |
| Supplementary | Up to 100MB, PDF or ZIP, must be anonymized | `python paper/submission/build_anonymous_zip.py` |
| Preprints | Allowed on arXiv with identity | Do **not** put an identified URL in the TMLR PDF |
| License | CC BY 4.0 from submission | Compatible with Apache-2.0 code |
| LLM use | Allowed; first-page footnote required | Title `\thanks{...}` |
| Surveys | Not considered as of 2026-09-01 | Not a survey |
| OpenReview | https://openreview.net/group?id=TMLR | Human login required |
| Public DOI | Identifying public archival would expose identity during double-blind review | Prepare Zenodo metadata now; mint/link DOI only when policy permits |
| Anonymous git mirror | Preferred reviewer-accessible git host: https://anonymous.4open.science/ | Human account; not claimed as created in this environment |

## Files to upload

1. Anonymous PDF compiled from `paper/tmlr/paper.tex`.
2. Anonymous supplementary ZIP (`paper/submission/anonymous_supplement.zip`).
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

This environment cannot complete OpenReview login, CAPTCHA, legal attestation, conflict-of-interest confirmation, Action Editor recommendations, anonymous.4open.science account creation, or a Zenodo deposition. Those steps are specified, not faked.

After a real submission, fill `paper/SUBMISSION_RECEIPT.json` with venue, timestamp, submission ID, submitted artifact hash, anonymized artifact hash, and paper commit. Only then may `research/state.json` set `paper_a.submitted = true`.
