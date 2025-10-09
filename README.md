<div align="center">

# 🎬 VoxDub - AI Video Dubbing System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Professional AI-powered video dubbing with automatic translation and lip synchronization**

Transform videos into any language with natural voice synthesis and perfect lip-sync using state-of-the-art AI models.

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture)

</div>

---

## ✨ Features

- 🎙️ **Automatic Speech Recognition** - Powered by OpenAI Whisper (99 languages)
- 🌍 **Neural Machine Translation** - Meta NLLB-200 (200+ languages)
- 🗣️ **Natural Voice Synthesis** - High-quality Coqui TTS
- 💋 **Lip Synchronization** - Realistic Wav2Lip GAN
- 📊 **Real-time Progress Tracking** - Live processing status updates
- 🎨 **Professional UI/UX** - Clean, modern, responsive interface
- ⚡ **Async Processing** - Fast, non-blocking architecture
- 🔒 **Secure** - Files automatically deleted after 24 hours

---

## 🎯 Demo

### How It Works

Input Video (English) → VoxDub AI Pipeline → Output Video (Spanish + Lip Sync)

1. **Upload** a video in any language
2. **Select** target language from 200+ options
3. **Process** with AI (3-5 minutes)
4. **Download** professionally dubbed video

**Supported Formats:** MP4, AVI, MOV, MKV  
**Max File Size:** 500 MB  
**Processing Time:** 2-5 minutes (depending on video length)

---

## 🏗️ Architecture

┌─────────────────────────────────────────────────────┐
│ React Frontend (Vite) │
│ Modern UI with Real-time Progress Tracking │
└─────────────────┬───────────────────────────────────┘
│ REST API (HTTP/JSON)
┌─────────────────▼───────────────────────────────────┐
│ FastAPI Backend (Python) │
│ Asynchronous AI Processing Pipeline │
└─────────────────┬───────────────────────────────────┘
│
┌─────────────┼─────────────┬──────────────┐
▼ ▼ ▼ ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Whisper │ │ NLLB │ │Coqui TTS │ │ Wav2Lip │
│ AI │ │Translation│ │ Voices │ │ Lip-Sync │
└─────────┘ └──────────┘ └──────────┘ └──────────────┘



### Processing Pipeline

Audio Extraction (FFmpeg)
↓

Speech Recognition (Whisper) → Text + Language
↓

Translation (NLLB) → Translated Text
↓

Voice Synthesis (TTS) → New Audio
↓

Lip Synchronization (Wav2Lip) → Final Video
↓

Output Encoding (FFmpeg) → Download Ready


---

## 🚀 Installation

### Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **FFmpeg** ([Download](https://ffmpeg.org/download.html))
- **8GB RAM** minimum (16GB recommended)
- **10GB disk space** (for AI models)

### Step 1: Clone Repository

git clone https://github.com/pranavpanchal1326/voxdub.git
cd voxdub


### Step 2: Backend Setup

cd backend

Create virtual environment
python -m venv venv

Activate virtual environment
Windows:
venv\Scripts\activate

Linux/Mac:
source venv/bin/activate

Upgrade pip
python -m pip install --upgrade pip

Install dependencies (this takes 10-15 minutes)
pip install -r requirements.txt


### Step 3: Download AI Models

**Wav2Lip Model (Required):**

Download from official repository
https://github.com/Rudrabha/Wav2Lip
Place checkpoint in:
backend/Wav2Lip/checkpoints/wav2lip_gan.pth
text

**Other models auto-download on first run:**
- Whisper (~140MB)
- NLLB (~2.5GB)
- Coqui TTS (~200MB)

**First run takes 5-10 minutes to load models.**

### Step 4: Frontend Setup

cd ../frontend

Install dependencies
npm install

Build for production (optional)
npm run build

text

### Step 5: Configure FFmpeg

**Windows:**
Download FFmpeg from: https://ffmpeg.org/download.html
Add to PATH or place in project folder
text

**Linux:**
sudo apt update
sudo apt install ffmpeg

text

**Mac:**
brew install ffmpeg

text

**Verify installation:**
ffmpeg -version

text

---

## 🎮 Usage

### Running the Application

Open **two terminals**:

**Terminal 1 - Backend:**
cd backend
venv\Scripts\activate # Windows

source venv/bin/activate # Linux/Mac
python app.py

text

**Terminal 2 - Frontend:**
cd frontend
npm run dev

text

**Open in browser:** http://localhost:5173

### Using the Application

1. **Upload Video**
   - Click upload area or drag & drop
   - Supported: MP4, AVI, MOV, MKV
   - Max size: 500MB

2. **Select Target Language**
   - Choose from 200+ languages
   - Auto-detects source language

3. **Start Processing**
   - Watch real-time progress
   - 5 processing stages displayed

4. **Download Result**
   - Video with dubbed audio
   - Lip movements synchronized
   - Same quality as original

---

## 🧠 AI Models

| Model | Purpose | Size | Provider | Accuracy |
|-------|---------|------|----------|----------|
| **Whisper Base** | Speech→Text | 140MB | OpenAI | 95%+ |
| **NLLB-200** | Translation | 2.5GB | Meta AI | 90%+ |
| **Coqui TTS** | Text→Speech | 200MB | Coqui | 90%+ |
| **Wav2Lip GAN** | Lip Sync | 350MB | IISc | 95%+ |

