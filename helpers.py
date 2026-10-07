from __future__ import annotations

from typing import Dict, List, Tuple
import math

from .constants import FRONT_BACK_SLEEVE_RATIO



### Neck & body target helpers

def cast_on_from_neck(neck_cm: float, gauge_sts_per_cm: float, rib_multiple: int) -> int:
    """Compute neck cast-on stitch count, aligned to rib multiple."""
    raw = neck_cm * gauge_sts_per_cm
    rounding_base = rib_multiple
    sts = round(raw / rounding_base) * rounding_base
    sts = max(sts, 60)  # ensure practical min
    if sts % 2:
        sts += 1
    return int(sts)


def body_target_stitches(chest_cm: float, gauge_sts_per_cm: float) -> int:
    """Compute body circumference target in stitches."""
    return int(round(chest_cm * gauge_sts_per_cm))


### Yoke plan helpers

def _round_to_multiple(x: int, m: int = 2) -> int:
    return int(round(x / m) * m)

def _split_neck(neck_sts: int, raglan_lines: int = 4, raglan_line_sts: int = 2,
                ratio: Tuple[int, int, int, int] = FRONT_BACK_SLEEVE_RATIO) -> Dict[str, int]:

    """
    Split neck stitches into back, front, and sleeves based on ratio.
    Raglan stitches are not included in this calculation.
    """

    total_rl = raglan_lines * raglan_line_sts
    base = neck_sts - total_rl
    assert base > 0, "Not enough neck stitches to allocate raglan lines."
    rsum = sum(ratio)
    front = round(base * ratio[0] / rsum)
    back = round(base * ratio[1] / rsum)
    sleeve = base - front - back
    sleeve_each = _round_to_multiple(sleeve // 2, 2)
    # adjust front and back to get even numbers
    front_and_back_even = base - (sleeve_each * 2)
    front = _round_to_multiple(front_and_back_even * ratio[0] // (ratio[0] + ratio[1]), 2)
    back = front_and_back_even - front

    return {'front': front, 'back': back, 'sleeve_L': sleeve_each, 'sleeve_R': sleeve_each}

def _inc_rounds_needed(start: int, target: int, per_round: int) -> int:
    return max (0, math.ceil ((target - start) / per_round))


def _schedule(inc_rounds: int, inc_every: int) -> List[bool]:

    """
    True marks an increase round. This will return a list of booleans indicating which rows are increase rounds.    

    """

    rows = inc_rounds * inc_every
    return [i % inc_every == 0 for i in range(rows)]


def _panel_schedule(rounds_needed: int, regular_rounds: int, inc_every: int) -> List[bool]:
    """
    Boolean list (len regular_rounds * inc_every), True on rows where this panel
    increases. The panel increases on the first `rounds_needed` scheduled slots
    (out of `regular_rounds` total slots), then holds for the remainder - this
    lets body and sleeves share early increase rounds and diverge later once one
    side reaches its target first.
    """
    total_rows = regular_rounds * inc_every
    return [(r % inc_every == 0) and (r // inc_every < rounds_needed) for r in range(total_rows)]


### Separator helpers

def _evenly_spaced_rows(total_rows: int, k: int) -> List[int]:
    """
    Return k events (could be decreases or increases) evenly spaced across total_rows.
    """
    if k <= 0:
        return []
    
    return sorted({max(1, round(i * total_rows / (k + 1))) for i in range(1, k + 1)})


def _even (x: int) -> int:
    """ Force an even number"""
    return x if x % 2 == 0 else x - 1

def _assert_nonneg (name: str, value: int) -> None:
    assert value >= 0, f"{name} must be non-negative."


### gauge conversion helpers

def cm_to_rows(length_cm: float, gauge_rows_per_cm: float) -> int:
    """
    Convert a measurement in cm to rows, based on row gauge.
    Example: 10 cm * 3.2 rows/cm = 32 rows
    Always rounds to nearest integer, since rows must be whole.
    """
    if length_cm < 0 or gauge_rows_per_cm <= 0:
        raise ValueError("Length and gauge must be positive.")
    return int(round(length_cm * gauge_rows_per_cm))


def rows_to_cm(length_rows: int, gauge_rows_per_cm: float) -> float:
    """
    Convert a number of rows to cm, based on row gauge.
    Example: 32 rows / 3.2 rows/cm = 10 cm
    Returns a float for precision.
    """
    if length_rows < 0 or gauge_rows_per_cm <= 0:
        raise ValueError("Length and gauge must be positive.")
    return length_rows / gauge_rows_per_cm


def cm_to_sts(width_cm: float, gauge_sts_per_cm: float) -> int:
    """
    Convert cm to stitches using stitch gauge.
    Example: 10 cm * 2.4 sts/cm = 24 sts
    """
    if width_cm < 0 or gauge_sts_per_cm <= 0:
        raise ValueError("Width and gauge must be positive.")
    return int(round(width_cm * gauge_sts_per_cm))


def sts_to_cm(sts: int, gauge_sts_per_cm: float) -> float:
    """
    Convert stitches to cm using stitch gauge.
    Example: 24 sts / 2.4 sts/cm = 10 cm
    """
    if sts < 0 or gauge_sts_per_cm <= 0:
        raise ValueError("Stitch count and gauge must be positive.")
    return sts / gauge_sts_per_cm

def adjust_split_for_short_rows(
    base_split: Dict[str, int],
    rounds: int,
    min_back: int = 4,
    min_sleeve: int = 3,
) -> Dict[str, int]:
    """
    Option D: given a *target* neck split (base_split) and the number of
    short-row rounds R (with raglan incs on back–sleeve lines), compute
    an *initial* split to use when you first place markers.

    After R short-row rounds:
      back     ≈ back_initial     + 2R
      sleeve_L ≈ sleeve_L_initial + R
      sleeve_R ≈ sleeve_R_initial + R
      front    ≈ front_initial

    We:
      - subtract those amounts from back and sleeves (with minimums),
      - then give all 'freed' stitches to the front to keep the total
        stitch count with markers unchanged.
    """
    if rounds <= 0:
        return base_split

    back_final = base_split["back"]
    sl_final = base_split["sleeve_L"]
    sr_final = base_split["sleeve_R"]
    front_final = base_split["front"]

    # naive backward step
    back_init = back_final - 2 * rounds
    sl_init = sl_final - rounds
    sr_init = sr_final - rounds

    # enforce minimums so things don't collapse
    back_init = max(back_init, min_back)
    sl_init = max(sl_init, min_sleeve)
    sr_init = max(sr_init, min_sleeve)

    # total before adjustment vs after
    total_before = back_final + sl_final + sr_final + front_final
    total_after_partial = back_init + sl_init + sr_init

    # whatever we subtracted, we allocate to front
    front_init = total_before - total_after_partial

    # sanity: front should stay >= 1
    if front_init <= 0:
        # fallback: clip everything but guarantee at least 1 front st
        front_init = 1
        # redistribute the rest proportionally / or just accept slight drift
        # for now, we won't over-engineer this
        # (this situation means R was too large for this size)

    return {
        "back": back_init,
        "sleeve_L": sl_init,
        "sleeve_R": sr_init,
        "front": front_init,
    }


def calculate_short_rows(
    depth_cm: float,
    gauge_rows_per_cm: float,
    sleeve_sts: int,
    back_sts: int,
    guard_sts: int = 2,
    max_short_rows: int = 10,  # individual rows, not pairs
    min_back: int = 4,
    min_sleeve: int = 4,
) -> int:
    """
    Calculate number of short rows (individual RS/WS rows, not pairs).
    Single source of truth for both CastOnPlan and ShortRowPlan.

    Parameters
    ----------
    depth_cm : float
        Target depth of short row shaping in cm.
    gauge_rows_per_cm : float
        Row gauge (rows per cm).
    sleeve_sts : int
        Stitches in the sleeve section (minimum of left/right).
    back_sts : int
        Stitches in the back section.
    guard_sts : int
        Stitches to leave before front raglan marker.
    max_short_rows : int
        Maximum individual rows (not pairs) allowed.
    min_back : int
        Minimum back stitches after adjustment.
    min_sleeve : int
        Minimum sleeve stitches after adjustment.

    Returns
    -------
    int
        Number of individual short rows (RS + WS), not pairs.
    """
    if depth_cm <= 0 or gauge_rows_per_cm <= 0:
        return 0

    # Calculate rows from depth (individual rows, must be even for RS/WS pairs)
    rows_from_depth = int(round(depth_cm * gauge_rows_per_cm))
    if rows_from_depth % 2 == 1:
        rows_from_depth -= 1
    rows_from_depth = max(rows_from_depth, 2)

    # Cap at maximum
    rows = min(rows_from_depth, max_short_rows)

    # Check sleeve constraint: need ~2 sts per turn minimum
    usable_sleeve = sleeve_sts - guard_sts
    if usable_sleeve > 0:
        max_rows_from_sleeve = (usable_sleeve // 2) * 2  # pairs * 2 = individual rows
        rows = min(rows, max_rows_from_sleeve)

    # Check back constraint: after R/2 pairs, back gains R sts (2 per pair from raglan incs)
    # Initial back = back_sts - R (for R/2 pairs)
    # So we need: back_sts - R >= min_back => R <= back_sts - min_back
    pairs = rows // 2
    max_pairs_from_back = (back_sts - min_back) // 2
    if pairs > max_pairs_from_back:
        pairs = max(1, max_pairs_from_back)
        rows = pairs * 2

    return max(rows, 2)  # at least 1 pair = 2 individual rows


__all__ = [
    "cast_on_from_neck",
    "body_target_stitches",
    "_round_to_multiple",
    "_split_neck",
    "_inc_rounds_needed",
    "_schedule",
    "_panel_schedule",
    "_evenly_spaced_rows",
    "_even",
    "_assert_nonneg",
    "cm_to_rows",
    "rows_to_cm",
    "cm_to_sts",
    "sts_to_cm",
    "adjust_split_for_short_rows",
    "calculate_short_rows",
]
