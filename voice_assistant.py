
import queue
import sounddevice as sd
import vosk
import sys
import json
import threading
import time
import select

class VoiceAssistant:
    def __init__(self, mode="hybrid"):
        self.mode = mode
        self.model = vosk.Model(lang="en-us")
        self.q = queue.Queue()
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        self.stream = sd.InputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=self.callback)
        self.listening = True if self.mode in ["always", "hybrid"] else False
        self.result = None

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def listen_for_command(self):
        if self.mode == "button":
            input("\nPress Enter to speak...")
            return self.capture_once()
        elif self.mode == "always":
            return self.listen_continuously()
        elif self.mode == "hybrid":
            print("[VOICE] Listening... (or press Enter to speak manually)")
            try:
                threading.Thread(target=self.listen_continuously, daemon=True).start()
                while True:
                    if self.result:
                        command = self.result
                        self.result = None
                        return command
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        input()
                        return self.capture_once()
                    time.sleep(0.2)
            except KeyboardInterrupt:
                return "exit"

    def listen_continuously(self):
        with self.stream:
            while True:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        return text

    def capture_once(self):
        print("[VOICE] Speak now...")
        self.listening = True
        buffer = b""
        with self.stream:
            start_time = time.time()
            while time.time() - start_time < 5:
                data = self.q.get()
                buffer += data
                if self.recognizer.AcceptWaveform(data):
                    break
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "")
            print(f"[VOICE] You said: {text}")
            return text
