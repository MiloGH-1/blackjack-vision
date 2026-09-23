"""Drawing: detection boxes, the dealer/player divider and the info panel."""

from __future__ import annotations

import cv2
import numpy as np

from .advisor import Analysis, summary_lines
from .detector import Detection
from .strategy import Rules
from .tracker import TrackedCard

PANEL_WIDTH = 460
FONT = cv2.FONT_HERSHEY_SIMPLEX

ACTION_COLOURS = {  # BGR
    "HIT": (60, 200, 60),
    "STAND": (60, 60, 230),
    "DOUBLE": (0, 200, 255),
    "SPLIT": (230, 160, 40),
    "SURRENDER": (180, 180, 180),
}


def draw_frame(frame, detections: list[Detection], stable: list[TrackedCard],
               divider: float, frozen: bool):
    h, w = frame.shape[:2]
    y = int(h * divider)
    cv2.line(frame, (0, y), (w, y), (255, 255, 255), 2)
    cv2.putText(frame, "DEALER", (10, y - 10), FONT, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "YOU", (10, y + 28), FONT, 0.7, (255, 255, 255), 2)

    for d in detections:
        cv2.rectangle(frame, d.box[:2], d.box[2:], (0, 255, 255), 1)
    for c in stable:
        cx, cy = int(c.center[0]), int(c.center[1])
        cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1)
        cv2.putText(frame, c.label, (cx + 8, cy - 8), FONT, 0.9, (0, 0, 0), 4)
        cv2.putText(frame, c.label, (cx + 8, cy - 8), FONT, 0.9, (0, 255, 0), 2)

    if frozen:
        cv2.putText(frame, "FROZEN", (w - 140, 35), FONT, 1.0, (0, 0, 255), 3)
    return frame


def draw_panel(height: int, analysis: Analysis, rules: Rules) -> np.ndarray:
    panel = np.full((height, PANEL_WIDTH, 3), 30, dtype=np.uint8)
    y = 45

    if analysis.advice and analysis.advice.action:
        colour = ACTION_COLOURS.get(analysis.advice.action, (255, 255, 255))
        cv2.putText(panel, analysis.advice.action, (15, y), FONT, 1.4, colour, 3)
        y += 30
        if analysis.advice.note:
            cv2.putText(panel, analysis.advice.note, (15, y), FONT, 0.55, colour, 1)
        y += 30
    else:
        hint = ("Waiting for cards..." if not analysis.player.cards
                else "Need exactly 1 dealer card")
        cv2.putText(panel, hint, (15, y), FONT, 0.7, (200, 200, 200), 2)
        y += 50

    for line in summary_lines(analysis):
        for chunk in _wrap(line, 44):
            cv2.putText(panel, chunk, (15, y), FONT, 0.52, (230, 230, 230), 1)
            y += 24

    y += 12
    rules_text = [
        f"[D] decks: {rules.decks}",
        f"[H] dealer {'hits' if rules.dealer_hits_soft_17 else 'stands'} soft 17",
        f"[S] double after split: {'yes' if rules.double_after_split else 'no'}",
        f"[R] surrender: {'yes' if rules.surrender else 'no'}",
        "[N] new shoe  [Space] freeze  [Q] quit",
        "[Up/Down] or [ ] move divider",
    ]
    for line in rules_text:
        cv2.putText(panel, line, (15, y), FONT, 0.5, (150, 200, 255), 1)
        y += 22
    return panel


def draw_waiting(width: int, height: int, source) -> np.ndarray:
    """Placeholder while the camera (e.g. a phone over Wi-Fi) connects or reconnects."""
    img = np.full((height, width, 3), 30, dtype=np.uint8)
    cv2.putText(img, "Waiting for camera...", (40, height // 2 - 20), FONT, 1.2,
                (230, 230, 230), 2)
    cv2.putText(img, str(source), (40, height // 2 + 25), FONT, 0.7, (150, 200, 255), 1)
    cv2.putText(img, "[Q] quit", (40, height // 2 + 65), FONT, 0.6, (150, 150, 150), 1)
    return img


def compose(frame, panel):
    return np.hstack([frame, panel])


def _wrap(text: str, width: int) -> list[str]:
    if len(text) <= width:
        return [text]
    words, lines, cur = text.split(), [], ""
    for word in words:
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines
