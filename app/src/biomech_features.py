import numpy as np


# =========================
# CONFIGURACIÓN GENERAL
# =========================

VISIBILITY_THRESHOLD = 0.60
EPS = 1e-8


# Índices de MediaPipe Pose
LM = {
    0: "nose",
    7: "left_ear",
    8: "right_ear",

    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",

    19: "left_index",
    20: "right_index",
    21: "left_thumb",
    22: "right_thumb",

    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",

    29: "left_heel",
    30: "right_heel",
    31: "left_foot_index",
    32: "right_foot_index",
}


FEATURE_LANDMARKS = list(LM.keys())


ANGLE_DEFS = {
    # Miembro superior
    "left_shoulder":  (13, 11, 23),
    "right_shoulder": (14, 12, 24),

    "left_elbow":     (11, 13, 15),
    "right_elbow":    (12, 14, 16),

    "left_wrist":     (13, 15, 19),
    "right_wrist":    (14, 16, 20),

    # Miembro inferior
    "left_hip":       (11, 23, 25),
    "right_hip":      (12, 24, 26),

    "left_knee":      (23, 25, 27),
    "right_knee":     (24, 26, 28),

    "left_ankle":     (25, 27, 31),
    "right_ankle":    (26, 28, 32),
}


SEGMENTS = {
    # Ejes corporales
    "shoulder_line": (11, 12),
    "hip_line": (23, 24),
    "left_torso": (11, 23),
    "right_torso": (12, 24),

    # Brazos
    "left_upper_arm": (11, 13),
    "right_upper_arm": (12, 14),
    "left_forearm": (13, 15),
    "right_forearm": (14, 16),
    "left_hand": (15, 19),
    "right_hand": (16, 20),

    # Piernas
    "left_thigh": (23, 25),
    "right_thigh": (24, 26),
    "left_shin": (25, 27),
    "right_shin": (26, 28),
    "left_foot": (27, 31),
    "right_foot": (28, 32),
}


DISTANCE_PAIRS = {
    # Separaciones principales
    "shoulders_distance": (11, 12),
    "hips_distance": (23, 24),
    "elbows_distance": (13, 14),
    "wrists_distance": (15, 16),
    "knees_distance": (25, 26),
    "ankles_distance": (27, 28),
    "feet_distance": (31, 32),

    # Alcance de brazos
    "left_shoulder_to_wrist": (11, 15),
    "right_shoulder_to_wrist": (12, 16),
    "left_hip_to_wrist": (23, 15),
    "right_hip_to_wrist": (24, 16),

    # Cruces brazo-pierna
    "left_wrist_to_left_ankle": (15, 27),
    "right_wrist_to_right_ankle": (16, 28),
    "left_wrist_to_right_ankle": (15, 28),
    "right_wrist_to_left_ankle": (16, 27),

    # Mano a cabeza / torso
    "left_wrist_to_nose": (15, 0),
    "right_wrist_to_nose": (16, 0),
    "left_wrist_to_right_shoulder": (15, 12),
    "right_wrist_to_left_shoulder": (16, 11),
}


MOTION_LANDMARKS = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_foot_index": 31,
    "right_foot_index": 32,
}


# =========================
# UTILIDADES BÁSICAS
# =========================

def _is_finite_array(x):
    return x is not None and np.all(np.isfinite(x))


def _landmark_visible(landmarks, idx, threshold=VISIBILITY_THRESHOLD):
    if landmarks is None:
        return False

    if idx >= len(landmarks):
        return False

    x, y, z, vis = landmarks[idx]

    if not np.isfinite(x) or not np.isfinite(y) or not np.isfinite(z) or not np.isfinite(vis):
        return False

    return vis >= threshold


def _point(landmarks, idx, threshold=VISIBILITY_THRESHOLD):
    if not _landmark_visible(landmarks, idx, threshold):
        return None

    return np.array(
        [
            landmarks[idx][0],
            landmarks[idx][1],
            landmarks[idx][2],
        ],
        dtype=np.float32
    )


def _mean_points(points):
    valid = [p for p in points if _is_finite_array(p)]

    if len(valid) == 0:
        return None

    return np.mean(np.stack(valid, axis=0), axis=0)


