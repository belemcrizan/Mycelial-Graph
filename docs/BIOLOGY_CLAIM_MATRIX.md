# Biology claim matrix

Physarum is **not** a fungus. Separate slime-mold-inspired transport if ever used.

| Biological observation | Species / group | Evidence | Computational abstraction | Grade | Implemented in V2.0-alpha? | V2.1? | Supported as biology? |
|---|---|---|---|---|---|---|---|
| Mycelium as flow–structure network | Mixed; review | Fricker et al. 2017 | Execution DAG + conductance | B | Partial (G update) | Same | Inspiration only |
| Transport efficiency/robustness/cost | Cord-forming basidiomycetes | Bebber et al. 2007 | Prune + reinforce corridors | A (organism), C (MG) | Yes (flags) | Same | Do not claim equivalence |
| Hyphal branching apical/lateral | Filamentous fungi (review) | Harris 2008/2019 | Dynamic extra trajectories | B | **No** (alias) | Deferred | No |
| Fusion / kind recognition | N. crassa-centric | Fischer & Glass 2019 | Compatibility-gated merge | A/B | **No** (disabled) | Deferred | No |
| Nutrient translocation | Network fungi (review) | Fricker et al. 2017 | Convex budget mix | C | Yes | Same | Metaphor unless flow conservation on F_ij is tested |
| Retraction of low-yield hyphae | General / cords | B/C | Persistence pruning | C | Yes | Same | Inspiration |
| Computational vegetative incompatibility | — | — | Fusion rejection | D | No | Deferred | Metaphor only |

Never promote C/D to A in prose.
