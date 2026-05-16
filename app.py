from flask import Flask, request, jsonify
import subprocess
import requests
import os

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract():

    data = request.json
    video_url = data['video_url']

    r = requests.get(video_url)

    with open("video.mp4", "wb") as f:
        f.write(r.content)

    os.makedirs("frames", exist_ok=True)

    subprocess.run([
        "ffmpeg",
        "-i", "video.mp4",
        "-vf", "fps=1/10",
        "frames/frame_%04d.jpg"
    ])

    return jsonify({"status": "done"})

app.run(host="0.0.0.0", port=8080)