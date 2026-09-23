"""Hand evaluation and splitting detected cards into dealer / player."""

from __future__ import annotations

from dataclasses import dataclass, field

from .cards import Card


@dataclass
class Hand:
    cards: list[Card] = field(default_factory=list)

    @property
    def hard_total(self) -> int:
        return sum(c.value for c in self.cards)

    @property
    def total(self) -> int:
        t = self.hard_total
        if self.has_ace and t + 10 <= 21:
            return t + 10
        return t

    @property
    def has_ace(self) -> bool:
        return any(c.rank == "A" for c in self.cards)

    @property
    def is_soft(self) -> bool:
        return self.has_ace and self.hard_total + 10 <= 21

    @property
    def is_pair(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].value == self.cards[1].value

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.total == 21

    @property
    def is_bust(self) -> bool:
        return self.total > 21

    def describe(self) -> str:
        if not self.cards:
            return "-"
        if self.is_blackjack:
            return "Blackjack"
        if self.is_bust:
            return f"Bust ({self.total})"
        kind = "Soft" if self.is_soft else "Hard"
        return f"{kind} {self.total}"

    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards)


def split_by_region(detections, frame_height: int, divider: float):
    """Split (card, (cx, cy)) pairs into dealer (above divider) and player (below).

    Cards are ordered left-to-right within each hand.
    """
    line = frame_height * divider
    dealer = sorted((d for d in detections if d[1][1] < line), key=lambda d: d[1][0])
    player = sorted((d for d in detections if d[1][1] >= line), key=lambda d: d[1][0])
    return Hand([d[0] for d in dealer]), Hand([d[0] for d in player])
