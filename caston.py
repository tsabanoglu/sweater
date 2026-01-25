# sweater/caston.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from .constants import NECK_SIZES
from .helpers import _split_neck, _round_to_multiple
from .shortrows import ShortRowPlan


@dataclass(frozen=True)
class CastOnPlan:
    """
    Compute neck cast-on stitches and the initial section split.

    - `neck_cm` / NECK_SIZES describe the *final* neck after short-row raglan incs.
    - We first compute a target split from that final neck.
    - Then, if short rows are used, we 'rewind' the back and sleeves by the amount
      they will grow during the short-row section, keeping the front fixed.
    - The *initial* split is used for cast-on and marker placement.
    """
    size: str
    gauge_sts_per_cm: float              # e.g. 22 / 10 => 2.2cd 
    rib_multiple: int = 2                # 1 (none), 2 (1x1), 4 (2x2)
    raglan_lines: int = 4
    raglan_line_sts: int = 2
    neck_ratio: Tuple[int, int, int, int] = (3, 3, 2, 2)  # front, back, sleeveL, sleeveR
    min_cast_on: int = 60
    custom_neck_cm: Optional[float] = None

    # short-row related knobs
    gauge_rows_per_cm: float = 0.0
    use_short_rows: bool = False
    short_row_depth_cm: float = 5.0
    guard_sts_before_front_raglan: int = 2

    # ---- basic neck size ----
    @property
    def neck_cm(self) -> float:
        return self.custom_neck_cm or NECK_SIZES.get(self.size, 38.0)

    def _final_neck_sts(self) -> int:
        """
        'Final' neck stitch count corresponding to neck_cm,
        i.e. after short-row raglan increases have happened.
        """
        raw = self.neck_cm * self.gauge_sts_per_cm
        sts = _round_to_multiple(int(round(raw)), max(1, self.rib_multiple))
        if sts < self.min_cast_on:
            sts = self.min_cast_on
        if sts % 2:
            sts += 1
        return sts

    # ---- core computation: initial split + cast-on ----
    def _compute_initial_split_and_caston(self) -> Tuple[Dict[str, int], int]:
        """
        Returns (initial_split, cast_on_sts).

        - initial_split is the distribution at cast-on (before SR incs),
          used for marker placement.
        - cast_on_sts is the number of sts to cast on for the neck.

        When short rows are used:
        - Cast-on total stays the same (based on neck circumference)
        - FINAL split (after SR increases) follows the target ratio (e.g., 3:3:2:2)
        - INITIAL split compensates: front gets MORE stitches, back/sleeves get FEWER
        - After R short row rounds, the split evens out to the target ratio
        """
        final_neck = self._final_neck_sts()

        # 1) Calculate 'final' split (after SR incs) based on target ratio
        #    This represents the stitch distribution we want AFTER short rows complete
        final_split = _split_neck(
            final_neck,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
            ratio=self.neck_ratio,
        )
        F_final = final_split["front"]
        B_final = final_split["back"]
        SL_final = final_split["sleeve_L"]
        SR_final = final_split["sleeve_R"]

        # 2) If no short rows, initial == final, cast-on == final_neck
        if not (self.use_short_rows and self.gauge_rows_per_cm > 0 and self.short_row_depth_cm > 0):
            return final_split, final_neck

        # 3) Calculate R (number of short row rounds) dynamically from depth
        # Start with depth-based calculation
        R_from_depth = round(self.short_row_depth_cm * self.gauge_rows_per_cm / 2)

        # Cap at maximum (similar to real patterns which use ~4-5 rounds)
        MAX_SHORT_ROW_ROUNDS = 5
        R = min(R_from_depth, MAX_SHORT_ROW_ROUNDS)
        R = max(R, 1)  # At least 1 round if short rows enabled

        # Important: Short rows add 4R stitches via raglan increases
        # So the FINAL total (after SR) will be final_neck + 4R
        # The final split should be calculated based on this larger total
        final_total_after_sr = final_neck + 4 * R

        # Recalculate FINAL split based on the total after short rows
        final_split_after_sr = _split_neck(
            final_total_after_sr,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
            ratio=self.neck_ratio,
        )
        F_final_after_sr = final_split_after_sr["front"]
        B_final_after_sr = final_split_after_sr["back"]
        SL_final_after_sr = final_split_after_sr["sleeve_L"]
        SR_final_after_sr = final_split_after_sr["sleeve_R"]

        # Verify R fits within the sleeve span (using final counts after SR)
        sleeve_span = min(SL_final_after_sr, SR_final_after_sr) - self.guard_sts_before_front_raglan
        if sleeve_span > 0:
            # Roughly 3 sts per turn (pattern uses this spacing)
            max_R_from_sleeve = max(1, sleeve_span // 3)
            if R > max_R_from_sleeve:
                # Recalculate with adjusted R
                R = max_R_from_sleeve
                final_total_after_sr = final_neck + 4 * R
                final_split_after_sr = _split_neck(
                    final_total_after_sr,
                    raglan_lines=self.raglan_lines,
                    raglan_line_sts=self.raglan_line_sts,
                    ratio=self.neck_ratio,
                )
                F_final_after_sr = final_split_after_sr["front"]
                B_final_after_sr = final_split_after_sr["back"]
                SL_final_after_sr = final_split_after_sr["sleeve_L"]
                SR_final_after_sr = final_split_after_sr["sleeve_R"]

        # Safety: ensure we don't go below minimums for initial split
        MIN_BACK = 4
        MIN_SLEEVE = 4

        # Check if R would make back/sleeves too small initially
        max_R_back = (B_final_after_sr - MIN_BACK) // 2
        max_R_sleeve = min(SL_final_after_sr, SR_final_after_sr) - MIN_SLEEVE
        R = max(1, min(R, max_R_back, max_R_sleeve))

        # Recalculate one more time with the final R
        final_total_after_sr = final_neck + 4 * R
        final_split_after_sr = _split_neck(
            final_total_after_sr,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
            ratio=self.neck_ratio,
        )

        # 4) Calculate INITIAL split by working backwards from final split
        # Short rows add: 2R to back, R to each sleeve, 0 to front
        # So initial = final - gains
        initial_split = {
            "front": final_split_after_sr["front"],          # Front unchanged during SR
            "back": final_split_after_sr["back"] - 2 * R,    # Back starts smaller
            "sleeve_L": final_split_after_sr["sleeve_L"] - R, # Sleeves start smaller
            "sleeve_R": final_split_after_sr["sleeve_R"] - R,
        }

        # 5) Cast-on stays constant (neck circumference unchanged)
        cast_on_sts = final_neck

        return initial_split, cast_on_sts

    # ---- public API ----
    @property
    def neck_sts(self) -> int:
        """Cast-on stitches for the neck."""
        _, co = self._compute_initial_split_and_caston()
        return co

    def split_map(self) -> Dict[str, int]:
        """
        Initial split (at cast-on) for placing markers:
        front/back/sleeve_L/sleeve_R, excluding raglan-line stitches.
        """
        split, _ = self._compute_initial_split_and_caston()
        return split

    def short_row_rounds(self) -> int:
        """
        Number of short row rounds (RS/WS pairs) that will be worked.
        Returns 0 if short rows are not enabled.
        """
        if not (self.use_short_rows and self.gauge_rows_per_cm > 0 and self.short_row_depth_cm > 0):
            return 0

        # Use the same logic as _compute_initial_split_and_caston to get R
        # This is a bit inefficient (recalculates), but ensures consistency
        split, _ = self._compute_initial_split_and_caston()

        # Calculate R from the split
        final_neck = self._final_neck_sts()
        R_from_depth = round(self.short_row_depth_cm * self.gauge_rows_per_cm / 2)
        MAX_SHORT_ROW_ROUNDS = 5
        R = min(R_from_depth, MAX_SHORT_ROW_ROUNDS)
        R = max(R, 1)

        # Iteratively check constraints
        final_total_after_sr = final_neck + 4 * R
        final_split_after_sr = _split_neck(
            final_total_after_sr,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
            ratio=self.neck_ratio,
        )

        sleeve_span = min(final_split_after_sr["sleeve_L"], final_split_after_sr["sleeve_R"]) - self.guard_sts_before_front_raglan
        if sleeve_span > 0:
            max_R_from_sleeve = max(1, sleeve_span // 3)
            R = min(R, max_R_from_sleeve)

        MIN_BACK = 4
        MIN_SLEEVE = 4

        # Recalculate with final R
        final_total_after_sr = final_neck + 4 * R
        final_split_after_sr = _split_neck(
            final_total_after_sr,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
            ratio=self.neck_ratio,
        )

        max_R_back = (final_split_after_sr["back"] - MIN_BACK) // 2
        max_R_sleeve = min(final_split_after_sr["sleeve_L"], final_split_after_sr["sleeve_R"]) - MIN_SLEEVE
        R = max(1, min(R, max_R_back, max_R_sleeve))

        return R

    def marker_segments(self) -> List[Tuple[str, int]]:
        """
        Neck CO order with stitch counts, including raglan lines in between segments:
        back_left, RL, sleeve_L, RL, front, RL, sleeve_R, RL, back_right
        """
        split = self.split_map()
        back_left = split["back"] // 2
        back_right = split["back"] - back_left
        rl = self.raglan_line_sts
        return [
            ("back_left", back_left),
            ("raglan", rl),
            ("sleeve_left", split["sleeve_L"]),
            ("raglan", rl),
            ("front", split["front"]),
            ("raglan", rl),
            ("sleeve_right", split["sleeve_R"]),
            ("raglan", rl),
            ("back_right", back_right),
        ]

    def cast_on_text(self, rib_label: str = "1x1") -> str:
        split = self.split_map()
        back_left = split["back"] // 2
        back_right = split["back"] - back_left
        rl = self.raglan_line_sts

        lines = [
            f"Cast on {self.neck_sts} sts. Work {rib_label} rib for collar (optional).",
            "Place BOR (beginning of round) marker, then place markers as follows:",
            f"  - Back left: {back_left} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Sleeve left: {split['sleeve_L']} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Front: {split['front']} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Sleeve right: {split['sleeve_R']} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Back right: {back_right} sts (to BOR)",
            "Join to work in the round. Raglan stitches are worked straight between markers.",
        ]
        return "\n".join(lines)

    def summary(self) -> str:
        s = self.split_map()
        return (
            f"[CastOnPlan size={self.size}] neck={self.neck_cm:.1f} cm "
            f"→ CO {self.neck_sts} sts | "
            f"split: front={s['front']}, back={s['back']}, "
            f"sleeves={s['sleeve_L']}/{s['sleeve_R']} | "
            f"raglan={self.raglan_lines}×{self.raglan_line_sts}"
        )
