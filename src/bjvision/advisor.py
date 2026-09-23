"""Glue: given the visible hands and the shoe, produce everything the UI shows."""

from __future__ import annotations

from dataclasses import dataclass

from .hands import Hand
from .probability import MoveEVs, bust_probability, dealer_outcomes, move_evs
from .shoe import Shoe
from .strategy import Advice, Rules, recommend


@dataclass
class Analysis:
    player: Hand
    dealer: Hand
    advice: Advice | None
    bust_if_hit: float | None
    dealer_dist: dict[str, float] | None
    evs: MoveEVs | None
    running_count: int
    true_count: float
    cards_left: int


def summary_lines(a: Analysis) -> list[str]:
    """Human-readable lines shared by the overlay and the CLI."""
    lines = [
        f"Dealer: {str(a.dealer) or '-'}   ({a.dealer.describe()})",
        f"You:    {str(a.player) or '-'}   ({a.player.describe()})",
    ]
    if a.advice and a.advice.action:
        lines.append(f"Move:   {a.advice}")
    if a.bust_if_hit is not None:
        lines.append(f"Bust if you hit: {a.bust_if_hit:.1%}")
    if a.dealer_dist:
        d = a.dealer_dist
        lines.append(f"Dealer busts: {d['bust']:.1%}")
        lines.append("Dealer ends: " + "  ".join(
            f"{k}:{d[k]:.0%}" for k in ("17", "18", "19", "20", "21")))
    if a.evs:
        e = a.evs
        parts = [f"stand {e.stand:+.3f}", f"hit {e.hit:+.3f}"]
        if e.double is not None:
            parts.append(f"double {e.double:+.3f}")
        if e.surrender is not None:
            parts.append(f"surr {e.surrender:+.3f}")
        lines.append("EV: " + "  ".join(parts))
    lines.append(f"Count RC {a.running_count:+d}  TC {a.true_count:+.1f}  "
                 f"({a.cards_left} cards left)")
    return lines


def analyse(player: Hand, dealer: Hand, shoe: Shoe, rules: Rules) -> Analysis:
    visible = [*player.cards, *dealer.cards]
    counts = shoe.remaining(visible)

    advice = dist = evs = None
    bust = bust_probability(player, counts) if player.cards else None

    if player.cards and len(dealer.cards) == 1:
        up = dealer.cards[0]
        advice = recommend(player, up, rules)
        dist = dealer_outcomes(up.value, counts, rules.dealer_hits_soft_17, rules.dealer_peeks)
        if not player.is_bust and player.total < 21:
            first_two = len(player.cards) == 2
            evs = move_evs(player, counts, dist, can_double=first_two,
                           can_surrender=first_two and rules.surrender)

    return Analysis(player, dealer, advice, bust, dist, evs,
                    shoe.running_count(visible), shoe.true_count(visible), sum(counts))
