# Collector

Instrument version: `MG-COLLECTOR-0.1.0`.

```text
mycelial-graph collect --dry-run --max-cost 0 --max-requests 1 --max-duration 1
```

Defaults are conservative. Live HTTP is **not implemented**. `--authorize-spend` is required before any future live path.

Treat local network, clock, and retries as confounders. A latency spike is not provider degradation.
