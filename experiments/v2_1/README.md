# MG-EXP-V2.1

Additive Evidence Bridge. Does not replace `experiments/v2/`.

```powershell
mycelial-graph v2-validate --config experiments/v2_1/config.development.yaml
mycelial-graph voc-bench --config experiments/v2_1/config.development.yaml
mycelial-graph real-smoke
```

The real-smoke track uses an isolated workspace and an autonomous read/test/edit loop. `apply_fix=True` is gone. Oracle sources remain on the task object for evaluation metadata only.
