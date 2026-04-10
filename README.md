# Final Project 2.0 - Advanced AI Secure Travel Identity System

Namaste! 🙏 Welcome to the **Advanced version** of your final year project. Ab yeh project bilkul ek real application ban chuka hai jisme **Live Webcams**, aur **In-browser QR Scanning** ki power add ki gayi hai.

Is advanced flow mein:
1. **Register → Live Face Capture → Validation → QR Ticket Generate.**
2. **Verification → QR Scan via Web Camera → Validation → Face Match via Webcam → Access Granted.**

---

### Step 1: Registration (Live Face Capture)
Humne frontend (`register.html`) mein JavaScript ka `navigator.mediaDevices.getUserMedia` API use kiya hai.
- Ye function browser ke andar directly aapka Laptop ya Mobile Camera open karta hai.
- Ye video frame se photo nikalta hai aur us photo ko `Base64 String` (Lamba text) mein badal kar server par API ke roop mein bhejta hai.
- **Backend (app.py):** Python mein Base64 text ko Numpy array image me tabdeel karke OpenCV `CascadeClassifier` ko diya jata hai.
- Agar koi chehra nahi hai (**No face detected**) ya tasveer me 2 log hain (**Multiple faces detected**), to system error deta hai aur reject kar deta hai.

### Step 2: Face Storage & Resizing
- **Accuracy Improvement:** Chehra crop karne ke baad OpenCV ( backend ) usay fix shape `(200, 200)` mein Resize karta hai. Resize karne se machine learning model ki duri/distance (Tolerance) galti nahi karti chahe photo camera se kitni hi dur q na ho.
- **Storage:** OpenCV un face pixels ko SQLite Database ke andar store/save kar deta hai. Aadhaar code ko encrypt karke QR image banega aur locally save hoga.

### Step 3: Live Checkpoint Verification (QR + Face)
Ab `verify.html` bilkul ek Checkpoint jaisa dikhta hai!
1. **QR Scan:** Woh aapse pehle apni Ticket (QR Code) dikhane kehega. JavaScript ki library `html5-qrcode` automatically aapke hardware camera se QR code ko padh kar uske andar ka aadhaar nikal legi.
2. **Face Scan:** QR verify hone ke baad camera dubara khulega Live Face photo khichne ke liye.
3. Backend par woh naya face wapas extract hota hai aur stored data se Compare (`global_recognizer.predict`) hota hai. Agar tolerance 110 se niche hui, **Match -> Verified**. Varna system "Not Verified" / Reject kar dega.

---

## 🎓 Advanced Viva Questions & Answers

**Q1: Tumne website par Webcam backend python/FastAPI se kaise connect kiya?**
**Ans:** Sir, Client-side (HTML) par humne JS ka `getUserMedia()` API use kiya hai camera capture karne ke liye. Capture hone par us frame ko `<canvas>` par draw kiya, phir us canvas image ko `base64 encoded string` mein convert karke AJAX (fetch backend) ke jariye secure HTTP POST request par Python API `/register` par bheja. Waha Base64 decode ho kar wapas image matrix ban jata hai.

**Q2: OpenCV "Encoding" ya Training background me kaise kam karta hai?**
**Ans:** OpenCV ka Local Binary Pattern Histogram (LBPH) kisi face ki photo ko chote-chote squares/grids me kaat-ta hai (jaise 8x8), aur unke ander ki brightness/pixels ko aspas ke pixels se compare kar k ek math "histogram pattern" banata hai. Isliye isko save karna easy hota hai. Match karte waqt ye dono histograms me farak (distance/confidence) ko paktar leta hai.

**Q3: Tumne Multiple faces aur No face wali galti kaise dur ki?**
**Ans:** Python OpenCV mein jab hum `face_cascade.detectMultiScale()` method run karte hain, toh wo kitne faces photo mein hain unki list return karta hai. Maine Logic likha hai ki `if len(faces) == 0` (to throw error "No Face") aur `if len(faces) > 1` (to throw error "Multiple faces").

**Q4: Accuracy improve karne k liye kya steps liye gye hain?**
**Ans:** 
1. **Light Check:** Code strict restrictions deta h agar lighting theek nhi ya chehre theek frame me nahi.
2. **Standardization:** Crop hone k baad har face ko `cv2.resize()` se `200x200` banaya gya hai, is se LBPH shape distortion k khatro sy bch jata hy.
3. **Tolerance limit:** Confidence cutoff logic tweak kiya gaya hai (at `110`) taking practical scenario of college laptop cameras into consideration.
