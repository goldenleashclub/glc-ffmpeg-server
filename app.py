from flask import Flask, request, jsonify
import subprocess
import os
import shutil
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Golden Leash FFmpeg server is running."

@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded. Field name must be 'file'."}), 400

    uploaded_file = request.files["file"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = f"job_{timestamp}"
    frames_dir = os.path.join(work_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    video_path = os.path.join(work_dir, "video.mp4")
    uploaded_file.save(video_path)

    result = subprocess.run([
        "ffmpeg",
        "-i", video_path,
        "-vf", "fps=1/10",
        os.path.join(frames_dir, "frame_%04d.jpg")
    ], capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({
            "status": "error",
            "message": "FFmpeg failed",
            "stderr": result.stderr
        }), 500

    frame_count = len([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])

    # Clean up so Railway storage doesn't fill up
    shutil.rmtree(work_dir, ignore_errors=True)

    return jsonify({
        "status": "done",
        "frames_extracted": frame_count
    })
