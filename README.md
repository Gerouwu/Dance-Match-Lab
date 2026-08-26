# Dance Biomechanics Comparator

Dance Biomechanics Comparator is a Python-based prototype for comparing dance choreographies using body landmarks, joint angles, and biomechanical features. The project uses video `100190` as the reference benchmark and is designed to support comparison against a second user-provided video.

The system aims to create a game-like visual experience inspired by dance rhythm games, displaying two choreographies side by side with body landmarks, skeletal connections, and relevant joint angles. It computes global and interval-based similarity scores using Dynamic Time Warping (DTW) and biomechanical analysis strategies.

Rather than performing a rigid clinical movement assessment, this project focuses on flexible choreography comparison. It tolerates natural differences in timing, speed, movement amplitude, and individual dance style. The system also analyzes the features generated in `biomech_features.py`, selects the most useful ones, normalizes them, and complements them when necessary.

The expected result is a modular interface capable of visualizing choreography similarity through scores, segment-level metrics, and interpretive feedback such as `Excellent`, `Good`, `Out of Sync`, or `Different Movement`.

## Current Status

This is an experimental prototype. It currently supports:

- Benchmark video comparison using `100190`.
- User video comparison through MediaPipe landmark extraction.
- Side-by-side visual interface.
- Body landmark and skeleton overlays.
- Selected joint angle visualization.
- DTW-based global similarity score.
- Similarity scores by body group: arms, legs, torso, and motion.
- Interval-based similarity metrics.
- Interpretive feedback per segment.

## Project Structure

```text
.
|-- app/
|   `-- src/
|       |-- biomech_features.py        # Biomechanical feature extraction
|       |-- dance_compare_ui.py        # Main visual comparison interface
|       |-- dance_similarity.py        # DTW, scoring, feature selection, intervals
|       |-- funciones_pose_engine.py   # MediaPipe pose extraction and drawing helpers
|       |-- landmark_saving.py         # Batch landmark/feature extraction script
|       `-- test_env.py                # Runtime dependency check
|-- data/
|   |-- input/                         # Optional input videos
|   `-- output/                        # Optional exported landmarks
|-- output/
|   |-- features/                      # Cached biomechanical feature matrices
|   `-- landmarks/                     # Cached landmark arrays
|-- videos/                            # Local video files
|-- pyproject.toml                     # Direct project dependencies
|-- uv.lock                            # Reproducible, cross-platform dependency lock
`-- run_dance_compare.ps1              # Windows launcher using uv
```

## Requirements

The project uses [uv](https://docs.astral.sh/uv/) to install Python and the locked dependencies locally.

Main dependencies:

- Python 3.10
- OpenCV
- MediaPipe
- NumPy
- SciPy
- Pillow
- Tkinter

Tkinter is included with the standard CPython installation on Windows. The visual interface uses Tkinter instead of `cv2.imshow`.

## Environment Setup

Install `uv`, clone the repository, and run:

```powershell
uv python install 3.10
uv sync --locked
```

`uv` creates the project environment in `.venv` and uses the Python version pinned in `.python-version`. Verify the complete runtime without activating the environment:

```powershell
uv run --locked python app\src\test_env.py
```

All project commands should be executed through `uv run --locked`, which uses the exact versions in `uv.lock`.

## Quick Start

Run a demo by comparing the benchmark video against itself. The PowerShell launcher delegates to `uv run --locked`:

```powershell
.\run_dance_compare.ps1 --demo
```

Compare the benchmark against a user video:

```powershell
.\run_dance_compare.ps1 --user-video videos\1000160.mp4
```

Run only the metric report without opening the interface:

```powershell
.\run_dance_compare.ps1 --user-video videos\1000160.mp4 --headless-report
```

Change the interval size for segment-level scoring:

```powershell
.\run_dance_compare.ps1 --user-video videos\1000160.mp4 --interval-seconds 5
```

The equivalent cross-platform command is:

```powershell
uv run --locked python app/src/dance_compare_ui.py --demo
```

## Interface Controls

When the visual interface is open:

- `Space`: pause or resume playback.
- `R`: restart playback.
- `Q` or `Esc`: close the interface.

## How the Comparison Works

The comparison pipeline has four main stages:

1. Extract body landmarks from each video using MediaPipe Pose.
2. Convert landmarks into biomechanical features.
3. Select and normalize dance-relevant features.
4. Compare both sequences with DTW and convert distances into similarity scores.

DTW is used because two dancers may perform the same choreography with different timing, small delays, or speed variations. This makes the comparison more tolerant than frame-by-frame matching.

## Feature Strategy

The full biomechanical feature set can contain hundreds of columns. For choreography comparison, the system does not use every feature blindly.

Currently prioritized:

- Normalized key body landmarks.
- Major joint angles.
- Segment orientations and lengths.
- Important body distances.
- Landmark speeds.
- Motion energy.
- Symmetry indicators.
- Trunk and posture-related metrics.

Currently de-emphasized or discarded from the main score:

- Raw body scale.
- Individual visibility flags.
- High-noise acceleration features.
- Features with too many missing values.

All selected features are robustly normalized before DTW.

## Scoring

The system computes:

- Global similarity score from `0` to `100`.
- Body group scores:
  - Arms
  - Legs
  - Torso
  - Motion
- Interval-level scores.
- Segment feedback labels.

Feedback labels are intentionally permissive:

- `Excellent`: strong similarity in movement pattern, posture, and rhythm.
- `Good`: acceptable similarity with natural variations.
- `Out of Sync`: similar movement pattern with timing differences.
- `Different Movement`: clear biomechanical difference from the benchmark segment.

## Using Precomputed Landmarks

If landmarks were already extracted, they can be passed directly:

```powershell
.\run_dance_compare.ps1 --user-video videos\1000160.mp4 --user-landmarks data\output\pose_landmarks_frontal.csv
```

Supported landmark formats:

- `.npy` arrays saved as `(frame_id, landmarks)` pairs.
- `.csv` files with `33 * (x, y, z)` landmark coordinates.
- `.csv` files with `33 * (x, y, z, visibility)` landmark coordinates.

If visibility is missing, it is filled with `1.0`.

## Development Notes

Recommended workflow:

1. Keep benchmark assets cached in `output/landmarks` and `output/features`.
2. Use `uv run --locked` or `run_dance_compare.ps1` to guarantee the locked environment.
3. Add new user videos under `videos/`.
4. Generate or cache landmarks/features for repeated experiments.
5. Tune feature weights in `dance_similarity.py` as the scoring model evolves.

## Limitations

- This is not a clinical biomechanics assessment tool.
- The scoring model is heuristic and should be calibrated with more dance examples.
- Camera angle, framing, occlusion, and MediaPipe detection quality can affect scores.
- DTW improves tolerance to timing differences, but large choreography mismatches may still produce misleading alignments.
- Current feedback labels are rule-based and should be validated with real users.

## Roadmap Ideas

- Add a file picker for user video selection.
- Export comparison reports to CSV or JSON.
- Save annotated comparison videos.
- Support multiple benchmark choreographies.
- Add per-joint score visualization.
- Improve temporal feedback for early/late movement detection.
- Add Streamlit or PyQt interface variants.
- Train a calibrated scoring model using labeled dance attempts.

## License

MIT License
