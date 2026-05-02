from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from biomech_features import extract_biomechanical_features, biomech_rows_to_matrix


KEY_LANDMARKS = {
    "nose",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "left_foot_index",
    "right_foot_index",
}

DANCE_ANGLES = {
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
}

DANCE_SEGMENTS = {
    "shoulder_line",
    "hip_line",
    "left_torso",
    "right_torso",
    "left_upper_arm",
    "right_upper_arm",
    "left_forearm",
    "right_forearm",
    "left_thigh",
    "right_thigh",
    "left_shin",
    "right_shin",
    "left_foot",
    "right_foot",
}

DANCE_DISTANCES = {
    "shoulders_distance",
    "hips_distance",
    "elbows_distance",
    "wrists_distance",
    "knees_distance",
    "ankles_distance",
    "feet_distance",
    "left_shoulder_to_wrist",
    "right_shoulder_to_wrist",
    "left_hip_to_wrist",
    "right_hip_to_wrist",
}

DRAW_ANGLES = (
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
)


@dataclass
class DanceSequence:
    name: str
    video_path: Path
    fps: float
    frame_count: int
    landmarks: list[tuple[int, np.ndarray]]
    matrix: np.ndarray
    feature_names: list[str]


@dataclass
class DtwAlignment:
    distance: float
    score: float
    path: list[tuple[int, int]]


@dataclass
class IntervalScore:
    index: int
    start_sec: float
    end_sec: float
    score: float
    distance: float
    label: str
    lag_sec: float
    amplitude_delta: float
    detail: str


@dataclass
class DanceComparison:
    global_score: float
    global_distance: float
    selected_features: list[str]
    group_scores: dict[str, float]
    intervals: list[IntervalScore]
    bench_to_user_frame: np.ndarray
    path: list[tuple[int, int]]
    bench_sample_idx: np.ndarray
    user_sample_idx: np.ndarray


def get_video_info(video_path: Path) -> tuple[float, int]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"No se pudo abrir el video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if fps is None or fps <= 0 or not np.isfinite(fps):
        fps = 30.0

    return float(fps), frame_count


def load_landmarks(path: Path) -> list[tuple[int, np.ndarray]]:
    if path.suffix.lower() == ".csv":
        return load_landmarks_csv(path)

    arr = np.load(path, allow_pickle=True)
    out: list[tuple[int, np.ndarray]] = []

    for i, item in enumerate(arr):
        frame_id = i + 1
        landmarks = item

        if isinstance(item, np.ndarray) and item.shape == (2,):
            frame_id = int(item[0])
            landmarks = item[1]
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            frame_id = int(item[0])
            landmarks = item[1]

        out.append((frame_id, np.asarray(landmarks, dtype=np.float32)))

    return out


def load_landmarks_csv(path: Path) -> list[tuple[int, np.ndarray]]:
    data = np.genfromtxt(path, delimiter=",", skip_header=1, dtype=np.float32)
    if data.ndim == 1:
        data = data.reshape(1, -1)

    col_count = data.shape[1]
    if col_count == 100:
        frame_ids = data[:, 0].astype(np.int32) + 1
        coords = data[:, 1:].reshape(len(data), 33, 3)
        visibility = np.ones((len(data), 33, 1), dtype=np.float32)
        landmarks = np.concatenate([coords, visibility], axis=2)
    elif col_count == 133:
        frame_ids = data[:, 0].astype(np.int32) + 1
        landmarks = data[:, 1:].reshape(len(data), 33, 4)
    elif col_count == 99:
        frame_ids = np.arange(1, len(data) + 1, dtype=np.int32)
        coords = data.reshape(len(data), 33, 3)
        visibility = np.ones((len(data), 33, 1), dtype=np.float32)
        landmarks = np.concatenate([coords, visibility], axis=2)
    elif col_count == 132:
        frame_ids = np.arange(1, len(data) + 1, dtype=np.int32)
        landmarks = data.reshape(len(data), 33, 4)
    else:
        raise ValueError(
            f"CSV de landmarks no soportado: {path} tiene {col_count} columnas. "
            "Se esperan 99/100 columnas para x,y,z o 132/133 para x,y,z,visibility."
        )

    return [(int(frame_id), landmarks[i].astype(np.float32)) for i, frame_id in enumerate(frame_ids)]


