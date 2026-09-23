import pytest

from bjvision.cards import Card
from bjvision.hands import Hand
from bjvision.strategy import Rules, recommend

SIX_S17 = Rules(decks=6, dealer_hits_soft_17=False)
SIX_H17 = Rules(decks=6, dealer_hits_soft_17=True)


def act(player, up, rules=SIX_S17):
    return recommend(Hand([Card(r) for r in player]), Card(up), rules).action


@pytest.mark.parametrize("player,up,expected", [
    # hard totals
    (("10", "6"), "6", "STAND"),
    (("10", "6"), "7", "HIT"),
    (("10", "6"), "10", "SURRENDER"),
    (("10", "5"), "10", "SURRENDER"),
    (("10", "2"), "3", "HIT"),
    (("10", "2"), "4", "STAND"),
    (("7", "4"), "10", "DOUBLE"),
    (("7", "4"), "A", "HIT"),
    (("6", "4"), "9", "DOUBLE"),
    (("6", "4"), "10", "HIT"),
    (("5", "4"), "2", "HIT"),
    (("5", "4"), "3", "DOUBLE"),
    (("5", "3"), "6", "HIT"),
    (("10", "7"), "A", "STAND"),
    # soft totals
    (("A", "7"), "2", "STAND"),
    (("A", "7"), "3", "DOUBLE"),
    (("A", "7"), "9", "HIT"),
    (("A", "7"), "8", "STAND"),
    (("A", "6"), "3", "DOUBLE"),
    (("A", "6"), "2", "HIT"),
    (("A", "2"), "5", "DOUBLE"),
    (("A", "2"), "4", "HIT"),
    (("A", "8"), "6", "STAND"),
    # pairs
    (("8", "8"), "10", "SPLIT"),
    (("8", "8"), "A", "SPLIT"),
    (("A", "A"), "10", "SPLIT"),
    (("K", "K"), "6", "STAND"),
    (("9", "9"), "7", "STAND"),
    (("9", "9"), "8", "SPLIT"),
    (("5", "5"), "9", "DOUBLE"),
    (("4", "4"), "5", "SPLIT"),
    (("4", "4"), "4", "HIT"),
    (("2", "2"), "2", "SPLIT"),
    (("7", "7"), "8", "HIT"),
    # blackjack
    (("A", "K"), "10", "STAND"),
])
def test_six_deck_s17(player, up, expected):
    assert act(player, up) == expected


@pytest.mark.parametrize("player,up,expected", [
    (("7", "4"), "A", "DOUBLE"),
    (("10", "5"), "A", "SURRENDER"),
    (("10", "7"), "A", "SURRENDER"),
    (("A", "7"), "2", "DOUBLE"),
    (("A", "8"), "6", "DOUBLE"),
    (("8", "8"), "A", "SURRENDER"),
])
def test_h17_changes(player, up, expected):
    assert act(player, up, SIX_H17) == expected


def test_no_das_changes_pair_splits():
    no_das = Rules(double_after_split=False)
    assert act(("2", "2"), "2", no_das) == "HIT"
    assert act(("4", "4"), "5", no_das) == "HIT"      # plays as hard 8
    assert act(("6", "6"), "2", no_das) == "HIT"


def test_no_surrender_falls_back():
    rules = Rules(surrender=False)
    assert act(("10", "6"), "10", rules) == "HIT"


def test_few_deck_deviations():
    two = Rules(decks=2)
    assert act(("5", "4"), "2", two) == "DOUBLE"
    assert act(("7", "4"), "A", two) == "DOUBLE"
    one = Rules(decks=1)
    assert act(("5", "3"), "6", one) == "DOUBLE"


def test_no_double_after_two_cards():
    assert act(("3", "3", "5"), "6") == "HIT"         # hard 11, 3 cards
    assert act(("A", "2", "5"), "4") == "STAND"       # soft 18 vs 4: Ds -> stand


def test_multi_card_21_stands():
    assert act(("5", "6", "K"), "A") == "STAND"
