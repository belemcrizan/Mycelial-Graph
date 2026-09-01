from __future__ import annotations

from dataclasses import dataclass


class ReservationError(RuntimeError):
    """Raised when an action would violate a hard remaining budget."""


@dataclass
class BudgetReservation:
    """Pre-action reserve / spend / release accounting.

    Hard budgets must not be silently exceeded. A planned action whose
    reserved upper bound exceeds remaining capacity is rejected.
    """

    cap: float
    reserved: float = 0.0
    spent: float = 0.0
    released: float = 0.0
    overruns: int = 0

    @property
    def remaining(self) -> float:
        return float(self.cap - self.spent - self.reserved)

    def reserve(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Reservation amount must be non-negative.")
        if amount > self.remaining + 1e-9:
            self.overruns += 1
            raise ReservationError(
                f"Cannot reserve {amount}; remaining={self.remaining} cap={self.cap}."
            )
        self.reserved += amount

    def commit(self, reserved_amount: float, actual: float) -> None:
        if reserved_amount > self.reserved + 1e-9:
            raise ReservationError("Commit exceeds outstanding reservation.")
        self.reserved -= reserved_amount
        self.spent += actual
        unused = reserved_amount - actual
        if unused > 0:
            self.released += unused
        elif unused < -1e-9:
            self.overruns += 1

    def to_dict(self) -> dict[str, float | int]:
        return {
            "cap": self.cap,
            "reserved": self.reserved,
            "spent": self.spent,
            "released": self.released,
            "remaining": self.remaining,
            "overruns": self.overruns,
        }
