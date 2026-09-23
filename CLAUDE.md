# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`bjvision`: a camera-based blackjack assistant. YOLOv8 detects playing cards in a live camera feed. The app then shows the basic-strategy move, the player's bust chance, the dealer's outcome distribution, the EV of each move and a Hi-Lo count. It's meant for learning and practice. The README covers user-facing setup, dataset/training steps, phone-camera setup and key bindings.

## Commands

The environment is Windows with a `.venv` (Python 3.11). Install with `pip install -e ".[dev]"`.

```powershell
pytest                                          # full suite (fast, no camera/model needed)
pytest tests/test_strategy.py                   # one file
pytest tests/test_strategy.py::test_name        # one test
pytest -k soft                                  # by keyword

python -m bjvision.cli --player A 7 --dealer 9 --decks 2 --h17 --seen 2 3 4   # camera-free advice
python -m bjvision [--camera 1] [--model path.pt] [--config config.yaml]      # live app
python scripts/train.py --data datasets/playing-cards/data.yaml --epochs 50   # writes models/cards.pt
python scripts/detect_image.py photo.jpg --show
python scripts/test_camera.py --source 1
```

pytest's `pythonpath = ["src"]` setting means tests run without an install. Scripts add `src/` to `sys.path` themselves. No linter or formatter is configured.

The live app needs `models/cards.pt`, which is not in the repo (`models/*.pt`, `datasets/` and `runs/` are gitignored). Without it, `python -m bjvision` exits early and points to the CLI. The model's class names must parse as cards (`10H`, `KS`, `AC`, `Th`…); `cards.parse_label` is the single source of truth for that format.

## Architecture

Pipeline (live app, `__main__.py`):

```
Camera (threaded) → CardDetector (YOLO) → CardTracker → hands.split_by_region → advisor.analyse → overlay
```

- **Pure logic vs I/O split.** `cards`, `hands`, `shoe`, `strategy`, `probability`, `advisor` and `tracker` are pure and fully unit-tested. `camera`, `detector` (ultralytics is imported lazily inside `CardDetector.__init__`) and `overlay` touch OpenCV/YOLO and have no tests. Keep new logic on the pure side.
- **`advisor.analyse`** is the single integration point. Both the live app and `cli.py` call it, and `summary_lines` formats the text for the overlay panel and the CLI output alike. A new statistic goes into `Analysis` + `summary_lines` so both frontends pick it up.
- **Card values vs ranks.** `Card` keeps the rank (J/Q/K are distinct). All probability maths works on `shoe.Counts`, a tuple indexed by blackjack value 1..10 (index 0 unused, A=1, 10-valued cards pooled at index 10). Aces are always 1 in counts and `hard_total`; soft handling happens in `Hand.total` and `probability._total`.
- **Shoe state.** `Shoe` stores only the `seen` cards from finished rounds. `remaining(visible)` / `running_count(visible)` also subtract the cards currently on the table. In the live app, a round's cards go to `shoe.discard` once the table has been empty for `ROUND_CLEAR_SECONDS`. The largest set of stable cards seen during the round is the one discarded.
- **Strategy (`strategy.py`).** Base tables are 4–8 deck S17 DAS late-surrender (HARD/SOFT/PAIRS). They use compact codes (`H S D Ds P Ph Rh Rs Rp -`) documented in the module docstring. Rule variations are override dicts keyed by `(table, key, upcard)`, checked in `lookup` in priority order: single-deck, then ≤2-deck, then H17. `_resolve` turns codes into `Advice`, falling back when double or surrender isn't allowed (they're only allowed on the first two cards). Pairs whose code doesn't split fall through to the total.
- **Probability (`probability.py`).** `_dealer` is an exact finite-shoe recursion memoised with `lru_cache` (args must stay hashable, which is why counts are tuples). `dealer_outcomes` conditions on no dealer blackjack when `peeks` is on and the upcard is 10/A. `move_evs` uses a fixed dealer distribution; it isn't recomputed after player draws, an approximation that's documented in the code. Split EV isn't computed.
- **Tracker (`tracker.py`).** Card datasets label corner indices, so one physical card yields about 2 detections. `merge_corners` clusters same-label detections within `merge_fraction` × frame diagonal. `stable()` supports duplicate labels (multi-deck), keeping k copies of a label if at least `min_hits` of the last `window` frames showed at least k copies.
- **Dealer/player split** is purely positional. Cards above `divider` (a fraction of frame height) belong to the dealer, cards below belong to the player, and each hand is sorted left to right. Advice is only produced when exactly one dealer card is visible. Only one player hand is supported.
- **Config.** `config.py` merges `config.yaml` over `DEFAULTS`. `rules_from` builds the frozen `Rules` dataclass. The live app changes rules at runtime with `dataclasses.replace`.

## Tests

Tests in `tests/` check strategy against the published charts, and dealer odds against published bust tables. When changing tables or the recursion, keep them passing rather than adjusting expected values.
