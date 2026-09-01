# V2 Failure Modes

These are expected ways the idea can fail. Tests and reports should make them visible rather than optimizing them away.

| Mode | Symptom | Alpha control |
|---|---|---|
| Premature pruning | Quality drop after one noisy failure | Persistence window + min evidence |
| Runaway reinforcement | One route absorbs all budget | G caps, decay, exploration floor |
| Resource starvation | A viable class never tried | Floor budget / G_min |
| Exploration explosion | Router tokens dominate | Per-candidate router cost in ledger |
| Loop explosion | Anastomosis V2.1 | Disabled in alpha |
| Negative transfer | Shared state contaminates | Anastomosis off |
| Hidden router overhead | Fake token savings | Ledger + audit command |
| Provider lock-in | Cord on a shocked vendor | Price/quality shocks |
| Price overfitting | Wins only on one price path | STATIC vs PRICE_SHOCK |
| Quality collapse | Tokens win, Q fails non-inferiority | Ordered gates |
| Catastrophic adaptation | Post-shock Q never recovers | Recovery metrics |
| Oscillation / thrashing | High route churn | Hysteresis, switch penalty, cooldown |
| Silent safety drop | Skip verify on hard tasks | Hard constraints |

Reports must be allowed to say REFUTED or INCONCLUSIVE. Absence of a V2 win in development is not a bug.
