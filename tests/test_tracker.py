from bjvision.cards import parse_label
from bjvision.detector import Detection
from bjvision.tracker import CardTracker, merge_corners


def det(label, cx, cy, conf=0.9, size=20):
    return Detection(label, parse_label(label),
                     (cx - size, cy - size, cx + size, cy + size), conf)


def test_two_corners_become_one_card():
    cards = merge_corners([det("KS", 100, 100), det("KS", 180, 220)], max_dist=300)
    assert len(cards) == 1
    assert cards[0].center == (140, 160)


def test_far_apart_duplicates_stay_separate():
    cards = merge_corners([det("KS", 100, 100), det("KS", 1100, 600)], max_dist=300)
    assert len(cards) == 2


def test_close_up_card_corners_merge():
    # Measured on a photo: one ace filling much of the frame, corners 422 px
    # apart with ~106 px corner boxes, beyond the 20%-of-diagonal limit (203 px).
    a = Detection("AS", parse_label("AS"), (443, 92, 489, 187), 0.94)
    b = Detection("AS", parse_label("AS"), (636, 467, 682, 563), 0.94)
    assert len(merge_corners([a, b], max_dist=203)) == 1


def test_different_labels_not_merged():
    cards = merge_corners([det("KS", 100, 100), det("QS", 110, 110)], max_dist=300)
    assert len(cards) == 2


def test_flicker_is_smoothed():
    tr = CardTracker(window=10, min_hits=6)
    shape = (720, 1280, 3)
    frames = [[det("7H", 500, 500)]] * 5 + [[]] * 1
    for f in frames:
        out = tr.update(f, shape)
    assert out == []                 # only 5 hits so far
    out = tr.update([det("7H", 500, 500)], shape)
    assert [c.label for c in out] == ["7H"]


def test_unmerged_corners_capped_by_deck_count():
    # Two far-apart KS detections: two cards in a 6-deck shoe, but only one
    # can exist in a single deck, so it's one card whose corners didn't merge.
    shape = (720, 1280, 3)
    frame = [det("KS", 100, 100), det("KS", 1100, 600)]
    for max_copies, expected in ((None, 2), (6, 2), (1, 1)):
        tr = CardTracker(window=10, min_hits=6, max_copies=max_copies)
        for _ in range(6):
            out = tr.update(frame, shape)
        assert len(out) == expected


def test_one_off_misdetection_ignored():
    tr = CardTracker(window=10, min_hits=6)
    shape = (720, 1280, 3)
    for i in range(10):
        extra = [det("2C", 900, 200)] if i == 4 else []
        out = tr.update([det("7H", 500, 500), *extra], shape)
    assert [c.label for c in out] == ["7H"]