def save_landmarks(path: Path, landmarks: list[tuple[int, np.ndarray]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.array(landmarks, dtype=object), allow_pickle=True)


def extract_landmarks_from_video(video_path: Path) -> list[tuple[int, np.ndarray]]:
    try:
        from funciones_pose_engine import vector_pose_engine
    except ModuleNotFoundError as exc:
        if exc.name == "mediapipe":
            raise RuntimeError(
                "No se pudieron extraer landmarks porque este Python no tiene mediapipe. "
                "Usa Python 3.10 con las dependencias del environment.yml, ejecuta dentro del contenedor, "
                "o pasa landmarks ya extraidos con --user-landmarks."
            ) from exc
        raise

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"No se pudo abrir el video: {video_path}")
    return vector_pose_engine(cap)


def load_feature_matrix(path: Path) -> tuple[np.ndarray, list[str]]:
    data = np.load(path, allow_pickle=True)
    return data["X"].astype(np.float32), [str(x) for x in data["feature_names"]]


def save_feature_matrix(path: Path, matrix: np.ndarray, feature_names: list[str], frame_ids: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        X=matrix,
        feature_names=np.array(feature_names),
        frame_ids=frame_ids,
    )


def sequence_from_video(
    name: str,
    video_path: Path,
    landmarks_path: Path | None = None,
    features_path: Path | None = None,
    cache_missing: bool = False,
) -> DanceSequence:
    fps, frame_count = get_video_info(video_path)

    if landmarks_path is not None and landmarks_path.exists():
        landmarks = load_landmarks(landmarks_path)
    else:
        landmarks = extract_landmarks_from_video(video_path)
        if cache_missing and landmarks_path is not None:
            save_landmarks(landmarks_path, landmarks)

    if features_path is not None and features_path.exists():
        matrix, feature_names = load_feature_matrix(features_path)
    else:
        rows = extract_biomechanical_features(
            landmarks,
            fps=fps,
            include_temporal=True,
        )
        matrix, feature_names, frame_ids = biomech_rows_to_matrix(rows)
        if cache_missing and features_path is not None:
            save_feature_matrix(features_path, matrix, feature_names, frame_ids)

    if frame_count <= 0:
        frame_count = len(landmarks)

    return DanceSequence(
        name=name,
        video_path=video_path,
        fps=fps,
        frame_count=frame_count,
        landmarks=landmarks,
        matrix=matrix,
        feature_names=feature_names,
    )


def feature_strategy_summary(feature_names: Iterable[str]) -> dict[str, object]:
    feature_names = list(feature_names)
    selected, weights = select_dance_features(feature_names)
    excluded_acc = [name for name in feature_names if name.endswith("_acc")]
    excluded_vis = [name for name in feature_names if name.startswith("vis_")]

    return {
        "total_features": len(feature_names),
        "selected_features": len(selected),
        "selected_examples": selected[:12],
        "discarded_accelerations": len(excluded_acc),
        "discarded_visibility_flags": len(excluded_vis),
        "weight_min": float(np.min(weights)) if len(weights) else 0.0,
        "weight_max": float(np.max(weights)) if len(weights) else 0.0,
    }


def select_dance_features(feature_names: Iterable[str]) -> tuple[list[str], np.ndarray]:
    selected: list[str] = []
    weights: list[float] = []

    for name in feature_names:
        weight = dance_feature_weight(name)
        if weight > 0:
            selected.append(name)
            weights.append(weight)

    return selected, np.asarray(weights, dtype=np.float32)


def dance_feature_weight(name: str) -> float:
    if name == "frame_id":
        return 0.0
    if name.startswith("vis_"):
        return 0.0
    if name.endswith("_acc"):
        return 0.0
    if name == "body_scale_raw":
        return 0.0

    if name == "visible_landmark_ratio":
        return 0.25

    if _is_key_landmark_coord(name):
        if name.endswith("_z_norm"):
            return 0.25
        return 0.95

    for angle in DANCE_ANGLES:
        if name == f"{angle}_angle_deg":
            if angle.endswith("ankle"):
                return 0.75
            return 1.35
        if name == f"{angle}_angle_deg_vel":
            return 0.65

    for segment in DANCE_SEGMENTS:
        if name == f"{segment}_orientation_deg":
            return 0.8
        if name == f"{segment}_length_norm":
            return 0.55

    for distance in DANCE_DISTANCES:
        if name == f"{distance}_norm":
            return 0.55
        if name == f"{distance}_norm_vel":
            return 0.35

    if name.endswith("_speed_norm_s"):
        return 0.65

    if name.startswith("motion_energy") or name == "angular_motion_energy":
        return 0.75

    if "symmetry" in name and not name.endswith("_vel"):
        return 0.45

    if name in {"trunk_lean_deg", "trunk_abs_lean_deg", "head_trunk_angle_deg"}:
        return 0.85

    if name in {"trunk_length_norm", "nose_to_mid_shoulders_norm"}:
        return 0.5

    return 0.0


