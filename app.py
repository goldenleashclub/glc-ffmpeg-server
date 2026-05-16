from flask import Flask, request, jsonify
import subprocess
import os
import shutil
from datetime import datetime
import boto3

app = Flask(__name__)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION"),
)

S3_BUCKET = os.environ.get("S3_BUCKET")


@app.route("/", methods=["GET"])
def home():
    return "Golden Leash FFmpeg server is running."


@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file uploaded. Field name must be 'file'."
        }), 400

    uploaded_file = request.files["file"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = uploaded_file.filename or "video.mp4"
    safe_name = original_filename.replace(" ", "_").replace("/", "_")

    work_dir = f"job_{timestamp}"
    frames_dir = os.path.join(work_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    video_path = os.path.join(work_dir, safe_name)
    uploaded_file.save(video_path)

    result = subprocess.run([
        "ffmpeg",
        "-i", video_path,
        "-vf", "fps=1/10",
        os.path.join(frames_dir, "frame_%04d.jpg")
    ], capture_output=True, text=True)

    if result.returncode != 0:
        shutil.rmtree(work_dir, ignore_errors=True)
        return jsonify({
            "status": "error",
            "message": "FFmpeg failed",
            "stderr": result.stderr
        }), 500

    uploaded_frames = []

    for filename in sorted(os.listdir(frames_dir)):
        if filename.endswith(".jpg"):
            local_path = os.path.join(frames_dir, filename)
            s3_key = f"frames/{timestamp}_{safe_name}/{filename}"

            s3.upload_file(
                local_path,
                S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "image/jpeg"}
            )

            uploaded_frames.append({
                "bucket": S3_BUCKET,
                "key": s3_key
            })

    shutil.rmtree(work_dir, ignore_errors=True)

    return jsonify({
        "status": "done",
        "frames_extracted": len(uploaded_frames),
        "frames": uploaded_frames
    })
