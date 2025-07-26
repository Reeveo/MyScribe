import sys
from dotenv import load_dotenv
import os
import time
import threading
import queue
import glob
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QAction, QPainter, QColor, QPixmap
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
import sounddevice as sd
import soundfile as sf
import keyboard
import pygame
import assemblyai as aai
import google.generativeai as genai
from src.utils import db

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

# Initialize the database
try:
    db.init_db()
except Exception as e:
    print(f"[MyScribe] Database initialization failed: {e}")

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

# Gemini prompt from PRD
GEMINI_PROMPT = (
    "Review the following raw transcript. Remove all filler words (like 'um', 'ah', 'err', 'you know'). "
    "Correct grammar and punctuation. Format the final output into clean paragraphs. "
    "If the user outlines a list, format it with bullet points. Do not add any commentary or text that was not in the original transcript."
)

# --- AssemblyAI Integration (SDK) ---
def transcribe_with_assemblyai(audio_path, timeout=120):
    aai.settings.api_key = SPEECH_TO_TEXT_KEY
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
    try:
        print("[MyScribe] Uploading and transcribing audio with AssemblyAI...")
        transcript = aai.Transcriber(config=config).transcribe(audio_path)
        if transcript.status == "error":
            print(f"[MyScribe] AssemblyAI transcription failed: {transcript.error}")
            return None
        print("[MyScribe] Transcript received from AssemblyAI.")
        return transcript.text
    except Exception as e:
        print(f"[MyScribe] AssemblyAI error: {e}")
        return None

# --- Gemini Integration (Google Generative AI) ---
def clean_with_gemini(raw_text, timeout=60):
    try:
        print("[MyScribe] Cleaning transcript with Gemini...")
        genai.configure(api_key=LLM_KEY)
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = GEMINI_PROMPT + "\n\n" + raw_text
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip()
        print("[MyScribe] Cleaned text received from Gemini.")
        return cleaned_text
    except Exception as e:
        print(f"[MyScribe] Gemini API error: {e}")
        return None

def process_audio_file(audio_path):
    def _process():
        print(f"[MyScribe] Processing audio: {audio_path}")
        raw_text = transcribe_with_assemblyai(audio_path)
        if not raw_text:
            print("[MyScribe] No transcript returned.")
            return
        cleaned_text = clean_with_gemini(raw_text)
        if not cleaned_text:
            print("[MyScribe] No cleaned text returned.")
            return
        db.insert_transcription(audio_path, cleaned_text)
        print("[MyScribe] Cleaned text:")
        print(cleaned_text)
        # Return the cleaned text so it can be used by the caller
        return cleaned_text
    # This will be called from the tray app, which will manage the thread
    return _process()

# --- Existing CLI logic ---
def play_chime():
    try:
        pygame.mixer.music.load(CHIME_PATH)
        pygame.mixer.music.play()
        # Add a small delay to ensure the chime plays fully
        time.sleep(0.5)
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
    # Process the audio file after recording (now in background)
    process_audio_file(filename)

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

def list_gemini_models():
    print("[MyScribe] Listing available Gemini models:")
    genai.configure(api_key=LLM_KEY)
    for m in genai.list_models():
        print(f"Model: {m.name}, Supported methods: {m.supported_generation_methods}")

# --- System Tray Application ---
class ClipboardSignalEmitter(QObject):
    text_copied = Signal(str)

class SystemTrayApp:
    def __init__(self, app):
        self.app = app
        self.tray_icon = QSystemTrayIcon(self.create_icon("grey"), self.app)
        self.tray_icon.setToolTip("MyScribe - Idle")

        menu = QMenu()
        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self.on_exit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        # Initialize and setup logic
        pygame.mixer.init()
        delete_old_audio_files()
        self.setup_hotkeys()

        # Setup clipboard signal
        self.clipboard_emitter = ClipboardSignalEmitter()
        self.clipboard_emitter.text_copied.connect(self.copy_text_to_clipboard)

    def create_icon(self, color_name):
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color_name))
        painter.setPen(QColor("white"))
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()
        return QIcon(pixmap)

    def set_idle_icon(self):
        self.tray_icon.setIcon(self.create_icon("grey"))
        self.tray_icon.setToolTip("MyScribe - Idle")

    def set_recording_icon(self):
        self.tray_icon.setIcon(self.create_icon("red"))
        self.tray_icon.setToolTip("MyScribe - Recording")

    def set_processing_icon(self):
        self.tray_icon.setIcon(self.create_icon("blue"))
        self.tray_icon.setToolTip("MyScribe - Processing")

    def on_exit(self):
        print("[MyScribe] Exiting...")
        if recording:
            stop_recording()
        self.app.quit()

    def process_audio_queue(self):
        """Monitors the queue for new audio files and processes them."""
        try:
            while True:
                audio_path = audio_queue.get()
                self.set_processing_icon()
                # Run processing in a background thread to not block the queue monitor
                threading.Thread(target=self.run_processing, args=(audio_path,), daemon=True).start()
                audio_queue.task_done()
        except queue.Empty:
            pass # This is expected when the queue is empty

    def run_processing(self, audio_path):
        cleaned_text = process_audio_file(audio_path)
        if cleaned_text:
            self.clipboard_emitter.text_copied.emit(cleaned_text)
        # Once processing is done, switch icon back to idle
        self.set_idle_icon()

    def copy_text_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        print("[MyScribe] Cleaned text copied to clipboard.")

    def start_recording_ui(self):
        self.set_recording_icon()
        start_recording()

    def stop_recording_ui(self):
        stop_recording()
        play_chime() # Play chime when recording stops
        # The icon will be set to processing when the file is picked up from the queue
        # and back to idle when it's done.

    def on_ctrl_alt_press(self, e=None):
        global last_press_time, continuous_mode
        now = time.time()
        if not recording:
            if now - last_press_time < DOUBLE_PRESS_INTERVAL:
                continuous_mode = True
                play_chime()
                self.start_recording_ui()
            else:
                last_press_time = now
                continuous_mode = False
                self.start_recording_ui()
        else:
            if continuous_mode:
                self.stop_recording_ui()
                continuous_mode = False

    def on_ctrl_alt_release(self, e=None):
        if recording and not continuous_mode:
            self.stop_recording_ui()

    def on_ctrl_alt_space(self, e=None):
        global continuous_mode
        if not recording:
            continuous_mode = True
            play_chime()
            self.start_recording_ui()

    def setup_hotkeys(self):
        keyboard.add_hotkey('ctrl+alt', self.on_ctrl_alt_press, suppress=False, trigger_on_release=False)
        keyboard.on_release_key('ctrl', self.on_ctrl_alt_release)
        keyboard.on_release_key('alt', self.on_ctrl_alt_release)
        keyboard.add_hotkey('ctrl+alt+space', self.on_ctrl_alt_space, suppress=False)
        print("[MyScribe] Hotkeys registered and application is running in the system tray.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        main_cli()
    elif len(sys.argv) > 1 and sys.argv[1] == '--list-gemini-models':
        list_gemini_models()
    else:
        app = QApplication(sys.argv)
        # Prevent app from quitting when last window is closed
        app.setQuitOnLastWindowClosed(False)
        tray_app = SystemTrayApp(app)

        # Start a thread to monitor the audio queue
        queue_monitor_thread = threading.Thread(target=tray_app.process_audio_queue, daemon=True)
        queue_monitor_thread.start()

        sys.exit(app.exec())