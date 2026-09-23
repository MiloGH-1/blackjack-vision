import pytest

from bjvision.cards import Card
from bjvision.hands import Hand
from bjvision.probability import bust_probability, dealer_outcomes, move_evs
from bjvision.shoe import Shoe, full_shoe


def hand(*ranks):
    return Hand([Card(r) for r in ranks])


def test_full_shoe_size():
    assert sum(full_shoe(1)) == 52
    assert sum(full_shoe(6)) == 312


def test_bust_hard_16_six_decks():
    # 10+6 vs dealer 6 removed: busting cards are 6..10
    shoe = Shoe(6)
    counts = shoe.remaining([Card("10"), Card("6"), Card("6")])
    expected = (22 + 24 + 24 + 24 + 95) / 309
    assert bust_probability(hand("10", "6"), counts) == pytest.approx(expected)
    assert expected == pytest.approx(8 / 13, abs=0.01)   # close to infinite-deck value


def test_soft_hand_never_busts_on_one_hit():
    assert bust_probability(hand("A", "6"), full_shoe(6)) == 0


def test_hard_11_never_busts():
    assert bust_probability(hand("6", "5"), full_shoe(6)) == 0


def test_hard_12_busts_on_tens_only():
    counts = full_shoe(1)
    assert bust_probability(hand("7", "5"), counts) == pytest.approx(16 / 52)


@pytest.mark.parametrize("up", range(1, 11))
@pytest.mark.parametrize("h17", [False, True])
def test_dealer_distribution_sums_to_one(up, h17):
    dist = dealer_outcomes(up, full_shoe(6), h17, peeks=True)
    assert sum(dist.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("up,bust", [
    (1, 0.1165), (2, 0.3536), (3, 0.3739), (4, 0.3945), (5, 0.4165),
    (6, 0.4231), (7, 0.2623), (8, 0.2447), (9, 0.2284), (10, 0.2123),
])
def test_dealer_bust_rates_match_published(up, bust):
    # Published S17 infinite-deck figures (no peek); 6 decks is within a hair.
    dist = dealer_outcomes(up, full_shoe(6), hits_soft_17=False, peeks=False)
    assert dist["bust"] == pytest.approx(bust, abs=0.003)


def test_peek_removes_dealer_blackjack():
    assert dealer_outcomes(10, full_shoe(6), False, peeks=True)["blackjack"] == 0
    assert dealer_outcomes(10, full_shoe(6), False, peeks=False)["blackjack"] > 0.07


def test_evs_agree_with_strategy():
    counts = full_shoe(6)
    d6 = dealer_outcomes(6, counts, False)
    ev20 = move_evs(hand("10", "10"), counts, d6, True, True)
    assert ev20.stand > ev20.hit

    ev11 = move_evs(hand("7", "4"), counts, d6, True, True)
    assert ev11.double > ev11.hit > ev11.stand

    d10 = dealer_outcomes(10, counts, False)
    ev16 = move_evs(hand("10", "6"), counts, d10, True, True)
    assert ev16.surrender > max(ev16.hit, ev16.stand)
