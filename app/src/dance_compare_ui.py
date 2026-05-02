from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

from dance_similarity import (
    DRAW_ANGLES,
    DanceComparison,
    DanceSequence,
    compare_dance_sequences,
    feature_strategy_summary,
    sequence_from_video,
)


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
WINDOW_NAME = "Dance Match Lab"
VISIBILITY_THRESHOLD = 0.60

PANEL_W = 620
PANEL_H = 360
MARGIN = 24
HEADER_H = 54
BOTTOM_H = 270
CANVAS_W = PANEL_W * 2 + MARGIN * 3
CANVAS_H = HEADER_H + PANEL_H + BOTTOM_H + MARGIN

POSE_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),
    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),
    (9, 10),
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (17, 19),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (18, 20),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (27, 29),
    (27, 31),
    (29, 31),
    (24, 26),
    (26, 28),
    (28, 30),
    (28, 32),
    (30, 32),
)

ANGLE_DEFS = {
    "left_shoulder": (13, 11, 23),
    "right_shoulder": (14, 12, 24),
    "left_elbow": (11, 13, 15),
    "right_elbow": (12, 14, 16),
    "left_wrist": (13, 15, 19),
    "right_wrist": (14, 16, 20),
    "left_hip": (11, 23, 25),
    "right_hip": (12, 24, 26),
    "left_knee": (23, 25, 27),
    "right_knee": (24, 26, 28),
    "left_ankle": (25, 27, 31),
    "right_ankle": (26, 28, 32),
}

ANGLE_LABELS = {
    "left_shoulder": "L-Shoulder",
    "right_shoulder": "R-Shoulder",
    "left_elbow": "L-Elbow",
    "right_elbow": "R-Elbow",
    "left_hip": "L-Hip",
    "right_hip": "R-Hip",
    "left_knee": "L-Knee",
    "right_knee": "R-Knee",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interfaz tipo juego para comparar coreografias con landmarks y DTW."
    )
    parser.add_argument("--benchmark-id", default="100190", help="Id del benchmark fijo.")
    parser.add_argument("--benchmark-video", default=None, help="Ruta explicita al video benchmark.")
    parser.add_argument("--user-video", default=None, help="Ruta al video del usuario.")
    parser.add_argument("--user-landmarks", default=None, help="Ruta a landmarks del usuario (.npy o .csv).")
    parser.add_argument("--user-features", default=None, help="Ruta a features del usuario (.npz).")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Usa el benchmark como video de usuario para probar la interfaz.",
    )
    parser.add_argument(
        "--target-fps",
        type=float,
        default=12.0,
        help="FPS de trabajo para DTW. Menor valor = comparacion mas rapida.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=10.0,
        help="Duracion de los segmentos para metricas parciales.",
    )
    parser.add_argument(
        "--cache-missing",
        action="store_true",
        help="Guarda landmarks/features si no existen en output/.",
    )
    parser.add_argument(
        "--headless-report",
        action="store_true",
        help="Calcula metricas y sale sin abrir ventana.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Python ejecutado: {sys.executable}")
    benchmark_video = resolve_benchmark_video(args.benchmark_id, args.benchmark_video)
    benchmark_landmarks = PROJECT_ROOT / "output" / "landmarks" / f"{args.benchmark_id}_landmarks.npy"
    benchmark_features = PROJECT_ROOT / "output" / "features" / f"{args.benchmark_id}_features.npz"

    print(f"Benchmark: {benchmark_video}")
    benchmark = sequence_from_video(
        name=f"Benchmark {args.benchmark_id}",
        video_path=benchmark_video,
        landmarks_path=benchmark_landmarks,
        features_path=benchmark_features,
        cache_missing=args.cache_missing,
    )

    print_feature_summary(benchmark)

    user: DanceSequence | None = None
    comparison: DanceComparison | None = None
    user_video = resolve_user_video(args.user_video, benchmark_video, args.demo)

    if args.demo:
        user = DanceSequence(
            name="Usuario demo",
            video_path=benchmark.video_path,
            fps=benchmark.fps,
            frame_count=benchmark.frame_count,
            landmarks=benchmark.landmarks,
            matrix=benchmark.matrix,
            feature_names=benchmark.feature_names,
        )
        comparison = compare_dance_sequences(
            benchmark,
            user,
            target_fps=args.target_fps,
            interval_seconds=args.interval_seconds,
        )
        print_report(comparison)
    elif user_video is not None:
        print(f"Usuario: {user_video}")
        user_landmarks = resolve_optional_path(args.user_landmarks)
        user_features = resolve_optional_path(args.user_features)
        if user_landmarks is None:
            user_landmarks = default_cache_path(user_video, "landmarks")
        if user_features is None:
            user_features = default_cache_path(user_video, "features")

        try:
            user = sequence_from_video(
                name="Usuario",
                video_path=user_video,
                landmarks_path=user_landmarks,
                features_path=user_features,
                cache_missing=args.cache_missing,
            )
            comparison = compare_dance_sequences(
                benchmark,
                user,
                target_fps=args.target_fps,
                interval_seconds=args.interval_seconds,
            )
            print_report(comparison)
        except RuntimeError as exc:
            print("\nNo pude calcular landmarks/features del usuario:")
            print(f"  {exc}")
            print("\nAbrire la interfaz en modo video, sin skeleton del usuario ni score.")
            print("Para calcular comparacion en este Python 3.13, pasa landmarks ya extraidos:")
            print("  python app\\src\\dance_compare_ui.py --user-video videos\\1000160.mp4 --user-landmarks data\\output\\pose_landmarks_frontal.csv")
            fps, frame_count = get_video_info_for_ui(user_video)
            user = DanceSequence(
                name="Usuario (sin landmarks)",
                video_path=user_video,
                fps=fps,
                frame_count=frame_count,
                landmarks=[],
                matrix=np.empty((0, 0), dtype=np.float32),
                feature_names=[],
            )
    else:
        print("Sin video de usuario. La interfaz mostrara un panel de carga pendiente.")
        print("Cuando tengas el video, ejecuta: python app/src/dance_compare_ui.py --user-video videos/tu_video.mp4")

    if args.headless_report:
        return

    run_interface(benchmark, user, comparison, args.interval_seconds)


