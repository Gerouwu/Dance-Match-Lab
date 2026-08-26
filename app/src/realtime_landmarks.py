from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from funciones_pose_engine import visualize_pose_engine_realtime


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Muestra landmarks y angulos en tiempo real desde una camara o un video."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--camera", type=int, help="Indice de la camara. Por defecto: 0.")
    source.add_argument("--video", help="Ruta a un video local.")
    parser.add_argument(
        "--mirror",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Activa o desactiva el reflejo horizontal.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.video:
        video_path = Path(args.video).expanduser()
        if not video_path.is_absolute():
            video_path = (PROJECT_ROOT / video_path).resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"No existe el video: {video_path}")
        source: int | str = str(video_path)
        mirror = False if args.mirror is None else args.mirror
        source_label = str(video_path)
    else:
        source = 0 if args.camera is None else args.camera
        mirror = True if args.mirror is None else args.mirror
        source_label = f"camara {source}"

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir {source_label}")

    print(f"Fuente: {source_label}")
    print("Presiona Q en la ventana para salir.")
    visualize_pose_engine_realtime(cap, mirror=mirror)


if __name__ == "__main__":
    main()
