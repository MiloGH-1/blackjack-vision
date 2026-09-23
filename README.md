# Blackjack Vision

Point a camera (laptop webcam or your phone) at a blackjack table and get:

- **The basic-strategy move**: hit, stand, double, split or surrender. It adjusts for deck count, whether the dealer hits soft 17, double after split, and surrender.
- **Your odds of busting if you hit**, worked out from the cards actually left in the shoe.
- **The dealer's outcome distribution**: bust %, and the chance of finishing on 17, 18, 19, 20 or 21.
- **The expected value** of each move, plus a Hi-Lo running and true count.

The dealer's cards go **above** the on-screen line and yours go **below** it.

> For learning and practice. Using a device to help you play in a real casino is illegal in many places.

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
pytest              # 100+ tests for strategy, odds and tracking
```

### Try it without a camera

```powershell
python -m bjvision.cli --player 10 6 --dealer 6
python -m bjvision.cli --player A 7 --dealer 9 --decks 2 --h17
python -m bjvision.cli --player 10 2 --dealer 4 --seen 2 3 4 5 6 5 4   # cards already played
```

## Card-detection model

The live app needs YOLOv8 weights at `models/cards.pt`. The model must be trained on playing-card classes named like `10H`, `KS` or `AC`.

1. Get a dataset in **YOLOv8 format**. Roboflow Universe has several 52-class sets; search for "playing cards" (e.g. the Augmented Startups *playing-cards* dataset). Export as "YOLOv8" and unzip into `datasets/playing-cards/`.
2. Train. A free Colab or Kaggle GPU takes about 1–2 hours. A local GTX 1070 works too once you install the CUDA build of PyTorch (see below).
   ```powershell
   python scripts/train.py --data datasets/playing-cards/data.yaml --epochs 50
   ```
   This copies the best weights to `models/cards.pt`.
3. Check it on a photo:
   ```powershell
   python scripts/detect_image.py my_table.jpg --show
   ```

Or, if you find already-trained weights for the same classes, drop them in `models/cards.pt`.

**GPU (optional):** by default pip installs CPU-only PyTorch on Windows. That's fine for running the app. For faster training on your NVIDIA card:
```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
```

## Using your phone as the camera

- **Easiest:** install **DroidCam** or **Iriun Webcam** on the phone and the laptop. The phone then shows up as an ordinary webcam, usually index `1`.
- **Or:** use an IP-camera app (e.g. "IP Webcam" on Android) and use its stream URL.

```powershell
python scripts/test_camera.py --source 1
python scripts/test_camera.py --source http://192.168.1.20:8080/video
```

Set the one that works as `camera:` in `config.yaml`.

## Run it

```powershell
python -m bjvision                 # uses config.yaml
python -m bjvision --camera 1      # override the camera
```

| Key | Action |
|---|---|
| `D` | cycle decks 1 / 2 / 4 / 6 / 8 (resets the shoe) |
| `H` | dealer hits / stands on soft 17 |
| `S` | double after split on/off |
| `R` | surrender on/off |
| `N` | new shoe (forget the cards already played) |
| `Space` | freeze the frame |
| `↑` / `↓` or `[` / `]` | move the dealer/player divider |
| `Q` / `Esc` | quit |

When the table has been clear for about 2 seconds, the round's cards count as played. They're removed from the shoe for the odds and added to the count.

## How it works

```
camera ─▶ detector (YOLOv8) ─▶ tracker ─▶ split by divider ─▶ advisor ─▶ overlay
                                 │                               ├─ strategy.py     basic-strategy tables + rule overrides
                                 │                               ├─ probability.py  bust %, dealer outcomes, EVs
                                 │                               └─ shoe.py         remaining cards, Hi-Lo count
                                 └─ merges the two corner detections of one card and
                                    requires a card in 6 of the last 10 frames
```

| File | What it does |
|---|---|
| `src/bjvision/strategy.py` | 4–8 deck S17 DAS chart, with H17 and 1–2 deck overrides |
| `src/bjvision/probability.py` | exact finite-shoe dealer recursion (matches published bust tables) |
| `src/bjvision/tracker.py` | corner merging + multi-frame smoothing |
| `config.yaml` | table rules, camera, detection thresholds |

## Known limitations

- Only one player hand. After a split, advise each hand by covering the other.
- The EV for splitting isn't calculated; the split advice comes from the strategy chart.
- Detection quality depends on the model. Good lighting, a plain background, and cards whose corners are visible help a lot.