def _is_key_landmark_coord(name: str) -> bool:
    for landmark in KEY_LANDMARKS:
        if (
            name == f"{landmark}_x_norm"
            or name == f"{landmark}_y_norm"
            or name == f"{landmark}_z_norm"
        ):
            return True
    return False


def compare_dance_sequences(
    benchmark: DanceSequence,
    user: DanceSequence,
    target_fps: float = 12.0,
    interval_seconds: float = 10.0,
) -> DanceComparison:
    b_mat, u_mat, names, weights = _select_common_feature_matrix(benchmark, user)
    b_norm, u_norm, names, weights = _robust_normalize_pair(b_mat, u_mat, names, weights)

    b_down, b_idx = downsample_matrix(b_norm, benchmark.fps, target_fps)
    u_down, u_idx = downsample_matrix(u_norm, user.fps, target_fps)

    alignment = dtw_align(b_down, u_down, weights)
    group_scores = score_groups_from_path(b_down, u_down, alignment.path, names, weights)
    intervals = score_intervals_from_path(
        b_down,
        u_down,
        alignment.path,
        b_idx,
        u_idx,
        benchmark.fps,
        user.fps,
        benchmark.frame_count,
        interval_seconds,
        weights,
    )

    frame_map = build_benchmark_to_user_frame_map(
        alignment.path,
        b_idx,
        u_idx,
        benchmark.frame_count,
        user.frame_count,
    )

    return DanceComparison(
        global_score=alignment.score,
        global_distance=alignment.distance,
        selected_features=names,
        group_scores=group_scores,
        intervals=intervals,
        bench_to_user_frame=frame_map,
        path=alignment.path,
        bench_sample_idx=b_idx,
        user_sample_idx=u_idx,
    )


def _select_common_feature_matrix(
    benchmark: DanceSequence,
    user: DanceSequence,
) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    b_index = {name: i for i, name in enumerate(benchmark.feature_names)}
    u_index = {name: i for i, name in enumerate(user.feature_names)}
    common = [name for name in benchmark.feature_names if name in u_index]
    selected, weight_by_position = select_dance_features(common)

    if not selected:
        raise ValueError("No hay features biomecanicas compatibles para comparar.")

    weights = []
    b_cols = []
    u_cols = []
    weight_lookup = dict(zip(selected, weight_by_position))

    for name in selected:
        b_cols.append(b_index[name])
        u_cols.append(u_index[name])
        weights.append(weight_lookup[name])

    return (
        benchmark.matrix[:, b_cols].astype(np.float32),
        user.matrix[:, u_cols].astype(np.float32),
        selected,
        np.asarray(weights, dtype=np.float32),
    )


def _robust_normalize_pair(
    benchmark: np.ndarray,
    user: np.ndarray,
    names: list[str],
    weights: np.ndarray,
    min_valid_ratio: float = 0.15,
) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    combined = np.vstack([benchmark, user])
    finite_ratio = np.mean(np.isfinite(combined), axis=0)
    keep = finite_ratio >= min_valid_ratio

    if not np.any(keep):
        raise ValueError("Las features seleccionadas estan vacias o contienen demasiados NaN.")

    benchmark = benchmark[:, keep]
    user = user[:, keep]
    weights = weights[keep]
    names = [name for name, ok in zip(names, keep) if ok]
    combined = np.vstack([benchmark, user])

    med = np.nanmedian(combined, axis=0)
    q25 = np.nanpercentile(combined, 25, axis=0)
    q75 = np.nanpercentile(combined, 75, axis=0)
    scale = q75 - q25

    fallback = np.nanstd(combined, axis=0)
    scale = np.where(np.isfinite(scale) & (scale > 1e-6), scale, fallback)
    scale = np.where(np.isfinite(scale) & (scale > 1e-6), scale, 1.0)
    med = np.where(np.isfinite(med), med, 0.0)

    b_norm = (benchmark - med) / scale
    u_norm = (user - med) / scale
    b_norm = np.where(np.isfinite(b_norm), b_norm, 0.0)
    u_norm = np.where(np.isfinite(u_norm), u_norm, 0.0)

    return (
        np.clip(b_norm, -6.0, 6.0).astype(np.float32),
        np.clip(u_norm, -6.0, 6.0).astype(np.float32),
        names,
        weights.astype(np.float32),
    )


