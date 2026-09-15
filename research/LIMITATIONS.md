# Limitations

First-class, not a footnote.

- Simulator assumptions (layered DAG, one shock, Gaussian/bounded local rewards in V1).
- Known topology in the current methods.
- Unknown structure not represented.
- Provider representativeness: none.
- External dataset bias and contamination if/when ingested.
- OPE support typically absent in public preference tables.
- Model-alias and cost drift for any future live work.
- Judge bias for quality proxies.
- No external reproduction.
- EQ-B effective-policy mismatch: Attribution of the V1 performance difference to hierarchical representation alone; effective policy scale was not equalized in the frozen comparison.
- Collector clock and path confounders.
- Execution DAG is not a causal DAG.
