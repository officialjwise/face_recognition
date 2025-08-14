#!/usr/bin/env python3
"""
Script to download face-api.js models and save them locally.
This ensures face detection works reliably without depending on external CDNs.
"""

import os
import urllib.request
import shutil

# Create directories if they don't exist
WEIGHTS_DIR = os.path.join('static', 'js', 'face-api', 'weights')
os.makedirs(WEIGHTS_DIR, exist_ok=True)

# Download face-api.js library
FACE_API_URL = 'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js'
FACE_API_PATH = os.path.join('static', 'js', 'face-api', 'face-api.min.js')

# Model files to download
MODEL_FILES = [
    # TinyFaceDetector model
    'tiny_face_detector_model-weights_manifest.json',
    'tiny_face_detector_model-shard1',
    
    # FaceLandmark68 model
    'face_landmark_68_model-weights_manifest.json',
    'face_landmark_68_model-shard1',
    
    # FaceRecognition model
    'face_recognition_model-weights_manifest.json',
    'face_recognition_model-shard1',
    'face_recognition_model-shard2'
]

print("Downloading face-api.js library...")
try:
    urllib.request.urlretrieve(FACE_API_URL, FACE_API_PATH)
    print(f"Downloaded face-api.js to {FACE_API_PATH}")
except Exception as e:
    print(f"Error downloading face-api.js: {e}")

# Download model files directly from the jsdelivr CDN
print("\nDownloading model files...")
BASE_URL = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/'

for file in MODEL_FILES:
    try:
        url = BASE_URL + file
        dest = os.path.join(WEIGHTS_DIR, file)
        print(f"Downloading {file}...")
        urllib.request.urlretrieve(url, dest)
        print(f"Downloaded {file} to {dest}")
    except Exception as e:
        print(f"Error downloading {file}: {e}")

print("\nDownload complete! The models are now available locally.")
print("Update your HTML to use local files with:")
print("const MODEL_URL = '/static/js/face-api/weights'")
