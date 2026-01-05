from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ShortRowPlan:
    """
    German short-row back-neck shaping for a top-down raglan.

    Used in two ways:
    - to *preview* how many short-row rounds we’ll have (for Option D)
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

    # ---------- basic props ----------

    @property
    def half_back_sts(self) -> int:
        """Stitches from BOR (center back) to each back raglan marker."""
        return self.back_sts // 2

    @property
    def short_row_depth_rows(self) -> int:
        """Total vertical depth in rows (forced even: RS+WS pairs)."""
        rows = int(round(self.short_row_depth_cm * self.gauge_rows_per_cm))
        if rows % 2 == 1:
            rows -= 1
        return max(rows, 2)

    @property
    def max_rounds_by_depth(self) -> int:
        """Max RS/WS short-row pairs allowed by vertical depth."""
        return self.short_row_depth_rows // 2

    # ---------- spacing helpers ----------

    def _max_rounds_for_span(self, span_sts: int) -> int:
        """
        How many short-row rounds can we reasonably fit into this shoulder span
        (back raglan → front raglan), without turns being 1 st apart.
        """
        usable_total = span_sts - self.guard_sts_before_front_raglan
        if usable_total <= 2:
            return 0

        max_rounds_by_stitches = usable_total // 2  # ~2 sts per turn minimum
        n = min(self.max_rounds_by_depth, max_rounds_by_stitches)
        return max(n, 1)

    def _turn_positions_for_span(self, span_sts: int) -> List[int]:
        """Turn positions measured from the back raglan marker."""
        usable_total = span_sts - self.guard_sts_before_front_raglan
        if usable_total <= 0:
            return []

        rounds = self._max_rounds_for_span(span_sts)
        if rounds <= 0:
            return []

        step_base = usable_total / (rounds + 1)
        turns: List[int] = []

        for i in range(1, rounds + 1):
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
        return self._turn_positions_for_span(self.right_shoulder_sts)

    def left_shoulder_turns(self) -> List[int]:
        return self._turn_positions_for_span(self.left_shoulder_sts)

    # Convenience: number of short-row rounds we’ll actually do
    @property
    def short_row_rounds(self) -> int:
        # one RS turn per right_turns entry, one WS per left
        return min(len(self.right_shoulder_turns()), len(self.left_shoulder_turns()))
