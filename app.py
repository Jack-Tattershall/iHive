from flask import Flask, Response, render_template, request, redirect, url_for, session
from picamera2 import Picamera2
from threading import Lock
from time import sleep
import cv2

app = Flask(__name__)
app.secret_key = "your_secret_key"
USERNAME = "admin"
PASSWORD = "password"

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 360)}))
lock = Lock()

try:
    picam2.start()
    sleep(2)
except Exception as e:
    print(f"Error initialising the camera: {e}")
    exit(1)


def generate_frames():
    """Stream frames from Picamera2."""
    while True:
        with lock:
            frame = picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, jpeg = cv2.imencode(".jpg", frame)
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
        )


@app.route("/", methods=["GET", "POST"])
def login():
    """Render the login page or handle login submission."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == USERNAME and password == PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        else:
            return "Invalid credentials. Please try again.", 401

    return render_template("login.html")


@app.route("/index")
def index():
    """Render the main webpage if authenticated."""
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    """Stream the video feed."""
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/start_stream", methods=["POST"])
def start_stream():
    """Start the video stream."""
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return "Stream started", 200


@app.route("/stop_stream", methods=["POST"])
def stop_stream():
    """Stop the video stream."""
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return "Stream stopped", 200


@app.route("/logout")
def logout():
    """Log out the user and clear the session."""
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
