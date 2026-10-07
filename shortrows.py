from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from .helpers import calculate_short_rows


@dataclass(frozen=True)
class ShortRowPlan:
    """
    German short-row back-neck shaping for a top-down raglan.

    Used in two ways:
    - to *preview* how many short-row rounds we'll have (for Option D)
    - to render human-readable short-row instructions later.

    Assumptions:
    - BOR = center back.
    - back_sts = stitches between the two back raglan markers.
    - shoulder sts are at neckline, before any short-row increases.
    """
    size: str
    gauge_rows_per_cm: float

    back_sts: int
    right_shoulder_sts: int
    left_shoulder_sts: int

    short_row_depth_cm: float = 5.0
    guard_sts_before_front_raglan: int = 2
    max_short_rows: int = 10  # max individual rows (not pairs)

    # Optional: pairs already decided elsewhere (e.g. Sweater, which needs the
    # count up front to size the initial cast-on split). When given, this is
    # used as-is instead of recomputing from back_sts/shoulder_sts, so the
    # turn positions rendered here always agree with whatever split math used
    # to decide stitch totals - the two must not diverge.
    precomputed_pairs: Optional[int] = None

    # ---------- basic props ----------

    @property
    def half_back_sts(self) -> int:
        """Stitches from BOR (center back) to each back raglan marker."""
        return self.back_sts // 2

    @property
    def _max_pairs(self) -> int:
        """
        Maximum number of short-row pairs, using the centralized calculation
        (or the precomputed value, if one was supplied).
        """
        if self.precomputed_pairs is not None:
            return self.precomputed_pairs

        sleeve_sts = min(self.right_shoulder_sts, self.left_shoulder_sts)
        individual_rows = calculate_short_rows(
            depth_cm=self.short_row_depth_cm,
            gauge_rows_per_cm=self.gauge_rows_per_cm,
            sleeve_sts=sleeve_sts,
            back_sts=self.back_sts,
            guard_sts=self.guard_sts_before_front_raglan,
            max_short_rows=self.max_short_rows,
        )
        return individual_rows // 2

    # ---------- spacing helpers ----------

    def _turn_positions_for_span(self, span_sts: int, max_pairs: int) -> List[int]:
        """Turn positions measured from the back raglan marker."""
        usable_total = span_sts - self.guard_sts_before_front_raglan
        if usable_total <= 0 or max_pairs <= 0:
            return []

        step_base = usable_total / (max_pairs + 1)
        turns: List[int] = []

        for i in range(1, max_pairs + 1):
            candidate = int(round(i * step_base))
            candidate = max(1, min(candidate, usable_total))
            turns.append(candidate)

        # strictly increasing
        result: List[int] = []
        last = 0
        for t in sorted(set(turns)):
            if t > last:
                result.append(t)
                last = t
        return result

    # ---------- per-shoulder turns ----------

    def right_shoulder_turns(self) -> List[int]:
        return self._turn_positions_for_span(self.right_shoulder_sts, self._max_pairs)

    def left_shoulder_turns(self) -> List[int]:
        return self._turn_positions_for_span(self.left_shoulder_sts, self._max_pairs)

    # Convenience: number of individual short rows (RS + WS, not pairs)
    @property
    def short_row_count(self) -> int:
        """
        Number of individual short rows (RS + WS rows, not RS/WS pairs).
        For example, 5 RS turns + 5 WS turns = 10 individual rows.
        """
        pairs = min(len(self.right_shoulder_turns()), len(self.left_shoulder_turns()))
        return pairs * 2  # individual rows, not pairs
