from __future__ import annotations

from typing import Dict, List
from dataclasses import dataclass
import math
from .helpers import _split_neck, _inc_rounds_needed, _round_to_multiple


### Yoke plan

@dataclass(frozen=True)
class YokePlan:
    size: str
    neck_sts: int
    raglan_line_sts: int # how many raglan sts
    raglan_lines: int # usually 4 - 2 back and 2 front
    split: Dict[str, int]
    inc_rounds: int
    inc_every: int # 1 for every round, 2 for every other round, etc.
    yoke_rows: int 
    body_sts_end_yoke: int # back and front sts (excluding sleeves) at end of yoke
    sleeve_sts_end_yoke: int # total sleeve sts at end of yoke (not per sleeve!!!)
    schedule: List[bool]
    target: Dict[str, int] # {"body": ..., "sleeve": ...} important: this is pre-underarm pickup sts

    
