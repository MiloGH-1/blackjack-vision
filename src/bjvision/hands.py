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


LAYOUTS = ("left-right", "top-bottom")


def split_by_region(detections, frame_size: tuple[int, int], divider: float,
                    layout: str = "left-right"):
    """Split (card, (cx, cy)) pairs into dealer and player hands.

    frame_size is (height, width). divider is a fraction of the frame width
    ("left-right": dealer left, player right) or height ("top-bottom": dealer
    above, player below). Cards are ordered left-to-right, then top-to-bottom.
    """
    if layout not in LAYOUTS:
        raise ValueError(f"layout must be one of {LAYOUTS}, not {layout!r}")
    axis = 0 if layout == "left-right" else 1       # x or y coordinate
    line = frame_size[1 - axis] * divider
    order = lambda d: (d[1][0], d[1][1])  # noqa: E731
    dealer = sorted((d for d in detections if d[1][axis] < line), key=order)
    player = sorted((d for d in detections if d[1][axis] >= line), key=order)
    return Hand([d[0] for d in dealer]), Hand([d[0] for d in player])
