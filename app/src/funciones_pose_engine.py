import cv2
from mediapipe.python.solutions import pose as mp_pose
import numpy as np

try:
    from scipy.signal import savgol_filter
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# =========================
# CONFIGURACIÓN
# =========================
VISIBILITY_THRESHOLD = 0.60

# Savitzky-Golay
SAVGOL_WINDOW = 11   # impar
SAVGOL_POLYORDER = 2

ANGLE_DEFS = {
    "left_shoulder":  (13, 11, 23),
    "right_shoulder": (14, 12, 24),

    "left_elbow":     (11, 13, 15),
    "right_elbow":    (12, 14, 16),

    "left_wrist":     (13, 15, 19),
    "right_wrist":    (14, 16, 20),

    "left_hip":       (11, 23, 25),
    "right_hip":      (12, 24, 26),

    "left_knee":      (23, 25, 27),
    "right_knee":     (24, 26, 28),

    "left_ankle":     (25, 27, 31),
    "right_ankle":    (26, 28, 32),
}

ANGLE_LABELS = {
    "left_shoulder": "L-Shoulder",
    "right_shoulder": "R-Shoulder",
    "left_elbow": "L-Elbow",
    "right_elbow": "R-Elbow",
    "left_wrist": "L-Wrist",
    "right_wrist": "R-Wrist",
    "left_hip": "L-Hip",
    "right_hip": "R-Hip",
    "left_knee": "L-Knee",
    "right_knee": "R-Knee",
    "left_ankle": "L-Ankle",
    "right_ankle": "R-Ankle",
}


# =========================
# LANDMARKS CRUDOS
# =========================
def landmarks_mp_to_array(curr_landmarks):
    """
    Convierte landmarks de MediaPipe a np.array (33, 4):
    [x, y, z, visibility]
    """
    out = []
    for lm in curr_landmarks:
        out.append((lm.x, lm.y, lm.z, lm.visibility))
    return np.array(out, dtype=np.float32)


def landmark_tuple_a_pixel(landmarks, idx, width, height):
    x = landmarks[idx][0]
    y = landmarks[idx][1]

    if not np.isfinite(x) or not np.isfinite(y):
        return None

    return (int(x * width), int(y * height))


def landmark_visible(landmarks, idx, visibility_threshold=0.6):
    x, y, z, vis = landmarks[idx]

    if not np.isfinite(x) or not np.isfinite(y) or not np.isfinite(z) or not np.isfinite(vis):
        return False

    return vis >= visibility_threshold


def trio_visible(landmarks, idx1, idx2, idx3, visibility_threshold=0.6):
    return (
        landmark_visible(landmarks, idx1, visibility_threshold)
        and landmark_visible(landmarks, idx2, visibility_threshold)
        and landmark_visible(landmarks, idx3, visibility_threshold)
    )


# =========================
# GEOMETRÍA
# =========================
def calcular_angulo(a, b, c):
    """
    Calcula el ángulo ABC en grados.
    """
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    c = np.array(c, dtype=np.float32)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return None

    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)

    return float(np.degrees(np.arccos(cos_angle)))


def angulo_vector(origen, destino):
    dx = destino[0] - origen[0]
    dy = destino[1] - origen[1]
    return np.degrees(np.arctan2(dy, dx))


def normalizar_angulo_360(ang):
    ang = ang % 360
    if ang < 0:
        ang += 360
    return ang


def dibujar_arco(frame, p1, p2, p3, radio=22, color=(0, 255, 255), thickness=2):
    ang1 = normalizar_angulo_360(angulo_vector(p2, p1))
    ang2 = normalizar_angulo_360(angulo_vector(p2, p3))

    diff = (ang2 - ang1) % 360
    if diff > 180:
        ang1, ang2 = ang2, ang1

    cv2.ellipse(
        frame,
        center=p2,
        axes=(radio, radio),
        angle=0,
        startAngle=ang1,
        endAngle=ang2,
        color=color,
        thickness=thickness
    )


