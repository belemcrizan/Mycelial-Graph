from __future__ import annotations

from dataclasses import dataclass
import math


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

    def __post_init__(self) -> None:
        if isinstance(self.cap, bool) or not math.isfinite(float(self.cap)) or self.cap < 0.0:
            raise ValueError("BudgetReservation.cap must be a finite non-negative number.")

    @property
    def remaining(self) -> float:
        return float(self.cap - self.spent - self.reserved)

    def can_afford(self, amount: float) -> bool:
        return amount >= 0.0 and amount <= self.remaining + 1e-9

    def sustainable_step_allowance(self, steps_remaining: int) -> float:
        denom = max(int(steps_remaining), 1)
        return max(0.0, self.remaining / float(denom))

    def reserve(self, amount: float) -> None:
        if isinstance(amount, bool) or not math.isfinite(float(amount)) or amount < 0:
            raise ValueError("Reservation amount must be a finite non-negative number.")
        if amount > self.remaining + 1e-9:
            self.overruns += 1
            raise ReservationError(
                f"Cannot reserve {amount}; remaining={self.remaining} cap={self.cap}."
            )
        self.reserved += amount

    def release(self, amount: float) -> None:
        if amount < 0 or amount > self.reserved + 1e-9:
            raise ReservationError("Release amount must be in [0, reserved].")
        self.reserved = max(0.0, self.reserved - amount)
        self.released += amount

    def commit(self, reserved_amount: float, actual: float) -> None:
        if isinstance(actual, bool) or not math.isfinite(float(actual)) or actual < 0:
            raise ValueError("Committed actual spend must be a finite non-negative number.")
        if reserved_amount < 0 or reserved_amount > self.reserved + 1e-9:
            raise ReservationError("Commit exceeds outstanding reservation.")
        self.reserved = max(0.0, self.reserved - reserved_amount)
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
