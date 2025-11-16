# Fish Speech TTS - Quick Start Guide

Get up and running with Fish Speech TTS in VoxDub in under 10 minutes!

## Prerequisites

- VoxDub already installed and working
- NVIDIA GPU with 12GB+ VRAM
- CUDA 11.8 or 12.1 installed

## Installation (5 minutes)

### Step 1: Run Setup Script

```bash
cd scripts
chmod +x setup_fish_speech.sh
./setup_fish_speech.sh
```

Follow the prompts. The script will:
- Install Fish Speech
- Download model weights (~2.8GB)
- Create configuration files
- Set up startup scripts

### Step 2: Start Fish Speech Server

```bash
cd ~/fish-speech
./start_api.sh
```

Wait for the message: `Server started on http://0.0.0.0:8080`

### Step 3: Configure VoxDub

Edit your `.env` file:

```env
TTS_PROVIDER=fish_speech
```

### Step 4: Restart VoxDub

```bash
cd backend
python app.py
```

You should see: `🐟 Fish Speech TTS Active`

## Verify Installation

```bash
# Test Fish Speech API
curl http://localhost:8080/health

# Test VoxDub integration
curl http://localhost:8000/api/fish-speech/info
```

## Basic Usage

### 1. Standard Dubbing (with Fish Speech)

Use the web interface as normal - Fish Speech is now active!

### 2. Generate Speech with Emotion

```bash
curl -X POST http://localhost:8000/api/fish-speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is amazing!",
    "language": "en",
    "emotion": "excited"
  }'
```

### 3. Voice Cloning

```bash
# Upload reference voice
curl -X POST http://localhost:8000/api/fish-speech/voices/add \
  -F "voice_id=my_voice" \
  -F "audio=@my_voice_sample.wav"

# Use it
curl -X POST http://localhost:8000/api/fish-speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "language": "en",
    "voice_id": "my_voice"
  }'
```

## Available Emotions

- `happy` - Joyful speech
- `sad` - Melancholic tone
- `angry` - Intense emotion
- `excited` - Energetic delivery
- `whispering` - Quiet, soft
- `shouting` - Loud, emphatic
- `surprised` - Shocked reaction
- `fearful` - Anxious tone
- `disgusted` - Negative reaction
- `neutral` - Natural speech

## Next Steps

- Read the [full integration guide](FISH_SPEECH_INTEGRATION.md)
- Explore the API at `http://localhost:8000/docs`
- Try different emotions and voice cloning
- Adjust inference parameters in `.env`

## Troubleshooting

**Server won't start?**
- Check CUDA: `nvidia-smi`
- Check logs: `~/fish-speech/logs/`

**Out of memory?**
- Use S1-mini (default): `FISH_SPEECH_MODEL=s1-mini`

**Poor quality?**
- Adjust temperature: `FISH_SPEECH_TEMPERATURE=0.5`
- Increase tokens: `FISH_SPEECH_MAX_NEW_TOKENS=2048`

## Support

- [Full Documentation](FISH_SPEECH_INTEGRATION.md)
- [Fish Speech GitHub](https://github.com/fishaudio/fish-speech)
- [VoxDub Issues](https://github.com/pranavpanchal1326/voxdub/issues)
