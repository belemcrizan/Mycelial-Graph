"""Scientific governance helpers that do not alter frozen V1 meaning."""

from .freeze import bind_run_contract
from .ledger import append_entry

__all__ = ["bind_run_contract", "append_entry"]