def _midpoint(landmarks, idx1, idx2, threshold=VISIBILITY_THRESHOLD):
    p1 = _point(landmarks, idx1, threshold)
    p2 = _point(landmarks, idx2, threshold)

    if p1 is None or p2 is None:
        return None

    return (p1 + p2) / 2.0


def _dist(a, b):
    if not _is_finite_array(a) or not _is_finite_array(b):
        return np.nan

    return float(np.linalg.norm(a - b))


def _angle_2d(a, b, c):
    """
    Calcula el ángulo ABC en grados usando coordenadas 2D normalizadas.
    """
    if not _is_finite_array(a) or not _is_finite_array(b) or not _is_finite_array(c):
        return np.nan

    a = a[:2]
    b = b[:2]
    c = c[:2]

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba < EPS or norm_bc < EPS:
        return np.nan

    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)

    return float(np.degrees(np.arccos(cos_angle)))


def _orientation_2d_deg(a, b):
    """
    Orientación del segmento a -> b en el plano de imagen.
    """
    if not _is_finite_array(a) or not _is_finite_array(b):
        return np.nan

    dx = b[0] - a[0]
    dy = b[1] - a[1]

    if abs(dx) < EPS and abs(dy) < EPS:
        return np.nan

    return float(np.degrees(np.arctan2(dy, dx)))


def _trunk_lean_deg(mid_hip, mid_shoulder):
    """
    Inclinación del tronco respecto a la vertical.

    En imagen:
    - 0 grados: tronco vertical.
    - positivo: inclinación hacia la derecha de la imagen.
    - negativo: inclinación hacia la izquierda de la imagen.
    """
    if not _is_finite_array(mid_hip) or not _is_finite_array(mid_shoulder):
        return np.nan

    v = mid_shoulder[:2] - mid_hip[:2]

    if np.linalg.norm(v) < EPS:
        return np.nan

    return float(np.degrees(np.arctan2(v[0], -v[1])))


def _safe_ratio(num, den):
    if not np.isfinite(num) or not np.isfinite(den) or abs(den) < EPS:
        return np.nan

    return float(num / den)


def _absdiff(a, b):
    if not np.isfinite(a) or not np.isfinite(b):
        return np.nan

    return float(abs(a - b))


def _signeddiff(a, b):
    if not np.isfinite(a) or not np.isfinite(b):
        return np.nan

    return float(a - b)


# =========================
# NORMALIZACIÓN CORPORAL
# =========================

def _body_center_and_scale(landmarks, threshold=VISIBILITY_THRESHOLD):
    """
    Centro corporal:
        preferiblemente punto medio de caderas.

    Escala corporal:
        mediana entre ancho de hombros, ancho de caderas y longitud de tronco.
        Esto reduce dependencia de la distancia a la cámara.
    """
    left_shoulder = _point(landmarks, 11, threshold)
    right_shoulder = _point(landmarks, 12, threshold)
    left_hip = _point(landmarks, 23, threshold)
    right_hip = _point(landmarks, 24, threshold)

    mid_shoulders = _mean_points([left_shoulder, right_shoulder])
    mid_hips = _mean_points([left_hip, right_hip])

    center = mid_hips
    if center is None:
        center = _mean_points([left_shoulder, right_shoulder, left_hip, right_hip])

    candidates = []

    shoulder_width = _dist(left_shoulder, right_shoulder)
    hip_width = _dist(left_hip, right_hip)
    torso_length = _dist(mid_shoulders, mid_hips)

    for value in [shoulder_width, hip_width, torso_length]:
        if np.isfinite(value) and value > EPS:
            candidates.append(value)

    if len(candidates) == 0:
        scale = np.nan
    else:
        scale = float(np.median(candidates))

    return center, scale, mid_shoulders, mid_hips


def _normalized_landmarks(landmarks, threshold=VISIBILITY_THRESHOLD):
    center, scale, mid_shoulders, mid_hips = _body_center_and_scale(
        landmarks,
        threshold
    )

    norm = np.full((33, 3), np.nan, dtype=np.float32)

    if center is None or not np.isfinite(scale) or scale < EPS:
        return norm, center, scale, mid_shoulders, mid_hips

    for idx in FEATURE_LANDMARKS:
        p = _point(landmarks, idx, threshold)

        if p is not None:
            norm[idx] = (p - center) / scale

    if mid_shoulders is not None:
        mid_shoulders = (mid_shoulders - center) / scale

    if mid_hips is not None:
        mid_hips = (mid_hips - center) / scale

    return norm, center, scale, mid_shoulders, mid_hips


