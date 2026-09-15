# Anonymization (TMLR double-blind)

Verified 2026-09-15 against TMLR author guide and FAQ.

Remove from the submission PDF and supplementary ZIP:

- author name (Crizan Belem Ribeiro);
- email;
- personal GitHub identity (`belemcrizan`);
- repository URL;
- acknowledgements that identify the author;
- institution if identifying;
- draft-only marks;
- PDF properties / creator metadata if they contain a username.

Do not anonymize scientific provenance that reviewers need:

- protocol ID `MG-EXP-V1`;
- freeze hashes;
- seed counts and population names (`development` / `pilot` / `confirmatory`);
- confirmatory result state `REFUTED`;
- CPU-hour measurement;
- claim-boundary language.

Anonymous mirror: https://anonymous.4open.science/ is the preferred reviewer-accessible git mirror **if** an account can be created without putting an identified GitHub URL in the PDF. This step requires a human login. Until then, upload the anonymized ZIP as TMLR supplementary material. Record the mirror URL and commit only in the non-blinded receipt after it exists; do not put an identified GitHub URL in the PDF.

Public DOI: prepare a Zenodo deposition after the TMLR PDF is accepted **or** use an embargoed/anonymous deposition that is not linked from the blinded PDF. Do not violate double-blind review merely to satisfy a literal URL.

Identified preprint (optional, not linked from the submission): compile `paper.tex` with `\usepackage[preprint]{tmlr}` and a real `\author{...}` **after** deciding that an arXiv posting is desired. TMLR allows identified preprints; reviewers are asked not to search for them.
