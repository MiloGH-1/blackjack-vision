"""Turn noisy per-frame detections into a stable list of cards.

Two problems are handled here:
1. Card datasets label the corner index, so one physical card usually gives
   two detections (top-left and bottom-right). Same-label detections close to
   each other are merged into one card, positioned at their midpoint.
2. Detections flicker frame to frame. A card only counts once it has been seen
   in `min_hits` of the last `window` frames.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

from .cards import Card
from .detector import Detection


@dataclass(frozen=True)
class TrackedCard:
    label: str
    card: Card
    center: tuple[float, float]


def merge_corners(detections: list[Detection], max_dist: float) -> list[TrackedCard]:
    """Cluster same-label detections within max_dist pixels into single cards."""
    clusters: list[tuple[str, Card, list[tuple[float, float]]]] = []
    for det in sorted(detections, key=lambda d: -d.conf):
        for label, _, pts in clusters:
            if label != det.label:
                continue
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            if math.dist((cx, cy), det.center) <= max_dist:
                pts.append(det.center)
                break
        else:
            clusters.append((det.label, det.card, [det.center]))

    return [
        TrackedCard(label, card, (sum(p[0] for p in pts) / len(pts),
                                  sum(p[1] for p in pts) / len(pts)))
        for label, card, pts in clusters
    ]


class CardTracker:
    def __init__(self, window: int = 10, min_hits: int = 6, merge_fraction: float = 0.2):
        self.window = window
        self.min_hits = min_hits
        self.merge_fraction = merge_fraction  # of the frame diagonal
        self.history: deque[list[TrackedCard]] = deque(maxlen=window)

    def reset(self) -> None:
        self.history.clear()

    def update(self, detections: list[Detection], frame_shape) -> list[TrackedCard]:
        h, w = frame_shape[:2]
        cards = merge_corners(detections, self.merge_fraction * math.hypot(w, h))
        self.history.append(cards)
        return self.stable()

    def stable(self) -> list[TrackedCard]:
        # How many copies of each label were visible in each recent frame
        per_frame: list[dict[str, int]] = []
        for frame in self.history:
            counts: dict[str, int] = {}
            for c in frame:
                counts[c.label] = counts.get(c.label, 0) + 1
            per_frame.append(counts)

        result: list[TrackedCard] = []
        labels = {lbl for counts in per_frame for lbl in counts}
        for label in labels:
            # largest k such that >= min_hits frames show at least k copies
            k = 0
            while sum(1 for c in per_frame if c.get(label, 0) >= k + 1) >= self.min_hits:
                k += 1
            if k == 0:
                continue
            # take positions from the most recent frame that had k copies
            for frame in reversed(self.history):
                matches = [c for c in frame if c.label == label]
                if len(matches) >= k:
                    result.extend(matches[:k])
                    break
        return result
