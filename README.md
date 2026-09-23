# Blackjack Vision

Point a camera (laptop webcam or your phone) at a blackjack table and get:

- **The basic-strategy move**: hit, stand, double, split or surrender. It adjusts for deck count, whether the dealer hits soft 17, double after split, and surrender.
- **Your odds of busting if you hit**, worked out from the cards actually left in the shoe.
- **The dealer's outcome distribution**: bust %, and the chance of finishing on 17, 18, 19, 20 or 21.
- **The expected value** of each move, plus a Hi-Lo running and true count.

The dealer's cards go **left** of the on-screen line and yours go **right** of it. Set `layout: top-bottom` in `config.yaml`, or press `L`, for dealer above and you below.

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

**Recommended: DroidCam over Wi-Fi (Android or iPhone, nothing to install on the laptop)**

1. Install **DroidCam** from the Play Store / App Store and open it. Allow camera access.
2. Put the phone and laptop on the **same Wi-Fi network** (not a guest network, which often blocks devices from seeing each other).
3. The app shows a **WiFi IP**, e.g. `192.168.1.20`. Optional check: open `http://192.168.1.20:4747/video` in a browser on the laptop. You should see the video.
4. Test it, then run the app with that address:
   ```powershell
   python scripts/test_camera.py --source 192.168.1.20
   python -m bjvision --camera 192.168.1.20
   ```
   Or set `camera: "192.168.1.20"` in `config.yaml`.

A bare IP means DroidCam's `http://<ip>:4747/video`. For other apps, give the port or the full URL, e.g. `192.168.1.20:8080` for **IP Webcam** (Android).

Tips:
- Fix the phone in place rather than holding it: prop it up facing a wall, or on a stand, with the dealer's cards on the left of the picture and yours on the right. If the picture comes out sideways, press `O` to rotate it, then set `rotate:` in `config.yaml` to keep it.
- Keep the phone app open and the screen on. If the stream drops, the window shows "Waiting for camera..." and reconnects on its own.
- Windows may ask whether Python can use the network the first time. Allow it on private networks.
- Only one program can read the phone's stream at a time. Close the browser tab after checking.

**Alternative: as a USB/virtual webcam.** Install **DroidCam Client** or **Iriun Webcam** on the laptop as well. The phone then shows up as a normal webcam. Find its index with:
```powershell
python scripts/test_camera.py --scan
python -m bjvision --camera 1
```

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
| `P` | save a snapshot (frame + detections) to `snapshots/`, for checking misreads |
| `[` / `]` or arrow keys | move the dealer/player divider |
| `L` | swap layout: dealer left / you right, or dealer above / you below |
| `O` | rotate the camera picture 90° (for a phone on its side) |
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