# =========================
# FEATURES POR FRAME
# =========================

def extract_frame_biomechanical_features(
    frame_id,
    landmarks,
    visibility_threshold=VISIBILITY_THRESHOLD
):
    """
    Extrae features biomecánicas estáticas de un frame.

    Entrada:
        frame_id: número de frame.
        landmarks: np.array shape (33, 4), formato [x, y, z, visibility].

    Salida:
        dict con features numéricas.
    """

    features = {}
    features["frame_id"] = int(frame_id)

    norm, center, scale, mid_shoulders, mid_hips = _normalized_landmarks(
        landmarks,
        visibility_threshold
    )

    # -------------------------
    # Calidad de detección
    # -------------------------

    visible_count = 0

    for idx, name in LM.items():
        is_visible = _landmark_visible(landmarks, idx, visibility_threshold)
        features[f"vis_{name}"] = float(is_visible)

        if is_visible:
            visible_count += 1

    features["visible_landmark_ratio"] = visible_count / len(LM)
    features["body_scale_raw"] = float(scale) if np.isfinite(scale) else np.nan

    # -------------------------
    # Coordenadas normalizadas
    # -------------------------

    for idx, name in LM.items():
        features[f"{name}_x_norm"] = float(norm[idx, 0]) if np.isfinite(norm[idx, 0]) else np.nan
        features[f"{name}_y_norm"] = float(norm[idx, 1]) if np.isfinite(norm[idx, 1]) else np.nan
        features[f"{name}_z_norm"] = float(norm[idx, 2]) if np.isfinite(norm[idx, 2]) else np.nan

    # -------------------------
    # Bounding box corporal
    # -------------------------

    xy = norm[FEATURE_LANDMARKS, :2]
    valid_xy = xy[np.all(np.isfinite(xy), axis=1)]

    if len(valid_xy) >= 2:
        min_xy = np.min(valid_xy, axis=0)
        max_xy = np.max(valid_xy, axis=0)

        bbox_width = float(max_xy[0] - min_xy[0])
        bbox_height = float(max_xy[1] - min_xy[1])
        bbox_area = bbox_width * bbox_height

        features["bbox_width_norm"] = bbox_width
        features["bbox_height_norm"] = bbox_height
        features["bbox_area_norm"] = bbox_area
        features["pose_compactness_norm"] = _safe_ratio(bbox_area, bbox_width + bbox_height)
    else:
        features["bbox_width_norm"] = np.nan
        features["bbox_height_norm"] = np.nan
        features["bbox_area_norm"] = np.nan
        features["pose_compactness_norm"] = np.nan

    # -------------------------
    # Ángulos articulares
    # -------------------------

    for angle_name, (idx1, idx2, idx3) in ANGLE_DEFS.items():
        angle = _angle_2d(norm[idx1], norm[idx2], norm[idx3])
        features[f"{angle_name}_angle_deg"] = angle

    # -------------------------
    # Segmentos: longitud y orientación
    # -------------------------

    for segment_name, (idx1, idx2) in SEGMENTS.items():
        p1 = norm[idx1]
        p2 = norm[idx2]

        features[f"{segment_name}_length_norm"] = _dist(p1, p2)
        features[f"{segment_name}_orientation_deg"] = _orientation_2d_deg(p1, p2)

    # -------------------------
    # Distancias biomecánicas importantes
    # -------------------------

    for dist_name, (idx1, idx2) in DISTANCE_PAIRS.items():
        features[f"{dist_name}_norm"] = _dist(norm[idx1], norm[idx2])

    # -------------------------
    # Tronco, pelvis y alineación
    # -------------------------

    if _is_finite_array(mid_shoulders) and _is_finite_array(mid_hips):
        trunk_length = _dist(mid_shoulders, mid_hips)
        trunk_lean = _trunk_lean_deg(mid_hips, mid_shoulders)
    else:
        trunk_length = np.nan
        trunk_lean = np.nan

    features["trunk_length_norm"] = trunk_length
    features["trunk_lean_deg"] = trunk_lean
    features["trunk_abs_lean_deg"] = abs(trunk_lean) if np.isfinite(trunk_lean) else np.nan

    shoulder_line_angle = features.get("shoulder_line_orientation_deg", np.nan)
    hip_line_angle = features.get("hip_line_orientation_deg", np.nan)

    features["shoulder_hip_orientation_diff_deg"] = _signeddiff(
        shoulder_line_angle,
        hip_line_angle
    )

    features["shoulder_hip_orientation_absdiff_deg"] = _absdiff(
        shoulder_line_angle,
        hip_line_angle
    )

    # -------------------------
    # Cabeza respecto al tronco
    # -------------------------

    nose = norm[0]

    if _is_finite_array(nose) and _is_finite_array(mid_shoulders) and _is_finite_array(mid_hips):
        features["head_trunk_angle_deg"] = _angle_2d(nose, mid_shoulders, mid_hips)
        features["nose_to_mid_shoulders_norm"] = _dist(nose, mid_shoulders)
    else:
        features["head_trunk_angle_deg"] = np.nan
        features["nose_to_mid_shoulders_norm"] = np.nan

    # -------------------------
    # Extensión funcional de brazos y piernas
    # -------------------------

    left_arm_reach = _dist(norm[11], norm[15])
    right_arm_reach = _dist(norm[12], norm[16])

    left_arm_chain = _dist(norm[11], norm[13]) + _dist(norm[13], norm[15])
    right_arm_chain = _dist(norm[12], norm[14]) + _dist(norm[14], norm[16])

    features["left_arm_reach_norm"] = left_arm_reach
    features["right_arm_reach_norm"] = right_arm_reach
    features["left_arm_extension_ratio"] = _safe_ratio(left_arm_reach, left_arm_chain)
    features["right_arm_extension_ratio"] = _safe_ratio(right_arm_reach, right_arm_chain)

    left_leg_reach = _dist(norm[23], norm[27])
    right_leg_reach = _dist(norm[24], norm[28])

    left_leg_chain = _dist(norm[23], norm[25]) + _dist(norm[25], norm[27])
    right_leg_chain = _dist(norm[24], norm[26]) + _dist(norm[26], norm[28])

    features["left_leg_reach_norm"] = left_leg_reach
    features["right_leg_reach_norm"] = right_leg_reach
    features["left_leg_extension_ratio"] = _safe_ratio(left_leg_reach, left_leg_chain)
    features["right_leg_extension_ratio"] = _safe_ratio(right_leg_reach, right_leg_chain)

    # -------------------------
    # Alturas relativas
    # En imagen, y menor significa más arriba.
    # -------------------------

    features["left_wrist_y_relative_to_left_shoulder"] = _signeddiff(norm[15, 1], norm[11, 1])
    features["right_wrist_y_relative_to_right_shoulder"] = _signeddiff(norm[16, 1], norm[12, 1])

    features["left_wrist_y_relative_to_left_hip"] = _signeddiff(norm[15, 1], norm[23, 1])
    features["right_wrist_y_relative_to_right_hip"] = _signeddiff(norm[16, 1], norm[24, 1])

    features["left_ankle_y_relative_to_left_hip"] = _signeddiff(norm[27, 1], norm[23, 1])
    features["right_ankle_y_relative_to_right_hip"] = _signeddiff(norm[28, 1], norm[24, 1])

    features["left_knee_y_relative_to_left_hip"] = _signeddiff(norm[25, 1], norm[23, 1])
    features["right_knee_y_relative_to_right_hip"] = _signeddiff(norm[26, 1], norm[24, 1])

    # -------------------------
    # Simetrías izquierda-derecha
    # -------------------------

    for joint in ["shoulder", "elbow", "wrist", "hip", "knee", "ankle"]:
        left_value = features.get(f"left_{joint}_angle_deg", np.nan)
        right_value = features.get(f"right_{joint}_angle_deg", np.nan)

        features[f"{joint}_angle_symmetry_absdiff_deg"] = _absdiff(left_value, right_value)
        features[f"{joint}_angle_symmetry_signeddiff_deg"] = _signeddiff(left_value, right_value)

    features["arm_reach_symmetry_absdiff_norm"] = _absdiff(
        features["left_arm_reach_norm"],
        features["right_arm_reach_norm"]
    )

    features["leg_reach_symmetry_absdiff_norm"] = _absdiff(
        features["left_leg_reach_norm"],
        features["right_leg_reach_norm"]
    )

    features["arm_extension_symmetry_absdiff"] = _absdiff(
        features["left_arm_extension_ratio"],
        features["right_arm_extension_ratio"]
    )

    features["leg_extension_symmetry_absdiff"] = _absdiff(
        features["left_leg_extension_ratio"],
        features["right_leg_extension_ratio"]
    )

    features["wrist_height_symmetry_absdiff_norm"] = _absdiff(
        norm[15, 1],
        norm[16, 1]
    )

    features["ankle_height_symmetry_absdiff_norm"] = _absdiff(
        norm[27, 1],
        norm[28, 1]
    )

    features["knee_height_symmetry_absdiff_norm"] = _absdiff(
        norm[25, 1],
        norm[26, 1]
    )

    return features


