# Failure modes

The V1 artifact validator handles data integrity failures. Most runtime phenomena below require separate experiments and are not claimed as mitigated.

| Failure mode | Detection / experiment | Metric | Mitigation or containment | Evidence / limitation | Priority |
|---|---|---|---|---|---|
| False shared cause / negative transfer | Frozen rho=0 control; future misspecified hierarchy | NI bound, excess RRT/regret | Do not promote without NI; adaptive gate is future work | Confirmatory evidence pending | P0/P1 |
| Stale node / edge state | Repeated/regime-reversal shocks | Belief error, recovery, forgetting | Existing decay; sweep without altering V1 | Synthetic future design | P2 |
| Oscillation | Alternating disturbances | Route switches, adaptation debt | Hysteresis candidate requires ablation | PLANNED | P2 |
| Overexploration / underexploration | Matched exploration sweep | Regret, recovery, probes | Frozen exploration in V1 | Generality unvalidated | P2 |
| Cascading reroutes | Capacity-sensitive graph | Cascade size, recovery, tail latency | Quarantine/probe only after design | PLANNED | P3 |
| Budget exhaustion | V2 ledger invariants | Spend/cap and failure rate | Existing separate V2 budget accounting | No real spend validation | P3 |
| Policy starvation | All candidates forbidden | Zero allowed-route rate | Hard filter and abstention require runtime protocol | PLANNED | P3 |
| Delayed feedback instability | Delay/missingness grid | Credit errors, regret | Timestamped feedback contract | PLANNED | P2 |
| CPD false positive / negative | Detector/reset comparison | Alarm rate, detection delay | Detector-specific tuning on development only | PLANNED | P2 |
| Incorrect structural assumptions | Misgrouped nodes | Negative transfer, calibration | Abstain from sharing when unjustified | PLANNED | P2 |
| Reward poisoning / telemetry poisoning | Controlled malicious observations | Harm amplification, selective risk | Robust estimation and quarantine experiments | PLANNED | P2 |
| Method exception / timeout | Injected exception | Failure count/type, missing observation population | Preserve diagnostic; suspend inference; no invented RRT | UNIT-TESTED; complete failure estimand pending | P0 |
| Missing pair / duplicate method | Delete/duplicate artifact | Expected vs actual population | Reject before statistics | UNIT-TESTED | P0 |
| Trace/raw corruption | Byte/hash mismatch | Invalid artifacts | Reject analysis and resume | UNIT-TESTED | P0 |
| Phase leakage / seed reuse | Relabel development; overlap populations | Provenance and seed mismatch | Reject; require committed confirmatory freeze | UNIT-TESTED | P0 |
| Post-result tuning / modified report | Seal verification / source digest | Hash mismatch | Preserve original; version any reanalysis | UNIT-TESTED | P0 |
| Recovery floor / ceiling | Pilot distribution and censoring | Fraction at earliest event / tau, paired SD | No automatic N with zero variance; amendment before redesign | Pilot check required | P0 |