# =========================
# ÁNGULOS CRUDOS POR FRAME
# =========================
def calcular_angulos_frame(landmarks, width, height, visibility_threshold=0.6):
    angles = {}

    for angle_name, (idx1, idx2, idx3) in ANGLE_DEFS.items():
        if not trio_visible(landmarks, idx1, idx2, idx3, visibility_threshold):
            angles[angle_name] = np.nan
            continue

        p1 = landmark_tuple_a_pixel(landmarks, idx1, width, height)
        p2 = landmark_tuple_a_pixel(landmarks, idx2, width, height)
        p3 = landmark_tuple_a_pixel(landmarks, idx3, width, height)

        if p1 is None or p2 is None or p3 is None:
            angles[angle_name] = np.nan
            continue

        angle = calcular_angulo(p1, p2, p3)
        angles[angle_name] = angle if angle is not None else np.nan

    return angles


# =========================
# SUAVIZADO DE ÁNGULOS
# =========================
def interpolar_nans_1d(y):
    y = np.asarray(y, dtype=np.float32).copy()
    n = len(y)

    if n == 0:
        return y

    x = np.arange(n)
    mask = np.isfinite(y)

    if mask.sum() < 2:
        return y

    y[~mask] = np.interp(x[~mask], x[mask], y[mask])
    return y


def moving_average_1d(y, window=5):
    y = np.asarray(y, dtype=np.float32)
    if len(y) < window:
        return y.copy()

    kernel = np.ones(window, dtype=np.float32) / window
    return np.convolve(y, kernel, mode='same')


def ajustar_savgol_window(n, desired_window, polyorder):
    if n <= polyorder + 1:
        return None

    w = min(desired_window, n)
    if w % 2 == 0:
        w -= 1

    min_valid = polyorder + 2
    if min_valid % 2 == 0:
        min_valid += 1

    if w < min_valid:
        w = min_valid

    if w > n:
        w = n if n % 2 == 1 else n - 1

    if w <= polyorder or w < 3:
        return None

    return w


def suavizar_serie_angular(y, desired_window=11, polyorder=2):
    """
    Suaviza una serie angular 1D.
    Mantiene NaN en salida donde originalmente no había dato visible.
    """
    y = np.asarray(y, dtype=np.float32)
    n = len(y)

    if n == 0:
        return y.copy()

    original_valid_mask = np.isfinite(y)
    y_interp = interpolar_nans_1d(y)

    if not np.isfinite(y_interp).any():
        return y.copy()

    if SCIPY_AVAILABLE:
        w = ajustar_savgol_window(n, desired_window, polyorder)
        if w is not None:
            y_smooth = savgol_filter(y_interp, window_length=w, polyorder=polyorder, mode='interp')
        else:
            y_smooth = y_interp.copy()
    else:
        y_smooth = moving_average_1d(y_interp, window=5)

    y_smooth[~original_valid_mask] = np.nan
    return y_smooth.astype(np.float32)


def suavizar_angulos_por_frame(angles_per_frame):
    """
    Entrada:
        [(frame_id, {angulo: valor, ...}), ...]
    Salida:
        [(frame_id, {angulo_suavizado: valor, ...}), ...]
    """
    if len(angles_per_frame) == 0:
        return []

    frame_ids = [frame_id for frame_id, _ in angles_per_frame]
    angle_names = list(ANGLE_DEFS.keys())

    mat = np.full((len(angles_per_frame), len(angle_names)), np.nan, dtype=np.float32)

    for i, (_, angle_dict) in enumerate(angles_per_frame):
        for j, name in enumerate(angle_names):
            mat[i, j] = angle_dict.get(name, np.nan)

    smooth_mat = np.empty_like(mat)
    for j in range(mat.shape[1]):
        smooth_mat[:, j] = suavizar_serie_angular(
            mat[:, j],
            desired_window=SAVGOL_WINDOW,
            polyorder=SAVGOL_POLYORDER
        )

    out = []
    for i, frame_id in enumerate(frame_ids):
        d = {
            name: float(smooth_mat[i, j]) if np.isfinite(smooth_mat[i, j]) else np.nan
            for j, name in enumerate(angle_names)
        }
        out.append((frame_id, d))

    return out