def resolve_benchmark_video(benchmark_id: str, explicit_path: str | None) -> Path:
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if path.exists():
            return path
        raise FileNotFoundError(f"No existe el benchmark indicado: {path}")

    candidates = [
        PROJECT_ROOT / "videos" / f"{benchmark_id}.mp4",
        PROJECT_ROOT / "data" / "input" / f"{benchmark_id}.mp4",
        Path.cwd() / "videos" / f"{benchmark_id}.mp4",
        Path.cwd() / "data" / "input" / f"{benchmark_id}.mp4",
        Path("/workspace/input") / f"{benchmark_id}.mp4",
    ]

    for path in candidates:
        if path.exists():
            return path.resolve()

    joined = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(f"No encontre el video benchmark {benchmark_id}. Busque en:\n{joined}")


def resolve_user_video(user_video: str | None, benchmark_video: Path, demo: bool) -> Path | None:
    if demo:
        return benchmark_video
    if not user_video:
        return None
    path = Path(user_video).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"No existe el video de usuario: {path}")
    return path


def resolve_optional_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo indicado: {path}")
    return path


def default_cache_path(video_path: Path, kind: str) -> Path | None:
    stem = video_path.stem
    if kind == "landmarks":
        candidates = [
            PROJECT_ROOT / "output" / "landmarks" / f"{stem}_landmarks.npy",
            PROJECT_ROOT / "output" / "landmarks" / f"{stem}_landmarks.csv",
        ]
    elif kind == "features":
        candidates = [PROJECT_ROOT / "output" / "features" / f"{stem}_features.npz"]
    else:
        return None

    for path in candidates:
        if path.exists():
            return path
    return None


