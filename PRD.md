# Product Requirements Document (PRD): MyScribe

## 1. Document Overview
- **Product Name:** MyScribe
- **Version:** 1.0
- **Owner:** Luke Callow
- **Date:** 16/07/2025
- **Status:** Draft
- **Related MVP:** Personal AI Dictation Desktop Tool

## 2. Executive Summary & Project Goals
- **Objective:** MyScribe is a personal desktop application designed for seamless, low-friction thought capture. It uses global hotkeys to trigger AI-powered voice dictation from within any application on the user's computer. The goal is to eliminate the context-switching required by traditional note-taking, creating an instant pipeline from spoken thought to clean, formatted digital text.
- **Primary User:** The developer (you) for personal productivity and content creation.
- **Project Goals:**
  - To create a highly efficient, personal tool that integrates smoothly into daily computer workflows.
  - To develop practical skills in Python, desktop application development, and the use of modern AI APIs.
  - To build a final product that is stable, responsive, and has a minimal system resource footprint.

## 3. Problem Statement (Project Rationale)
- **Core Problem:** Capturing fleeting thoughts or notes while working involves multiple steps of friction: stopping the current task, opening a note-taking app, typing the note, and returning to the original task. This context-switching can break concentration and lead to lost ideas.
- **Why Solve It:** By creating a tool that works globally, from anywhere in the OS, this friction can be almost entirely eliminated. It allows for a more natural and fluid way of working, capturing ideas at the moment of inspiration without disrupting workflow.

## 4. Proposed Solution
- **Overview:** MyScribe will run as a background application on a Windows PC. The user can press a global hotkey combination (Alt+Ctrl) to instantly start recording audio. A visual indicator will appear at the bottom of the screen. 
Pressing the hotkey again stops the recording, sends the audio for AI processing (transcription and cleaning), and then automatically populates the resulting clean text into the currently selected text field. All transcriptions are also saved within the application's history log for later review and retrieval.
- **Product Scope:**
  - **Included Features (Phase 1 - MVP):**
    - Background application that listens for global hotkeys (Alt+Ctrl for start/stop, Alt+Ctrl+Space for continue/stop).
    - Core AI processing chain: Sends audio to a Speech-to-Text API, then sends the raw text to an LLM API for cleaning.
    - Primary Output: The final, clean text is automatically copied to the clipboard.
    - Visual Feedback: A simple icon in the system tray indicates the app's status (e.g., Idle, Recording, Processing).
    - History: A basic GUI window that lists all past transcriptions, with a "Copy" button for each entry.
  - **Excluded Features (Reserved for Phase 2 - Enhancements):**
    - The persistent, interactive bar at the bottom of the screen.
    - The real-time sound wave visualization.
    - The advanced functionality to automatically paste/populate text into a selected field in another application.
- **Value Proposition:** To provide an "always-on" personal scribe that makes capturing thoughts as easy as speaking, dramatically boosting productivity and reducing mental overhead.

## 5. AI-Specific Considerations
- **Guardrails and Parameters:**
  - The tool is for personal productivity; it should not be used to dictate highly sensitive information like passwords or private keys, as the data is sent to third-party APIs.
  - The AI must not be prompted to create harmful or illegal content.
- **Prompt & Context Design:**
  - The prompt sent to the LLM (e.g., Gemini) will be clearly defined: "Review the following raw transcript. Remove all filler words (like 'um', 'ah', 'err', 'you know'). Correct grammar and punctuation. Format the final output into clean paragraphs. If the user outlines a list, format it with bullet points. Do not add any commentary or text that was not in the original transcript."
- **Explainability & Traceability:**
  - For this personal tool, deep explainability is not required. The history log provides a clear record of the final outputs.
- **Known AI Limitations & Mitigations:**
  - **Risk:** The STT API may inaccurately transcribe words, especially proper nouns or technical jargon.
  - **Mitigation:** There is no mitigation in the MVP beyond choosing a high-quality API. The user will have to manually correct any errors in the final text.