# =========================
# DIBUJO
# =========================
def dibujar_angulo_en_articulacion(
    frame,
    landmarks,
    angle_name,
    angle_value,
    width,
    height,
    visibility_threshold=0.6
):
    """
    Dibuja usando landmarks crudos.
    Muestra ángulo suavizado.
    """
    idx1, idx2, idx3 = ANGLE_DEFS[angle_name]

    if not trio_visible(landmarks, idx1, idx2, idx3, visibility_threshold):
        return None

    if angle_value is None or not np.isfinite(angle_value):
        return None

    p1 = landmark_tuple_a_pixel(landmarks, idx1, width, height)
    p2 = landmark_tuple_a_pixel(landmarks, idx2, width, height)
    p3 = landmark_tuple_a_pixel(landmarks, idx3, width, height)

    if p1 is None or p2 is None or p3 is None:
        return None

    if angle_name.startswith("left"):
        line_color = (0, 255, 0)
        arc_color = (0, 255, 255)
        point_color = (255, 100, 0)
    else:
        line_color = (255, 0, 0)
        arc_color = (255, 255, 0)
        point_color = (0, 100, 255)

    cv2.line(frame, p2, p1, line_color, 2)
    cv2.line(frame, p2, p3, line_color, 2)

    cv2.circle(frame, p1, 4, point_color, -1)
    cv2.circle(frame, p2, 5, (0, 0, 255), -1)
    cv2.circle(frame, p3, 4, point_color, -1)

    dibujar_arco(frame, p1, p2, p3, radio=22, color=arc_color, thickness=2)

    label = ANGLE_LABELS[angle_name]
    text = f"{label}: {int(round(angle_value))}°"
    text_pos = (p2[0] + 8, p2[1] - 8)

    cv2.putText(
        frame,
        text,
        text_pos,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    return angle_value


def dibujar_esqueleto_manual(frame, landmarks, visibility_threshold=0.6):
    h, w = frame.shape[:2]

    for start_idx, end_idx in mp_pose.POSE_CONNECTIONS:
        if landmark_visible(landmarks, start_idx, visibility_threshold) and landmark_visible(landmarks, end_idx, visibility_threshold):
            p1 = landmark_tuple_a_pixel(landmarks, start_idx, w, h)
            p2 = landmark_tuple_a_pixel(landmarks, end_idx, w, h)
            if p1 is not None and p2 is not None:
                cv2.line(frame, p1, p2, (245, 117, 66), 2)

    for idx in range(33):
        if landmark_visible(landmarks, idx, visibility_threshold):
            p = landmark_tuple_a_pixel(landmarks, idx, w, h)
            if p is not None:
                cv2.circle(frame, p, 2, (245, 66, 230), -1)


# =========================
# LANDMARKS CRUDOS POR FRAME
# =========================
def vector_pose_engine(cap):
    """
    Devuelve:
        [(frame_id, landmarks_crudos), ...]
    landmarks_crudos shape = (33, 4)
    """
    frame_id = 0
    landmarks_per_frame = []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.7
    ) as pose:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_id += 1
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results.pose_landmarks:
                vec = landmarks_mp_to_array(results.pose_landmarks.landmark)
            else:
                vec = np.full((33, 4), np.nan, dtype=np.float32)

            landmarks_per_frame.append((frame_id, vec))

    cap.release()
    return landmarks_per_frame


