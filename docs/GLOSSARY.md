# Glossary

| Term | Plain meaning | Technical meaning |
| --- | --- | --- |
| AI execution graph | The available ways an AI task can be completed | Typed directed acyclic graph of execution components |
| Edge | A connection between two choices | Directed transition `(u, v)` with local state |
| Conductance | How attractive a connection currently is | Bounded scalar `g_e` used in local softmax routing |
| Temporal decay | Old confidence gradually fades | Lazy multiplication by `(1 - lambda)^delta` |
| Local feedback | A connection learns only from what happened there | Edge observation with quality, latency, cost, failure, and load |
| Basal exploration | Occasional deliberate testing of alternatives | Separately logged uniform choice with probability `p_expl` |
| Hard policy | A rule optimization cannot override | Pre-routing feasibility filter |
| Sparse shock | A sudden problem in a small part of the system | Localized change affecting one or few graph components |
| Structural reuse | Keeping useful knowledge about unaffected routes | Reduced post-shock relearning associated with shared unaffected edges |
| SRC | Feedback needed for stable recovery | Sample Recovery Cost under a sustained criterion |
| CPST | Cost of useful work | Cost per Successful Task |
| SER | Unnecessary rechecking of healthy structure | Structural Re-exploration Rate |
| Right-censored | Recovery was not observed in time | Event time exceeds the observation horizon and is not replaced by the bound |
| Frozen trial | The same world used for fair comparison | Pre-generated potential outcomes, schedule, seed, and digest |
| Oracle | Perfect descriptive reference | Best path under known current expected utility; not deployable |

