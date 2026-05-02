import cv2
import os
import numpy as np
from funciones_pose_engine import visualize_pose_engine_realtime as vp_engine


video = os.path.join('videos','1000170.mp4')

print("Ruta:", os.path.abspath(video))
print("Existe:", os.path.exists(video))

cap = cv2.VideoCapture(video)

print("Video abierto:", cap.isOpened())
if not cap.isOpened():
    raise FileNotFoundError(f"No se pudo abrir el video: {os.path.abspath(video)}")

vp_engine(cap)
