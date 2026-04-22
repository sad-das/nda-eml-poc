from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class EvidencePair:
    positive: bool
    negative: bool

    @property
    def belnap(self) -> str:
        if self.positive and self.negative:
            return "B"
        if self.positive:
            return "T"
        if self.negative:
            return "F"
        return "N"
