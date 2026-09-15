# External validation layer

Track C. Isolated from MG-EXP-V1.

No raw third-party corpora are stored in this repository.

```text
Synthetic (Layer A)
  -> real-trace replay (Layer B)
    -> bounded live (Layer C)
```

Paid provider calls are forbidden unless the operator passes collector safety flags. The collector defaults to dry-run and does not open a network client in this version.
