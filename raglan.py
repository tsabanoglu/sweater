# sweater/raglan.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List

from .constants import NECK_SIZES, CHEST_SIZES, BODY_FIT_EASE, BODY_FIT_INC_ROUNDS, COMBINED_PHASE_DEPTH_CM
from .helpers import (
    body_target_stitches, cm_to_rows, _split_neck,
    _inc_rounds_needed, _schedule, _panel_schedule, _even, _round_to_multiple,
    calculate_short_rows,
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
    inc_every: int = 2                # every other row by default
    underarm_each: Optional[int] = None  # CO per underarm (auto-calculated if None)
    underarm_cm: float = 2.5          # target underarm width in cm (if underarm_each not specified)
    body_length_cm: float = 40.0
    body_fit: str = "straight"        # "straight" (tube), "fitted" (1-2 inc rounds), "loose" (7-9 inc rounds)
    sleeve_length_cm: float = 45.0
    sleeve_cuff_rows_cm: float = 6.0  # rib length at cuff

    # optional override: skip neck-size calculation and use this count directly
    neck_sts_override: Optional[int] = None

    # short-row controls
    use_short_rows: bool = False
    short_row_depth_cm: float = 5.0
    short_rows_with_raglan_incs: bool = True

    # neckband (standard 8cm default)
    neckband_cm: float = 8.0

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

    @property
    def neckband_rows(self) -> int:
        """Number of rows for neckband (0 if no neckband)."""
        if self.neckband_cm <= 0:
            return 0
        return cm_to_rows(self.neckband_cm, self.gauge_rows_per_cm)

    # --- orchestration helpers (moved from CastOnPlan) ---
    def _compute_neck_sts(self, neck_cm: float) -> int:
        """Compute neck cast-on stitch count from circumference."""
        raw = neck_cm * self.gauge_sts_per_cm
        sts = _round_to_multiple(int(round(raw)), max(1, self.rib_multiple))
        if sts < 60:
            sts = 60
        if sts % 2:
            sts += 1
        return sts

    def _compute_initial_split_and_short_rows(self) -> tuple:
        """
        Compute the initial split and short row count.

        Returns: (split, neck_sts, short_row_count)
        """
        if self.neck_sts_override is not None:
            final_neck = self.neck_sts_override
        else:
            neck_cm = NECK_SIZES.get(self.size, 38.0)
            final_neck = self._compute_neck_sts(neck_cm)

        # Calculate final split (after short rows)
        final_split = _split_neck(
            final_neck,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
        )

        # If no short rows, return final split directly
        if not (self.use_short_rows and self.gauge_rows_per_cm > 0 and self.short_row_depth_cm > 0):
            return final_split, final_neck, 0

        MIN_BACK = 4
        MIN_SLEEVE = 4

        # The short-row count depends on the post-short-row split (back/sleeve
        # sizes), but that split depends on the short-row count. Iterate to a
        # fixed point so the count used here to size the initial split is the
        # SAME count ShortRowPlan will later use to place turns - otherwise
        # the two can disagree (e.g. split math assumes 5 pairs while the
        # rendered turns only fit 4, so stitch totals don't add up).
        pairs = 0
        initial_split = final_split
        for _ in range(5):
            final_total_after_sr = final_neck + 4 * pairs
            final_split_after_sr = _split_neck(
                final_total_after_sr,
                raglan_lines=self.raglan_lines,
                raglan_line_sts=self.raglan_line_sts,
            )

            # Short rows add: 2*pairs to back, pairs to each sleeve, 0 to front
            initial_split = {
                "front": final_split_after_sr["front"],
                "back": max(final_split_after_sr["back"] - 2 * pairs, MIN_BACK),
                "sleeve_L": max(final_split_after_sr["sleeve_L"] - pairs, MIN_SLEEVE),
                "sleeve_R": max(final_split_after_sr["sleeve_R"] - pairs, MIN_SLEEVE),
            }

            # Recompute short row count from these candidate numbers: sleeve_sts
            # is the pre-short-row (initial) shoulder width, since that's the
            # actual span turns get placed within; back_sts is the post-short-row
            # (final) back width, since that's what calculate_short_rows checks
            # against min_back. This matches exactly what ShortRowPlan uses.
            sleeve_sts = min(initial_split["sleeve_L"], initial_split["sleeve_R"])
            short_row_count = calculate_short_rows(
                depth_cm=self.short_row_depth_cm,
                gauge_rows_per_cm=self.gauge_rows_per_cm,
                sleeve_sts=sleeve_sts,
                back_sts=final_split_after_sr["back"],
                guard_sts=2,
                max_short_rows=10,
                min_back=MIN_BACK,
                min_sleeve=MIN_SLEEVE,
            )
            new_pairs = short_row_count // 2

            if new_pairs == pairs:
                break
            pairs = new_pairs

        return initial_split, final_neck, pairs * 2

    # --- build steps ---
    def _target_body_final_sts(self) -> int:
        """Full bust circumference target in stitches (incl. underarms), from size + gauge alone."""
        chest_cm = CHEST_SIZES.get(self.size, CHEST_SIZES["M"])
        return body_target_stitches(chest_cm, self.gauge_sts_per_cm)

    def _build_yoke(self, split: Dict[str, int], neck_sts: int, short_row_count: int = 0) -> YokePlan:
        # Targets & yoke math
        target_body_final = self._target_body_final_sts()
        target_body = target_body_final - (2 * self.underarm_sts_each)

        body_start = split["front"] + split["back"]
        sleeve_total_start = split["sleeve_L"] + split["sleeve_R"]
        per_round = self.raglan_lines  # sts added to a panel pair per active increase round

        # Short row count is now individual rows, convert to pairs for calculations
        short_row_pairs = short_row_count // 2
        body_after_sr = body_start + short_row_pairs * 2
        sleeves_after_sr = sleeve_total_start + short_row_pairs * 2

        # Phase 1 - combined (body + sleeves increase together): its length is
        # driven by a realistic physical depth (COMBINED_PHASE_DEPTH_CM),
        # converted to rounds via this pattern's own row gauge - not by
        # chasing a sleeve stitch-count target. Sleeve width is whatever this
        # phase naturally produces - it is not solved for.
        combined_phase_rows = cm_to_rows(COMBINED_PHASE_DEPTH_CM, self.gauge_rows_per_cm)
        combined_rounds = combined_phase_rows // self.inc_every

        sleeve_inc_rounds = combined_rounds
        sleeves_total_end = sleeves_after_sr + sleeve_inc_rounds * per_round
        body_after_combined = body_after_sr + combined_rounds * per_round

        # Phase 2 - body only (sleeves held): uncapped, runs however many
        # rounds it takes to reach the true bust target. This is what scales
        # with size - bigger sizes simply need more of these rounds.
        body_only_rounds = _inc_rounds_needed(body_after_combined, target_body, per_round)
        body_inc_rounds = combined_rounds + body_only_rounds
        body_end = body_after_combined + body_only_rounds * per_round

        regular_rounds = body_inc_rounds  # total distinct schedule rounds (body runs the whole way)

        # Total increase-round count (SR pairs + regular rounds); kept for
        # callers that want a round count rather than a row count.
        inc_rounds = short_row_pairs + regular_rounds

        # Physical rows from end of neckband to separation: short rows are
        # always 2 physical rows per pair (RS+WS), independent of inc_every -
        # only the regular increase rounds scale by inc_every.
        yoke_rows = short_row_count + regular_rounds * self.inc_every
        schedule = _schedule(regular_rounds, self.inc_every)
        body_schedule = _panel_schedule(body_inc_rounds, regular_rounds, self.inc_every)
        sleeve_schedule = _panel_schedule(sleeve_inc_rounds, regular_rounds, self.inc_every)

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
            body_inc_rounds=body_inc_rounds,
            sleeve_inc_rounds=sleeve_inc_rounds,
            body_schedule=body_schedule,
            sleeve_schedule=sleeve_schedule,
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
        body_start = sep_map["body_total"]
        inc_per_round = 4  # evenly spaced at the two underarm "seam" points

        # Mandatory catch-up: if the yoke's depth cap left the body short of
        # full bust circumference, make up the difference here first,
        # regardless of fit (even "straight" must still reach true bust size).
        target_body_final = self._target_body_final_sts()
        mandatory_rounds = _inc_rounds_needed(body_start, target_body_final, inc_per_round)
        body_after_mandatory = body_start + mandatory_rounds * inc_per_round

        # Stylistic hem ease, on top of true bust circumference.
        ease = BODY_FIT_EASE.get(self.body_fit, 0.0)
        min_rounds, max_rounds = BODY_FIT_INC_ROUNDS.get(self.body_fit, (0, 0))

        ease_target = int(round(body_after_mandatory * (1 + ease)))
        if ease_target % 2:
            ease_target += 1

        ease_rounds = _inc_rounds_needed(body_after_mandatory, ease_target, inc_per_round)
        ease_rounds = max(min_rounds, min(max_rounds, ease_rounds))
        hem_circ_sts = body_after_mandatory + ease_rounds * inc_per_round

        return BodyPlan(
            size=self.size,
            body_total_sts=body_start,
            hem_circ_sts=hem_circ_sts,
            length_rows=rows,
            gauge_rows_per_cm=self.gauge_rows_per_cm,
            gauge_sts_per_cm=self.gauge_sts_per_cm,
            fit=self.body_fit,
            rib_multiple=self.rib_multiple,
            dec_schedule_rows=None,
            inc_per_round=inc_per_round,
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

    # ---- accessors ----
    def build(self) -> Dict[str, object]:
        """Run the full pipeline and return all parts + maps."""

        # 1) Compute split and short rows (orchestration moved here from CastOnPlan)
        split, neck_sts, short_row_count = self._compute_initial_split_and_short_rows()

        # 2) Create CastOnPlan with pre-computed values
        co = CastOnPlan(
            size=self.size,
            neck_sts=neck_sts,
            split=split,
            short_row_count=short_row_count,
            raglan_lines=self.raglan_lines,
            raglan_line_sts=self.raglan_line_sts,
            rib_multiple=self.rib_multiple,
        )

        # 3) Yoke based on this (possibly adjusted) split
        yoke = self._build_yoke(split, neck_sts, short_row_count=short_row_count)

        # 4) Separator, body, sleeves
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

        # 5) Optional ShortRowPlan (back + shoulders only)
        if self.use_short_rows and short_row_count > 0:
            sr = ShortRowPlan(
                size=self.size,
                gauge_rows_per_cm=self.gauge_rows_per_cm,
                back_sts=split["back"],
                right_shoulder_sts=split["sleeve_R"],
                left_shoulder_sts=split["sleeve_L"],
                short_row_depth_cm=self.short_row_depth_cm,
                precomputed_pairs=short_row_count // 2,
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
        lines.append(f"Work {self.neckband_rows} rows ({self.neckband_cm:.1f} cm) in rib for neckband.")

        # OPTIONAL: BACK-NECK SHORT ROWS (simple text using ShortRowPlan)
        if short_rows is not None:
            sr = short_rows
            right_turns = sr.right_shoulder_turns()
            left_turns = sr.left_shoulder_turns()
            n = min(len(right_turns), len(left_turns))
            hb = sr.half_back_sts

            lines.append("\n— BACK-NECK SHORT-ROW SHAPING —")
            lines.append(f"(Raglan line = {self.raglan_line_sts} sts between markers)")
            if n == 0:
                lines.append("No short rows planned for this size.")
            else:
                for i in range(n):
                    r = right_turns[i]
                    l = left_turns[i]
                    rs_num = 2 * i + 1
                    ws_num = 2 * i + 2

                    if i == 0:
                        # First pair: full instructions
                        lines.append(
                            f"Short row {rs_num} (RS): "
                            f"From BOR, k to marker, M1R, k {self.raglan_line_sts} raglan sts, M1L, "
                            f"k {r} sts into shoulder. Turn."
                        )
                        lines.append(
                            f"Short row {ws_num} (WS): "
                            f"P to marker (past BOR), M1R, p {self.raglan_line_sts} raglan sts, M1L, "
                            f"p {l} sts into shoulder. Turn."
                        )
                    else:
                        # Subsequent pairs: relative to last turn
                        r_prev = right_turns[i - 1]
                        l_prev = left_turns[i - 1]
                        r_diff = r - r_prev
                        l_diff = l - l_prev
                        lines.append(
                            f"Short row {rs_num} (RS): "
                            f"K to marker, M1R, k {self.raglan_line_sts} raglan sts, M1L, "
                            f"k {r_diff} sts past last RS turn. Turn."
                        )
                        lines.append(
                            f"Short row {ws_num} (WS): "
                            f"P to marker, M1R, p {self.raglan_line_sts} raglan sts, M1L, "
                            f"p {l_diff} sts past last WS turn. Turn."
                        )

                # Calculate stitch counts after short rows
                split = co.split_map()
                short_row_pairs = co.short_row_count // 2
                back_after = split["back"] + 2 * short_row_pairs
                front_after = split["front"]  # unchanged
                sleeve_l_after = split["sleeve_L"] + short_row_pairs
                sleeve_r_after = split["sleeve_R"] + short_row_pairs
                total_after = back_after + front_after + sleeve_l_after + sleeve_r_after + (self.raglan_line_sts * 4)

                lines.append("")
                lines.append(f"After short rows ({co.short_row_count} rows worked):")
                lines.append(f"  - Back: {back_after} sts")
                lines.append(f"  - Front: {front_after} sts")
                lines.append(f"  - Sleeve left: {sleeve_l_after} sts")
                lines.append(f"  - Sleeve right: {sleeve_r_after} sts")
                lines.append(f"  - Total: {total_after} sts")

        # RAGLAN YOKE (explicit increase instruction)
        lines.append("\n— RAGLAN YOKE —")
        both_rounds = min(yoke.body_inc_rounds, yoke.sleeve_inc_rounds)
        extra_rounds = max(yoke.body_inc_rounds, yoke.sleeve_inc_rounds) - both_rounds
        lines.append(
            f"Work raglan increases (body and sleeves) every {self.inc_every} round(s) "
            f"for {both_rounds} increase rounds."
        )
        if extra_rounds > 0:
            extra_side = "body" if yoke.body_inc_rounds > yoke.sleeve_inc_rounds else "sleeves"
            held_side = "sleeve" if extra_side == "body" else "body"
            lines.append(
                f"Then continue raglan increases on the {extra_side} only (hold {held_side} stitches) "
                f"every {self.inc_every} round(s) for {extra_rounds} more increase rounds."
            )
        lines.append(f"(≈ {yoke.yoke_rows} rows total.)")

        # SEPARATION
        lines.append("\n— SEPARATION —")
        lines.append(sep.summary())

        # BODY
        lines.append("\n— BODY —")
        lines.append(f"Work body {body.length_rows} rows (≈ {self.body_length_cm:.1f} cm), fit: {self.body_fit}.")
        lines.append(
            f"Body after separation: {sep_map['body_total']} sts "
            f"(front {sep_map['body_front']} / back {sep_map['body_back']})."
        )
        body_m = body.stitch_map_end()
        if body_m["inc_rounds"] > 0:
            lines.append(
                f"Increase to hem {body_m['hem_sts']} sts via {body_m['inc_rounds']} inc rounds "
                f"({body.inc_per_round} sts per round, evenly spaced at the underarm seam points)."
            )
        else:
            lines.append("Work body straight to hem (no shaping).")

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
