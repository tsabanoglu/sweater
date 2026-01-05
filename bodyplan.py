from __future__ import annotations

from typing import Optional, Literal, List
from dataclasses import dataclass
import math
from .helpers import _evenly_spaced_rows, cm_to_rows, rows_to_cm


### Body plan

Fit = Literal["straight", "fitted"]
@dataclass(frozen=True)
class BodyPlan:
    size: str
    body_total_sts: int
    hem_circ_sts: int
    length_rows: int
    gauge_rows_per_cm: float
    gauge_sts_per_cm: float
    fit: Fit = "straight"
    rib_multiple: int = 2
    dec_schedule_rows: Optional[List[bool]] = None # None or a list 

    @property
    def dec_count(self) -> int:
       return 0 if not self.dec_schedule_rows else len(self.dec_schedule_rows)
    