def get_video_info_for_ui(video_path: Path) -> tuple[float, int]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"No se pudo abrir el video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps is None or fps <= 0 or not np.isfinite(fps):
        fps = 30.0
    return float(fps), frame_count


def print_feature_summary(sequence: DanceSequence) -> None:
    summary = feature_strategy_summary(sequence.feature_names)
    print("Features revisadas:")
    print(f"  total: {summary['total_features']}")
    print(f"  seleccionadas para baile: {summary['selected_features']}")
    print(f"  aceleraciones descartadas: {summary['discarded_accelerations']}")
    print(f"  flags de visibilidad descartadas: {summary['discarded_visibility_flags']}")
    print("  ejemplos seleccionados:", ", ".join(summary["selected_examples"]))


def print_report(comparison: DanceComparison) -> None:
    print(f"Similarity Score: {comparison.global_score:.1f}/100")
    if comparison.group_scores:
        groups = ", ".join(f"{name}={score:.1f}" for name, score in comparison.group_scores.items())
        print(f"Grupos: {groups}")

    print("Intervalos:")
    for interval in comparison.intervals:
        print(
            f"  {interval.start_sec:5.1f}-{interval.end_sec:5.1f}s "
            f"{interval.score:5.1f}/100 {interval.label} "
            f"lag={interval.lag_sec:+.2f}s"
        )


def run_interface(
    benchmark: DanceSequence,
    user: DanceSequence | None,
    comparison: DanceComparison | None,
    interval_seconds: float,
) -> None:
    import tkinter as tk
    from PIL import Image, ImageTk

    cap_b = cv2.VideoCapture(str(benchmark.video_path))
    cap_u = cv2.VideoCapture(str(user.video_path)) if user is not None else None

    if not cap_b.isOpened():
        raise FileNotFoundError(f"No se pudo abrir benchmark: {benchmark.video_path}")
    if user is not None and (cap_u is None or not cap_u.isOpened()):
        raise FileNotFoundError(f"No se pudo abrir usuario: {user.video_path}")

    delay = max(1, int(1000 / max(benchmark.fps, 1.0)))
    frame_idx = 0
    paused = False
    last_canvas = None
    closed = False

    root = tk.Tk()
    root.title(WINDOW_NAME)
    root.configure(bg="#160f28")
    root.resizable(False, False)

    image_label = tk.Label(root, bg="#160f28", bd=0)
    image_label.pack()

    print("Ventana Tkinter abierta. Teclas: q/Esc salir, espacio pausa, r reiniciar.")

    def release() -> None:
        nonlocal closed
        if closed:
            return
        closed = True
        cap_b.release()
        if cap_u is not None:
            cap_u.release()
        root.destroy()

    def reset() -> None:
        nonlocal frame_idx, last_canvas
        frame_idx = 0
        last_canvas = None
        cap_b.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if cap_u is not None:
            cap_u.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def on_key(event: tk.Event) -> None:
        nonlocal paused
        key = event.keysym.lower()
        if key in {"q", "escape"}:
            release()
        elif key == "space":
            paused = not paused
        elif key == "r":
            reset()

    def build_next_canvas() -> np.ndarray:
        nonlocal frame_idx

        if frame_idx >= benchmark.frame_count:
            frame_idx = 0
            cap_b.set(cv2.CAP_PROP_POS_FRAMES, 0)

        ret_b, frame_b = cap_b.read()
        if not ret_b:
            frame_idx = 0
            cap_b.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_b, frame_b = cap_b.read()
            if not ret_b:
                return placeholder_full_canvas("No se pudo leer el benchmark")

        frame_b = prepare_video_frame(frame_b, benchmark, frame_idx)

        if user is not None and cap_u is not None:
            user_idx = mapped_user_frame(frame_idx, benchmark, user, comparison)
            cap_u.set(cv2.CAP_PROP_POS_FRAMES, int(user_idx))
            ret_u, frame_u = cap_u.read()
            if ret_u:
                frame_u = prepare_video_frame(frame_u, user, user_idx)
            else:
                frame_u = placeholder_panel("USER VIDEO", "Frame no disponible")
        else:
            frame_u = placeholder_panel("USER VIDEO SLOT", "Pendiente --user-video")

        current_time = frame_idx / max(benchmark.fps, 1e-6)
        frame_idx += 1
        return compose_canvas(
            frame_b,
            frame_u,
            benchmark,
            user,
            comparison,
            current_time,
            interval_seconds,
        )

    def tick() -> None:
        nonlocal last_canvas
        if closed:
            return

        if not paused or last_canvas is None:
            last_canvas = build_next_canvas()

        rgb = cv2.cvtColor(last_canvas, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        photo = ImageTk.PhotoImage(image=image)
        image_label.configure(image=photo)
        image_label.image = photo

        root.after(delay if not paused else 60, tick)

    root.bind("<Key>", on_key)
    root.protocol("WM_DELETE_WINDOW", release)
    tick()
    root.mainloop()


def mapped_user_frame(
    bench_frame_idx: int,
    benchmark: DanceSequence,
    user: DanceSequence,
    comparison: DanceComparison | None,
) -> int:
    if comparison is not None and 0 <= bench_frame_idx < len(comparison.bench_to_user_frame):
        return int(comparison.bench_to_user_frame[bench_frame_idx])

    user_frame = int(round((bench_frame_idx / max(benchmark.fps, 1e-6)) * user.fps))
    return int(np.clip(user_frame, 0, max(0, user.frame_count - 1)))


def prepare_video_frame(frame: np.ndarray, sequence: DanceSequence, frame_idx: int) -> np.ndarray:
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (PANEL_W, PANEL_H), interpolation=cv2.INTER_AREA)
    landmarks = landmarks_at(sequence, frame_idx)

    if landmarks is not None and np.isfinite(landmarks).any():
        draw_pose_overlay(frame, landmarks)

    return frame