# =========================
# SOLO ÁNGULOS SUAVIZADOS
# =========================
def angles_pose_engine(cap):
    """
    Devuelve:
        [(frame_id, dict_de_angulos_suavizados), ...]
    """
    frame_id = 0
    angles_per_frame_raw = []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.7
    ) as pose:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_id += 1
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            h, w, _ = frame.shape

            if results.pose_landmarks:
                landmarks = landmarks_mp_to_array(results.pose_landmarks.landmark)
                angles_dict = calcular_angulos_frame(
                    landmarks,
                    w,
                    h,
                    visibility_threshold=VISIBILITY_THRESHOLD
                )
            else:
                angles_dict = {name: np.nan for name in ANGLE_DEFS.keys()}

            angles_per_frame_raw.append((frame_id, angles_dict))

    cap.release()
    return suavizar_angulos_por_frame(angles_per_frame_raw)


# =========================
# VISUALIZACIÓN OFFLINE
# =========================
def visualize_pose_engine(cap):
    """
    Visualiza:
    - esqueleto con landmarks crudos
    - ángulos suavizados
    """
    raw_frames = []
    raw_landmarks_list = []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.7
    ) as pose:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results.pose_landmarks:
                landmarks = landmarks_mp_to_array(results.pose_landmarks.landmark)
            else:
                landmarks = np.full((33, 4), np.nan, dtype=np.float32)

            raw_frames.append(frame.copy())
            raw_landmarks_list.append(landmarks)

    cap.release()

    # Ángulos crudos
    angles_raw = []
    for i, (frame, landmarks) in enumerate(zip(raw_frames, raw_landmarks_list), start=1):
        h, w, _ = frame.shape

        if np.isfinite(landmarks).any():
            angle_dict = calcular_angulos_frame(
                landmarks,
                w,
                h,
                visibility_threshold=VISIBILITY_THRESHOLD
            )
        else:
            angle_dict = {name: np.nan for name in ANGLE_DEFS.keys()}

        angles_raw.append((i, angle_dict))

    # Ángulos suavizados
    angles_smooth = suavizar_angulos_por_frame(angles_raw)

    # Reproducción
    for i, frame in enumerate(raw_frames):
        landmarks = raw_landmarks_list[i]
        _, angle_dict = angles_smooth[i]

        dibujar_esqueleto_manual(frame, landmarks, VISIBILITY_THRESHOLD)

        for angle_name in ANGLE_DEFS:
            dibujar_angulo_en_articulacion(
                frame=frame,
                landmarks=landmarks,
                angle_name=angle_name,
                angle_value=angle_dict.get(angle_name, np.nan),
                width=frame.shape[1],
                height=frame.shape[0],
                visibility_threshold=VISIBILITY_THRESHOLD
            )

        cv2.imshow("MediaPipe Pose + Angulos Suavizados", frame)

        key = cv2.waitKey(25) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()

def visualize_pose_engine_realtime(cap):
    """
    Visualiza el video frame por frame.
    Muestra el esqueleto y los ángulos sin suavizado offline.
    """

    if not cap.isOpened():
        print("Error: no se pudo abrir el video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps is None or fps <= 0:
        delay = 25
    else:
        delay = int(1000 / fps)

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.7
    ) as pose:

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break

            frame = cv2.flip(frame, 1)

            h, w, _ = frame.shape

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results.pose_landmarks:
                landmarks = landmarks_mp_to_array(results.pose_landmarks.landmark)

                dibujar_esqueleto_manual(
                    frame,
                    landmarks,
                    VISIBILITY_THRESHOLD
                )

                angles_dict = calcular_angulos_frame(
                    landmarks,
                    w,
                    h,
                    visibility_threshold=VISIBILITY_THRESHOLD
                )

                for angle_name in ANGLE_DEFS:
                    dibujar_angulo_en_articulacion(
                        frame=frame,
                        landmarks=landmarks,
                        angle_name=angle_name,
                        angle_value=angles_dict.get(angle_name, np.nan),
                        width=w,
                        height=h,
                        visibility_threshold=VISIBILITY_THRESHOLD
                    )

            cv2.imshow("MediaPipe Pose - Realtime", frame)

            key = cv2.waitKey(delay) & 0xFF

            if key == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()