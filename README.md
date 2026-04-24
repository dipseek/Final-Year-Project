# Aadhaar Secure Travel Identity System (Face-Only Verification)

This project is a final-year style biometric checkpoint system built with FastAPI, OpenCV, and SQLite.
It allows passenger registration with face enrollment and performs live **face-only verification** at checkpoint time.

## Features

- Live face capture from browser camera or uploaded image
- Face detection validation:
  - No face detected -> rejected
  - Multiple faces detected -> rejected
- Face preprocessing and normalization (`200x200` grayscale)
- Passenger face enrollment in SQLite
- Live checkpoint verification using OpenCV LBPH recognizer
- Clear success/error responses with match score

## Current Flow

1. **Register Passenger**
   - Enter name and 12-digit Aadhaar
   - Capture/upload face image
   - Backend validates and stores processed face data

2. **Verify Passenger (Face-Only)**
   - Open verification page
   - Capture live face
   - System predicts identity and checks confidence threshold
   - Access granted/denied with result details

## Tech Stack

- **Backend:** FastAPI, Uvicorn
- **Computer Vision:** OpenCV (`opencv-contrib-python`)
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript, Jinja2 templates
- **Other:** NumPy, Pillow, python-multipart

## Project Structure

```text
aadhar-project/
|- app.py
|- requirements.txt
|- templates/
|  |- base.html
|  |- index.html
|  |- register.html
|  |- verify.html
|  |- success.html
|- static/
|  |- style.css
|- data/
|  |- travel_system.db
```

## Installation

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the Project

```bash
python app.py
```

Open in browser:

- `http://127.0.0.1:10000`

## Main Endpoints

- `GET /` - Home page
- `GET /register_page` - Registration page
- `POST /register` - Register passenger
- `GET /verify` - Face verification page
- `POST /api/verify_face` - Verify live face

## Notes

- Aadhaar is validated as exactly 12 digits.
- Face recognition uses LBPH model retrained from enrolled users.
- Current matching threshold is controlled in `app.py` using `MATCH_THRESHOLD`.

## Future Enhancements

- Liveness detection (anti-spoofing)
- Admin dashboard for logs and analytics
- Multi-camera checkpoint support
- Better model calibration and dataset management
