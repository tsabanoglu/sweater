from __future__ import annotations

from typing import Optional, Literal
from pydantic import validate_call, constr, confloat


class RaglanSweater:
    """
    A Python class to construct a raglan sweater:
    - Calculates neck/cast-on stitches
    - Divides stitches across garment sections
    - Estimates final stitch count for full body
    - Prepares for short row and raglan shaping
    """

    # Standard neck circumferences by size (in cm)
    NECK_SIZES = {
        'XS': 34,
        'S': 36,
        'M': 38,
        'L': 40,
        'XL': 42,
        'XXL': 44,
        'XXXL': 46
    }

    # Standard finished chest measurements by size (in cm)
    CHEST_SIZES = {
        'XS': 86,
        'S': 92,
        'M': 98,
        'L': 104,
        'XL': 110,
        'XXL': 116,
        'XXXL': 122
    }

    def __init__(self, gauge_stitches_per_10cm: float, gauge_rows_per_10cm: float):
        assert gauge_stitches_per_10cm > 0, "Stitch gauge must be positive"
        assert gauge_rows_per_10cm > 0, "Row gauge must be positive"

        self.gauge_stitches = gauge_stitches_per_10cm
        self.gauge_rows = gauge_rows_per_10cm
        self.stitches_per_cm = gauge_stitches_per_10cm / 10
        self.rows_per_cm = gauge_rows_per_10cm / 10

    @validate_call
    def calculate_neck_stitches(
        self,
        size: constr(strip_whitespace=True, to_upper=True) = "M", # type: ignore
        custom_neck_cm: Optional[confloat(gt=0)] = None, # type: ignore
        ribbing_style: Optional[Literal["1x1", "2x2", "none"]] = None
    ) -> dict:
        """
        Calculate cast-on stitches based on neck size and ribbing.

        Ensures:
        - Minimum of 60 stitches or 32cm neck width
        - Rounded to match ribbing style
        - Even stitch count
        """
        ribbing_style = ribbing_style or "1x1"
        neck_cm = custom_neck_cm if custom_neck_cm is not None else self.NECK_SIZES.get(size, 38)

        raw_stitches = neck_cm * self.stitches_per_cm
        rounding_base = 4 if ribbing_style == "2x2" else 2
        neck_stitches = round(raw_stitches / rounding_base) * rounding_base

        min_stitches = max(60, round(32 * self.stitches_per_cm))
        neck_stitches = max(neck_stitches, min_stitches)

        assert neck_stitches % 2 == 0, "Neck stitch count must be even."

        return {
            'size': size,
            'ribbing_style': ribbing_style,
            'neck_circumference_cm': neck_cm,
            'raw_calculation': raw_stitches,
            'cast_on_stitches': neck_stitches,
            'actual_neck_cm': neck_stitches / self.stitches_per_cm
        }

    @validate_call
    def calculate_target_stitches(
        self,
        size: constr(strip_whitespace=True, to_upper=True) = "M", # type: ignore
        custom_chest_cm: Optional[confloat(gt=0)] = None # type: ignore
    ) -> dict:
        """
        Calculate final body circumference in stitches.

        Returns:
        - Target chest cm used
        - Stitch count needed after yoke/body
        - Positive ease (if custom_chest_cm used)
        """
        chest_cm = custom_chest_cm if custom_chest_cm is not None else self.CHEST_SIZES.get(size, self.CHEST_SIZES["M"])
        target_stitches = round(chest_cm * self.stitches_per_cm)

        standard_cm = self.CHEST_SIZES.get(size, chest_cm)
        positive_ease_cm = chest_cm - standard_cm

        return {
            'target_chest_cm': chest_cm,
            'target_stitches': target_stitches,
            'positive_ease_cm': positive_ease_cm
        }