def landmarks_at(sequence: DanceSequence, frame_idx: int) -> np.ndarray | None:
    if frame_idx < 0 or frame_idx >= len(sequence.landmarks):
        return None
    return sequence.landmarks[frame_idx][1]


def landmark_visible(landmarks: np.ndarray, idx: int, threshold: float = VISIBILITY_THRESHOLD) -> bool:
    if landmarks is None or idx >= len(landmarks):
        return False
    x, y, z, visibility = landmarks[idx]
    if not np.isfinite(x) or not np.isfinite(y) or not np.isfinite(z) or not np.isfinite(visibility):
        return False
    return visibility >= threshold


def landmark_to_pixel(landmarks: np.ndarray, idx: int, width: int, height: int) -> tuple[int, int] | None:
    x = landmarks[idx][0]
    y = landmarks[idx][1]
    if not np.isfinite(x) or not np.isfinite(y):
        return None
    return int(x * width), int(y * height)


def trio_visible(
    landmarks: np.ndarray,
    idx1: int,
    idx2: int,
    idx3: int,
    threshold: float = VISIBILITY_THRESHOLD,
) -> bool:
    return (
        landmark_visible(landmarks, idx1, threshold)
        and landmark_visible(landmarks, idx2, threshold)
        and landmark_visible(landmarks, idx3, threshold)
    )


