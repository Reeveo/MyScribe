# Development Plan: MyScribe MVP (PySide6)

## Overview
This plan outlines the actionable steps to deliver the MVP for MyScribe, a personal AI dictation desktop tool, using PySide6 (Qt for Python). The plan is derived from the PRD and focuses strictly on MVP features.

---

## Milestone 1: Core Hotkey Listener & Audio Recorder (CLI Prototype)
- **Goal:** User can start/stop audio recording via a global hotkey (Alt+Ctrl) from anywhere in Windows.
- **Tasks:**
  - Set up Python environment and dependencies (PySide6, sounddevice/pyaudio, keyboard/hotkey library).
  - Implement a global hotkey listener (Alt+Ctrl for start/stop recording).
  - Record audio from the default microphone
  - Save audio to a temporary file.
- **Acceptance Criteria:**
  - Pressing Alt+Ctrl starts recording; pressing again stops.
  - Audio is saved and deleted after 30 days.
- **Test Considerations:**
  - Unit test hotkey detection logic.
  - Manual test: Record and playback audio file.

---

## Milestone 2: AI Processing Chain Integration
- **Goal:** Convert recorded audio to clean, formatted text using external APIs.
- **Tasks:**
  - Integrate with a Speech-to-Text API (e.g., AssemblyAI, Deepgram).
  - Integrate with an LLM API (e.g., Gemini) for transcript cleaning.
  - Implement secure API key management (config file or environment variable).
  - Handle errors and API failures gracefully.
- **Acceptance Criteria:**
  - Audio file is transcribed and cleaned text is returned.
  - Errors are logged and surfaced to the user.
- **Test Considerations:**
  - Unit test API integration (mock responses).
  - Manual test: End-to-end audio-to-text flow.

---

## Milestone 3: System Tray Application & Clipboard Integration
- **Goal:** Provide a background app with a system tray icon and clipboard copy functionality.
- **Tasks:**
  - Create a PySide6 system tray application with three icon states (Idle, Recording, Processing).
  - Integrate hotkey and audio logic into the tray app.
  - Automatically copy the final clean text to the clipboard.
  - Ensure low resource usage when idle.
- **Acceptance Criteria:**
  - Tray icon reflects app state.
  - Clean text is copied to clipboard after processing.
- **Test Considerations:**
  - Unit test clipboard logic.
  - Manual test: Visual feedback and clipboard copy.

---

## Milestone 4: History Viewer Window
- **Goal:** Display a list of all past transcriptions with timestamps and copy buttons.
- **Tasks:**
  - Design and implement a PySide6 window for history log.
  - Store transcriptions locally (e.g., JSON or SQLite).
  - Each entry shows timestamp, text, and a "Copy" button.
  - Ensure UI follows design guidelines (white base, black/grey accents, modern look).
- **Acceptance Criteria:**
  - User can open history window from tray.
  - All past transcriptions are listed with copy functionality.
- **Test Considerations:**
  - Unit test history storage/retrieval.
  - Manual test: UI usability and styling.

---

## General Acceptance Criteria
- All MVP features are implemented and tested.
- The app is stable, responsive, and has minimal idle resource usage.
- All code is documented and follows consistent style.
- API keys are never hard-coded.
- Error handling is present throughout.

---

## Out of Scope (Phase 2+)
- Persistent on-screen bar
- Real-time sound wave visualization
- Auto-paste into selected field in other apps

---

## Notes
- Prioritize accessibility and keyboard navigation in UI.
- Ensure all user-facing text is easy to read (contrast, font size).
- Prepare for future enhancements by keeping code modular. 