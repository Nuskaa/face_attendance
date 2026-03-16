"""
debug_detection.py
==================
Run this inside face_attendance_app/ to diagnose why faces aren't detected.
It tries EVERY combination of settings and shows you what works.

Usage:
    python debug_detection.py group_photos/your_photo.jpg
"""

import cv2
import sys
import os
import numpy as np

# ── Get image path from argument or ask user ──────────────────
if len(sys.argv) > 1:
    img_path = sys.argv[1]
else:
    # Auto-find first image in group_photos/
    folder = "group_photos"
    images = [f for f in os.listdir(folder)
              if f.lower().endswith(('.jpg','.jpeg','.png','.bmp'))]
    if not images:
        print("❌ No images found in group_photos/")
        sys.exit(1)
    img_path = os.path.join(folder, images[0])
    print(f"Using: {img_path}")

# ── Load image ────────────────────────────────────────────────
img = cv2.imread(img_path)
if img is None:
    print(f"❌ Could not load image: {img_path}")
    sys.exit(1)

h, w = img.shape[:2]
print(f"\n📐 Image size: {w} x {h} pixels")

# ── Try resizing if image is very large or very small ─────────
sizes_to_try = []

if w > 1200:
    # Downscale large images
    for scale in [0.5, 0.75, 1.0]:
        new_w = int(w * scale)
        new_h = int(h * scale)
        sizes_to_try.append((scale, cv2.resize(img, (new_w, new_h))))
else:
    # Try upscaling small images
    for scale in [1.0, 1.5, 2.0]:
        new_w = int(w * scale)
        new_h = int(h * scale)
        sizes_to_try.append((scale, cv2.resize(img, (new_w, new_h))))

# ── Cascades to try ───────────────────────────────────────────
cascades = {
    "Frontal (default)": cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
    "Frontal (alt)":     cv2.data.haarcascades + "haarcascade_frontalface_alt.xml",
    "Frontal (alt2)":    cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml",
}

# ── Parameter combinations to try ────────────────────────────
params = [
    (1.05, 2, 20),
    (1.05, 3, 20),
    (1.1,  2, 20),
    (1.1,  3, 30),
    (1.1,  4, 30),
    (1.15, 3, 30),
    (1.2,  3, 40),
    (1.3,  5, 60),
]

print("\n🔍 Trying all combinations...\n")

best_result = None
best_count  = 0

for scale_factor, (img_scale, resized) in enumerate(sizes_to_try):
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    # Equalise histogram to improve contrast
    gray = cv2.equalizeHist(gray)

    for cascade_name, cascade_path in cascades.items():
        cascade = cv2.CascadeClassifier(cascade_path)

        for (scaleFactor, minNeighbors, minSize) in params:
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=scaleFactor,
                minNeighbors=minNeighbors,
                minSize=(minSize, minSize)
            )

            n = len(faces) if isinstance(faces, np.ndarray) else 0

            if n > 0:
                print(f"  ✅ FOUND {n} face(s)!")
                print(f"     Cascade:       {cascade_name}")
                print(f"     Image scale:   {img_scale}x")
                print(f"     scaleFactor:   {scaleFactor}")
                print(f"     minNeighbors:  {minNeighbors}")
                print(f"     minSize:       {minSize}px")
                print()

                if n > best_count:
                    best_count  = n
                    best_result = {
                        "cascade_path":  cascade_path,
                        "cascade_name":  cascade_name,
                        "img_scale":     img_scale,
                        "scaleFactor":   scaleFactor,
                        "minNeighbors":  minNeighbors,
                        "minSize":       minSize,
                        "faces":         faces,
                        "gray":          gray,
                        "resized":       resized,
                    }

# ── Summary ───────────────────────────────────────────────────
print("=" * 55)

if best_result is None:
    print("❌ NO faces detected with ANY setting.")
    print()
    print("This usually means:")
    print("  1. Faces are too small in the photo")
    print("  2. Faces are at an angle (profile/looking down)")
    print("  3. Image is very blurry or low contrast")
    print("  4. Face is partially covered")
    print()
    print("💡 Try uploading a clearer, brighter, front-facing photo.")

else:
    print(f"✅ Best result: {best_count} face(s) found!")
    print()
    print("📋 Copy these settings into your app.py:\n")
    print(f"""
# Replace your detectMultiScale call with this:
gray = cv2.equalizeHist(gray)   # add this line before detection!

""")

    if best_result["img_scale"] != 1.0:
        sc = best_result["img_scale"]
        print(f"img = cv2.resize(img, (int(img.shape[1]*{sc}), int(img.shape[0]*{sc})))")
        print(f"gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)")
        print(f"gray = cv2.equalizeHist(gray)")
        print()

    print(f"""cascade = cv2.CascadeClassifier(
    r"{best_result['cascade_path']}"
)

faces = cascade.detectMultiScale(
    gray,
    scaleFactor={best_result['scaleFactor']},
    minNeighbors={best_result['minNeighbors']},
    minSize=({best_result['minSize']}, {best_result['minSize']})
)""")

    # Save annotated image so you can see the detections
    annotated = best_result["resized"].copy()
    for (x, y, w2, h2) in best_result["faces"]:
        cv2.rectangle(annotated, (x, y), (x+w2, y+h2), (0, 255, 120), 2)
        cv2.putText(annotated, "Face", (x, y-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 120), 2)

    out_path = "debug_result.jpg"
    cv2.imwrite(out_path, annotated)
    print(f"\n📸 Annotated image saved → {out_path}")
    print("    Open it to see which faces were detected.")

print("=" * 55)