def downsample_matrix(matrix: np.ndarray, source_fps: float, target_fps: float) -> tuple[np.ndarray, np.ndarray]:
    if len(matrix) == 0:
        return matrix, np.array([], dtype=np.int32)

    if source_fps <= 0 or target_fps <= 0:
        step = 1
    else:
        step = max(1, int(round(source_fps / target_fps)))

    idx = np.arange(0, len(matrix), step, dtype=np.int32)
    return matrix[idx], idx


def dtw_align(a: np.ndarray, b: np.ndarray, weights: np.ndarray) -> DtwAlignment:
    if len(a) == 0 or len(b) == 0:
        raise ValueError("DTW necesita dos secuencias no vacias.")

    n, m = len(a), len(b)
    inf = np.float32(1e12)
    direction = np.zeros((n, m), dtype=np.uint8)
    prev = np.full(m + 1, inf, dtype=np.float32)
    prev[0] = 0.0

    for i in range(1, n + 1):
        curr = np.full(m + 1, inf, dtype=np.float32)
        costs = weighted_row_distance(a[i - 1], b, weights)

        for j in range(1, m + 1):
            diag = prev[j - 1]
            up = prev[j]
            left = curr[j - 1]

            if diag <= up and diag <= left:
                best = diag
                move = 0
            elif up <= left:
                best = up
                move = 1
            else:
                best = left
                move = 2

            curr[j] = costs[j - 1] + best
            direction[i - 1, j - 1] = move

        prev = curr

    path = _backtrack_path(direction)
    distance = float(prev[m] / max(1, len(path)))
    score = score_from_distance(distance)

    return DtwAlignment(distance=distance, score=score, path=path)


def _backtrack_path(direction: np.ndarray) -> list[tuple[int, int]]:
    i = direction.shape[0] - 1
    j = direction.shape[1] - 1
    path: list[tuple[int, int]] = []

    while i >= 0 and j >= 0:
        path.append((i, j))

        if i == 0 and j == 0:
            break
        if i == 0:
            j -= 1
            continue
        if j == 0:
            i -= 1
            continue

        move = direction[i, j]
        if move == 0:
            i -= 1
            j -= 1
        elif move == 1:
            i -= 1
        else:
            j -= 1

    path.reverse()
    return path


