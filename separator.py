### Separator


from __future__ import annotations

from typing import Optional, Dict
from dataclasses import dataclass
from .helpers import _even, _assert_nonneg

# helpers



@dataclass(frozen=True)
class SeparatorPlan:
    """
    Computes the split at the end of yoke/at the separation round. 
    - Moves sleeve stitches to waste yarn (or holders)
    - Keeps body stitches on the needle
    - Optionally adds underarm cast-ons to connect the body in the round
    Inputs use YokePlan totals *before* underarm cast-ons.
    """
    size: str
    # from YokePlan at the end of yoke
    body_sts_end_yoke: int
    sleeve_sts_end_yoke: int

    #construction options
    underarm_each: int = 8
    rib_multiple: int = 2
    include_raglan_lines_in_body: bool = False

    # (optional) book-keeping
    separate_at_row: Optional[int] = None


    def stitch_map_at_separation(self) -> Dict[str, int]:
        """
        Returns a dictionary with final stitch counts *after* separation and underarm cast-ons.
            Keys:
            - body_total
            - body_front
            - body_back
            - sleeve_each (per sleeve, post-separation, *without* cuffs)
            - underarm_each
            Notes:
            - Evenness is enforced on front/back for rib symmetry.
            - Raglan line stitches are assumed already excluded in the inputs. If you prefer to
                absorb them into the body, set include_raglan_lines_in_body=True and add them externally.
        """
        _assert_nonneg("body_sts_end_yoke", self.body_sts_end_yoke)
        _assert_nonneg("sleeve_sts_end_yoke", self.sleeve_sts_end_yoke)
        _assert_nonneg("underarm_each", self.underarm_each)

        if self.sleeve_sts_end_yoke % 2 != 0:
            raise ValueError("Total sleeve stitches must be even to split evenly.")
        if self.sleeve_sts_end_yoke >= self.body_sts_end_yoke:
            raise ValueError(
            "Total sleeve stitches look too large vs body; did you pass per-sleeve by mistake?"
        )


        # body splits evenly into front and back 
        base_half = self.body_sts_end_yoke // 2

        front = _even(base_half)
        back = self.body_sts_end_yoke - front


        # add underarm sts to front and back (each side contributes equally)
        front += self.underarm_each
        back += self.underarm_each

        body_total = front + back

        sleeve_each = self.sleeve_sts_end_yoke // 2


        # sanity check: keep everything even where it makes sense
        front = _even(front)
        back = _even(back)
        # body_total = _even(body_total)
        sleeve_each = _even(sleeve_each)

        return {
            "body_total": body_total,
            "body_front": front,
            "body_back": back,
            "sleeve_each": sleeve_each,
            "underarm_each": self.underarm_each
        }

    def summary(self) -> str:
        m = self.stitch_map_at_separation()
        row_info = f" at row {self.separate_at_row}" if self.separate_at_row is not None else ""
        return (
            f"[Separator{row_info}]"
            f"Body: {m['body_total']} sts (front: {m['body_front']}, back: {m['body_back']}), "
            f"Sleeves: {m['sleeve_each']} sts each, "
            f"Underarm cast-on: {m['underarm_each']} sts per side."
        )