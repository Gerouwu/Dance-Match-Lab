import sys

import cv2
import mediapipe as mp
import numpy as np
import scipy
from PIL import Image

print("Python:", sys.version.split()[0])
print("OpenCV:", cv2.__version__)
print("MediaPipe:", mp.__version__)
print("NumPy:", np.__version__)
print("SciPy:", scipy.__version__)
print("Pillow:", Image.__version__)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

print("MediaPipe pose model loaded")