**Total Model Size:** ~3.2GB  
**Supported Languages:** 200+  
**Processing Speed:** 2-5 minutes per video

---

## 📂 Project Structure

voxdub/
├── backend/ # Python FastAPI backend
│ ├── app.py # Main FastAPI application
│ ├── requirements.txt # Python dependencies
│ │
│ ├── models/ # AI model integrations
│ │ ├── init.py
│ │ ├── transcription.py # Whisper wrapper
│ │ ├── translation.py # NLLB wrapper
│ │ ├── voice_synthesis.py # TTS wrapper
│ │ └── lipsync.py # Wav2Lip wrapper
│ │
│ ├── utils/ # Utility modules
│ │ ├── init.py
│ │ ├── video_processor.py # FFmpeg operations
│ │ └── file_handler.py # File management
│ │
│ ├── Wav2Lip/ # Wav2Lip repository
│ │ ├── models/
│ │ ├── checkpoints/ # Model weights (download)
│ │ └── inference.py
│ │
│ └── venv/ # Virtual environment
│
├── frontend/ # React frontend
│ ├── src/
│ │ ├── main.jsx # React entry
│ │ ├── App.jsx # Main component
│ │ ├── App.css # App styles
│ │ ├── index.css # Global styles
│ │ │
│ │ └── components/ # React components
│ │ ├── VideoUpload.jsx
│ │ ├── VideoUpload.css
│ │ ├── LanguageSelector.jsx
│ │ ├── LanguageSelector.css
│ │ ├── ProcessingStatus.jsx
│ │ ├── ProcessingStatus.css
│ │ ├── ResultPreview.jsx
│ │ └── ResultPreview.css
│ │
│ ├── public/ # Static assets
│ ├── index.html # HTML template
│ ├── package.json # npm dependencies
│ └── vite.config.js # Vite config
│
├── uploads/ # User uploaded videos (auto-created)
├── outputs/ # Processed videos (auto-created)
├── temp/ # Temporary files (auto-created)
│
├── .gitignore # Git ignore rules
├── README.md # This file
└── LICENSE # MIT License

text

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Uvicorn** - ASGI server
- **PyTorch** - Deep learning framework
- **Transformers** - Hugging Face model hub
- **OpenCV** - Computer vision library
- **Librosa** - Audio processing
- **FFmpeg** - Video/audio manipulation

### Frontend
- **React 18** - UI library
- **Vite** - Next-generation build tool
- **Axios** - HTTP client
- **Modern CSS** - Professional styling

### AI/ML
- **OpenAI Whisper** - Speech recognition
- **Meta NLLB** - Neural translation
- **Coqui TTS** - Text-to-speech
- **Wav2Lip** - Lip synchronization

---

## ⚙️ Configuration

### Environment Variables (Optional)

Create `.env` in `backend/` folder:

Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

Model Configuration
WHISPER_MODEL=base
NLLB_MODEL=facebook/nllb-200-distilled-600M
TTS_MODEL=tts_models/multilingual/multi-dataset/your_tts

File Limits
MAX_FILE_SIZE_MB=500
ALLOWED_FORMATS=mp4,avi,mov,mkv
AUTO_DELETE_HOURS=24

Processing
USE_GPU=True
MAX_WORKERS=2

text

---

## 📊 API Documentation

Once backend is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

POST /api/dub - Upload video and start dubbing
GET /api/status/{job_id} - Check processing status
GET /api/download/{job_id} - Download processed video
GET /api/languages - Get supported languages
GET /api/health - Health check

text

---

## 🎬 Example Use Cases

- **Content Localization** - YouTubers dubbing videos for global audience
- **E-Learning** - Educational content translation
- **Marketing** - Multilingual advertising campaigns
- **Entertainment** - Indie film dubbing
- **Accessibility** - Making content accessible worldwide
- **Business** - International training videos

---

## 🚧 Troubleshooting

### Common Issues

**1. "FFmpeg not found"**
Verify FFmpeg is in PATH
ffmpeg -version

If not, add to PATH or install
text

**2. "Module not found" errors**
Reinstall dependencies
pip install -r requirements.txt



**3. "Out of memory" during processing**
Use smaller Whisper model in config
WHISPER_MODEL=tiny # Instead of 'base'

Or process shorter videos


**4. "Port 8000 already in use"**
Kill process using port
Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

Linux/Mac:
lsof -ti:8000 | xargs kill -9



**5. Slow processing**
- First run downloads models (10 mins)
- Subsequent runs are faster (2-5 mins)
- GPU significantly speeds up processing

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - Whisper speech recognition model
- **Meta AI** - NLLB translation model
- **Coqui AI** - Text-to-speech system
- **IISc Bangalore** - Wav2Lip lip synchronization
- **FFmpeg** - Video/audio processing
- **Hugging Face** - Model hosting and transformers library

---

## 📧 Contact

**Pranav Panchal** - [GitHub](https://github.com/YOUR_USERNAME)

Project Link: [https://github.com/YOUR_USERNAME/voxdub](https://github.com/YOUR_USERNAME/voxdub)

---

## ⭐ Show Your Support

If you find this project helpful, please give it a ⭐ on GitHub!

---

<div align="center">

**Built with ❤️ using AI and modern web technologies**

</div>