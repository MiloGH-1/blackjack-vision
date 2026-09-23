"""Camera-free mode: type the cards in.

    python -m bjvision.cli --player 10 6 --dealer 6
    python -m bjvision.cli --player A 7 --dealer 9 --decks 2 --h17
"""

from __future__ import annotations

import argparse

from .advisor import analyse, summary_lines
from .cards import Card, normalise_rank
from .hands import Hand
from .shoe import Shoe
from .strategy import Rules


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Blackjack advice from typed-in cards")
    ap.add_argument("--player", nargs="+", required=True, help="your cards, e.g. A 7")
    ap.add_argument("--dealer", required=True, help="dealer upcard, e.g. 9")
    ap.add_argument("--decks", type=int, default=6)
    ap.add_argument("--h17", action="store_true", help="dealer hits soft 17")
    ap.add_argument("--no-das", action="store_true", help="no double after split")
    ap.add_argument("--no-surrender", action="store_true")
    ap.add_argument("--seen", nargs="*", default=[],
                    help="cards already played from this shoe (improves the odds)")
    args = ap.parse_args(argv)

    rules = Rules(decks=args.decks, dealer_hits_soft_17=args.h17,
                  double_after_split=not args.no_das, surrender=not args.no_surrender)
    player = Hand([Card(normalise_rank(r)) for r in args.player])
    dealer = Hand([Card(normalise_rank(args.dealer))])
    shoe = Shoe(rules.decks)
    shoe.discard(Card(normalise_rank(r)) for r in args.seen)

    for line in summary_lines(analyse(player, dealer, shoe, rules)):
        print(line)


if __name__ == "__main__":
    main()
