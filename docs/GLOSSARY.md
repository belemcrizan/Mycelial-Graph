# Glossary

**Agent** - A routing method evaluated in the benchmark; not necessarily an LLM agent.

**Conductance** - Adaptive numeric state associated with a connection. Higher conductance increases selection probability in the Mycelial policy.

**Dynamic regret** - Cumulative difference between the expected utility of the time-specific oracle and the selected paths.

**Edge interaction** - Behavior specific to one directed source-target connection.

**Immutable scenario** - A frozen graph, shock, optimum, and table of potential outcomes shared by every method.

**Negative transfer** - Damage caused by sharing information across components when the underlying effect is actually specific.

**Oracle** - An unattainable reference that knows expected utilities. It validates the simulator and defines regret; it is not a competing deployable method.

**Partial pooling** - Sharing some learned state through nodes while retaining edge-specific residual state.

**Restricted recovery time (RRT)** - `min(recovery_time, post_shock_horizon)` for an individual trial.

**Restricted mean survival time (RMST)** - Group-level mean time without the recovery event, restricted to a fixed horizon. With only administrative censoring at that horizon, mean RRT is its direct estimate.

**rho** - Controlled fraction of squared shock magnitude assigned to the shared node component.

**Semi-bandit feedback** - A composite path is selected, and local outcomes are observed for traversed components.

**Structural reuse** - Retaining useful learned state on unaffected or shared parts of the graph after a local change.

