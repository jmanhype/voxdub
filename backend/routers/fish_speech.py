"""
Fish Speech TTS API Endpoints
Enhanced TTS features for voice cloning and emotion synthesis
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from pathlib import Path
import uuid
import os
from pydantic import BaseModel

from models.voice_synthesis import get_synthesizer
from models.providers import FishSpeechProvider

router = APIRouter(
    prefix="/api/fish-speech",
    tags=["Fish Speech TTS"]
)

# Reference audio storage
REFERENCE_DIR = Path("references")
REFERENCE_DIR.mkdir(exist_ok=True)


class TTSRequest(BaseModel):
    """TTS generation request"""
    text: str
    language: str = "en"
    emotion: Optional[str] = None
    voice_id: Optional[str] = None
    streaming: bool = False
    speed: float = 1.0


class VoiceCloneRequest(BaseModel):
    """Voice cloning request"""
    text: str
    language: str = "en"
    emotion: Optional[str] = None
    reference_text: Optional[str] = None
    streaming: bool = False


@router.get("/info")
def get_fish_speech_info():
    """
    Get Fish Speech TTS provider information
    """
    try:
        synthesizer = get_synthesizer()

        # Check if Fish Speech is active
        if not isinstance(synthesizer.provider, FishSpeechProvider):
            return {
                "enabled": False,
                "active_provider": synthesizer.provider_name,
                "message": "Fish Speech is not the active TTS provider. Set TTS_PROVIDER=fish_speech in .env"
            }

        return {
            "enabled": True,
            "provider": "fish_speech",
            "model": synthesizer.provider.model,
            "api_url": synthesizer.provider.api_url,
            "supported_languages": synthesizer.get_supported_languages(),
            "available_emotions": synthesizer.get_available_emotions(),
            "features": {
                "voice_cloning": True,
                "emotion_synthesis": True,
                "streaming": True,
                "multilingual": True
            },
            "quality_metrics": {
                "wer": 0.008,
                "cer": 0.004,
                "benchmark": "#1 on TTS-Arena2"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting info: {str(e)}")


@router.get("/emotions")
def get_available_emotions():
    """
    Get list of available emotion markers
    """
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active"
            )

        emotions = synthesizer.get_available_emotions()

        return {
            "emotions": emotions,
            "usage": "Add emotion parameter to TTS requests",
            "example": {
                "text": "Hello, how are you?",
                "emotion": "happy"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/voices/add")
async def add_reference_voice(
    voice_id: str = Form(..., description="Unique voice identifier"),
    audio: UploadFile = File(..., description="Reference audio file"),
    text: Optional[str] = Form(None, description="Transcript of reference audio")
):
    """
    Add a reference voice for voice cloning

    Upload a reference audio sample to create a custom voice.
    The audio should be clear, 3-30 seconds long, and contain the target voice.
    """
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active. Set TTS_PROVIDER=fish_speech"
            )

        # Validate file type
        if not audio.filename.endswith(('.wav', '.mp3', '.flac', '.ogg')):
            raise HTTPException(
                status_code=400,
                detail="Only audio files are supported (.wav, .mp3, .flac, .ogg)"
            )

        # Save reference audio
        audio_path = REFERENCE_DIR / f"{voice_id}_{audio.filename}"
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)

        # Add to Fish Speech
        success = synthesizer.add_reference_voice(
            voice_id=voice_id,
            audio_path=str(audio_path),
            text=text
        )

        if not success:
            audio_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to add reference voice to Fish Speech"
            )

        return {
            "success": True,
            "voice_id": voice_id,
            "message": "Reference voice added successfully",
            "usage": f"Use voice_id='{voice_id}' in TTS requests"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding voice: {str(e)}")


@router.get("/voices/list")
def list_reference_voices():
    """
    List all available reference voices
    """
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active"
            )

        voices = synthesizer.list_reference_voices()

        return {
            "voices": voices,
            "count": len(voices)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing voices: {str(e)}")


@router.delete("/voices/{voice_id}")
def delete_reference_voice(voice_id: str):
    """
    Delete a reference voice
    """
    try:
        # Find and delete local file
        deleted_files = []
        for file in REFERENCE_DIR.glob(f"{voice_id}_*"):
            file.unlink()
            deleted_files.append(str(file))

        if not deleted_files:
            raise HTTPException(404, f"Voice '{voice_id}' not found")

        return {
            "success": True,
            "voice_id": voice_id,
            "deleted_files": deleted_files,
            "message": "Reference voice deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting voice: {str(e)}")


@router.post("/synthesize")
async def synthesize_with_fish_speech(request: TTSRequest):
    """
    Synthesize speech using Fish Speech TTS

    Supports:
    - Multiple languages (en, zh, ja)
    - Emotion markers (happy, sad, angry, etc.)
    - Custom voices (using voice_id)
    - Streaming output
    """
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active. Set TTS_PROVIDER=fish_speech"
            )

        # Generate output path
        output_id = str(uuid.uuid4())
        output_path = Path("temp") / f"{output_id}_synthesized.wav"
        output_path.parent.mkdir(exist_ok=True)

        # Synthesize
        result_path = synthesizer.synthesize(
            text=request.text,
            output_path=str(output_path),
            language=request.language,
            speaker=request.voice_id,
            speed=request.speed,
            emotion=request.emotion,
            streaming=request.streaming
        )

        file_size = Path(result_path).stat().st_size / 1024

        return {
            "success": True,
            "output_id": output_id,
            "file_path": result_path,
            "file_size_kb": round(file_size, 2),
            "text_length": len(request.text),
            "language": request.language,
            "emotion": request.emotion,
            "download_url": f"/api/fish-speech/download/{output_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.post("/clone-voice")
async def clone_voice_and_synthesize(
    text: str = Form(...),
    language: str = Form("en"),
    audio: UploadFile = File(..., description="Reference audio for voice cloning"),
    reference_text: Optional[str] = Form(None),
    emotion: Optional[str] = Form(None),
    streaming: bool = Form(False)
):
    """
    Voice cloning with synthesis in one step

    Upload a reference audio and generate speech with that voice.
    No need to register the voice - it's used directly for this request.
    """
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active"
            )

        # Validate audio file
        if not audio.filename.endswith(('.wav', '.mp3', '.flac', '.ogg')):
            raise HTTPException(400, "Only audio files supported")

        # Save temporary reference audio
        temp_id = str(uuid.uuid4())
        ref_path = Path("temp") / f"{temp_id}_reference.wav"
        ref_path.parent.mkdir(exist_ok=True)

        with open(ref_path, "wb") as f:
            content = await audio.read()
            f.write(content)

        # Generate output path
        output_path = Path("temp") / f"{temp_id}_cloned.wav"

        # Synthesize with voice cloning
        result_path = synthesizer.synthesize(
            text=text,
            output_path=str(output_path),
            language=language,
            emotion=emotion,
            reference_audio=str(ref_path),
            reference_text=reference_text,
            streaming=streaming
        )

        # Cleanup reference audio
        ref_path.unlink(missing_ok=True)

        file_size = Path(result_path).stat().st_size / 1024

        return {
            "success": True,
            "output_id": temp_id,
            "file_path": result_path,
            "file_size_kb": round(file_size, 2),
            "text_length": len(text),
            "language": language,
            "emotion": emotion,
            "voice_cloning": True,
            "download_url": f"/api/fish-speech/download/{temp_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        if 'ref_path' in locals():
            Path(ref_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@router.get("/download/{output_id}")
def download_synthesized_audio(output_id: str):
    """
    Download synthesized audio file
    """
    from fastapi.responses import FileResponse

    # Find the file
    temp_dir = Path("temp")

    # Try different suffixes
    for suffix in ["_synthesized.wav", "_cloned.wav"]:
        file_path = temp_dir / f"{output_id}{suffix}"
        if file_path.exists():
            return FileResponse(
                path=file_path,
                filename=f"fish_speech_{output_id}.wav",
                media_type="audio/wav"
            )

    raise HTTPException(404, "Audio file not found or expired")


@router.get("/health")
def check_fish_speech_health():
    """
    Check Fish Speech API server health
    """
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            return {
                "status": "inactive",
                "message": "Fish Speech provider not active",
                "active_provider": synthesizer.provider_name
            }

        # Test API connection
        synthesizer.provider.load_model()

        return {
            "status": "healthy",
            "provider": "fish_speech",
            "model": synthesizer.provider.model,
            "api_url": synthesizer.provider.api_url,
            "message": "Fish Speech API is running"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Fish Speech API is not accessible"
        }
