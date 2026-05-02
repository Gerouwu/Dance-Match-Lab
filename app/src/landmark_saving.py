import cv2
import os
import numpy as np

from funciones_pose_engine import vector_pose_engine
from biomech_features import extract_biomechanical_features, biomech_rows_to_matrix


errores = []

videos = os.path.join("videos")
output_landmarks = os.path.join("output", "landmarks")
output_features = os.path.join("output", "features")

os.makedirs(output_landmarks, exist_ok=True)
os.makedirs(output_features, exist_ok=True)


for video in os.listdir(videos):
    if not video.lower().endswith(".mp4"):
        continue

    cap = None

    try:
        full_path = os.path.join(videos, video)
        cap = cv2.VideoCapture(full_path)

        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {full_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)

        stem = os.path.splitext(video)[0]

        # 1. Extraer landmarks crudos
        data = vector_pose_engine(cap)

        # 2. Guardar landmarks crudos
        landmark_path = os.path.join(output_landmarks, f"{stem}_landmarks.npy")
        np.save(landmark_path, np.array(data, dtype=object))

        # 3. Extraer features biomecánicas
        feature_rows = extract_biomechanical_features(
            data,
            fps=fps,
            include_temporal=True
        )

        # 4. Convertir a matriz
        X, feature_names, frame_ids = biomech_rows_to_matrix(feature_rows)

        # 5. Guardar features
        feature_path = os.path.join(output_features, f"{stem}_features.npz")

        np.savez_compressed(
            feature_path,
            X=X,
            feature_names=np.array(feature_names),
            frame_ids=frame_ids
        )

        print(f"Procesado correctamente: {video}")
        print(f"Features shape: {X.shape}")

    except Exception as e:
        errores.append([video, str(e)])
        print(f"Error procesando {video}: {e}")

        if cap is not None:
            cap.release()

        continue


if len(errores) > 0:
    print("\nErrores encontrados:")
    for error in errores:
        print(error)