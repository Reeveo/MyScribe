import sys
from dotenv import load_dotenv
import os
import time
import threading
import queue
import glob
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
import sounddevice as sd
import soundfile as sf
import keyboard
import pygame

CHIME_PATH = os.path.join('resources', 'notification_bell.mp3')

# Load environment variables from .env file
load_dotenv()

SPEECH_TO_TEXT_KEY = os.getenv('SPEECH_TO_TEXT_KEY')
LLM_KEY = os.getenv('LLM_KEY')
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', 30))
AUDIO_DIR = os.getenv('AUDIO_STORAGE_PATH', './audio')

# Warn if API keys are missing
if not SPEECH_TO_TEXT_KEY or not LLM_KEY:
    print("[MyScribe] Warning: API keys are missing from your .env file.")

# Ensure audio directory exists
os.makedirs(AUDIO_DIR, exist_ok=True)

# Audio recording state
recording = False
continuous_mode = False
recording_thread = None
stop_recording_event = threading.Event()

# For double-press detection
last_press_time = 0
DOUBLE_PRESS_INTERVAL = 0.5  # seconds

# For thread-safe communication
audio_queue = queue.Queue()

def play_chime():
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(CHIME_PATH)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"[MyScribe] Could not play chime: {e}")

def delete_old_audio_files():
    now = datetime.now()
    for file in glob.glob(os.path.join(AUDIO_DIR, '*.wav')):
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(file))
            if now - mtime > timedelta(days=RETENTION_DAYS):
                os.remove(file)
                print(f"Deleted old audio file: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

def record_audio(filename, stop_event):
    samplerate = 44100
    channels = 1
    print(f"Recording to {filename}...")
    with sf.SoundFile(filename, mode='w', samplerate=samplerate, channels=channels) as file:
        with sd.InputStream(samplerate=samplerate, channels=channels) as stream:
            while not stop_event.is_set():
                data, _ = stream.read(1024)
                file.write(data)
    print(f"Recording saved: {filename}")
    audio_queue.put(filename)

def start_recording():
    global recording, recording_thread, stop_recording_event
    if recording:
        return
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(AUDIO_DIR, f"myscribe_{timestamp}.wav")
    stop_recording_event.clear()
    recording_thread = threading.Thread(target=record_audio, args=(filename, stop_recording_event))
    recording_thread.start()
    recording = True
    print("[MyScribe] Recording started.")

def stop_recording():
    global recording, recording_thread, stop_recording_event
    if not recording:
        return
    stop_recording_event.set()
    if recording_thread:
        recording_thread.join()
    recording = False
    print("[MyScribe] Recording stopped.")

def on_ctrl_alt_press(e=None):
    global last_press_time, continuous_mode
    now = time.time()
    if not recording:
        # Check for double-press
        if now - last_press_time < DOUBLE_PRESS_INTERVAL:
            continuous_mode = True
            play_chime()
            print("[MyScribe] Continuous mode enabled.")
            start_recording()
        else:
            last_press_time = now
            # Start hold-to-record
            continuous_mode = False
            start_recording()
    else:
        if continuous_mode:
            # Stop continuous mode
            stop_recording()
            continuous_mode = False
            print("[MyScribe] Continuous mode disabled.")
        else:
            # Already recording in hold-to-record, ignore
            pass

def on_ctrl_alt_release(e=None):
    if recording and not continuous_mode:
        stop_recording()

def on_ctrl_alt_space(e=None):
    global continuous_mode
    if not recording:
        continuous_mode = True
        play_chime()
        print("[MyScribe] Continuous mode enabled (via Space).")
        start_recording()
    else:
        # If already recording, ignore
        pass

def setup_hotkeys():
    # Listen for Ctrl+Alt press
    keyboard.add_hotkey('ctrl+alt', on_ctrl_alt_press, suppress=False, trigger_on_release=False)
    # Listen for Ctrl+Alt release (for hold-to-record mode)
    keyboard.on_release_key('ctrl', on_ctrl_alt_release)
    keyboard.on_release_key('alt', on_ctrl_alt_release)
    # Listen for Ctrl+Alt+Space for continuous mode
    keyboard.add_hotkey('ctrl+alt+space', on_ctrl_alt_space, suppress=False)
    print("[MyScribe] Hotkeys registered: Ctrl+Alt (hold or double-press), Ctrl+Alt+Space (continuous mode)")


def main_cli():
    print("[MyScribe] CLI prototype started. Press Ctrl+Alt to record, double-press for continuous, Ctrl+Alt+Space for continuous mode.")
    pygame.mixer.init()
    delete_old_audio_files()
    setup_hotkeys()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MyScribe] Exiting...")
        if recording:
            stop_recording()


# PySide6 window placeholder
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyScribe")
        self.setGeometry(100, 100, 800, 600)
        # Placeholder for future UI

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        main_cli()
    else:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec()) 