# =========================
# DERIVADAS TEMPORALES
# =========================

def _interpolate_nans_1d(y):
    y = np.asarray(y, dtype=np.float32).copy()
    n = len(y)

    if n == 0:
        return y

    x = np.arange(n)
    mask = np.isfinite(y)

    if mask.sum() < 2:
        return np.full_like(y, np.nan)

    y[~mask] = np.interp(x[~mask], x[mask], y[mask])
    return y


def _temporal_gradient(y, dt):
    y = np.asarray(y, dtype=np.float32)
    mask = np.isfinite(y)

    if mask.sum() < 2:
        return np.full_like(y, np.nan)

    y_interp = _interpolate_nans_1d(y)
    grad = np.gradient(y_interp, dt)

    grad[~mask] = np.nan

    return grad.astype(np.float32)


def _add_temporal_features(rows, fps=None):
    """
    Agrega velocidades y aceleraciones de:
    - coordenadas normalizadas
    - ángulos articulares
    - inclinación del tronco
    - distancias principales
    """

    if len(rows) == 0:
        return rows

    if fps is None or fps <= 0 or not np.isfinite(fps):
        dt = 1.0
    else:
        dt = 1.0 / fps

    feature_names = sorted(
        key for row in rows for key in row.keys()
        if key != "frame_id"
    )

    temporal_candidates = []

    for key in feature_names:
        if key.startswith("vis_"):
            continue

        if (
            key.endswith("_x_norm")
            or key.endswith("_y_norm")
            or key.endswith("_z_norm")
            or key.endswith("_angle_deg")
            or key.endswith("_length_norm")
            or key.endswith("_distance_norm")
            or key.endswith("_norm")
            or key.endswith("_lean_deg")
        ):
            temporal_candidates.append(key)

    temporal_candidates = sorted(set(temporal_candidates))

    for key in temporal_candidates:
        y = np.array(
            [row.get(key, np.nan) for row in rows],
            dtype=np.float32
        )

        vel = _temporal_gradient(y, dt)
        acc = _temporal_gradient(vel, dt)

        for i, row in enumerate(rows):
            row[f"{key}_vel"] = float(vel[i]) if np.isfinite(vel[i]) else np.nan
            row[f"{key}_acc"] = float(acc[i]) if np.isfinite(acc[i]) else np.nan

    # -------------------------
    # Velocidad y aceleración por punto corporal
    # -------------------------

    for landmark_name in MOTION_LANDMARKS.keys():
        vx_key = f"{landmark_name}_x_norm_vel"
        vy_key = f"{landmark_name}_y_norm_vel"
        vz_key = f"{landmark_name}_z_norm_vel"

        ax_key = f"{landmark_name}_x_norm_acc"
        ay_key = f"{landmark_name}_y_norm_acc"
        az_key = f"{landmark_name}_z_norm_acc"

        for row in rows:
            vx = row.get(vx_key, np.nan)
            vy = row.get(vy_key, np.nan)
            vz = row.get(vz_key, np.nan)

            ax = row.get(ax_key, np.nan)
            ay = row.get(ay_key, np.nan)
            az = row.get(az_key, np.nan)

            if np.isfinite(vx) and np.isfinite(vy) and np.isfinite(vz):
                row[f"{landmark_name}_speed_norm_s"] = float(
                    np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
                )
            else:
                row[f"{landmark_name}_speed_norm_s"] = np.nan

            if np.isfinite(ax) and np.isfinite(ay) and np.isfinite(az):
                row[f"{landmark_name}_acc_norm_s2"] = float(
                    np.sqrt(ax ** 2 + ay ** 2 + az ** 2)
                )
            else:
                row[f"{landmark_name}_acc_norm_s2"] = np.nan

    # -------------------------
    # Energía de movimiento
    # -------------------------

    upper = [
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
    ]

    lower = [
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
        "left_foot_index",
        "right_foot_index",
    ]

    left_side = [
        "left_shoulder",
        "left_elbow",
        "left_wrist",
        "left_hip",
        "left_knee",
        "left_ankle",
        "left_foot_index",
    ]

    right_side = [
        "right_shoulder",
        "right_elbow",
        "right_wrist",
        "right_hip",
        "right_knee",
        "right_ankle",
        "right_foot_index",
    ]

    def nanmean_from_keys(row, names, suffix):
        values = np.array(
            [row.get(f"{name}_{suffix}", np.nan) for name in names],
            dtype=np.float32
        )

        if np.isfinite(values).any():
            return float(np.nanmean(values))

        return np.nan

    angle_velocity_keys = [
        key for key in rows[0].keys()
        if key.endswith("_angle_deg_vel")
    ]

    for row in rows:
        row["motion_energy_total"] = nanmean_from_keys(
            row,
            list(MOTION_LANDMARKS.keys()),
            "speed_norm_s"
        )

        row["motion_energy_upper_body"] = nanmean_from_keys(
            row,
            upper,
            "speed_norm_s"
        )

        row["motion_energy_lower_body"] = nanmean_from_keys(
            row,
            lower,
            "speed_norm_s"
        )

        row["motion_energy_left_side"] = nanmean_from_keys(
            row,
            left_side,
            "speed_norm_s"
        )

        row["motion_energy_right_side"] = nanmean_from_keys(
            row,
            right_side,
            "speed_norm_s"
        )

        left_energy = row.get("motion_energy_left_side", np.nan)
        right_energy = row.get("motion_energy_right_side", np.nan)

        row["motion_energy_side_absdiff"] = _absdiff(left_energy, right_energy)

        angular_velocities = np.array(
            [abs(row.get(key, np.nan)) for key in angle_velocity_keys],
            dtype=np.float32
        )

        if np.isfinite(angular_velocities).any():
            row["angular_motion_energy"] = float(np.nanmean(angular_velocities))
        else:
            row["angular_motion_energy"] = np.nan

    return rows


