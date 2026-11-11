# 🕷️ VENOM AI ASSISTANT

> *"We are Venom."* — An intelligent symbiotic AI assistant powered by Gemini & local LLMs with real-time voice activation.

A personal AI assistant inspired by [OpenJarvis](https://github.com/open-jarvis/OpenJarvis) with a Marvel Venom symbiote aesthetic.

---

## 🚀 Key Features

- 🖤 **Venom Symbiote UI**: Interactive dark symbiote aesthetic with animated tendrils and responsive frequency bars.
- 🎙️ **Voice Wake & Hands-Free Calling**:
  - Call **"Venom"** or **"Hey Venom"** to wake the assistant hands-free.
  - Dedicated **CALL "VENOM"** live audio session mode for continuous voice conversation.
  - Push-to-talk dictation microphone in the input bar.
  - Synthetic Web Audio chime sound feedback upon awakening.
- 🗣️ **ElevenLabs Voice Integration**:
  - Native vocalization using Venom Voice ID `cgSgspJ2msm6clMCkdW9`.
  - Client-side deep guttural symbiote voice synthesis fallback.
- 🧠 **Multi-Engine Intelligence**:
  - **Google AI Studio (Gemini)**: Fast streaming inference (`gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`).
  - **Local Ollama**: Offline private models (`llama3.2`, `mistral`, `deepseek-r1`).
  - **OpenAI Compatible**: Connect to any OpenAI-compatible endpoint.
- ⚡ **Full-Duplex Streaming**: Server-Sent Events (SSE) and WebSocket support (`/ws/chat`).
- 🌐 **Cloud-Ready**: 1-click deployments for Vercel, Netlify, Render, and Railway.

---

## 🏗️ Architecture

```
venom/
├── backend/          # FastAPI server (OpenAI & Gemini API)
│   ├── core/         # EventBus, config, logging
│   ├── engine/       # Gemini, Ollama, OpenAI inference engines
│   ├── agent/        # Venom persona & orchestration logic
│   ├── memory/       # Conversation memory
│   ├── audio/        # ElevenLabs TTS engine
│   └── api/          # REST endpoints & WebSockets
├── frontend/         # React + TypeScript + Vite Venom UI
│   ├── src/
│   │   ├── components/  # Voice overlay, chat window, symbiote canvas
│   │   ├── hooks/       # useVoiceWake, useWebSocket
│   │   ├── store/       # Zustand state management
│   │   └── utils/       # Synthetic Web Audio FX
├── render.yaml       # 1-Click Render backend blueprint
├── vercel.json       # Vercel frontend deployment config
└── netlify.toml      # Netlify frontend deployment config
```

---

## ⚡ Quick Start (Local)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment & install dependencies
pip install -r requirements.txt

# Configure your keys in .env
cp .env.example .env
# Edit .env and paste your Google Gemini or ElevenLabs API key

# Start Venom server
python main.py serve
```

### 2. Frontend Setup

```bash
cd frontend

# Install packages
npm install

# Start Vite dev server
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## 🎙️ Voice Wake & Calling Instructions

1. Click **CALL "VENOM"** in the top navigation bar (or click the microphone icon in the chat input).
2. Allow microphone access when prompted.
3. Simply speak:
   - *"Venom, who are you?"*
   - *"Hey Venom, tell me our mission today."*
   - Or just say *"Venom!"* to wake the symbiote and hear its response.
4. Venom will transcribe your voice, generate the answer, and speak it aloud.
5. In **CALL: ACTIVE** mode, Venom automatically resumes listening after each response for a continuous hands-free dialogue.

---

## 🌐 Cloud Hosting Guide

### Frontend on Vercel
1. Import your GitHub repository into [Vercel](https://vercel.com).
2. The included `vercel.json` will automatically configure build and output directories.
3. Add environment variable:
   - `VITE_API_BASE_URL`: URL of your hosted backend (e.g. `https://venom-backend.onrender.com`).
4. Click **Deploy**.

### Backend on Render (Free)
1. Push this project to your GitHub account.
2. In [Render](https://render.com), click **New +** -> **Blueprint**.
3. Select your repository. Render will automatically detect `render.yaml`.
4. Fill in `VENOM_GEMINI_API_KEY` and `VENOM_ELEVENLABS_API_KEY`.
5. Click **Apply** to deploy.

---

## ⚙️ Environment Variables (`backend/.env`)

```env
# AI Engine: "gemini" or "ollama"
VENOM_ENGINE=gemini
VENOM_MODEL=gemini-1.5-flash
VENOM_GEMINI_API_KEY=your_gemini_key_here

# ElevenLabs Voice (Optional)
VENOM_ELEVENLABS_API_KEY=your_elevenlabs_key_here
VENOM_ELEVENLABS_VOICE_ID=cgSgspJ2msm6clMCkdW9
VENOM_ELEVENLABS_MODEL_ID=eleven_multilingual_v2

# Server Port
PORT=7777
```
