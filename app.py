import os
import shutil
import sqlite3
import base64
import numpy as np
import cv2
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

os.makedirs("data/faces", exist_ok=True)

# OpenCV face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def init_db():
    conn = sqlite3.connect("data/travel_system.db")
    cursor = conn.cursor()
    # Ensure fresh DB schema without mobile
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, aadhaar TEXT UNIQUE NOT NULL, face_pixels BLOB NOT NULL, qr_path TEXT NOT NULL)')
    
    # checking if it has mobile, drop if yes
    try:
        cursor.execute("SELECT mobile FROM users LIMIT 1")
        cursor.execute("DROP TABLE users")
        cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, aadhaar TEXT UNIQUE NOT NULL, face_pixels BLOB NOT NULL, qr_path TEXT NOT NULL)')
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

init_db()

MATCH_THRESHOLD = 85

def decode_data_url_image(image_base64: str):
    if "," not in image_base64:
        raise ValueError("Invalid image format. Please capture image again.")
    encoded_data = image_base64.split(",", 1)[1]
    return np.frombuffer(base64.b64decode(encoded_data), np.uint8)

def get_trained_model():
    conn = sqlite3.connect("data/travel_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, face_pixels FROM users")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        return None
        
    faces = []
    ids = []
    for u in users:
        user_id = u[0]
        face_pixels = u[1]
        nparr = np.frombuffer(face_pixels, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        img_np = cv2.resize(img_np, (200, 200))
        faces.append(img_np)
        ids.append(user_id)
        
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(ids))
    return recognizer

global_recognizer = get_trained_model()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@app.get("/register_page", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {})

@app.post("/register")
async def register(
    name: str = Form(...),
    aadhaar: str = Form(...),
    image_base64: str = Form(...)  # Webcam or File data URL
):
    global global_recognizer
    
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        return JSONResponse({"status": "error", "message": "Aadhaar System Error: Aadhaar must be exactly 12 digits."})

    try:
        # Decode base64 image
        nparr = decode_data_url_image(image_base64)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return JSONResponse({"status": "error", "message": "Invalid image data. Please upload/capture a clear photo."})
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        
        if len(faces) == 0:
            return JSONResponse({"status": "error", "message": "No face detected. Please look into the camera with proper lighting."})
        elif len(faces) > 1:
            return JSONResponse({"status": "error", "message": f"Multiple faces detected ({len(faces)}). Please ensure only 1 person is in frame."})
            
        x, y, w, h = faces[0]
        cropped_face = gray[y:y+h, x:x+w]
        cropped_face = cv2.resize(cropped_face, (200, 200)) 
        
        _, buffer = cv2.imencode('.jpg', cropped_face)
        face_pixels = buffer.tobytes()
        
        conn = sqlite3.connect("data/travel_system.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, aadhaar, face_pixels, qr_path) VALUES (?, ?, ?, ?)",
                       (name, aadhaar, face_pixels, ""))
        conn.commit()
        conn.close()
        
        global_recognizer = get_trained_model()
        
        return JSONResponse({"status": "success", "aadhaar": aadhaar, "name": name})
        
    except sqlite3.IntegrityError:
        return JSONResponse({"status": "error", "message": "User with this Aadhaar already exists."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, name: str, aadhaar: str):
    return templates.TemplateResponse(request, "success.html", {
            "name": name,
            "aadhaar": aadhaar,
            "message": "Registration successful! Face profile has been enrolled."
    })

@app.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request):
    return templates.TemplateResponse(request, "verify.html", {})

@app.post("/api/verify_face")
async def api_verify_face(image_base64: str = Form(...)):
    if global_recognizer is None:
        return JSONResponse({"status": "error", "message": "No registered passengers in the system!"})
        
    try:
        # 2. Decode Photo
        nparr = decode_data_url_image(image_base64)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return JSONResponse({"status": "error", "message": "Invalid live capture. Please rescan your face."})
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. Detect Face
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        if len(faces) == 0:
            return JSONResponse({"status": "error", "message": "No face detected in live camera. Try adjusting light."})
        elif len(faces) > 1:
            return JSONResponse({"status": "error", "message": "Multiple faces detected. Only one person allowed at checkpoint."})
            
        x, y, w, h = faces[0]
        cropped_face = gray[y:y+h, x:x+w]
        cropped_face = cv2.resize(cropped_face, (200, 200))
        
        # 4. Predict
        label, confidence = global_recognizer.predict(cropped_face)
        
        conn = sqlite3.connect("data/travel_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, aadhaar FROM users WHERE id = ?", (label,))
        user_row = cursor.fetchone()
        conn.close()
        
        if not user_row:
             return JSONResponse({"status": "error", "message": "Face not linked to any enrolled passenger profile."})
             
        db_id, db_name, db_aadhaar = user_row
        
        # Lower LBPH confidence indicates better match.
        if confidence <= MATCH_THRESHOLD and label == db_id:
            return JSONResponse({
                "status": "success", 
                "message": f"MATCH: Verified! Access Granted for {db_name}.",
                "name": db_name,
                "aadhaar": db_aadhaar,
                "score": round(confidence, 1)
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": "NO MATCH: Passenger face does not match enrolled profile.",
                "score": round(confidence, 1)
            })
            
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"System error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=10000)