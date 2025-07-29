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
from src.ui.history_window import HistoryWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

CHIME_PATH = resource_path(os.path.join('resources', 'notification_bell.mp3'))
BUBBLE_POP_PATH = resource_path(os.path.join('resources', 'bubble_pop.mp3'))
DOUBLE_POP_PATH = resource_path(os.path.join('resources', 'double_pop.mp3'))
ICON_PATH = resource_path(os.path.join('resources', 'Myscribe_icon.ico'))

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

def play_pop():
    try:
        pygame.mixer.music.load(BUBBLE_POP_PATH)
        pygame.mixer.music.play()
        # Add a small delay to ensure the chime plays fully
        time.sleep(0.6)
    except Exception as e:
        print(f"[MyScribe] Could not play pop: {e}")        

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
    # The audio file will be picked up and processed by the queue monitor

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
    global continuous_mode
    # This hotkey now ONLY stops continuous recording.
    if recording and continuous_mode:
        stop_recording()
        continuous_mode = False
        print("[MyScribe] Continuous mode disabled.")

def on_ctrl_shift_press(e=None):
    global continuous_mode
    if not recording:
        continuous_mode = False # Hold-to-record
        start_recording()

def on_key_release(e=None):
    # Stops hold-to-record when keys are released
    if recording and not continuous_mode:
        stop_recording()

def on_ctrl_alt_space(e=None):
    global continuous_mode
    # Toggles continuous recording
    if not recording:
        continuous_mode = True
        print("[MyScribe] Continuous mode enabled.")
        start_recording()
    elif continuous_mode:
        stop_recording()
        continuous_mode = False
        print("[MyScribe] Continuous mode disabled.")

def setup_hotkeys():
    keyboard.unhook_all()  # Start fresh
    keyboard.add_hotkey('ctrl+alt+space', on_ctrl_alt_space, suppress=False)
    keyboard.add_hotkey('ctrl+alt', on_ctrl_alt_press, suppress=False)
    keyboard.add_hotkey('ctrl+shift', on_ctrl_shift_press, suppress=False, trigger_on_release=False)
    keyboard.on_release_key('ctrl', on_key_release)
    keyboard.on_release_key('shift', on_key_release)
    print("[MyScribe] Hotkeys: Ctrl+Alt+Space (toggle continuous), Ctrl+Alt (stop), Ctrl+Shift (hold to record)")


def main_cli():
    print("[MyScribe] CLI prototype started. Press Ctrl+Alt+Space to toggle continuous, Ctrl+Shift to hold-to-record, Ctrl+Alt to stop.")
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
class WorkerSignals(QObject):
    started = Signal()
    finished = Signal(str)
    processing_finished_sound = Signal()

class SystemTrayApp:
    def __init__(self, app):
        self.app = app
        self.signals = WorkerSignals()
        self.history_window = None # To hold the history window instance

        self.tray_icon = QSystemTrayIcon(QIcon(ICON_PATH), self.app)
        self.tray_icon.setToolTip("MyScribe - Idle")

        menu = QMenu()
        history_action = QAction("History", self.app)
        history_action.triggered.connect(self.show_history)
        menu.addAction(history_action)

        self.auto_paste_action = QAction("Auto-paste", self.app)
        self.auto_paste_action.setCheckable(True)
        self.auto_paste_action.setChecked(True) # Default to on
        menu.addAction(self.auto_paste_action)

        menu.addSeparator()

        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self.on_exit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        # Initialize and setup logic
        pygame.mixer.init()
        delete_old_audio_files()
        self.setup_hotkeys()

        # Show the history window on startup
        self.show_history()

        # Setup thread-safe signals
        self.signals.started.connect(self.on_processing_started)
        self.signals.finished.connect(self.on_processing_finished)
        self.signals.processing_finished_sound.connect(self.play_double_pop)

    def set_idle_icon(self):
        self.tray_icon.setIcon(QIcon(ICON_PATH))
        self.tray_icon.setToolTip("MyScribe - Idle")

    def set_recording_icon(self):
        # For now, we'll just change the tooltip. A more advanced implementation
        # could overlay a red dot on the icon.
        self.tray_icon.setToolTip("MyScribe - Recording")

    def set_processing_icon(self):
        # Tooltip change for processing state
        self.tray_icon.setToolTip("MyScribe - Processing")

    def on_exit(self):
        print("[MyScribe] Exiting...")
        if recording:
            stop_recording()
        keyboard.unhook_all()
        self.app.quit()

    def process_audio_queue(self):
        """Monitors the queue for new audio files and processes them."""
        while True:
            try:
                audio_path = audio_queue.get(timeout=1) # Use timeout to allow periodic checks
                # Run processing in a background thread to not block the queue monitor
                threading.Thread(target=self.run_processing, args=(audio_path,), daemon=True).start()
                audio_queue.task_done()
            except queue.Empty:
                continue # This is expected, just continue the loop

    def run_processing(self, audio_path):
        self.signals.started.emit()
        cleaned_text = process_audio_file(audio_path)
        self.signals.finished.emit(cleaned_text or "")
        self.signals.processing_finished_sound.emit()

    def on_processing_started(self):
        self.set_processing_icon()

    def on_processing_finished(self, cleaned_text):
        if cleaned_text:
            if self.auto_paste_action.isChecked():
                keyboard.write(cleaned_text)
                print("[MyScribe] Cleaned text auto-pasted.")
            else:
                clipboard = QApplication.clipboard()
                clipboard.setText(cleaned_text)
                print("[MyScribe] Cleaned text copied to clipboard.")
        self.set_idle_icon()
        if self.history_window:
            self.history_window.populate_history()

    def show_history(self):
        if self.history_window is None:
            self.history_window = HistoryWindow()
        self.history_window.populate_history()
        self.history_window.show()
        self.history_window.activateWindow()

    def play_double_pop(self):
        try:
            pygame.mixer.music.load(DOUBLE_POP_PATH)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"[MyScribe] Could not play double pop: {e}")

    def start_recording_ui(self):
        self.set_recording_icon()
        play_pop()
        start_recording()

    def stop_recording_ui(self):
        stop_recording()
        play_chime() # Play chime when recording stops
        # The icon will be set to processing when the file is picked up from the queue
        # and back to idle when it's done.

    def on_ctrl_alt_press(self, e=None):
        global continuous_mode
        # This hotkey now ONLY stops continuous recording.
        if recording and continuous_mode:
            self.stop_recording_ui()
            continuous_mode = False

    def on_ctrl_shift_press(self, e=None):
        global continuous_mode
        if not recording:
            continuous_mode = False # Hold-to-record
            self.start_recording_ui()

    def on_key_release(self, e=None):
        # Stops hold-to-record when keys are released
        if recording and not continuous_mode:
            self.stop_recording_ui()

    def on_ctrl_alt_space(self, e=None):
        global continuous_mode
        # Toggles continuous recording
        if not recording:
            continuous_mode = True
            self.start_recording_ui()
        elif continuous_mode:
            self.stop_recording_ui()
            continuous_mode = False

    def setup_hotkeys(self):
        keyboard.unhook_all()  # Start fresh
        keyboard.add_hotkey('ctrl+alt+space', self.on_ctrl_alt_space, suppress=False)
        keyboard.add_hotkey('ctrl+alt', self.on_ctrl_alt_press, suppress=False)
        keyboard.add_hotkey('ctrl+shift', self.on_ctrl_shift_press, suppress=False, trigger_on_release=False)
        keyboard.on_release_key('ctrl', self.on_key_release)
        keyboard.on_release_key('shift', self.on_key_release)
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