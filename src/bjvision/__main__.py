"""Live camera app: python -m bjvision [--camera 1] [--config config.yaml]"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace

import cv2

from .advisor import analyse
from .camera import Camera
from .config import load_config, rules_from
from .detector import CardDetector
from .hands import split_by_region
from .overlay import compose, draw_frame, draw_panel, draw_waiting
from .shoe import Shoe
from .tracker import CardTracker

WINDOW = "Blackjack Vision"
DECK_OPTIONS = [1, 2, 4, 6, 8]
ROUND_CLEAR_SECONDS = 2.0

# cv2.waitKeyEx codes for arrow keys on Windows / Linux
KEY_UP = {2490368, 65362}
KEY_DOWN = {2621440, 65364}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--camera", help="webcam index or stream URL (overrides config)")
    ap.add_argument("--model", help="path to YOLO weights (overrides config)")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    if args.camera is not None:
        cfg["camera"] = args.camera
    if args.model:
        cfg["model_path"] = args.model

    rules = rules_from(cfg)
    try:
        detector = CardDetector(cfg["model_path"], cfg["confidence"])
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Tip: try the camera-free mode: python -m bjvision.cli --player 10 6 --dealer 6",
              file=sys.stderr)
        return 1

    try:
        camera = Camera(cfg["camera"], cfg["frame_width"], cfg["frame_height"])
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Phone setup: see 'Using your phone as the camera' in README.md",
              file=sys.stderr)
        return 1
    tracker = CardTracker(cfg["smoothing_window"], cfg["smoothing_min_hits"])
    shoe = Shoe(rules.decks)
    divider = float(cfg["divider"])

    frozen = False
    last_frame = None
    detections, stable = [], []
    round_cards = []          # biggest set of cards seen during the current round
    empty_since = None

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    try:
        while True:
            if not frozen:
                frame = camera.read()
                if frame is None:
                    cv2.imshow(WINDOW, draw_waiting(cfg["frame_width"], cfg["frame_height"],
                                                    camera.source))
                    if cv2.waitKey(30) & 0xFF in (ord("q"), 27):
                        break
                    continue
                last_frame = frame
                detections = detector.detect(frame)
                stable = tracker.update(detections, frame.shape)

                # When the table has been clear for a moment, the round is over:
                # those cards have left the shoe.
                if stable:
                    empty_since = None
                    if len(stable) >= len(round_cards):
                        round_cards = [c.card for c in stable]
                elif round_cards:
                    empty_since = empty_since or time.monotonic()
                    if time.monotonic() - empty_since > ROUND_CLEAR_SECONDS:
                        shoe.discard(round_cards)
                        round_cards, empty_since = [], None

            frame = last_frame.copy()
            h = frame.shape[0]
            dealer, player = split_by_region(
                [(c.card, c.center) for c in stable], h, divider)
            analysis = analyse(player, dealer, shoe, rules)

            draw_frame(frame, detections, stable, divider, frozen)
            cv2.imshow(WINDOW, compose(frame, draw_panel(h, analysis, rules)))

            key = cv2.waitKeyEx(1)
            if key == -1:
                continue
            ch = chr(key & 0xFF).lower() if key < 256 else ""
            if ch == "q" or key == 27:
                break
            elif ch == " ":
                frozen = not frozen
            elif ch == "d":
                i = DECK_OPTIONS.index(rules.decks) if rules.decks in DECK_OPTIONS else 0
                rules = replace(rules, decks=DECK_OPTIONS[(i + 1) % len(DECK_OPTIONS)])
                shoe.reset(rules.decks)
            elif ch == "h":
                rules = replace(rules, dealer_hits_soft_17=not rules.dealer_hits_soft_17)
            elif ch == "s":
                rules = replace(rules, double_after_split=not rules.double_after_split)
            elif ch == "r":
                rules = replace(rules, surrender=not rules.surrender)
            elif ch == "n":
                shoe.reset()
                round_cards = []
            elif key in KEY_UP or ch == "[":
                divider = max(0.1, divider - 0.02)
            elif key in KEY_DOWN or ch == "]":
                divider = min(0.9, divider + 0.02)
    finally:
        camera.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