def weighted_row_distance(row: np.ndarray, matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    diff = np.abs(matrix - row)
    denom = float(np.sum(weights))
    if denom <= 1e-8:
        return np.mean(diff, axis=1)
    return np.sum(diff * weights, axis=1) / denom


def weighted_path_distance(
    a: np.ndarray,
    b: np.ndarray,
    path: list[tuple[int, int]],
    weights: np.ndarray,
    cols: np.ndarray | None = None,
) -> float:
    if not path:
        return float("nan")

    if cols is not None:
        a = a[:, cols]
        b = b[:, cols]
        weights = weights[cols]

    denom = float(np.sum(weights))
    if denom <= 1e-8:
        denom = float(len(weights))
        weights = np.ones_like(weights)

    costs = []
    for i, j in path:
        costs.append(float(np.sum(np.abs(a[i] - b[j]) * weights) / denom))

    return float(np.mean(costs)) if costs else float("nan")


def score_from_distance(distance: float, sensitivity: float = 1.55) -> float:
    if not np.isfinite(distance):
        return 0.0
    score = 100.0 * np.exp(-max(0.0, distance) / sensitivity)
    return float(np.clip(score, 0.0, 100.0))


def score_groups_from_path(
    a: np.ndarray,
    b: np.ndarray,
    path: list[tuple[int, int]],
    names: list[str],
    weights: np.ndarray,
) -> dict[str, float]:
    groups = {
        "arms": _group_columns(names, ("arm", "elbow", "wrist", "hand")),
        "legs": _group_columns(names, ("leg", "knee", "ankle", "foot", "thigh", "shin")),
        "torso": _group_columns(names, ("torso", "trunk", "hip", "shoulder", "nose")),
        "motion": _group_columns(names, ("speed", "motion_energy", "angular_motion")),
    }

    scores: dict[str, float] = {}
    for group_name, cols in groups.items():
        if len(cols) == 0:
            continue
        distance = weighted_path_distance(a, b, path, weights, cols=cols)
        scores[group_name] = score_from_distance(distance)

    return scores


def _group_columns(names: list[str], tokens: tuple[str, ...]) -> np.ndarray:
    cols = [i for i, name in enumerate(names) if any(token in name for token in tokens)]
    return np.asarray(cols, dtype=np.int32)


def score_intervals_from_path(
    a: np.ndarray,
    b: np.ndarray,
    path: list[tuple[int, int]],
    b_idx: np.ndarray,
    u_idx: np.ndarray,
    b_fps: float,
    u_fps: float,
    b_frame_count: int,
    interval_seconds: float,
    weights: np.ndarray,
) -> list[IntervalScore]:
    if not path:
        return []

    path_arr = np.asarray(path, dtype=np.int32)
    b_path_frames = b_idx[path_arr[:, 0]]
    u_path_frames = u_idx[path_arr[:, 1]]
    b_times = b_path_frames / max(b_fps, 1e-6)
    u_times = u_path_frames / max(u_fps, 1e-6)

    total_seconds = b_frame_count / max(b_fps, 1e-6)
    interval_seconds = max(1.0, float(interval_seconds))
    interval_count = int(np.ceil(total_seconds / interval_seconds))
    intervals: list[IntervalScore] = []

    for index in range(interval_count):
        start = index * interval_seconds
        end = min(total_seconds, start + interval_seconds)
        mask = (b_times >= start) & (b_times < end)

        if np.count_nonzero(mask) < 2:
            intervals.append(
                IntervalScore(
                    index=index,
                    start_sec=start,
                    end_sec=end,
                    score=0.0,
                    distance=float("nan"),
                    label="Sin datos",
                    lag_sec=0.0,
                    amplitude_delta=float("nan"),
                    detail="Pocos landmarks utiles",
                )
            )
            continue

        segment_path = [tuple(x) for x in path_arr[mask]]
        distance = weighted_path_distance(a, b, segment_path, weights)
        score = score_from_distance(distance)
        lag = float(np.median(u_times[mask] - b_times[mask]))
        amplitude_delta = segment_amplitude_delta(a, b, segment_path)
        label, detail = interval_feedback(score, lag, amplitude_delta, interval_seconds)

        intervals.append(
            IntervalScore(
                index=index,
                start_sec=start,
                end_sec=end,
                score=score,
                distance=distance,
                label=label,
                lag_sec=lag,
                amplitude_delta=amplitude_delta,
                detail=detail,
            )
        )

    return intervals


def segment_amplitude_delta(
    a: np.ndarray,
    b: np.ndarray,
    path: list[tuple[int, int]],
) -> float:
    if len(path) < 2:
        return float("nan")

    b_rows = sorted({i for i, _ in path})
    u_rows = sorted({j for _, j in path})
    if len(b_rows) < 2 or len(u_rows) < 2:
        return float("nan")

    b_std = np.std(a[b_rows], axis=0)
    u_std = np.std(b[u_rows], axis=0)
    denom = np.maximum(np.abs(b_std), 0.35)
    delta = np.abs(b_std - u_std) / denom
    return float(np.nanmedian(delta))


def interval_feedback(
    score: float,
    lag_sec: float,
    amplitude_delta: float,
    interval_seconds: float,
) -> tuple[str, str]:
    lag_limit = max(0.55, interval_seconds * 0.12)
    lagged = abs(lag_sec) > lag_limit
    amplitude_high = np.isfinite(amplitude_delta) and amplitude_delta > 0.55

    if score >= 86 and not lagged:
        return "Excelente", "Patron, postura y ritmo muy similares"
    if score >= 72:
        if lagged:
            return "Desfasado", "Movimiento parecido con diferencia de tiempo"
        if amplitude_high:
            return "Bien", "Patron correcto con amplitud distinta"
        return "Bien", "Similitud aceptable con variaciones naturales"
    if score >= 58 and lagged:
        return "Desfasado", "La forma general aparece antes o despues"
    return "Movimiento diferente", "El patron biomecanico se aleja del benchmark"


def build_benchmark_to_user_frame_map(
    path: list[tuple[int, int]],
    b_idx: np.ndarray,
    u_idx: np.ndarray,
    b_frame_count: int,
    u_frame_count: int,
) -> np.ndarray:
    if not path:
        return np.full(b_frame_count, -1, dtype=np.int32)

    path_arr = np.asarray(path, dtype=np.int32)
    b_frames = b_idx[path_arr[:, 0]]
    u_frames = u_idx[path_arr[:, 1]]

    unique_b = []
    mapped_u = []

    for frame in np.unique(b_frames):
        values = u_frames[b_frames == frame]
        unique_b.append(frame)
        mapped_u.append(float(np.median(values)))

    unique_b_arr = np.asarray(unique_b, dtype=np.float32)
    mapped_u_arr = np.asarray(mapped_u, dtype=np.float32)
    all_b = np.arange(b_frame_count, dtype=np.float32)
    interp = np.interp(all_b, unique_b_arr, mapped_u_arr)

    return np.clip(np.rint(interp), 0, max(0, u_frame_count - 1)).astype(np.int32)