## 6. Functional Requirements
- **User Stories (for the MVP):**
  - As the user, I want to press Alt+Ctrl at any time to start a voice recording so that I can capture my thoughts instantly.
  - As the user, I want to press Alt+Ctrl again to stop the recording so that I have full control over the duration.
  - As the user, when I stop a recording, I want the clean text to be automatically copied to my clipboard so that I can immediately paste it into my document, email, or IDE.
  - As the user, I want to see a history of all my past transcriptions in a simple window so that I can find and reuse a previous thought.
  - As the user, I want a simple icon in my system tray to change colour so that I have clear visual confirmation of the application's current state (idle, recording, or processing).

## 7. Non-Functional Requirements
- **Performance:** Hotkey detection must be near-instant (<200ms). The end-to-end processing time (from stop-record to text-on-clipboard) should ideally be under 10 seconds for a 1-minute recording.
- **Security:** API keys must be stored securely in a configuration file or environment variable, not hard-coded in the script.
- **Resource Usage:** As a background app, it must have very low CPU and RAM usage when idle.

## 8. Integrations & Data Sources
- **External APIs:**
  - A Speech-to-Text API (e.g., AssemblyAI, Deepgram).
  - An LLM API (e.g., Google's Gemini API).
- **Internal Sources:** The computer's default microphone input.

## 9. UI/UX Requirements
- **Phase 1 (MVP):**
  - A single system tray icon with at least 3 states (e.g., Grey mic for Idle, Red mic for Recording, Blue cog for Processing).
  - A simple window for the history log, showing a list of timestamped transcriptions. Each item in the list will have a "Copy" button next to it.
- **Phase 2 (Full Vision):**
  - A persistent, slim bar docked at the bottom of the screen.
  - On hotkey press, the bar expands to show a real-time sound wave visualization.

## 10. Design & Styling Guidelines
- **Base Color:** White
- **Accent Colors:** Black and grey
- **Style:** Modern, clean, and stylish
- **UI Elements:**
  - Use flat design principles with subtle shadows for depth.
  - Rounded corners for windows and buttons.
  - Clear, legible sans-serif fonts (e.g., Segoe UI, Arial, or Roboto).
  - Minimalist icons for system tray and buttons.
  - Consistent spacing and padding for a balanced look.
  - Responsive layouts for different DPI settings.

## 11. Success Metrics & KPIs (Project Success Criteria)
- The application reliably captures and transcribes audio with an accuracy level sufficient for personal use.
- The hotkey system works globally without interfering with other applications (e.g., video games, IDEs).
- The end-to-end workflow is faster and feels more fluid than manually opening a text editor to type a note.
- The project serves as a successful learning experience in Python and AI development.

## 12. Roadmap & Milestones
- **Phase 1: MVP Build (Target: 2-4 weeks)**
  - Milestone 1: Core hotkey listener and audio recorder work from the command line.
  - Milestone 2: AI processing chain is integrated. Script can take a local audio file and produce clean text.
  - Milestone 3: Basic system tray application is built, and logic is integrated. Clipboard copy is implemented.
  - Milestone 4: History viewer window is created and functional.
- **Phase 2: Advanced UI/UX (Post-MVP)**
  - Milestone 5: Research and develop the persistent on-screen bar UI.
  - Milestone 6: Implement the real-time sound wave visualization.
  - Milestone 7: Research and implement the "populate selected field" functionality.

## 13. Risks & Mitigations
- **Risk:** The technical complexity of the Phase 2 features (live UI bar, OS integration) is significantly higher than the MVP.
  - **Mitigation:** Adhere strictly to the phased roadmap. Ensure a stable and useful MVP is complete before beginning work on Phase 2.
- **Risk:** API costs could become a factor if usage is higher than the free tiers allow.
  - **Mitigation:** Implement logging to track API usage. Choose services with clear pricing and generous free tiers.
- **Risk:** Global hotkeys might conflict with shortcuts in other specific applications.
  - **Mitigation:** The hotkey combination can be made configurable in a simple settings file.

## 14. Glossary / Key Terms
- **Global Hotkey:** A keyboard shortcut that can be detected by an application even when it is not in focus.
- **STT (Speech-to-Text):** The process of converting spoken audio into written text.
- **LLM (Large Language Model):** An advanced AI that can understand and generate human-like text (used here for cleaning and formatting). 