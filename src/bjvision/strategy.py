"""Basic strategy lookup with rule variations.

Base tables are the standard 4-8 deck, dealer-stands-soft-17, double-after-split,
late-surrender chart. Overrides are layered on for H17 and for 1-2 deck games
(the main, well-known deviations only).

Codes:
  H  hit            S  stand
  D  double, else hit        Ds double, else stand
  P  split          Ph split if double-after-split allowed, else play as total
  Rh surrender, else hit     Rs surrender, else stand
  Rp surrender, else split   -  don't split (play as total)
"""

from __future__ import annotations

from dataclasses import dataclass

from .cards import Card
from .hands import Hand

UPCARDS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]


def _row(s: str) -> dict[str, str]:
    codes = s.split()
    assert len(codes) == 10, s
    return dict(zip(UPCARDS, codes))


#                  2  3  4  5  6  7  8  9  10 A
HARD = {
    9:  _row("H  D  D  D  D  H  H  H  H  H"),
    10: _row("D  D  D  D  D  D  D  D  H  H"),
    11: _row("D  D  D  D  D  D  D  D  D  H"),
    12: _row("H  H  S  S  S  H  H  H  H  H"),
    13: _row("S  S  S  S  S  H  H  H  H  H"),
    14: _row("S  S  S  S  S  H  H  H  H  H"),
    15: _row("S  S  S  S  S  H  H  H  Rh H"),
    16: _row("S  S  S  S  S  H  H  Rh Rh Rh"),
    17: _row("S  S  S  S  S  S  S  S  S  S"),
}

SOFT = {  # keyed by soft total (A2 = 13 ... A9 = 20)
    13: _row("H  H  H  D  D  H  H  H  H  H"),
    14: _row("H  H  H  D  D  H  H  H  H  H"),
    15: _row("H  H  D  D  D  H  H  H  H  H"),
    16: _row("H  H  D  D  D  H  H  H  H  H"),
    17: _row("H  D  D  D  D  H  H  H  H  H"),
    18: _row("S  Ds Ds Ds Ds S  S  H  H  H"),
    19: _row("S  S  S  S  S  S  S  S  S  S"),
    20: _row("S  S  S  S  S  S  S  S  S  S"),
}

PAIRS = {  # keyed by card value, A = 11
    2:  _row("Ph Ph P  P  P  P  -  -  -  -"),
    3:  _row("Ph Ph P  P  P  P  -  -  -  -"),
    4:  _row("-  -  -  Ph Ph -  -  -  -  -"),
    5:  _row("-  -  -  -  -  -  -  -  -  -"),
    6:  _row("Ph P  P  P  P  -  -  -  -  -"),
    7:  _row("P  P  P  P  P  P  -  -  -  -"),
    8:  _row("P  P  P  P  P  P  P  P  P  P"),
    9:  _row("P  P  P  P  P  -  P  P  -  -"),
    10: _row("-  -  -  -  -  -  -  -  -  -"),
    11: _row("P  P  P  P  P  P  P  P  P  P"),
}

# (table, key, upcard) -> code
H17_OVERRIDES = {
    ("hard", 11, "A"): "D",
    ("hard", 15, "A"): "Rh",
    ("hard", 17, "A"): "Rs",
    ("soft", 18, "2"): "Ds",
    ("soft", 19, "6"): "Ds",
    ("pair", 8, "A"): "Rp",
}

FEW_DECK_OVERRIDES = {  # 1 or 2 decks
    ("hard", 9, "2"): "D",
    ("hard", 11, "A"): "D",
}

SINGLE_DECK_OVERRIDES = {
    ("hard", 8, "5"): "D",
    ("hard", 8, "6"): "D",
    ("soft", 18, "A"): "S",
}


@dataclass(frozen=True)
class Rules:
    decks: int = 6
    dealer_hits_soft_17: bool = False
    double_after_split: bool = True
    surrender: bool = True
    dealer_peeks: bool = True


@dataclass(frozen=True)
class Advice:
    action: str   # HIT, STAND, DOUBLE, SPLIT, SURRENDER, or "" when nothing to do
    note: str = ""

    def __str__(self) -> str:
        return f"{self.action} ({self.note})" if self.note else self.action


def upcard_key(card: Card) -> str:
    v = card.value
    return "A" if v == 1 else str(v)


def lookup(table: str, key: int, up: str, rules: Rules) -> str:
    if rules.decks == 1 and (table, key, up) in SINGLE_DECK_OVERRIDES:
        return SINGLE_DECK_OVERRIDES[(table, key, up)]
    if rules.decks <= 2 and (table, key, up) in FEW_DECK_OVERRIDES:
        return FEW_DECK_OVERRIDES[(table, key, up)]
    if rules.dealer_hits_soft_17 and (table, key, up) in H17_OVERRIDES:
        return H17_OVERRIDES[(table, key, up)]
    if table == "pair":
        return PAIRS[key][up]
    if table == "soft":
        return SOFT[min(key, 20)][up]
    if key <= 8:
        return "H"
    return HARD[min(key, 17)][up]


def recommend(player: Hand, dealer_up: Card, rules: Rules = Rules()) -> Advice:
    if not player.cards:
        return Advice("", "no player cards")
    if player.is_bust:
        return Advice("", "bust")
    if player.is_blackjack:
        return Advice("STAND", "blackjack!")
    if player.total == 21:
        return Advice("STAND", "21")

    up = upcard_key(dealer_up)
    first_two = len(player.cards) == 2
    can_double = first_two
    can_surrender = first_two and rules.surrender

    if player.is_pair:
        pv = 11 if player.cards[0].rank == "A" else player.cards[0].value
        code = lookup("pair", pv, up, rules)
        if code == "P":
            return Advice("SPLIT")
        if code == "Ph" and rules.double_after_split:
            return Advice("SPLIT", "because double after split is allowed")
        if code == "Rp":
            if can_surrender:
                return Advice("SURRENDER", "else split")
            return Advice("SPLIT")
        # otherwise fall through and play the total

    if player.is_soft:
        code = "H" if player.total <= 12 else lookup("soft", player.total, up, rules)
    else:
        code = lookup("hard", player.total, up, rules)

    return _resolve(code, can_double, can_surrender)


def _resolve(code: str, can_double: bool, can_surrender: bool) -> Advice:
    if code == "H":
        return Advice("HIT")
    if code == "S":
        return Advice("STAND")
    if code == "D":
        return Advice("DOUBLE", "else hit") if can_double else Advice("HIT", "double not allowed")
    if code == "Ds":
        return Advice("DOUBLE", "else stand") if can_double else Advice("STAND", "double not allowed")
    if code == "Rh":
        return Advice("SURRENDER", "else hit") if can_surrender else Advice("HIT")
    if code == "Rs":
        return Advice("SURRENDER", "else stand") if can_surrender else Advice("STAND")
    raise ValueError(f"Unknown strategy code {code!r}")
