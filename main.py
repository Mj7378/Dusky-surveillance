from modules.voice_assistant import VoiceAssistant
from modules.surveillance import SurveillanceSystem
from modules.logger import ActivityLogger
from modules.threat_ai import ThreatAnalyzer

def main():
    print("[SYSTEM] Dusky AI Surveillance System Starting...")
    voice = VoiceAssistant(mode="hybrid")  # 'always', 'button', or 'hybrid'
    camera = SurveillanceSystem()
    logger = ActivityLogger()
    ai = ThreatAnalyzer()
    while True:
        command = voice.listen_for_command()
        if command:
            if "start monitoring" in command:
                logger.log("Surveillance started")
                camera.start_stream(logger)
            elif "show report" in command:
                summary = ai.analyze_logs("surveillance_logs.db")
                print("\n[AI REPORT]\n", summary)
            elif "exit" in command:
                logger.log("Surveillance stopped")
                break
