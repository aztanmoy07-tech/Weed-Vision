from flask import Flask, render_template, request, redirect, url_for, session
import os, uuid, time
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
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

# ---------------- DETECTION FUNCTION ----------------
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

        # noise reduction
        kernel = np.ones((7, 7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        weed_boxes = []
        output_img = img.copy()

        for c in contours:
            area = cv2.contourArea(c)

            # ❌ ignore main crop (dynamic)
            if area > (img.shape[0] * img.shape[1]) * 0.1:
                continue

            # ❌ ignore noise
            if area < 1200:
                continue

            x, y, w, h = cv2.boundingRect(c)

            merged = False
            for i, (mx, my, mw, mh) in enumerate(weed_boxes):
                cx1, cy1 = x + w//2, y + h//2
                cx2, cy2 = mx + mw//2, my + mh//2

                dist = math.hypot(cx1 - cx2, cy1 - cy2)

                if dist < 80:
                    nx = min(x, mx)
                    ny = min(y, my)
                    nw = max(x+w, mx+mw) - nx
                    nh = max(y+h, my+mh) - ny

                    weed_boxes[i] = (nx, ny, nw, nh)
                    merged = True
                    break

            if not merged:
                weed_boxes.append((x, y, w, h))

        weed_count = len(weed_boxes)

        # draw boxes
        for (x, y, w, h) in weed_boxes:
            cv2.rectangle(output_img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # ✅ FIXED PATH HANDLING
        name, ext = os.path.splitext(image_path)
        mask_path = name + "_mask" + ext
        output_path = name + "_box" + ext

        mask_colored = cv2.bitwise_and(img, img, mask=mask)

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
    error = None

    weed_count = 0
    confidence = 0
    health = 100
    density = 0

    lat = 20.5937
    lng = 78.9629

    if request.method == "POST":

        file = request.files.get("image")

        # ❌ FILE CHECK
        if not file or file.filename == "":
            error = "Please upload an image"
        elif not allowed_file(file.filename):
            error = "Only JPG/PNG allowed"

        else:
            # 🌍 GPS
            try:
                lat = float(request.form.get("lat"))
                lng = float(request.form.get("lng"))
            except:
                pass

            # save file
            filename = str(uuid.uuid4()) + "_" + file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            input_image = filepath

            # 🔥 DETECTION
            weed_count, mask_path, boxed_path = detect_weeds(filepath)

            # 📊 METRICS
            density = min(100, weed_count * 4)
            health = max(0, 100 - density)

            confidence = min(95, max(65, int(100 - (density * 0.5))))

            # 📊 STATUS
            if density > 70:
                status = "Critical"
            elif density > 40:
                status = "High"
            elif density > 15:
                status = "Moderate"
            else:
                status = "Low"

            result = {
                "weed_count": weed_count,
                "confidence": confidence,
                "status": status,
                "output": boxed_path,
                "mask": mask_path,
                "recommendation": "Spray immediately" if density > 40 else "Monitor field",
                "health": health,
                "density": density,
                "lat": lat,
                "lng": lng
            }

            # 📜 HISTORY
            history.append({
                "weed_count": weed_count,
                "status": status,
                "lat": lat,
                "lng": lng
            })

            if len(history) > 20:
                history.pop(0)

            # 🧹 CLEAN OLD FILES
            for f in os.listdir(UPLOAD_FOLDER):
                path = os.path.join(UPLOAD_FOLDER, f)
                if os.path.isfile(path):
                    if time.time() - os.path.getmtime(path) > 86400:
                        os.remove(path)

    return render_template(
        "index.html",
        result=result,
        input_image=input_image,
        user=session.get("user"),
        history=history,
        error=error
    )


# ---------------- LOGIN ----------------
@app.route("/login")
def login():
    return google.authorize_redirect(url_for("callback", _external=True))


@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    session["user"] = token["userinfo"]
    return redirect("/")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)