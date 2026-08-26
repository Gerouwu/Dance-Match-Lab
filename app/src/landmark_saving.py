from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from biomech_features import biomech_rows_to_matrix, extract_biomechanical_features
from funciones_pose_engine import vector_pose_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrae landmarks y features biomecanicas de uno o varios videos."
    )
    parser.add_argument(
        "videos",
        nargs="*",
        help="Rutas de videos. Si se omiten, procesa los videos de videos/.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directorio para landmarks/ y features/. Por defecto: output/.",
    )
    return parser.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def discover_videos(values: list[str]) -> list[Path]:
    if values:
        paths = [resolve_path(value) for value in values]
    else:
        videos_dir = PROJECT_ROOT / "videos"
        if not videos_dir.exists():
            raise FileNotFoundError(
                "No existe videos/. Crea la carpeta, agrega archivos o pasa sus rutas al comando."
            )
        paths = sorted(
            path for path in videos_dir.iterdir() if path.suffix.lower() in VIDEO_EXTENSIONS
        )

    missing = [path for path in paths if not path.is_file()]
    if missing:
        joined = "\n".join(str(path) for path in missing)
        raise FileNotFoundError(f"No se encontraron estos videos:\n{joined}")
    if not paths:
        raise FileNotFoundError("No se encontraron videos para procesar.")
    return paths


def process_video(video_path: Path, output_dir: Path) -> tuple[Path, Path, tuple[int, int]]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        landmarks = vector_pose_engine(cap)
    finally:
        cap.release()

    landmarks_dir = output_dir / "landmarks"
    features_dir = output_dir / "features"
    landmarks_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    landmark_path = landmarks_dir / f"{video_path.stem}_landmarks.npy"
    np.save(landmark_path, np.array(landmarks, dtype=object), allow_pickle=True)

    feature_rows = extract_biomechanical_features(
        landmarks,
        fps=fps,
        include_temporal=True,
    )
    matrix, feature_names, frame_ids = biomech_rows_to_matrix(feature_rows)

    feature_path = features_dir / f"{video_path.stem}_features.npz"
    np.savez_compressed(
        feature_path,
        X=matrix,
        feature_names=np.array(feature_names),
        frame_ids=frame_ids,
    )
    return landmark_path, feature_path, matrix.shape


def main() -> None:
    args = parse_args()
    videos = discover_videos(args.videos)
    output_dir = resolve_path(args.output_dir)
    errors: list[tuple[Path, Exception]] = []

    for index, video_path in enumerate(videos, start=1):
        print(f"[{index}/{len(videos)}] Procesando: {video_path}")
        try:
            landmark_path, feature_path, shape = process_video(video_path, output_dir)
            print(f"  Landmarks: {landmark_path}")
            print(f"  Features: {feature_path} ({shape[0]} frames x {shape[1]} features)")
        except Exception as exc:  # Continue processing the remaining videos.
            errors.append((video_path, exc))
            print(f"  Error: {exc}")

    if errors:
        print("\nVideos con error:")
        for video_path, exc in errors:
            print(f"  - {video_path}: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
