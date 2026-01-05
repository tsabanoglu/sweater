from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict


# Reuse helper
from .helpers import _even, _evenly_spaced_rows

@dataclass(frozen=True)
class SleevePlan:
    """
    Plan sleeve shaping from armhole to cuff.

    Two modes:
    - AUTO-to-target: provide target_cuff_sts (preferred). Decrease rounds are
      spread across length_rows using an even schedule.
    - FIXED-INTERVAL: provide dec_every_rows (no target). Decreases occur every
      N rows and determine the final cuff stitches.

    Conventions:
    - Each *decrease round* removes `dec_per_round` stitches total (e.g., SSK + K2tog).
    - `dec_per_round` defaults to 2, i.e., one decrease on each "seam".
    - Rib alignment at cuff: final cuff stitches get forced to `rib_multiple`.
    """

    size: str
    start_sts: int  # from SeparatorPlan.sleeve_each
    length_rows: int   # sleeve length from separation to cuff
    gauge_rows_per_cm: float
    rib_multiple: int = 2

    # choose one of the two modes:
    target_cuff_sts: Optional[int] = None  # AUTO-to-target mode
    dec_every_rows: Optional[int] = None   # FIXED-INTERVAL mode

    # shaping controls
    dec_per_round: int = 2  # total sts decreased per decrease round
    min_rows_between_decs: int = 4 # guardrail to avoid crowding

    # Optional rib section at the end (not modeled in length_rows if you prefer):
    cuff_rib_rows: int = 0


    def _auto_dec_count(self) -> int:
        """
        How many decrease rounds are needed to reach target_cuff_sts?
        """

        if self.target_cuff_sts is None:
            return 0
        need = max (0, self.start_sts - self.target_cuff_sts)
        return (need + self.dec_per_round - 1) // self.dec_per_round # ceiling division
    
    def _fixed_interval_dec_count(self) -> int:
        """
        How many decrease rounds fit if dec_every_rows is specified?
        """

        if not self.dec_every_rows or self.dec_every_rows <= 0:
            return 0
        
        # Don’t place a dec on row 0; start at dec_every_rows, then every N rows
        # Fit within length_rows (excluding any rib tail if you treat it separately)
        usable_rows = max(0, self.length_rows - self.cuff_rib_rows)
        return usable_rows // self.dec_every_rows
    
    def _even_schedule(self, k: int) -> List[int]:
        """
        Return 1-based row indices for k decrease rounds spread across usable length.
        Enforces minimal spacing via min_rows_between_decs when possible.
        """
        usable_rows = max(1, self.length_rows - self.cuff_rib_rows)
        raw = _evenly_spaced_rows(usable_rows, k)
        if k <= 1 or self.min_rows_between_decs <= 1:
            return raw

        # Enforce a minimum spacing by nudging forward when needed
        spaced: List[int] = []
        last = 0
        for r in raw:
            r_adj = r
            if last and r_adj - last < self.min_rows_between_decs:
                r_adj = min(usable_rows, last + self.min_rows_between_decs)
            spaced.append(r_adj)
            last = r_adj
        # Ensure strictly increasing and inside bounds
        spaced = sorted(set([min(max(1, x), usable_rows) for x in spaced]))
        while len(spaced) > k:
            spaced.pop()  # trim duplicates if spacing collapsed
        return spaced

    def schedule_rows(self) -> List[bool]:
        """
        Boolean list of length `length_rows` where True marks a decrease round.
        - AUTO mode spreads k dec rounds evenly.
        - FIXED-INTERVAL marks every Nth row.
        """
        usable_rows = max(1, self.length_rows - self.cuff_rib_rows)
        sched = [False] * self.length_rows

        if self.target_cuff_sts is not None:
            k = self._auto_dec_count()
            for r in self._even_schedule(k):
                sched[r - 1] = True  # 1-based -> 0-based
            return sched

        if self.dec_every_rows and self.dec_every_rows > 0:
            r = self.dec_every_rows
            i = r
            while i <= usable_rows:
                sched[i - 1] = True
                i += self.dec_every_rows
            return sched

        # No shaping
        return sched

    @property
    def dec_count(self) -> int:
        if self.target_cuff_sts is not None:
            return self._auto_dec_count()
        return self._fixed_interval_dec_count()

    def stitch_map_end(self) -> Dict[str, int]:
        """
        Returns stitch counts at the end of the sleeve (before rib, unless included in length).
        Applies rib_multiple to cuff stitch count.
        Keys:
          - start_sts
          - dec_rounds
          - cuff_sts (rounded to rib_multiple, kept >= 0 and even-friendly)
        """
        k = self.dec_count
        cuff = max(0, self.start_sts - k * self.dec_per_round)
        # Align cuff stitches to rib_multiple for neat ribbing:
        if self.rib_multiple > 1:
            cuff = cuff - (cuff % self.rib_multiple)
        cuff = max(0, cuff)
        cuff = _even(cuff)
        return {
            "start_sts": self.start_sts,
            "dec_rounds": k,
            "cuff_sts": cuff,
        }

    def summary(self) -> str:
        sched = self.schedule_rows()
        m = self.stitch_map_end()
        usable_rows = max(1, self.length_rows - self.cuff_rib_rows)
        mode = "AUTO→target" if self.target_cuff_sts is not None else (
            f"FIXED every {self.dec_every_rows} rows" if self.dec_every_rows else "NO SHAPING"
        )
        return (
            f"[SleevePlan {self.size}] mode={mode}, length_rows={self.length_rows} "
            f"(usable={usable_rows}, rib_tail={self.cuff_rib_rows}) | "
            f"start={m['start_sts']} sts → cuff={m['cuff_sts']} sts "
            f"via {m['dec_rounds']} dec rounds "
            f"(dec_per_round={self.dec_per_round}). "
            f"First 12 rows sched: "
            f"{''.join('D' if x else '.' for x in sched[:12])}"
        )