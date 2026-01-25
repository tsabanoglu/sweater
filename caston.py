# sweater/caston.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class CastOnPlan:
    """
    Data holder for neck cast-on stitches and the initial section split.

    All values are pre-computed by Sweater.build() and passed in.
    This class just holds the data and provides convenient accessors.
    """
    size: str
    neck_sts: int                              # pre-computed cast-on count
    split: Dict[str, int] = field(default_factory=dict)  # pre-computed initial split
    short_row_count: int = 0                   # individual rows (not pairs)
    raglan_lines: int = 4
    raglan_line_sts: int = 2
    rib_multiple: int = 2

    # ---- accessors ----
    def split_map(self) -> Dict[str, int]:
        """
        Initial split (at cast-on) for placing markers:
        front/back/sleeve_L/sleeve_R, excluding raglan-line stitches.
        """
        return self.split

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
            f"Cast on {self.neck_sts} sts. Join to work in the round, place BOR (beginning of round) marker.",
            "Place section markers as follows:",
            f"  - Back left: {back_left} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Sleeve left: {split['sleeve_L']} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Front: {split['front']} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Sleeve right: {split['sleeve_R']} sts, PM",
            f"  - Raglan: {rl} sts, PM",
            f"  - Back right: {back_right} sts (to BOR)",
        ]
        return "\n".join(lines)

    def summary(self) -> str:
        s = self.split_map()
        short_row_info = f" | short_rows={self.short_row_count}" if self.short_row_count > 0 else ""
        return (
            f"[CastOnPlan size={self.size}] "
            f"CO {self.neck_sts} sts | "
            f"split: front={s['front']}, back={s['back']}, "
            f"sleeves={s['sleeve_L']}/{s['sleeve_R']} | "
            f"raglan={self.raglan_lines}×{self.raglan_line_sts}"
            f"{short_row_info}"
        )
