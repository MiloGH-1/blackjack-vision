"""Bust odds, dealer outcome distribution and move EVs from the remaining shoe.

All maths works on value counts (see shoe.Counts): index v holds how many cards
of blackjack value v (A = 1, 10/J/Q/K = 10) are left.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .hands import Hand
from .shoe import Counts

OUTCOMES = ["17", "18", "19", "20", "21", "blackjack", "bust"]


def _total(hard: int, has_ace: bool) -> tuple[int, bool]:
    if has_ace and hard + 10 <= 21:
        return hard + 10, True
    return hard, False


def _take(counts: Counts, v: int) -> Counts:
    lst = list(counts)
    lst[v] -= 1
    return tuple(lst)


def bust_probability(hand: Hand, counts: Counts) -> float:
    """Chance the next card busts this hand."""
    if not hand.cards or hand.is_bust:
        return 1.0 if hand.is_bust else 0.0
    left = sum(counts)
    if left == 0:
        return 0.0
    # A soft hand can always count its ace as 1, so the hard total decides
    hard = hand.hard_total
    busting = sum(counts[v] for v in range(1, 11) if hard + v > 21)
    return busting / left


def dealer_outcomes(up_value: int, counts: Counts, hits_soft_17: bool,
                    peeks: bool = True) -> dict[str, float]:
    """Probability of each final dealer result given the upcard.

    With peeks=True the dealer has already checked for blackjack, so the result
    is conditioned on the dealer NOT having blackjack.
    """
    left = sum(counts)
    result = dict.fromkeys(OUTCOMES, 0.0)
    if left == 0:
        return result

    excluded = None
    if peeks and up_value == 10:
        excluded = 1
    elif peeks and up_value == 1:
        excluded = 10
    denom = left - (counts[excluded] if excluded else 0)
    if denom <= 0:
        return result

    for v in range(1, 11):
        if counts[v] == 0 or v == excluded:
            continue
        p = counts[v] / denom
        sub = _dealer(up_value + v, up_value == 1 or v == 1, 2, _take(counts, v), hits_soft_17)
        for k, pk in zip(OUTCOMES, sub):
            result[k] += p * pk
    return result


@lru_cache(maxsize=500_000)
def _dealer(hard: int, has_ace: bool, n_cards: int, counts: Counts,
            h17: bool) -> tuple[float, ...]:
    total, soft = _total(hard, has_ace)
    if total > 21:
        return (0, 0, 0, 0, 0, 0, 1.0)
    if n_cards == 2 and total == 21:
        return (0, 0, 0, 0, 0, 1.0, 0)
    if total >= 17 and not (total == 17 and soft and h17):
        out = [0.0] * 7
        out[total - 17] = 1.0
        return tuple(out)

    left = sum(counts)
    if left == 0:  # shoe ran out (only in tiny test shoes): call it a 17
        return (1.0, 0, 0, 0, 0, 0, 0)

    acc = [0.0] * 7
    for v in range(1, 11):
        c = counts[v]
        if c == 0:
            continue
        sub = _dealer(hard + v, has_ace or v == 1, n_cards + 1, _take(counts, v), h17)
        p = c / left
        for i in range(7):
            acc[i] += p * sub[i]
    return tuple(acc)


# ---------------------------------------------------------------- EVs

@dataclass(frozen=True)
class MoveEVs:
    stand: float
    hit: float
    double: float | None
    surrender: float | None


def stand_ev(total: int, dealer: dict[str, float]) -> float:
    if total > 21:
        return -1.0
    win = dealer["bust"]
    lose = dealer["blackjack"]
    for t in range(17, 22):
        p = dealer[str(t)]
        if t < total:
            win += p
        elif t > total:
            lose += p
    return win - lose


def move_evs(hand: Hand, counts: Counts, dealer: dict[str, float],
             can_double: bool, can_surrender: bool) -> MoveEVs:
    """Expected value per unit bet for each move.

    Approximation: the dealer's distribution is computed once from the current
    shoe and is not updated for cards the player draws. The effect is tiny.
    """
    dkey = tuple(dealer[k] for k in OUTCOMES)
    hard, has_ace = hand.hard_total, hand.has_ace
    s = stand_ev(hand.total, dealer)
    h = _hit_ev(hard, has_ace, counts, dkey)

    d = None
    if can_double:
        left = sum(counts)
        d = 0.0
        for v in range(1, 11):
            if counts[v]:
                t, _ = _total(hard + v, has_ace or v == 1)
                d += counts[v] / left * 2 * stand_ev(t, dealer)
    return MoveEVs(s, h, d, -0.5 if can_surrender else None)


@lru_cache(maxsize=200_000)
def _hit_ev(hard: int, has_ace: bool, counts: Counts, dkey: tuple[float, ...]) -> float:
    dealer = dict(zip(OUTCOMES, dkey))
    left = sum(counts)
    if left == 0:
        return stand_ev(_total(hard, has_ace)[0], dealer)
    ev = 0.0
    for v in range(1, 11):
        c = counts[v]
        if c == 0:
            continue
        nh, na = hard + v, has_ace or v == 1
        t, _ = _total(nh, na)
        if t > 21:
            best = -1.0
        elif t == 21:
            best = stand_ev(21, dealer)
        else:
            best = max(stand_ev(t, dealer), _hit_ev(nh, na, _take(counts, v), dkey))
        ev += c / left * best
    return ev
