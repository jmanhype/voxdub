# Fish Speech (OpenAudio S1) Integration Guide

## Overview

VoxDub now supports **Fish Speech (OpenAudio S1)**, a state-of-the-art TTS system that delivers exceptional quality and advanced features.

### Key Features

- **SOTA Quality**: WER: 0.008, CER: 0.004
- **#1 on TTS-Arena2 Benchmark**
- **Voice Cloning**: Clone any voice from a 3-30 second audio sample
- **Emotion Synthesis**: 10+ emotion markers (angry, sad, excited, whispering, etc.)
- **Multilingual**: English, Chinese, Japanese
- **Streaming Support**: Real-time audio generation
- **Model Options**: S1 (full) and S1-mini (faster, 12GB VRAM)

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [API Endpoints](#api-endpoints)
4. [Usage Examples](#usage-examples)
5. [Voice Cloning](#voice-cloning)
6. [Emotion Synthesis](#emotion-synthesis)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- **GPU**: CUDA-compatible with 12GB+ VRAM (recommended)
- **Python**: 3.10+
- **Git**: For cloning repositories
- **CUDA Toolkit**: 11.8 or 12.1

### Automatic Installation

Use the provided setup script for easy installation:

```bash
cd scripts
chmod +x setup_fish_speech.sh
./setup_fish_speech.sh
```

The script will:
1. Check system requirements
2. Clone Fish Speech repository
3. Install dependencies
4. Download model weights (S1-mini or S1)
5. Create API configuration
6. Set up startup scripts

### Manual Installation

If you prefer manual installation:

```bash
# Clone Fish Speech
git clone https://github.com/fishaudio/fish-speech.git ~/fish-speech
cd ~/fish-speech

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Fish Speech
pip install -e .

# Download model weights
pip install -U "huggingface_hub[cli]"
huggingface-cli download fishaudio/fish-speech-1.4 \
    --local-dir checkpoints/fish-speech-1.4 \
    --include "model.pth" "config.json"
```

### Install VoxDub Dependencies

Update VoxDub backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

This includes the Fish Speech client libraries and dependencies.

---

## Configuration

### 1. Environment Variables

Edit your `.env` file in the VoxDub root directory:

```env
# TTS Provider Selection
TTS_PROVIDER=fish_speech  # Options: coqui, fish_speech

# Fish Speech Configuration
FISH_SPEECH_API_URL=http://localhost:8080
FISH_SPEECH_MODEL=s1-mini  # Options: s1, s1-mini
FISH_SPEECH_DEVICE=cuda    # Options: cuda, cpu
FISH_SPEECH_COMPILE=False  # Enable torch.compile for faster inference

# Inference Parameters
FISH_SPEECH_MAX_NEW_TOKENS=1024
FISH_SPEECH_TOP_P=0.7
FISH_SPEECH_TEMPERATURE=0.7
FISH_SPEECH_REPETITION_PENALTY=1.2
```

### 2. Start Fish Speech API Server

Before using Fish Speech in VoxDub, start the Fish Speech API server:

```bash
cd ~/fish-speech
./start_api.sh
```

The server will start on `http://localhost:8080` by default.

To run as a systemd service (optional):

```bash
sudo systemctl start fish-speech
sudo systemctl enable fish-speech  # Auto-start on boot
```

### 3. Verify Installation

Check that Fish Speech is working:

```bash
# Test Fish Speech API
curl http://localhost:8080/health

# Test VoxDub integration
curl http://localhost:8000/api/fish-speech/health
```

---

## API Endpoints

Fish Speech integration adds several new endpoints to VoxDub:

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fish-speech/info` | GET | Get Fish Speech provider info |
| `/api/fish-speech/health` | GET | Check Fish Speech API health |
| `/api/fish-speech/emotions` | GET | List available emotions |

### Voice Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fish-speech/voices/list` | GET | List registered voices |
| `/api/fish-speech/voices/add` | POST | Add reference voice |
| `/api/fish-speech/voices/{id}` | DELETE | Delete reference voice |

### Synthesis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fish-speech/synthesize` | POST | Generate speech with Fish Speech |
| `/api/fish-speech/clone-voice` | POST | Voice cloning in one step |
| `/api/fish-speech/download/{id}` | GET | Download synthesized audio |

---

## Usage Examples

### 1. Basic TTS (Using Main Dubbing Pipeline)

When Fish Speech is configured as the active provider, the main dubbing endpoint automatically uses it:

```bash
curl -X POST http://localhost:8000/api/dub \
  -F "video=@input.mp4" \
  -F "target_language=es"
```

### 2. Direct TTS with Emotion

```bash
curl -X POST http://localhost:8000/api/fish-speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! How are you doing today?",
    "language": "en",
    "emotion": "happy",
    "streaming": false
  }'
```

Response:
```json
{
  "success": true,
  "output_id": "abc123...",
  "file_path": "temp/abc123_synthesized.wav",
  "file_size_kb": 156.32,
  "text_length": 32,
  "language": "en",
  "emotion": "happy",
  "download_url": "/api/fish-speech/download/abc123"
}
```

### 3. Available Emotions

```bash
curl http://localhost:8000/api/fish-speech/emotions
```

Response:
```json
{
  "emotions": [
    "neutral", "happy", "sad", "angry",
    "fearful", "disgusted", "surprised",
    "excited", "whispering", "shouting"
  ],
  "usage": "Add emotion parameter to TTS requests",
  "example": {
    "text": "Hello, how are you?",
    "emotion": "happy"
  }
}
```

---

## Voice Cloning

Fish Speech supports voice cloning from reference audio samples.

### Register a Reference Voice

Upload a reference audio file (3-30 seconds, clear speech):

```bash
curl -X POST http://localhost:8000/api/fish-speech/voices/add \
  -F "voice_id=morgan_freeman" \
  -F "audio=@reference_audio.wav" \
  -F "text=This is the transcript of the reference audio"
```

### Use Registered Voice

```bash
curl -X POST http://localhost:8000/api/fish-speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "New text to synthesize with cloned voice",
    "language": "en",
    "voice_id": "morgan_freeman"
  }'
```

### One-Shot Voice Cloning

Clone a voice without registration (for one-time use):

```bash
curl -X POST http://localhost:8000/api/fish-speech/clone-voice \
  -F "text=Welcome to VoxDub with Fish Speech!" \
  -F "language=en" \
  -F "audio=@reference.wav" \
  -F "reference_text=Original audio transcript" \
  -F "emotion=excited"
```

### List Registered Voices

```bash
curl http://localhost:8000/api/fish-speech/voices/list
```

### Delete a Voice

```bash
curl -X DELETE http://localhost:8000/api/fish-speech/voices/morgan_freeman
```

---

## Emotion Synthesis

Fish Speech supports emotion markers that can be embedded in text or specified as parameters.

### Method 1: Parameter-Based

```bash
curl -X POST http://localhost:8000/api/fish-speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I am so excited to announce this!",
    "language": "en",
    "emotion": "excited"
  }'
```

### Method 2: Inline Markers

Emotions are automatically formatted by the API, but you can also use them in text:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/fish-speech/synthesize",
    json={
        "text": "This is amazing! I can't believe it!",
        "language": "en",
        "emotion": "surprised"
    }
)

# The text will be formatted as: [surprised]This is amazing![/surprised]
```

### Supported Emotions

| Emotion | Use Case |
|---------|----------|
| `neutral` | Default, natural speech |
| `happy` | Joyful, positive content |
| `sad` | Melancholic, somber content |
| `angry` | Intense, frustrated speech |
| `fearful` | Anxious, worried tone |
| `disgusted` | Repulsed, negative reaction |
| `surprised` | Shocked, amazed response |
| `excited` | Energetic, enthusiastic |
| `whispering` | Quiet, confidential |
| `shouting` | Loud, emphatic |

---

## Troubleshooting

### Fish Speech API Not Accessible

**Error**: `Fish Speech API not available at http://localhost:8080`

**Solution**:
1. Ensure Fish Speech server is running:
   ```bash
   cd ~/fish-speech
   ./start_api.sh
   ```
2. Check server status:
   ```bash
   curl http://localhost:8080/health
   ```
3. Check logs for errors

### Out of Memory (OOM) Errors

**Error**: CUDA out of memory

**Solution**:
1. Use S1-mini instead of S1:
   ```env
   FISH_SPEECH_MODEL=s1-mini
   ```
2. Reduce batch size or max_new_tokens:
   ```env
   FISH_SPEECH_MAX_NEW_TOKENS=512
   ```
3. Enable compilation for better memory usage:
   ```env
   FISH_SPEECH_COMPILE=True
   ```

### Poor Voice Cloning Quality

**Issue**: Cloned voice doesn't sound like reference

**Solution**:
1. Use high-quality reference audio (16kHz+, clear speech)
2. Provide 10-30 seconds of reference audio
3. Include the transcript for better results:
   ```bash
   -F "reference_text=Exact transcript of reference audio"
   ```
4. Ensure reference audio has minimal background noise

### Slow Inference

**Issue**: TTS generation is slow

**Solution**:
1. Enable torch.compile:
   ```env
   FISH_SPEECH_COMPILE=True
   ```
2. Use S1-mini model:
   ```env
   FISH_SPEECH_MODEL=s1-mini
   ```
3. Ensure GPU is being used:
   ```bash
   nvidia-smi  # Should show Fish Speech process
   ```

### Provider Not Active

**Error**: "Fish Speech provider not active"

**Solution**:
Set the TTS provider in `.env`:
```env
TTS_PROVIDER=fish_speech
```

Restart VoxDub backend:
```bash
cd backend
python app.py
```

---

## Python SDK Examples

### Basic Usage

```python
from models.voice_synthesis import get_synthesizer

# Initialize Fish Speech provider
synthesizer = get_synthesizer(provider="fish_speech")

# Generate speech
synthesizer.synthesize(
    text="Hello from Fish Speech!",
    output_path="output.wav",
    language="en",
    emotion="happy"
)
```

### Voice Cloning

```python
# Add reference voice
synthesizer.add_reference_voice(
    voice_id="custom_voice",
    audio_path="reference.wav",
    text="Reference transcript"
)

# Use cloned voice
synthesizer.synthesize(
    text="New speech with cloned voice",
    output_path="cloned_output.wav",
    speaker="custom_voice"
)
```

### One-Shot Cloning

```python
synthesizer.synthesize(
    text="Hello world!",
    output_path="output.wav",
    reference_audio="reference.wav",
    reference_text="Original transcript",
    emotion="excited"
)
```

---

## Performance Comparison

| Feature | Coqui TTS | Fish Speech |
|---------|-----------|-------------|
| Quality (WER) | ~0.05 | **0.008** |
| Voice Cloning | Limited | ✅ Advanced |
| Emotions | ❌ | ✅ 10+ emotions |
| Languages | 5 | 3 (en, zh, ja) |
| Speed | Medium | Fast |
| VRAM Required | 4-6GB | 12GB (S1-mini) |

---

## Additional Resources

- **Fish Speech GitHub**: https://github.com/fishaudio/fish-speech
- **Model Weights**: https://huggingface.co/fishaudio/fish-speech-1.4
- **TTS-Arena2**: https://github.com/TTS-Arena/TTS-Arena
- **VoxDub API Docs**: http://localhost:8000/docs

---

## Support

For issues with Fish Speech integration:
1. Check Fish Speech logs: `~/fish-speech/logs/`
2. Verify VoxDub health: `GET /api/health`
3. Test Fish Speech API: `GET /api/fish-speech/health`
4. Review this documentation

For Fish Speech specific issues, visit the [Fish Speech repository](https://github.com/fishaudio/fish-speech/issues).