def angle_between_points(a: tuple[int, int], b: tuple[int, int], c: tuple[int, int]) -> float:
    a_arr = np.asarray(a, dtype=np.float32)
    b_arr = np.asarray(b, dtype=np.float32)
    c_arr = np.asarray(c, dtype=np.float32)
    ba = a_arr - b_arr
    bc = c_arr - b_arr
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-6:
        return float("nan")
    cos_angle = np.clip(float(np.dot(ba, bc) / denom), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def calcular_angulos_frame(
    landmarks: np.ndarray,
    width: int,
    height: int,
    visibility_threshold: float = VISIBILITY_THRESHOLD,
) -> dict[str, float]:
    angles: dict[str, float] = {}

    for name, (idx1, idx2, idx3) in ANGLE_DEFS.items():
        if not trio_visible(landmarks, idx1, idx2, idx3, visibility_threshold):
            angles[name] = np.nan
            continue

        p1 = landmark_to_pixel(landmarks, idx1, width, height)
        p2 = landmark_to_pixel(landmarks, idx2, width, height)
        p3 = landmark_to_pixel(landmarks, idx3, width, height)
        if p1 is None or p2 is None or p3 is None:
            angles[name] = np.nan
            continue

        angles[name] = angle_between_points(p1, p2, p3)

    return angles


def draw_skeleton(frame: np.ndarray, landmarks: np.ndarray) -> None:
    h, w = frame.shape[:2]
    for start_idx, end_idx in POSE_CONNECTIONS:
        if landmark_visible(landmarks, start_idx) and landmark_visible(landmarks, end_idx):
            p1 = landmark_to_pixel(landmarks, start_idx, w, h)
            p2 = landmark_to_pixel(landmarks, end_idx, w, h)
            if p1 is not None and p2 is not None:
                cv2.line(frame, p1, p2, (0, 235, 255), 2)

    for idx in range(min(33, len(landmarks))):
        if landmark_visible(landmarks, idx):
            point = landmark_to_pixel(landmarks, idx, w, h)
            if point is not None:
                cv2.circle(frame, point, 3, (255, 0, 180), -1)


def draw_joint_angle(
    frame: np.ndarray,
    landmarks: np.ndarray,
    angle_name: str,
    angle_value: float,
) -> None:
    if angle_name not in ANGLE_DEFS or not np.isfinite(angle_value):
        return

    h, w = frame.shape[:2]
    idx1, idx2, idx3 = ANGLE_DEFS[angle_name]

    if not trio_visible(landmarks, idx1, idx2, idx3):
        return

    p1 = landmark_to_pixel(landmarks, idx1, w, h)
    p2 = landmark_to_pixel(landmarks, idx2, w, h)
    p3 = landmark_to_pixel(landmarks, idx3, w, h)
    if p1 is None or p2 is None or p3 is None:
        return

    side_color = (60, 255, 120) if angle_name.startswith("left") else (255, 70, 210)
    cv2.line(frame, p2, p1, side_color, 2)
    cv2.line(frame, p2, p3, side_color, 2)
    cv2.circle(frame, p2, 6, (255, 255, 255), -1)

    label = ANGLE_LABELS.get(angle_name, angle_name)
    text = f"{label}: {int(round(angle_value))}"
    cv2.putText(frame, text, (p2[0] + 8, p2[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 3)
    cv2.putText(frame, text, (p2[0] + 8, p2[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)


def draw_pose_overlay(frame: np.ndarray, landmarks: np.ndarray) -> None:
    h, w = frame.shape[:2]
    draw_skeleton(frame, landmarks)
    angles = calcular_angulos_frame(landmarks, w, h, visibility_threshold=VISIBILITY_THRESHOLD)

    for angle_name in DRAW_ANGLES:
        draw_joint_angle(frame, landmarks, angle_name, angles.get(angle_name, np.nan))


def placeholder_panel(title: str, subtitle: str) -> np.ndarray:
    panel = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
    panel[:, :] = (22, 16, 40)
    cv2.rectangle(panel, (0, 0), (PANEL_W - 1, PANEL_H - 1), (255, 0, 180), 3)
    cv2.line(panel, (0, PANEL_H - 45), (PANEL_W, 40), (0, 220, 255), 2)
    draw_centered_text(panel, title, PANEL_H // 2 - 12, 1.0, (255, 255, 255), 2)
    draw_centered_text(panel, subtitle, PANEL_H // 2 + 28, 0.65, (0, 230, 255), 2)
    return panel


def placeholder_full_canvas(message: str) -> np.ndarray:
    canvas = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
    paint_background(canvas)
    draw_centered_text(canvas, WINDOW_NAME, CANVAS_H // 2 - 28, 1.1, (255, 255, 255), 2)
    draw_centered_text(canvas, message, CANVAS_H // 2 + 18, 0.7, (0, 230, 255), 2)
    return canvas


def compose_canvas(
    frame_b: np.ndarray,
    frame_u: np.ndarray,
    benchmark: DanceSequence,
    user: DanceSequence | None,
    comparison: DanceComparison | None,
    current_time: float,
    interval_seconds: float,
) -> np.ndarray:
    canvas = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
    paint_background(canvas)

    cv2.putText(canvas, "DANCE MATCH LAB", (MARGIN, 36), cv2.FONT_HERSHEY_DUPLEX, 1.05, (255, 255, 255), 2)
    score_text = "Similarity Score: --/100"
    if comparison is not None:
        score_text = f"Similarity Score: {comparison.global_score:05.1f}/100"
    cv2.putText(canvas, score_text, (CANVAS_W - 430, 36), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 245, 255), 2)

    left_x = MARGIN
    right_x = MARGIN * 2 + PANEL_W
    top_y = HEADER_H

    put_panel(canvas, frame_b, left_x, top_y, benchmark.name, (0, 240, 255))
    user_name = user.name if user is not None else "Usuario pendiente"
    put_panel(canvas, frame_u, right_x, top_y, user_name, (255, 0, 190))

    bottom_y = HEADER_H + PANEL_H + 18
    draw_score_dashboard(canvas, comparison, bottom_y, current_time, interval_seconds)

    return canvas


def paint_background(canvas: np.ndarray) -> None:
    h, w = canvas.shape[:2]
    for y in range(h):
        blend = y / max(1, h - 1)
        base = np.array([35 + 25 * blend, 15 + 10 * blend, 55 + 45 * blend])
        canvas[y, :] = base.astype(np.uint8)

    cv2.line(canvas, (0, 52), (w, 12), (255, 0, 180), 2)
    cv2.line(canvas, (0, h - 65), (w, h - 130), (0, 220, 255), 2)
    cv2.line(canvas, (w // 2, 52), (w // 2, HEADER_H + PANEL_H + 8), (255, 255, 255), 1)


def put_panel(
    canvas: np.ndarray,
    frame: np.ndarray,
    x: int,
    y: int,
    title: str,
    border_color: tuple[int, int, int],
) -> None:
    cv2.rectangle(canvas, (x - 4, y - 4), (x + PANEL_W + 4, y + PANEL_H + 4), border_color, 3)
    cv2.rectangle(canvas, (x - 4, y - 34), (x + PANEL_W + 4, y - 5), border_color, -1)
    cv2.putText(canvas, title.upper(), (x + 12, y - 13), cv2.FONT_HERSHEY_DUPLEX, 0.62, (20, 15, 35), 2)
    canvas[y : y + PANEL_H, x : x + PANEL_W] = frame


def draw_score_dashboard(
    canvas: np.ndarray,
    comparison: DanceComparison | None,
    y: int,
    current_time: float,
    interval_seconds: float,
) -> None:
    x = MARGIN
    score = comparison.global_score if comparison is not None else 0.0
    draw_metric_bar(canvas, x, y, CANVAS_W - MARGIN * 2, 26, score, "GLOBAL")

    group_y = y + 44
    group_x = x
    groups = comparison.group_scores if comparison is not None else {}
    for label in ("arms", "legs", "torso", "motion"):
        value = groups.get(label, 0.0)
        draw_metric_bar(canvas, group_x, group_y, 285, 20, value, label.upper())
        group_x += 310

    intervals_y = group_y + 45
    cv2.putText(canvas, "SEGMENTOS", (x, intervals_y - 8), cv2.FONT_HERSHEY_DUPLEX, 0.58, (255, 255, 255), 1)

    if comparison is None or not comparison.intervals:
        cv2.putText(
            canvas,
            "Carga un video de usuario para calcular similitud global y por intervalos.",
            (x, intervals_y + 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            (210, 210, 230),
            2,
        )
        return

    active_idx = int(current_time // max(interval_seconds, 1.0))
    draw_interval_strip(canvas, comparison, x, intervals_y + 4, CANVAS_W - MARGIN * 2, active_idx)
    draw_active_interval(canvas, comparison, x, intervals_y + 82, active_idx)


def draw_metric_bar(
    canvas: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    value: float,
    label: str,
) -> None:
    value = float(np.clip(value, 0.0, 100.0))
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (55, 45, 75), -1)
    fill_w = int(w * value / 100.0)
    cv2.rectangle(canvas, (x, y), (x + fill_w, y + h), color_for_score(value), -1)
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (235, 235, 245), 1)
    cv2.putText(canvas, f"{label} {value:04.1f}", (x + 8, y + h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)


def draw_interval_strip(
    canvas: np.ndarray,
    comparison: DanceComparison,
    x: int,
    y: int,
    w: int,
    active_idx: int,
) -> None:
    intervals = comparison.intervals
    gap = 5
    cell_w = max(34, int((w - gap * (len(intervals) - 1)) / max(1, len(intervals))))
    cell_h = 54

    for i, interval in enumerate(intervals):
        cell_x = x + i * (cell_w + gap)
        if cell_x + cell_w > x + w:
            break

        color = color_for_score(interval.score)
        cv2.rectangle(canvas, (cell_x, y), (cell_x + cell_w, y + cell_h), color, -1)
        border = (255, 255, 255) if i == active_idx else (80, 70, 100)
        cv2.rectangle(canvas, (cell_x, y), (cell_x + cell_w, y + cell_h), border, 2)

        cv2.putText(
            canvas,
            f"{int(interval.score):02d}",
            (cell_x + 8, y + 22),
            cv2.FONT_HERSHEY_DUPLEX,
            0.58,
            (20, 15, 35),
            2,
        )
        cv2.putText(
            canvas,
            interval.label[:10],
            (cell_x + 6, y + 43),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (20, 15, 35),
            1,
        )


def draw_active_interval(
    canvas: np.ndarray,
    comparison: DanceComparison,
    x: int,
    y: int,
    active_idx: int,
) -> None:
    active_idx = int(np.clip(active_idx, 0, len(comparison.intervals) - 1))
    interval = comparison.intervals[active_idx]
    cv2.rectangle(canvas, (x, y), (CANVAS_W - MARGIN, y + 72), (35, 25, 55), -1)
    cv2.rectangle(canvas, (x, y), (CANVAS_W - MARGIN, y + 72), color_for_score(interval.score), 2)

    text = (
        f"{interval.start_sec:04.1f}-{interval.end_sec:04.1f}s  "
        f"{interval.label}  {interval.score:04.1f}/100"
    )
    cv2.putText(canvas, text, (x + 14, y + 27), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2)
    detail = f"{interval.detail} | lag {interval.lag_sec:+.2f}s | amplitud {safe_number(interval.amplitude_delta)}"
    cv2.putText(canvas, detail, (x + 14, y + 56), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (210, 225, 245), 1)


def color_for_score(score: float) -> tuple[int, int, int]:
    if score >= 86:
        return (45, 230, 100)
    if score >= 72:
        return (0, 220, 255)
    if score >= 58:
        return (0, 165, 255)
    return (80, 80, 245)


def safe_number(value: float) -> str:
    if not np.isfinite(value):
        return "--"
    return f"{value:.2f}"


def draw_centered_text(
    image: np.ndarray,
    text: str,
    y: int,
    scale: float,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale, thickness)
    x = max(0, (image.shape[1] - tw) // 2)
    cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, color, thickness)


if __name__ == "__main__":
    main()
