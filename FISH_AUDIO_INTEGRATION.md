# 🐟 Fish Audio TTS Integration Guide

## Overview

VoxDub now supports **Fish Audio** as an alternative TTS provider alongside Coqui TTS. Fish Audio offers high-quality, cloud-based text-to-speech with advanced voice cloning capabilities and support for 200+ languages.

---

## Features

✅ **Cloud-Based Processing** - No local GPU required
✅ **High-Quality Voices** - Professional, natural-sounding speech
✅ **Voice Cloning** - Clone voices from reference audio
✅ **Multi-Language Support** - 200+ languages supported
✅ **Fast Processing** - Optimized cloud infrastructure
✅ **Auto-Fallback** - Seamlessly falls back to Coqui TTS if unavailable

---

## Installation

### 1. Install Fish Audio SDK

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fish-audio-sdk
```

### 2. Get Your API Key

1. Visit [Fish Audio API Keys](https://fish.audio/app/api-keys)
2. Sign up or log in to your account
3. Generate a new API key
4. Copy the key securely

### 3. Configure Environment

Create/edit `.env` file in the `backend/` directory:

```bash
# Fish Audio TTS Configuration
FISH_API_KEY=your-fish-audio-api-key-here
TTS_PROVIDER=auto  # Options: auto, fish_audio, coqui
```

**Provider Options:**
- `auto` - Automatically selects Fish Audio if API key is set, otherwise uses Coqui
- `fish_audio` - Force use of Fish Audio (requires API key)
- `coqui` - Force use of Coqui TTS (local processing)

---

## Usage

### Basic Usage (Automatic Provider Selection)

The system will automatically detect and use Fish Audio if the API key is configured:

```bash
# Start backend with Fish Audio enabled
cd backend
export FISH_API_KEY=your-api-key-here
python app.py
```

### API Endpoints

#### 1. Check Available Providers

```bash
GET /api/tts/providers
```

**Response:**
```json
{
  "providers": {
    "fish_audio": {
      "name": "Fish Audio",
      "features": ["voice_cloning", "multi_language", "cloud_based", "high_quality"],
      "requires_api_key": true,
      "available": true
    },
    "coqui": {
      "name": "Coqui TTS",
      "features": ["multi_language", "local_processing", "offline"],
      "requires_api_key": false,
      "available": true
    }
  },
  "current": {
    "provider": "fish_audio",
    "features": ["voice_cloning", "multi_language", "cloud_based"],
    "account": {
      "provider": "fish_audio",
      "credits": 1000,
      "status": "active"
    }
  }
}
```

#### 2. Process Video with Specific Provider

```bash
POST /api/dub
Content-Type: multipart/form-data

video: [video file]
target_language: es
tts_provider: fish_audio
```

**Response:**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Video uploaded successfully. Processing started.",
  "status_url": "/api/status/550e8400-e29b-41d4-a716-446655440000",
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000",
  "tts_provider": "fish_audio"
}
```

---

## Programming Examples

### Python - Direct Usage

```python
from models.voice_synthesis import synthesize_speech, get_synthesizer
import os

# Option 1: Set default via environment variable (before server starts)
os.environ["TTS_PROVIDER"] = "fish_audio"

# Option 2: Specify per-request (recommended)
synthesize_speech(
    "Hello world",
    "output.wav",
    language="en",
    provider="fish_audio",
    speed=1.2,  # Fish Audio specific: speech speed
    volume=5    # Fish Audio specific: volume in dB
)

# Option 3: Use synthesizer directly
from models.voice_synthesis import FishAudioSynthesizer

fish_tts = FishAudioSynthesizer(api_key="your-api-key")
fish_tts.synthesize(
    text="Hola mundo",
    output_path="spanish.wav",
    language="es",
    speed=1.0,
    volume=0,
    audio_format="wav"
)

# Check account info
account = fish_tts.get_account_info()
print(f"Credits remaining: {account['credits']}")
```

### JavaScript - Frontend Integration

