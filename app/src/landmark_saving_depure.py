import cv2
import os
import numpy as np
from funciones_pose_engine import vector_pose_engine

errores = []

videos_dir = 'videos'
output_dir = 'output'

print("Directorio actual:", os.getcwd())
print("¿Existe carpeta videos?:", os.path.exists(videos_dir))
print("Contenido de videos:", os.listdir(videos_dir) if os.path.exists(videos_dir) else "NO EXISTE")

os.makedirs(output_dir, exist_ok=True)

videos_mp4 = [v for v in os.listdir(videos_dir) if v.lower().endswith('.mp4')]
print("Videos encontrados:", videos_mp4)

for i, video in enumerate(videos_mp4, start=1):
    print(f"\n[{i}/{len(videos_mp4)}] Procesando: {video}")
    full_path = os.path.join(videos_dir, video)
    cap = None

    try:
        cap = cv2.VideoCapture(full_path)

        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {full_path}")

        data = vector_pose_engine(cap)
        print("Tipo de data:", type(data))

        if data is None:
            raise ValueError("vector_pose_engine devolvió None")

        try:
            print("Longitud de data:", len(data))
        except Exception:
            print("No se pudo calcular len(data)")

        id_video = os.path.splitext(video)[0]
        output_path = os.path.join(output_dir, id_video + '.npy')
        print("Guardando en:", output_path)

        np.save(output_path, np.array(data, dtype=object), allow_pickle=True)

        print("¿Archivo guardado?:", os.path.exists(output_path))

    except Exception as e:
        print("ERROR:", e)
        errores.append([video, str(e)])

    finally:
        if cap is not None:
            cap.release()

print("\nProceso finalizado.")
print("Errores:", errores)
print("Contenido de output:", os.listdir(output_dir))