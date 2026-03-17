from flask import Flask, render_template, request, jsonify, Response
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import base64
import os
import json

app = Flask(__name__)

with open("label_map.json", "r") as f:
    raw = json.load(f)
    label_map = {int(k): v for k, v in raw.items()}
print(f"[INFO] Label map: {label_map}")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("face_model.yml")

DNN_PROTO = "deploy.prototxt"
DNN_MODEL = "res10_300x300_ssd_iter_140000.caffemodel"
USE_DNN   = os.path.exists(DNN_PROTO) and os.path.exists(DNN_MODEL)

if USE_DNN:
    net = cv2.dnn.readNetFromCaffe(DNN_PROTO, DNN_MODEL)
    print("[INFO] DNN detector ✅")
else:
    net  = None
    haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    print("[WARN] Haar fallback")

# PWA ROUTES
@app.route('/manifest.json')
def manifest():
    data = {
        "name": "AI Face Attendance System",
        "short_name": "Attendance",
        "description": "AI Face Recognition Attendance System",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0f1a",
        "theme_color": "#00d4ff",
        "orientation": "portrait-primary",
        "scope": "/",
        "id": "/",
        "icons": [
            {"src": "/static/icons/icon-72.png",  "sizes": "72x72",   "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-96.png",  "sizes": "96x96",   "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-128.png", "sizes": "128x128", "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable any"}
        ],
        "screenshots": [
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "form_factor": "narrow"}
        ],
        "categories": ["education", "utilities"]
    }
    return Response(json.dumps(data), mimetype='application/manifest+json')

@app.route('/sw.js')
def service_worker():
    sw = """
const CACHE_NAME="ai-attendance-v1";
const ASSETS=["/","/static/style.css","/static/script.js"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(ASSETS)));self.skipWaiting();});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener("fetch",e=>{if(e.request.url.includes("/api/"))return;e.respondWith(fetch(e.request).then(r=>{const c=r.clone();caches.open(CACHE_NAME).then(ca=>ca.put(e.request,c));return r;}).catch(()=>caches.match(e.request)));});
"""
    return Response(sw, mimetype='application/javascript')

# FACE DETECTION
def detect_faces_dnn(img_bgr, conf_threshold=0.2):
    h, w = img_bgr.shape[:2]
    found = {}
    for scaled_img in [img_bgr, cv2.resize(img_bgr,(int(w*.5),int(h*.5))), cv2.resize(img_bgr,(int(w*.75),int(h*.75)))]:
        sh, sw2 = scaled_img.shape[:2]
        sx, sy = w/sw2, h/sh
        for input_size in [300, 600]:
            blob = cv2.dnn.blobFromImage(cv2.resize(scaled_img,(input_size,input_size)),1.0,(input_size,input_size),(104.,177.,123.))
            net.setInput(blob)
            dets = net.forward()
            for i in range(dets.shape[2]):
                conf = dets[0,0,i,2]
                if conf < conf_threshold: continue
                box = dets[0,0,i,3:7]*np.array([sw2,sh,sw2,sh])
                x1,y1,x2,y2 = box.astype(int)
                x1,y1=int(x1*sx),int(y1*sy); x2,y2=int(x2*sx),int(y2*sy)
                x1,y1=max(0,x1),max(0,y1); x2,y2=min(w,x2),min(h,y2)
                fw,fh=x2-x1,y2-y1
                if fw<20 or fh<20: continue
                key=(round(x1/30),round(y1/30))
                if key not in found or found[key][4]<conf:
                    found[key]=(x1,y1,fw,fh,conf)
    return [(x,y,fw,fh) for x,y,fw,fh,_ in found.values()]

def detect_faces_haar(gray):
    gray_eq = cv2.equalizeHist(gray)
    faces = haar.detectMultiScale(gray_eq,1.05,3,minSize=(30,30))
    return faces.tolist() if isinstance(faces,np.ndarray) else []

