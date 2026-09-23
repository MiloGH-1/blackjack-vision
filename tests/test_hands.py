import pytest

from bjvision.cards import Card, parse_label
from bjvision.hands import Hand, split_by_region


def hand(*ranks):
    return Hand([Card(r) for r in ranks])


@pytest.mark.parametrize("ranks,total,soft", [
    (("10", "6"), 16, False),
    (("A", "6"), 17, True),
    (("A", "6", "10"), 17, False),
    (("A", "A"), 12, True),
    (("A", "A", "9"), 21, True),
    (("K", "Q", "5"), 25, False),
])
def test_totals(ranks, total, soft):
    h = hand(*ranks)
    assert h.total == total
    assert h.is_soft == soft


def test_blackjack_and_pairs():
    assert hand("A", "K").is_blackjack
    assert not hand("A", "5", "5").is_blackjack
    assert hand("8", "8").is_pair
    assert hand("K", "10").is_pair          # same value counts as a pair
    assert hand("K", "5", "7").is_bust


@pytest.mark.parametrize("label,rank,suit", [
    ("10H", "10", "H"), ("KS", "K", "S"), ("ac", "A", "C"), ("Th", "10", "H"),
])
def test_parse_label(label, rank, suit):
    c = parse_label(label)
    assert (c.rank, c.suit) == (rank, suit)


def test_parse_label_rejects_junk():
    with pytest.raises(ValueError):
        parse_label("joker")


def test_split_top_bottom():
    dets = [
        (Card("6"), (500, 100)),    # dealer
        (Card("6"), (700, 600)),    # player, right
        (Card("10"), (400, 600)),   # player, left
    ]
    dealer, player = split_by_region(dets, (720, 1280), 0.45, layout="top-bottom")
    assert [c.rank for c in dealer.cards] == ["6"]
    assert [c.rank for c in player.cards] == ["10", "6"]


def test_split_left_right_is_default():
    dets = [
        (Card("9"), (200, 300)),    # dealer (left half)
        (Card("K"), (900, 400)),    # player, further right
        (Card("5"), (700, 500)),    # player
    ]
    dealer, player = split_by_region(dets, (720, 1280), 0.5)
    assert [c.rank for c in dealer.cards] == ["9"]
    assert [c.rank for c in player.cards] == ["5", "K"]


def test_split_rejects_unknown_layout():
    with pytest.raises(ValueError):
        split_by_region([], (720, 1280), 0.5, layout="diagonal")
