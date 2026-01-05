# sweater/raglan.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List

from .constants import NECK_SIZES, CHEST_SIZES
from .helpers import (
    cast_on_from_neck, body_target_stitches, cm_to_rows, _split_neck,
    _inc_rounds_needed, _schedule, _even,
)
from .yokeplan import YokePlan
from .separator import SeparatorPlan
from .sleeveplan import SleevePlan
from .bodyplan import BodyPlan
from .caston import CastOnPlan
from .shortrows import ShortRowPlan


_RIB_INDEX = {0: "none", 1: "1x1", 2: "2x2"}
_RIB_MULT = {"none": 1, "1x1": 2, "2x2": 4}


@dataclass
class Sweater:
    """
    Facade/orchestrator: main idea is it takes the below specified inputs
    and generates a full pattern.

    Parameters
    ----------
    sts_per_10cm : int/float
        Stitch gauge per 10 cm (e.g. 22).
    rows_per_10cm : int/float
        Row gauge per 10 cm (e.g. 18).
    size : str
        Size key in your constants, e.g. "XS", "S", "M", "L", ...
    rib_pref : int
        0 = no rib multiple, 1 = 1x1, 2 = 2x2 (maps to multiples 1/2/4).
    """

    sts_per_10cm: float
    rows_per_10cm: float
    size: str
    rib_pref: int = 1   # 1x1 default

    # construction knobs (reasonable defaults)
    raglan_lines: int = 4
    raglan_line_sts: int = 2
    inc_every: int = 2                # every other round by default
    underarm_each: Optional[int] = None  # CO per underarm (auto-calculated if None)
    underarm_cm: float = 2.5          # target underarm width in cm (if underarm_each not specified)
    body_length_cm: float = 40.0
    sleeve_length_cm: float = 45.0
    sleeve_cuff_rows_cm: float = 6.0  # rib length at cuff

    # short-row controls
    use_short_rows: bool = False
    short_row_depth_cm: float = 5.0
    short_rows_with_raglan_incs: bool = True

    # --- derived props ---
    @property
    def gauge_sts_per_cm(self) -> float:
        return self.sts_per_10cm / 10.0

    @property
    def gauge_rows_per_cm(self) -> float:
        return self.rows_per_10cm / 10.0

    @property
    def ribbing_style(self) -> str:
        return _RIB_INDEX.get(self.rib_pref, "1x1")

    @property
    def rib_multiple(self) -> int:
        return _RIB_MULT[self.ribbing_style]

    @property
    def underarm_sts_each(self) -> int:
        """
        Calculate underarm cast-on stitches per side.
        If underarm_each is specified, use that. Otherwise calculate from underarm_cm.
        Result is rounded to nearest even number.
        """
        if self.underarm_each is not None:
            return self.underarm_each

        # Calculate based on underarm_cm and gauge
        sts = int(round(self.underarm_cm * self.gauge_sts_per_cm))
        # Round to even number
        if sts % 2 == 1:
            sts += 1
        # Minimum of 4 sts
        return max(4, sts)

    # --- build steps ---
    def _build_yoke(self, split: Dict[str, int], neck_sts: int, short_row_rounds: int = 0) -> YokePlan:
        chest_cm = CHEST_SIZES.get(self.size, CHEST_SIZES["M"])

        # Targets & yoke math
        # Note: target_body is the FINAL body circumference after underarm cast-ons
        # The yoke should end with: target - (2 × underarm_sts_each) stitches
        # Then after adding underarms, we reach the exact target
        target_body_final = body_target_stitches(chest_cm, self.gauge_sts_per_cm)
        target_body = target_body_final - (2 * self.underarm_sts_each)

        target_sleeves_total = int(round(0.60 * target_body_final))
        if target_sleeves_total % 2:
            target_sleeves_total += 1

        body_start = split["front"] + split["back"]
        sleeve_total_start = split["sleeve_L"] + split["sleeve_R"]
        per_round = self.raglan_lines  # = 4 (increases to body per regular round)

        # When short rows are used, the first R rounds only increase back raglan lines
        # Short row rounds: +2 sts to body, +2 sts to sleeves per round
        # Regular rounds: +4 sts to body, +4 sts to sleeves per round
        if short_row_rounds > 0:
            # After short rows
            body_after_sr = body_start + short_row_rounds * 2
            sleeves_after_sr = sleeve_total_start + short_row_rounds * 2

            # Calculate remaining regular rounds needed
            remaining_for_body = _inc_rounds_needed(body_after_sr, target_body, per_round)
            remaining_for_sleeves = _inc_rounds_needed(sleeves_after_sr, target_sleeves_total, per_round)
            remaining_rounds = max(remaining_for_body, remaining_for_sleeves)

            # Total increase rounds = SR rounds + remaining regular rounds
            inc_rounds = short_row_rounds + remaining_rounds

            # Final stitch counts
            body_end = body_after_sr + remaining_rounds * per_round
            sleeves_total_end = sleeves_after_sr + remaining_rounds * per_round
        else:
            # No short rows: standard calculation
            inc_rounds = max(
                _inc_rounds_needed(body_start, target_body, per_round),
                _inc_rounds_needed(sleeve_total_start, target_sleeves_total, per_round),
            )
            body_end = body_start + inc_rounds * per_round
            sleeves_total_end = sleeve_total_start + inc_rounds * per_round

        yoke_rows = inc_rounds * self.inc_every
        schedule = _schedule(inc_rounds, self.inc_every)

        return YokePlan(
            size=self.size,
            neck_sts=neck_sts,
            raglan_line_sts=self.raglan_line_sts,
            raglan_lines=self.raglan_lines,
            split=split,
            inc_rounds=inc_rounds,
            inc_every=self.inc_every,
            yoke_rows=yoke_rows,
            body_sts_end_yoke=body_end,
            sleeve_sts_end_yoke=sleeves_total_end,  # TOTAL (both sleeves)
            schedule=schedule,
            target={"body": target_body, "sleeve": sleeves_total_end // 2},
        )

    def _build_separator(self, yoke: YokePlan) -> SeparatorPlan:
        return SeparatorPlan(
            size=self.size,
            body_sts_end_yoke=yoke.body_sts_end_yoke,
            sleeve_sts_end_yoke=yoke.sleeve_sts_end_yoke,  # TOTAL
            underarm_each=self.underarm_sts_each,
            separate_at_row=yoke.yoke_rows,
        )

    def _build_body(self, sep_map: Dict[str, int]) -> BodyPlan:
        rows = cm_to_rows(self.body_length_cm, self.gauge_rows_per_cm)
        return BodyPlan(
            size=self.size,
            body_total_sts=sep_map["body_total"],
            hem_circ_sts=sep_map["body_total"],  # can add shaping later
            length_rows=rows,
            gauge_rows_per_cm=self.gauge_rows_per_cm,
            gauge_sts_per_cm=self.gauge_sts_per_cm,
            rib_multiple=self.rib_multiple,
            dec_schedule_rows=None,
        )

    def _build_sleeve(self, sep_map: Dict[str, int]) -> SleevePlan:
        rows = cm_to_rows(self.sleeve_length_cm, self.gauge_rows_per_cm)
        cuff_rows = cm_to_rows(self.sleeve_cuff_rows_cm, self.gauge_rows_per_cm)

        # Auto target: aim cuff ≈ ~70% of start, round to rib multiple
        start = sep_map["sleeve_each"]
        target = int(round(0.70 * start))
        # align to rib multiple and keep even
        if self.rib_multiple > 1:
            target -= (target % self.rib_multiple)
        target = max(0, _even(target))

        return SleevePlan(
            size=self.size,
            start_sts=start,                 # PER-SLEEVE from Separator
            length_rows=rows,
            gauge_rows_per_cm=self.gauge_rows_per_cm,
            target_cuff_sts=target,          # AUTO-to-target
            cuff_rib_rows=cuff_rows,
            rib_multiple=self.rib_multiple,
        )

    # ---- public API ----
    def build(self) -> Dict[str, object]:
        """Run the full pipeline and return all parts + maps."""

        # 1) Cast-on plan: single source of truth for neck_sts + split
        co = CastOnPlan(
            size=self.size,
            gauge_sts_per_cm=self.gauge_sts_per_cm,
            rib_multiple=self.rib_multiple,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
            gauge_rows_per_cm=self.gauge_rows_per_cm,
            use_short_rows=self.use_short_rows,
            short_row_depth_cm=self.short_row_depth_cm,
        )
        split = co.split_map()              # {'front','back','sleeve_L','sleeve_R'}
        neck_sts = co.neck_sts
        R = co.short_row_rounds() if self.use_short_rows else 0

        # 2) Yoke based on this (possibly adjusted) split
        yoke = self._build_yoke(split, neck_sts, short_row_rounds=R)

        # 3) Separator, body, sleeves
        sep = self._build_separator(yoke)
        sep_map = sep.stitch_map_at_separation()
        body = self._build_body(sep_map)
        sleeve = self._build_sleeve(sep_map)

        parts: Dict[str, object] = {
            "cast_on": co,
            "neck_split": split,
            "yoke": yoke,
            "separator": sep,
            "sep_map": sep_map,
            "body": body,
            "sleeve": sleeve,
        }

        # 4) Optional ShortRowPlan (back + shoulders only)
        if self.use_short_rows:
            sr = ShortRowPlan(
                size=self.size,
                gauge_rows_per_cm=self.gauge_rows_per_cm,
                back_sts=split["back"],
                right_shoulder_sts=split["sleeve_R"],
                left_shoulder_sts=split["sleeve_L"],
                short_row_depth_cm=self.short_row_depth_cm,
            )
            parts["short_rows"] = sr

        return parts

    def render_text(self) -> str:
        parts = self.build()
        
        co: CastOnPlan = parts["cast_on"]                 # type: ignore
        yoke: YokePlan = parts["yoke"]                    # type: ignore
        sep: SeparatorPlan = parts["separator"]           # type: ignore
        sep_map: Dict[str, int] = parts["sep_map"]        # type: ignore
        sleeve: SleevePlan = parts["sleeve"]              # type: ignore
        body: BodyPlan = parts["body"]                    # type: ignore
        short_rows: Optional[ShortRowPlan] = parts.get("short_rows")  # type: ignore

        sleeve_end = sleeve.stitch_map_end()
        rib_label = {0: "no rib", 1: "1x1", 2: "2x2"}.get(self.rib_pref, "1x1")

        lines: List[str] = []
        lines.append(f"Size {self.size}")
        lines.append(
            f"Gauge: {self.sts_per_10cm:.1f} sts / {self.rows_per_10cm:.1f} rows per 10 cm "
            f"({self.gauge_sts_per_cm:.2f} sts/cm, {self.gauge_rows_per_cm:.2f} rows/cm)"
        )

        # CAST-ON & MARKERS
        lines.append("\n— CAST-ON & MARKERS —")
        lines.append(co.cast_on_text(rib_label=rib_label))

        # OPTIONAL: BACK-NECK SHORT ROWS (simple text using ShortRowPlan)
        if short_rows is not None:
            sr = short_rows
            right_turns = sr.right_shoulder_turns()
            left_turns = sr.left_shoulder_turns()
            n = min(len(right_turns), len(left_turns))
            hb = sr.half_back_sts

            lines.append("\n— BACK-NECK SHORT-ROW SHAPING —")
            if n == 0:
                lines.append("No short rows planned for this size.")
            else:
                for i in range(n):
                    r = right_turns[i]
                    l = left_turns[i]
                    rs_num = 2 * i + 1
                    ws_num = 2 * i + 2
                    lines.append(
                        f"Short row {rs_num} (RS, beg at BOR / center back): "
                        f"k {hb} to right back raglan marker, work raglan incs as established, "
                        f"k {r} sts into right shoulder, turn (German short row)."
                    )
                    lines.append(
                        f"Short row {ws_num} (WS, beg at BOR / center back): "
                        f"p {hb} to left back raglan marker, work raglan incs as established, "
                        f"p {l} sts into left shoulder, turn (German short row)."
                    )

        # RAGLAN YOKE (explicit increase instruction)
        lines.append("\n— RAGLAN YOKE —")
        lines.append(
            f"Work raglan increases every {self.inc_every} round(s) "
            f"for {yoke.inc_rounds} increase rounds (≈ {yoke.yoke_rows} rows total)."
        )

        # SEPARATION
        lines.append("\n— SEPARATION —")
        lines.append(sep.summary())

        # BODY
        lines.append("\n— BODY —")
        lines.append(f"Work body {body.length_rows} rows (≈ {self.body_length_cm:.1f} cm).")
        lines.append(
            f"Body after separation: {sep_map['body_total']} sts "
            f"(front {sep_map['body_front']} / back {sep_map['body_back']})."
        )

        # SLEEVES
        lines.append("\n— SLEEVES —")
        lines.append(
            f"Each sleeve starts with {sep_map['sleeve_each']} sts; "
            f"work {sleeve.length_rows} rows (≈ {self.sleeve_length_cm:.1f} cm)."
        )
        lines.append(
            f"Decrease to cuff {sleeve_end['cuff_sts']} sts via {sleeve_end['dec_rounds']} dec rounds. "
            f"Rib tail ≈ {self.sleeve_cuff_rows_cm:.1f} cm."
        )

        return "\n".join(lines)