```javascript
// Check available providers
const response = await fetch('http://localhost:8000/api/tts/providers');
const data = await response.json();
console.log('Available providers:', data.providers);
console.log('Current provider:', data.current.provider);

// Submit video with specific provider (per-request override)
const formData = new FormData();
formData.append('video', videoFile);
formData.append('target_language', 'es');
formData.append('tts_provider', 'fish_audio');

const result = await fetch('http://localhost:8000/api/dub', {
  method: 'POST',
  body: formData
});
```

---

## Advanced Features

### Voice Cloning (Fish Audio Only)

Fish Audio supports voice cloning using reference audio:

```python
from models.voice_synthesis import FishAudioSynthesizer

fish_tts = FishAudioSynthesizer(api_key="your-api-key")

# Use a reference voice ID
fish_tts.synthesize(
    text="This will sound like the reference voice",
    output_path="cloned_voice.wav",
    language="en",
    reference_id="voice-reference-id-from-fish-audio"
)
```

To create custom voices:
1. Visit [Fish Audio Dashboard](https://fish.audio/app)
2. Upload reference audio samples
3. Generate voice reference ID
4. Use the ID in your API calls

### Speed and Volume Control

```python
# Faster speech
synthesize_speech(
    "Quick announcement",
    "fast.wav",
    language="en",
    provider="fish_audio",
    speed=1.5  # 1.5x faster
)

# Louder output
synthesize_speech(
    "Important message",
    "loud.wav",
    language="en",
    provider="fish_audio",
    volume=10  # +10dB
)
```

---

## Performance Comparison

| Feature | Fish Audio | Coqui TTS |
|---------|-----------|-----------|
| **Processing Location** | Cloud | Local |
| **GPU Required** | No | Optional (faster) |
| **Quality** | Very High | High |
| **Speed (CPU)** | Fast (cloud) | Slow |
| **Speed (GPU)** | Fast | Very Fast |
| **Voice Cloning** | Yes | Limited |
| **Languages** | 200+ | ~50 |
| **Offline Support** | No | Yes |
| **Cost** | API Credits | Free (local) |
| **Setup Complexity** | Easy (API key) | Medium (models) |

---

## Troubleshooting

### 1. "Fish Audio SDK not installed"

```bash
pip install fish-audio-sdk
```

### 2. "Fish Audio API key required"

Set the environment variable:
```bash
export FISH_API_KEY=your-api-key-here
```

Or create `.env` file:
```
FISH_API_KEY=your-api-key-here
```

### 3. "Fish Audio authentication failed"

- Verify your API key is correct
- Check that your account is active at https://fish.audio/app
- Ensure you have credits remaining

### 4. "Fish Audio rate limit exceeded"

- Wait a few minutes before retrying
- Check your account limits at https://fish.audio/app/api-keys
- Consider upgrading your plan for higher limits

### 5. Fallback to Coqui TTS

If Fish Audio fails, the system automatically falls back to Coqui TTS:

```
⚠️  Fish Audio initialization failed: Invalid API key
🎤 Falling back to Coqui TTS
```

This ensures uninterrupted service even if Fish Audio is unavailable.

---

## Cost Considerations

Fish Audio is a paid service with credit-based pricing:

- **Free Tier**: Limited credits for testing
- **Paid Plans**: Various tiers based on usage
- **Check Credits**: Visit https://fish.audio/app/account

Monitor your usage:
```python
from models.voice_synthesis import FishAudioSynthesizer

fish_tts = FishAudioSynthesizer()
info = fish_tts.get_account_info()
print(f"Credits: {info['credits']}")
print(f"Status: {info['status']}")
```

---

## Architecture

### Provider Selection Logic

```
1. User specifies provider (or uses "auto")
   ↓
2. If "fish_audio":
   - Check FISH_API_KEY env var
   - Initialize FishAudioSynthesizer
   - If fails → raise error
   ↓
3. If "coqui":
   - Initialize CoquiVoiceSynthesizer
   - Load local TTS models
   ↓
4. If "auto":
   - Check if Fish Audio available (API key set)
   - Try Fish Audio first
   - If fails → fallback to Coqui
   ↓
5. VoiceSynthesizer wraps selected provider
   ↓
6. All calls route through unified interface
```

### File Structure

```
backend/models/voice_synthesis.py
├── FishAudioSynthesizer (lines 33-175)
│   ├── __init__() - Initialize with API key
│   ├── synthesize() - Generate speech
│   └── get_account_info() - Check credits
│
├── CoquiVoiceSynthesizer (lines 178-299)
│   ├── __init__() - Initialize with device
│   ├── load_model() - Load TTS model
│   ├── synthesize() - Generate speech
│   └── get_model_for_language() - Select model
│
└── VoiceSynthesizer (lines 302-408)
    ├── __init__() - Provider selection
    ├── synthesize() - Route to provider
    └── get_provider_info() - Provider details
```

---

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** periodically
4. **Monitor usage** to detect anomalies
5. **Set up alerts** for high usage or errors

### Secure Configuration

```bash
# .env (NEVER commit this file)
FISH_API_KEY=fa_live_1234567890abcdef

# .gitignore (ensure this is included)
.env
.env.local
*.env
```

---

## Migration Guide

### From Coqui-Only to Dual Provider

**Step 1:** Install Fish Audio SDK
```bash
pip install fish-audio-sdk
```

**Step 2:** Get API key from https://fish.audio/app/api-keys

**Step 3:** Update environment
```bash
# .env
FISH_API_KEY=your-api-key
TTS_PROVIDER=auto
```

**Step 4:** Restart backend
```bash
python app.py
```

**No code changes required!** The system automatically detects and uses Fish Audio.

### Switching Default Provider

To change the default provider, update the environment variable and restart:

```bash
# Update .env file
echo "TTS_PROVIDER=fish_audio" >> .env

# Restart the server
pkill -f "python app.py"
python app.py
```

Or for per-request overrides (no restart needed):
```python
# Each request can specify its own provider
POST /api/dub
  video: file.mp4
  target_language: es
  tts_provider: fish_audio  # This request uses Fish Audio

POST /api/dub
  video: file2.mp4
  target_language: fr
  tts_provider: coqui  # This request uses Coqui
```

---

## FAQ

**Q: Do I need to use Fish Audio?**
A: No, Coqui TTS remains fully supported. Fish Audio is optional.

**Q: Can I use both providers?**
A: Yes! Switch between them per-request or globally.

**Q: Which provider is better?**
A: Fish Audio has higher quality and faster cloud processing. Coqui TTS is free and works offline.

**Q: What happens if my API key expires?**
A: The system automatically falls back to Coqui TTS.

**Q: Can I use custom voices?**
A: Yes, with Fish Audio voice cloning. Upload reference audio at https://fish.audio/app.

**Q: Does this work with all languages?**
A: Both providers support 200+ languages. Fish Audio may have better coverage.

**Q: What are the costs?**
A: Fish Audio is credit-based (check pricing at fish.audio). Coqui TTS is free (local processing).

---

## Resources

- **Fish Audio Docs**: https://docs.fish.audio
- **Fish Audio Dashboard**: https://fish.audio/app
- **Fish Audio Python SDK**: https://github.com/fishaudio/fish-audio-python
- **Get API Key**: https://fish.audio/app/api-keys
- **Pricing**: https://fish.audio/pricing

---

## Support

### Fish Audio Issues

For Fish Audio-specific problems:
- Check status: https://status.fish.audio
- Contact support: https://fish.audio/support
- Community: https://discord.gg/fishaudio

### VoxDub Integration Issues

For integration problems:
- Open issue: https://github.com/yourusername/voxdub/issues
- Check logs: `backend/logs/` (if configured)
- Enable debug logging:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

---

## Changelog

### Version 1.1.0 (2025-01-15)

- ✨ Added Fish Audio TTS provider support
- ✨ Auto-detection and fallback logic
- ✨ New API endpoints for provider management
- ✨ Voice cloning support
- ✨ Speed and volume controls
- 📚 Comprehensive documentation
- 🔧 Environment variable configuration

---

**Built with ❤️ using Fish Audio and VoxDub**
