# Literature Review (verified sources only)

**Search date:** 2026-08-31  
**Protocol:** `docs/LITERATURE_SEARCH_PROTOCOL.md`  
**This is not a systematic review.** Unverified memory citations were not added.

## Fungal / mycelial networks

| Source | Use | Evidence grade for MG claims |
|---|---|---|
| Fricker, Heaton, Jones, Boddy (2017). *The Mycelium as a Network*. Microbiology Spectrum. DOI [10.1128/microbiolspec.FUNK-0033-2017](https://doi.org/10.1128/microbiolspec.FUNK-0033-2017) | Architecture, flow–structure coupling, plasticity under patchy resources | B (review). Species mixed; not a proof of our controller |
| Bebber, Hynes, Darrah, Boddy, Fricker (2007). *Biological solutions to transport network design*. Proc. R. Soc. B. DOI [10.1098/rspb.2007.0459](https://doi.org/10.1098/rspb.2007.0459) PMID 17623638 | Decentralized transport, cords, robustness vs cost in **basidiomycete** cord-formers | A for *Phanerochaete velutina* experimental networks; C for MG abstraction |
| Fischer, Glass (2019). *Communicate and Fuse*. Front. Microbiol. DOI [10.3389/fmicb.2019.00619](https://doi.org/10.3389/fmicb.2019.00619) | Anastomosis, kind recognition, fusion genetics; primarily **Neurospora crassa** | A/B for N. crassa fusion; D if used as “merge dicts” |
| Harris (2008). *Branching of fungal hyphae*. Mycologia. DOI [10.3852/08-177](https://doi.org/10.3852/08-177) | Apical vs lateral branching | B; species-general review, not MG validation |
| Harris (2019). *Hyphal branching in filamentous fungi*. Dev. Biol. DOI [10.1016/j.ydbio.2019.02.012](https://doi.org/10.1016/j.ydbio.2019.02.012) | Updated branching cell biology | B |

**Physarum firewall.** Physarum polycephalum is a slime mold (Amoebozoa), not a fungus. It must not be cited as fungal validation. Alpha already states this; V2.1 keeps the firewall.

**Species-specificity.** Bebber et al. 2007 is cord-forming basidiomycetes at the soil–litter interface. Fischer & Glass 2019 is ascomycete cell-fusion genetics. Do not write “fungi do X” as if the clade were uniform.

## Value of computation / adaptive compute / routing

| Source | How Mycelial differs |
|---|---|
| Russell, Wefald (1991). *Principles of metareasoning*. Artificial Intelligence. DOI [10.1016/0004-3702(91)90015-C](https://doi.org/10.1016/0004-3702(91)90015-C) | VOC is the parent concept. MG must **measure calibration**, not rename MVC |
| Schuster et al. (2022). *Confident Adaptive Language Modeling* (CALM). NeurIPS. arXiv [2207.07061](https://arxiv.org/abs/2207.07061) DOI [10.52202/068431-1269](https://doi.org/10.52202/068431-1269) | Per-token early exit inside one model. MG is graph allocation over retrieval/tools/verify/routes under shocks |
| Ong et al. (2024/2025). *RouteLLM*. arXiv [2406.18665](https://arxiv.org/abs/2406.18665); ICLR 2025 PDF | Strong/weak **model** routing from preferences. MG’s iso-model track exists specifically so a RouteLLM-like win cannot be the only story |

## Positioning (rhetoric is insufficient)

- **vs RouteLLM:** if Mycelial only wins when model classes differ, claim discipline must say so. Iso-model is the firewall.  
- **vs CALM / TTC:** if Mycelial only skips verification like early-exit, it is TTC on a DAG, not a new object.  
- **vs compression:** compression is a baseline action, not the system.  
- **vs bandits:** Thompson and cost-sensitive linear scores are **implemented as adversaries** in V2.1. A Mycelial win requires beating them or documenting a region of advantage.

## Biological literature still incomplete

Read et al. on self-signalling/self-fusion was requested; it is **not** entered in `research/references.yaml` until a DOI/publisher page is attached in a later search pass. Same for Fricker, Bebber & Boddy “Mycelial networks: Structure and dynamics” as a separate bibliographic unit from the 2017 Spectrum chapter.

Forward/backward citation chaining of Fricker 2017 and Bebber 2007 remains open work (search protocol records the first pass only).