def mark_attendance(name):
    today = datetime.now().strftime("%d-%m-%Y")
    time  = datetime.now().strftime("%I:%M %p")
    try:
        df = pd.read_csv("attendance.csv")
        if not df[(df["Name"]==name)&(df["Date"]==today)].empty: return False
    except: pass
    with open("attendance.csv","a") as f: f.write(f"{name},{time},{today},Present\n")
    return True

def img_to_base64(img):
    _,buf = cv2.imencode('.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,88])
    return "data:image/jpeg;base64,"+base64.b64encode(buf).decode()

# MAIN ROUTES
@app.route('/')
def index():
    return render_template("index.html", students=list(label_map.values()))

@app.route('/api/students')
def get_students():
    return jsonify({"students":list(label_map.values()),"count":len(label_map)})

@app.route('/api/attendance')
def get_attendance():
    today=datetime.now().strftime("%d-%m-%Y"); records=[]; today_count=0
    try:
        df=pd.read_csv("attendance.csv"); df.columns=["Name","Time","Date","Status"]
        records=df.iloc[::-1].to_dict(orient="records"); today_count=len(df[df["Date"]==today])
    except: pass
    return jsonify({"records":records,"today_count":today_count,"total":len(records)})

@app.route('/api/reset_attendance',methods=['POST'])
def reset_attendance():
    with open("attendance.csv","w") as f: f.write("Name,Time,Date,Status\n")
    return jsonify({"success":True,"message":"Cleared."})

@app.route('/api/upload',methods=['POST'])
def upload():
    if 'image' not in request.files: return jsonify({"success":False,"error":"No image."}),400
    file=request.files['image']
    file_bytes=np.frombuffer(file.read(),np.uint8)
    img=cv2.imdecode(file_bytes,cv2.IMREAD_COLOR)
    if img is None: return jsonify({"success":False,"error":"Cannot decode."}),400
    h,w=img.shape[:2]
    if max(h,w)>1400:
        scale=1400/max(h,w); img=cv2.resize(img,(int(w*scale),int(h*scale)))
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    faces=detect_faces_dnn(img,0.2) if USE_DNN else detect_faces_haar(gray)
    print(f"[INFO] Faces: {len(faces)}")
    results=[]
    for (x,y,fw,fh) in faces:
        roi=cv2.equalizeHist(cv2.resize(gray[y:y+fh,x:x+fw],(200,200)))
        lbl,conf=recognizer.predict(roi)
        print(f"  → {lbl} conf={conf:.1f}")
        name=label_map.get(lbl,"Unknown") if conf<100 else "Unknown"
        is_new=mark_attendance(name) if name!="Unknown" else False
        results.append({"name":name,"status":"Present" if name!="Unknown" else "Unknown","is_new":is_new,"confidence":round(float(conf),1)})
        if name=="Unknown": continue
        color=(0,255,120)
        cv2.rectangle(img,(x,y),(x+fw,y+fh),color,2)
        txt=f" {name} ({round(conf)}) "
        (tw,th),_=cv2.getTextSize(txt,cv2.FONT_HERSHEY_DUPLEX,0.55,1)
        cv2.rectangle(img,(x,y-th-10),(x+tw+4,y),color,-1)
        cv2.putText(img,txt,(x+2,y-5),cv2.FONT_HERSHEY_DUPLEX,0.55,(255,255,255),1)
    return jsonify({"success":True,"results":results,"annotated_image":img_to_base64(img),"faces_detected":len(faces),"recognized":sum(1 for r in results if r["name"]!="Unknown")})

@app.route('/video_feed')
def video_feed(): return "Camera not enabled",200
@app.route('/api/camera/start',methods=['POST'])
def camera_start(): return jsonify({"success":False,"message":"Not enabled."})
@app.route('/api/camera/stop',methods=['POST'])
def camera_stop(): return jsonify({"success":True})

if __name__=="__main__":
    if not os.path.exists("attendance.csv"):
        with open("attendance.csv","w") as f: f.write("Name,Time,Date,Status\n")
    print("="*50); print(f"  Detector: {'DNN' if USE_DNN else 'Haar'}"); print("="*50)

port=int(os.environ.get("PORT",10000))
app.run(host="0.0.0.0",port=port)