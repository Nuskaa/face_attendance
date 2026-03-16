# 🎓 AI Face Recognition Attendance System

A modern, full-stack student attendance system using Python, Flask, and face recognition — designed as a polished college project demonstration.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📸 **Upload Photo** | Upload any image; the system detects & marks all recognised students |
| 🎥 **Live Camera** | Real-time webcam stream with face detection overlays |
| 📋 **Attendance Log** | Searchable, filterable table saved to `attendance.csv` |
| 👥 **Student Roster** | Live presence indicators that update automatically |
| 💡 **Toast Alerts** | Animated notifications for every recognition event |
| 🔄 **Reset & Export** | One-click CSV export and attendance reset |

---

## 🗂️ Project Structure

```
face_attendance_app/
│
├── app.py                          ← Flask backend (routes + face recognition)
├── generate_placeholder_dataset.py ← Generates demo student images
├── attendance.csv                  ← Auto-generated attendance log
├── requirements.txt                ← Python dependencies
│
├── dataset/
│   ├── alice.jpg
│   ├── bob.jpg
│   ├── charlie.jpg
│   ├── david.jpg
│   └── emma.jpg
│
├── static/
│   ├── style.css                   ← Dark-tech UI stylesheet
│   └── script.js                   ← Frontend logic (fetch, DOM, toasts)
│
└── templates/
    └── index.html                  ← Jinja2 dashboard template
```

---

## 🚀 Setup & Run

### Step 1 — Prerequisites

Make sure you have:
- **Python 3.9 – 3.11** (face_recognition has limited support on 3.13; 3.10/3.11 recommended)
- **pip** (latest)
- **CMake** (required by dlib, which face_recognition depends on)

Install CMake if missing:
```bash
# macOS
brew install cmake

# Ubuntu / Debian
sudo apt-get install cmake build-essential

# Windows — download from https://cmake.org/download/
```

---

### Step 2 — Clone / Copy the Project

Place the `face_attendance_app/` folder anywhere on your machine and open a terminal inside it:

```bash
cd face_attendance_app
```

---

### Step 3 — Create a Virtual Environment (recommended)

```bash
python -m venv venv

# Activate:
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

---

### Step 4 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ `dlib` (a dependency of `face_recognition`) compiles from source and may take **2–5 minutes**.  
> On Windows you may need Microsoft Visual C++ Build Tools.

---

### Step 5 — Add Student Photos

**Option A — Use the auto-generated placeholders (demo only)**

```bash
python generate_placeholder_dataset.py
```

This creates stylised placeholder images in `dataset/`. They demonstrate the UI flow but **will not produce accurate recognition** since they don't contain real human faces.

**Option B — Add real photos (recommended for actual demos)**

Place one clear, front-facing photo of each student in the `dataset/` folder:

```
dataset/
    alice.jpg     ← real photo of Alice
    bob.jpg       ← real photo of Bob
    charlie.jpg
    david.jpg
    emma.jpg
```

> Tips for best recognition accuracy:
> - Well-lit, front-facing photo
> - Only one face per file
> - JPG or PNG format
> - At least 200×200 pixels

---

### Step 6 — Run the App

```bash
python app.py
```

You should see:
```
=======================================================
   AI Face Recognition Attendance System
=======================================================
  [OK] Loaded face for: Alice
  [OK] Loaded face for: Bob
  ...
[INFO] 5 student(s) loaded from dataset/

 * Running on http://0.0.0.0:5000
```

---

### Step 7 — Open in Browser

Navigate to: **http://localhost:5000**

---

## 🖥️ How to Use

### Upload a Photo
1. Click **"Upload Photo"** in the Quick Actions panel
2. Select an image containing one or more student faces
3. The system will:
   - Detect all faces in the image
   - Match them against the known students
   - Draw green bounding boxes with names
   - Automatically mark matched students as "Present"
   - Show toast notifications for each result

### Live Camera
1. Click **"Start Camera"** — your webcam will activate
2. Students who appear in the camera view are automatically marked Present
3. The `REC` indicator in the viewport turns red when live
4. Click **"Stop Camera"** to release the webcam

### Attendance Table
- Records appear in the right-hand panel with name, time, and date
- Use the **search bar** to filter by student name
- Use the **date dropdown** to view a specific day
- Click **"Export CSV"** to download `attendance.csv`

### Reset Records
- Click **"Reset Records"** and confirm to wipe all attendance data

---

## ⚙️ Configuration

| Setting | Location | Default |
|---|---|---|
| Face match threshold | `app.py` → `recognize_faces_in_image()` | `0.55` |
| Camera resolution | `app.py` → `camera_worker()` | `640×480` |
| Max upload size | `app.py` → `MAX_CONTENT_LENGTH` | `16 MB` |
| Port | `app.py` → last line | `5000` |

---

## 🐛 Troubleshooting

**`dlib` fails to install**  
→ Install CMake and C++ build tools (see Step 1)  
→ Or try: `pip install dlib --find-links https://github.com/z-mahmud22/Dlib_Windows_Python3.x`

**"No module named face_recognition"**  
→ Make sure your virtual environment is activated  
→ Re-run `pip install face_recognition`

**Camera not opening**  
→ Check that no other app is using the webcam  
→ On Linux, you may need `sudo` or to add yourself to the `video` group

**No faces detected in uploaded image**  
→ Ensure the photo is well-lit and front-facing  
→ The system uses HOG-based detection (fast but needs clear faces)

---

## 📦 Dependencies

```
flask          — Web framework
opencv-python  — Image processing & webcam capture  
face-recognition — Face detection & recognition (wraps dlib)
numpy          — Array operations
pandas         — CSV attendance management
Pillow         — Image generation for placeholders
```

---

## 📝 Notes

- Each student is marked **Present only once per day** (duplicates are prevented)
- Attendance is saved in `attendance.csv` in the format: `Name | Time | Date | Status`
- The system runs entirely **locally** — no cloud or internet required
- Replace placeholder images with real photos for actual use

---

*Built with ❤️ for college project demonstration*
