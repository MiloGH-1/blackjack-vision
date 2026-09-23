"""Card parsing helpers shared by the detector, hands and shoe."""

from __future__ import annotations

from dataclasses import dataclass

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["C", "D", "H", "S"]


def rank_value(rank: str) -> int:
    """Blackjack value of a rank, with aces as 1 (soft handling lives in Hand)."""
    rank = normalise_rank(rank)
    if rank == "A":
        return 1
    if rank in ("10", "J", "Q", "K"):
        return 10
    return int(rank)


def normalise_rank(rank: str) -> str:
    r = rank.strip().upper()
    if r in ("T", "1"):
        return "10"
    if r in ("ACE",):
        return "A"
    if r not in RANKS:
        raise ValueError(f"Unknown rank: {rank!r}")
    return r


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str | None = None

    @property
    def value(self) -> int:
        return rank_value(self.rank)

    def __str__(self) -> str:
        return f"{self.rank}{self.suit or ''}"


def parse_label(label: str) -> Card:
    """Parse a detector class name like '10H', 'KS', 'ac', 'Th' into a Card."""
    s = label.strip().upper()
    if len(s) < 2:
        raise ValueError(f"Bad card label: {label!r}")
    suit = s[-1]
    if suit not in SUITS:
        raise ValueError(f"Bad suit in label: {label!r}")
    return Card(normalise_rank(s[:-1]), suit)