# =========================
# EXTRACTOR PRINCIPAL
# =========================

def extract_biomechanical_features(
    landmarks_per_frame,
    fps=None,
    visibility_threshold=VISIBILITY_THRESHOLD,
    include_temporal=True
):
    """
    Entrada:
        landmarks_per_frame:
            salida de vector_pose_engine(cap)
            [(frame_id, landmarks), ...]

        fps:
            frames por segundo del video.
            Si no se pasa, las velocidades quedan en unidades por frame.

    Salida:
        rows:
            lista de diccionarios.
            Cada diccionario corresponde a un frame.
    """

    rows = []

    for frame_id, landmarks in landmarks_per_frame:
        row = extract_frame_biomechanical_features(
            frame_id=frame_id,
            landmarks=landmarks,
            visibility_threshold=visibility_threshold
        )

        rows.append(row)

    if include_temporal:
        rows = _add_temporal_features(rows, fps=fps)

    return rows


# =========================
# CONVERTIR A MATRIZ
# =========================

def biomech_rows_to_matrix(rows):
    """
    Convierte la lista de diccionarios en matriz numérica.

    Salida:
        X: np.array shape (n_frames, n_features)
        feature_names: lista con nombres de features
        frame_ids: np.array con los ids de frame
    """

    if len(rows) == 0:
        return np.empty((0, 0)), [], np.array([])

    feature_names = sorted(
        key for row in rows for key in row.keys()
        if key != "frame_id"
    )

    feature_names = sorted(set(feature_names))

    X = np.full((len(rows), len(feature_names)), np.nan, dtype=np.float32)
    frame_ids = np.zeros(len(rows), dtype=np.int32)

    for i, row in enumerate(rows):
        frame_ids[i] = int(row.get("frame_id", i))

        for j, key in enumerate(feature_names):
            value = row.get(key, np.nan)

            if value is None:
                value = np.nan

            X[i, j] = value if np.isfinite(value) else np.nan

    return X, feature_names, frame_ids