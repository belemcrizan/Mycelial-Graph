from __future__ import annotations

import hashlib

import numpy as np


def derive_seed(master_seed: int, namespace: str) -> int:
    payload = f"mycelial-graph-v1:{master_seed}:{namespace}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def create_rng(master_seed: int, namespace: str) -> np.random.Generator:
    return np.random.default_rng(derive_seed(master_seed, namespace))

