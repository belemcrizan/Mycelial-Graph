# Adapters

Implementations live in `src/mycelial_graph/external/adapters.py`.

Malformed rows return `{ok: false, errors: [...]}` and are never dropped silently.
