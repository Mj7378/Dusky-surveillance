
# dusky-surveillance/app.py

import streamlit as st
import cv2
import tempfile
import threading
import time
import os
import sounddevice as sd
import queue
import vosk
import json

from modules.logger import ActivityLogger
from modules.threat_ai import ThreatAnalyzer
from modules.surveillance import SurveillanceSystem

st.set_page_config(page_title="Dusky Surveillance", layout="wide")

logger = ActivityLogger()
ai = ThreatAnalyzer()
surveillance = SurveillanceSystem()

# Global flag to control the camera thread
camera_running = False
frame_placeholder = st.empty()
q = queue.Queue()
model = vosk.Model(lang="en-us")
recognizer = vosk.KaldiRecognizer(model, 16000)

def callback(indata, frames, time, status):
    q.put(bytes(indata))

def run_camera():
    global camera_running
    cam_index = surveillance.select_camera()
    cap = cv2.VideoCapture(cam_index)
    face_cascade = surveillance.face_cascade

    while camera_running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            logger.log("Face detected", details=f"[{x},{y},{w},{h}]")

        _, img = cv2.imencode('.jpg', frame)
        frame_placeholder.image(img.tobytes(), channels="BGR")
        time.sleep(0.03)

    cap.release()
    frame_placeholder.empty()

def record_and_transcribe():
    with sd.InputStream(samplerate=16000, channels=1, callback=callback):
        st.info("🎙️ Speak now (5 sec)...")
        frames = b""
        start = time.time()
        while time.time() - start < 5:
            frames += q.get()
        if recognizer.AcceptWaveform(frames):
            result = json.loads(recognizer.Result())
            return result.get("text", "")
        return ""

tabs = st.tabs(["🎥 Surveillance", "📄 Log Viewer", "🤖 AI Threat Report"])

with tabs[0]:
    st.title("🎥 Live Surveillance")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Camera"):
            if not camera_running:
                camera_running = True
                threading.Thread(target=run_camera, daemon=True).start()
    with col2:
        if st.button("⏹ Stop Camera"):
            camera_running = False

    st.markdown("---")
    st.subheader("🎙️ Voice Command")
    if st.button("🗣️ Speak Command"):
        transcript = record_and_transcribe()
        st.success(f"You said: {transcript}")
        if "start monitoring" in transcript:
            camera_running = True
            threading.Thread(target=run_camera, daemon=True).start()
        elif "stop" in transcript:
            camera_running = False
        elif "report" in transcript:
            summary = ai.analyze_logs("surveillance_logs.db")
            st.markdown(f"**AI Summary:**\n\n{summary}")

with tabs[1]:
    st.title("📄 Event Logs")
    logs = logger.fetch_all_logs()
    st.table(logs)

with tabs[2]:
    st.title("🤖 Threat Report")
    if st.button("🧠 Generate AI Summary"):
        summary = ai.analyze_logs("surveillance_logs.db")
        st.markdown(f"**Summary:**\n\n{summary}")
