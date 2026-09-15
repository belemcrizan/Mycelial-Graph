# Engineering debt

Do not burn cycles here while P0 confirmatory evidence is missing.

- CLI unification of leftover V0 `docs/QUICKSTART.md` freeze language versus V1 CLI.
- `__version__` mismatch between `src/mycelial_graph/__init__.py` (0.2.0) and `pyproject.toml` (0.2.2).
- Packaging, dashboards, Kubernetes, extra databases: **not justified**.
- Live HTTP collector client: intentionally unimplemented.
