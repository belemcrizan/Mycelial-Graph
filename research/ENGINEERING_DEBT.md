# Engineering debt

Do not burn cycles here while Paper A remains unsubmitted.

- CLI unification of leftover V0 `docs/QUICKSTART.md` freeze language versus V1 CLI.
- Packaging, dashboards, Kubernetes, extra databases: **not justified**.
- Live HTTP collector client: intentionally unimplemented.
- Original confirmatory wall-clock was not stored in `manifest.json`; CPU-hours were measured from per-trial `decision_cpu_seconds` (0.122).
- `__version__` is aligned to `pyproject.toml` (0.2.2). Line endings are normalized with `.gitattributes` (`eol=lf`).
