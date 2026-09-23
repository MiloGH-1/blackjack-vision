"""Tracks which cards have left the shoe, so odds use what's actually left."""

from __future__ import annotations

from collections.abc import Iterable

from .cards import Card

# counts are indexed by blackjack value 1..10 (index 0 unused, A = 1, 10/J/Q/K = 10)
Counts = tuple[int, ...]


def full_shoe(decks: int) -> Counts:
    return tuple([0] + [4 * decks] * 9 + [16 * decks])


def hilo_value(card: Card) -> int:
    v = card.value
    if 2 <= v <= 6:
        return 1
    if v in (1, 10):
        return -1
    return 0


class Shoe:
    def __init__(self, decks: int):
        self.decks = decks
        self.seen: list[Card] = []

    def reset(self, decks: int | None = None) -> None:
        if decks is not None:
            self.decks = decks
        self.seen.clear()

    def discard(self, cards: Iterable[Card]) -> None:
        """Mark cards from a finished round as gone."""
        self.seen.extend(cards)

    def remaining(self, visible: Iterable[Card] = ()) -> Counts:
        counts = list(full_shoe(self.decks))
        for c in [*self.seen, *visible]:
            counts[c.value] = max(0, counts[c.value] - 1)
        return tuple(counts)

    def running_count(self, visible: Iterable[Card] = ()) -> int:
        return sum(hilo_value(c) for c in [*self.seen, *visible])

    def true_count(self, visible: Iterable[Card] = ()) -> float:
        left = sum(self.remaining(visible))
        decks_left = max(left / 52, 0.5)
        return self.running_count(visible) / decks_left
