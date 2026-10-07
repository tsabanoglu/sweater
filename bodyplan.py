from __future__ import annotations

from typing import Optional, Literal, List, Dict
from dataclasses import dataclass
import math
from .helpers import _evenly_spaced_rows, _even, cm_to_rows, rows_to_cm


### Body plan

Fit = Literal["straight", "fitted", "loose"]
@dataclass(frozen=True)
class BodyPlan:
    """
    Plan hem shaping from underarm (separation) to hem.

    AUTO-to-target, mirroring SleevePlan: provide hem_circ_sts and increase
    rounds are spread evenly across length_rows via _evenly_spaced_rows.

    Conventions:
    - Each *increase round* adds `inc_per_round` stitches total, evenly spaced
      around the circumference (e.g. at the two underarm "seam" points).
    - `inc_per_round` defaults to 4, matching the raglan-line increment style
      used elsewhere in the pattern.
    """
    size: str
    body_total_sts: int
    hem_circ_sts: int
    length_rows: int
    gauge_rows_per_cm: float
    gauge_sts_per_cm: float
    fit: Fit = "straight"
    rib_multiple: int = 2
    dec_schedule_rows: Optional[List[bool]] = None  # reserved for future waist decreases
    inc_per_round: int = 4
    min_rows_between_incs: int = 4  # guardrail to avoid crowding
    hem_rib_rows: int = 0  # optional rib tail excluded from the shaping distribution

    @property
    def dec_count(self) -> int:
        return 0 if not self.dec_schedule_rows else len(self.dec_schedule_rows)

    def _auto_inc_count(self) -> int:
        need = max(0, self.hem_circ_sts - self.body_total_sts)
        return (need + self.inc_per_round - 1) // self.inc_per_round  # ceiling division

    @property
    def inc_count(self) -> int:
        return self._auto_inc_count()

    def _even_schedule(self, k: int) -> List[int]:
        """
        Return 1-based row indices for k increase rounds spread across usable length.
        Enforces minimal spacing via min_rows_between_incs when possible.
        """
        usable_rows = max(1, self.length_rows - self.hem_rib_rows)
        raw = _evenly_spaced_rows(usable_rows, k)
        if k <= 1 or self.min_rows_between_incs <= 1:
            return raw

        spaced: List[int] = []
        last = 0
        for r in raw:
            r_adj = r
            if last and r_adj - last < self.min_rows_between_incs:
                r_adj = min(usable_rows, last + self.min_rows_between_incs)
            spaced.append(r_adj)
            last = r_adj
        spaced = sorted(set([min(max(1, x), usable_rows) for x in spaced]))
        while len(spaced) > k:
            spaced.pop()
        return spaced

    def schedule_rows(self) -> List[bool]:
        """Boolean list of length `length_rows` where True marks an increase round."""
        sched = [False] * self.length_rows
        for r in self._even_schedule(self.inc_count):
            sched[r - 1] = True
        return sched

    def stitch_map_end(self) -> Dict[str, int]:
        k = self.inc_count
        hem = self.body_total_sts + k * self.inc_per_round
        return {
            "start_sts": self.body_total_sts,
            "inc_rounds": k,
            "hem_sts": hem,
        }

    def summary(self) -> str:
        sched = self.schedule_rows()
        m = self.stitch_map_end()
        return (
            f"[BodyPlan {self.size}] fit={self.fit}, length_rows={self.length_rows} | "
            f"start={m['start_sts']} sts -> hem={m['hem_sts']} sts "
            f"via {m['inc_rounds']} inc rounds (inc_per_round={self.inc_per_round}). "
            f"First 12 rows sched: "
            f"{''.join('I' if x else '.' for x in sched[:12])}"
        )
