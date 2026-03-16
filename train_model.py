import cv2
import os
import numpy as np
import json

dataset_path = "dataset"

faces  = []
labels = []
label_map = {}

# ── IMPORTANT: sort folders so label order is always consistent ──
# This ensures label 0 is always the same person every time you retrain
person_folders = sorted([
    p for p in os.listdir(dataset_path)
    if os.path.isdir(os.path.join(dataset_path, p))
])

print(f"Found {len(person_folders)} students: {person_folders}\n")

for current_label, person in enumerate(person_folders):
    person_folder = os.path.join(dataset_path, person)
    label_map[current_label] = person.capitalize()

    img_count = 0
    for image_name in os.listdir(person_folder):
        img_path = os.path.join(person_folder, image_name)
        img = cv2.imread(img_path)

        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (200, 200))
        gray = cv2.equalizeHist(gray)   # ← must match app.py recognition step

        faces.append(gray)
        labels.append(current_label)
        img_count += 1

    print(f"  [{current_label}] {person.capitalize()} — {img_count} image(s)")

print()

# ── Train ──────────────────────────────────────────────────────
labels_np = np.array(labels)
model = cv2.face.LBPHFaceRecognizer_create()
model.train(faces, labels_np)
model.save("face_model.yml")

# ── Save label map to JSON so app.py always stays in sync ─────
with open("label_map.json", "w") as f:
    json.dump(label_map, f, indent=2)

print("✅ Model trained and saved → face_model.yml")
print("✅ Label map saved        → label_map.json")
print()
print("Label map (copy this into app.py if needed):")
for k, v in label_map.items():
    print(f"  {k}: {v}")