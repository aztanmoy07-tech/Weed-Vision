from flask import Flask, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os

client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
import cv2
from yolo_inference import detect_weeds
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- GOOGLE AUTH ----------------
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
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

# ---------------- MAIN APP ----------------
@app.route("/", methods=["GET", "POST"])
def index():

    result = None
    input_image = None

    if request.method == "POST":
        file = request.files.get("image")

        if file:
            filepath = os.path.join("static/uploads", file.filename)
            file.save(filepath)

            image, weed_count, confidence = detect_weeds(filepath)

            output_path = "static/uploads/output.jpg"
            cv2.imwrite(output_path, image)

            result = {
                "weed_count": weed_count,
                "confidence": confidence,
                "status": "High" if weed_count > 15 else "Moderate" if weed_count > 5 else "Low",
                "output": output_path
            }

            input_image = filepath
    return render_template(
    "index.html",
    result=result,
    input_image=input_image,
    user=session.get("user")
)

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(host="127.0.0.1", port=5000, debug=True)