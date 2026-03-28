from flask import Flask, render_template, request, redirect, url_for, session
import os
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import uuid
import cv2
import numpy as np

# ---------------- GLOBALS ----------------
history = []

# ---------------- LOAD ENV ----------------
load_dotenv()

app = Flask(__name__)
app.secret_key = "weedvision_secret_123"

# ✅ LIMIT FILE SIZE (5MB)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# ---------------- UPLOAD FOLDER ----------------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ ALLOWED FILE TYPES
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- GOOGLE AUTH ----------------
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# ---------------- REAL DETECTION FUNCTION ----------------
def detect_weeds(image_path):
    try:
        import math

        img = cv2.imread(image_path)

        if img is None:
            return 0, None, None

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])

        mask = cv2.inRange(hsv, lower_green, upper_green)

        # 🔥 BETTER NOISE HANDLING
        kernel = np.ones((7, 7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        weed_boxes = []
        output_img = img.copy()

        for c in contours:
            area = cv2.contourArea(c)

            # ❌ IGNORE MAIN PLANT
            if area > 7000:
                continue

            # ❌ IGNORE SMALL NOISE
            if area < 1200:
                continue

            x, y, w, h = cv2.boundingRect(c)

            # 🔥 MERGE CLOSE CONTOURS (KEY FIX)
            merged = False
            for i, (mx, my, mw, mh) in enumerate(weed_boxes):

                cx1 = x + w // 2
                cy1 = y + h // 2

                cx2 = mx + mw // 2
                cy2 = my + mh // 2

                dist = math.hypot(cx1 - cx2, cy1 - cy2)

                if dist < 80:   # 🔥 adjust if needed
                    nx = min(x, mx)
                    ny = min(y, my)
                    nw = max(x+w, mx+mw) - nx
                    nh = max(y+h, my+mh) - ny

                    weed_boxes[i] = (nx, ny, nw, nh)
                    merged = True
                    break

            if not merged:
                weed_boxes.append((x, y, w, h))

        # 🔥 FINAL COUNT
        weed_count = len(weed_boxes)

        # 🔥 DRAW ONLY FINAL BOXES
        for (x, y, w, h) in weed_boxes:
            cv2.rectangle(output_img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # 🔥 MASK IMAGE
        mask_colored = cv2.bitwise_and(img, img, mask=mask)

        mask_path = image_path.replace(".", "_mask.")
        output_path = image_path.replace(".", "_box.")

        cv2.imwrite(mask_path, mask_colored)
        cv2.imwrite(output_path, output_img)

        return weed_count, mask_path, output_path

    except Exception as e:
        print("Detection error:", e)
        return 0, None, None
# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def index():

    global history

    result = None
    input_image = None

    weed_count = 0
    confidence = 0
    output_path = None
    health = 100
    density = 0

    # 🌍 DEFAULT GPS (India center)
    lat = 20.5937
    lng = 78.9629

    if request.method == "POST":

        file = request.files.get("image")

        # ✅ FILE CHECK
        if not file or file.filename == "":
            return render_template(
                "index.html",
                result=None,
                input_image=None,
                user=session.get("user"),
                history=history
            )

        # ✅ FILE TYPE CHECK
        if not allowed_file(file.filename):
            return render_template(
                "index.html",
                result=None,
                input_image=None,
                user=session.get("user"),
                history=history
            )

        # 🌍 GET GPS FROM FORM
        lat_input = request.form.get("lat")
        lng_input = request.form.get("lng")

        try:
            lat = float(lat_input)
            lng = float(lng_input)
        except:
            lat = 20.5937
            lng = 78.9629

        # ✅ UNIQUE FILE NAME
        filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        input_image = filepath

        # ✅ REAL DETECTION
        weed_count, mask_path, boxed_path = detect_weeds(filepath)
        # ✅ CONFIDENCE LOGIC
        confidence = min(95, max(60, weed_count * 3))

        # ✅ METRICS
        density = min(100, weed_count * 4)
        health = max(0, 100 - density)

        output_path = filepath

        result = {
    "weed_count": weed_count,
    "confidence": confidence,
    "status": "High" if weed_count > 15 else "Moderate" if weed_count > 5 else "Low",
    "output": boxed_path,   # 🔥 SHOW BOXED IMAGE
    "mask": mask_path,
    "recommendation": "Spray immediately" if weed_count > 15 else "Monitor field",
    "health": health,
    "density": density,
    "lat": lat,
    "lng": lng
}

        # ✅ HISTORY UPDATE
        history.append({
            "weed_count": weed_count,
            "status": result["status"]
        })

        if len(history) > 20:
            history.pop(0)

    return render_template(
        "index.html",
        result=result,
        input_image=input_image,
        user=session.get("user"),
        history=history
    )


# ---------------- LOGIN ----------------

@app.route("/login")
def login():
    return google.authorize_redirect(url_for("callback", _external=True))


@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    user = token["userinfo"]
    session["user"] = user
    return redirect("/")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)