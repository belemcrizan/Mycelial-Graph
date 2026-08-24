# Contributing

Thank you for helping improve Mycelial Graph.

## Scientific integrity first

- Do not change a frozen protocol in place.
- Keep development, pilot, and confirmatory artifacts separate.
- Add a numbered amendment for changes after a freeze.
- Preserve negative and inconclusive results.
- Never remove seeds or method failures because they are unfavorable.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
mycelial-graph demo
```

Changes to scenario generation, randomness, recovery definitions, or statistical analysis require corresponding tests and documentation. New provider, UI, database, and orchestration features should target a later version unless they directly satisfy a measured V1 requirement.

