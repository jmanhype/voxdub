"""
Fish Speech TTS API Endpoints
Enhanced TTS features for voice cloning and emotion synthesis with security
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import uuid
import logging
from pydantic import BaseModel, validator

from models.voice_synthesis import get_synthesizer
from models.providers import FishSpeechProvider
from utils.security import (
    validate_audio_file,
    generate_secure_filename,
    sanitize_voice_id,
    validate_text_input,
    validate_language_code,
    validate_emotion,
    MAX_REFERENCE_AUDIO_SIZE
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/fish-speech",
    tags=["Fish Speech TTS"]
)

# Reference audio storage
REFERENCE_DIR = Path("references")
REFERENCE_DIR.mkdir(exist_ok=True)
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


class TTSRequest(BaseModel):
    """TTS generation request with validation"""
    text: str
    language: str = "en"
    emotion: Optional[str] = None
    voice_id: Optional[str] = None
    streaming: bool = False
    speed: float = 1.0

    @validator('text')
    def validate_text(cls, v):
        return validate_text_input(v, max_length=5000)

    @validator('speed')
    def validate_speed(cls, v):
        if not 0.5 <= v <= 2.0:
            raise ValueError('Speed must be between 0.5 and 2.0')
        return v


@router.get("/info")
def get_fish_speech_info():
    """Get Fish Speech TTS provider information"""
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
        logger.error(f"Error getting Fish Speech info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider information")


@router.get("/emotions")
def get_available_emotions():
    """Get list of available emotion markers"""
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
        logger.error(f"Error getting emotions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emotions")


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
    audio_path = None
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active. Set TTS_PROVIDER=fish_speech"
            )

        # Sanitize voice ID
        voice_id = sanitize_voice_id(voice_id)

        # Validate audio file with MIME type checking
        content, mime_type = await validate_audio_file(audio, MAX_REFERENCE_AUDIO_SIZE)

        # Generate secure filename
        secure_filename = generate_secure_filename(audio.filename or "audio.wav", prefix=voice_id)
        audio_path = REFERENCE_DIR / secure_filename

        # Save validated audio
        with open(audio_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved reference audio: {secure_filename} ({len(content)} bytes, {mime_type})")

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
        # Cleanup on error
        if audio_path and audio_path.exists():
            audio_path.unlink(missing_ok=True)
        logger.error(f"Error adding voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reference voice")


@router.get("/voices/list")
def list_reference_voices():
    """List all available reference voices"""
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
        logger.error(f"Error listing voices: {e}")
        raise HTTPException(status_code=500, detail="Failed to list voices")


@router.delete("/voices/{voice_id}")
def delete_reference_voice(voice_id: str):
    """Delete a reference voice from both server and local storage"""
    try:
        # Sanitize voice ID
        voice_id = sanitize_voice_id(voice_id)

        synthesizer = get_synthesizer()
        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active"
            )

        # Try to delete from Fish Speech server first (best effort)
        server_deleted = False
        try:
            # Note: This assumes the provider has a delete method
            # If it doesn't exist, we'll catch the exception
            if hasattr(synthesizer.provider, 'delete_reference_voice'):
                server_deleted = synthesizer.provider.delete_reference_voice(voice_id)
                logger.info(f"Deleted voice from server: {voice_id}")
        except Exception as e:
            # Log but don't fail - voice might not exist on server
            logger.warning(f"Could not delete from server (may not exist): {e}")

        # Find and delete local files
        deleted_files = []
        for file in REFERENCE_DIR.glob(f"{voice_id}_*"):
            file.unlink()
            deleted_files.append(file.name)  # Return only filename, not full path
            logger.info(f"Deleted reference file: {file.name}")

        if not deleted_files and not server_deleted:
            raise HTTPException(404, f"Voice '{voice_id}' not found locally or on server")

        return {
            "success": True,
            "voice_id": voice_id,
            "deleted_count": len(deleted_files),
            "server_deleted": server_deleted,
            "message": "Reference voice deleted successfully from server and local storage"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete voice")


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

        # Validate language
        language = validate_language_code(
            request.language,
            synthesizer.get_supported_languages()
        )

        # Validate emotion
        emotion = validate_emotion(
            request.emotion,
            synthesizer.get_available_emotions()
        )

        # Generate secure output path
        output_id = str(uuid.uuid4())
        output_path = TEMP_DIR / f"{output_id}_synthesized.wav"

        # Synthesize
        result_path = synthesizer.synthesize(
            text=request.text,
            output_path=str(output_path),
            language=language,
            speaker=request.voice_id,
            speed=request.speed,
            emotion=emotion,
            streaming=request.streaming
        )

        file_size = Path(result_path).stat().st_size / 1024

        logger.info(f"Synthesized speech: {output_id} ({file_size:.1f} KB)")

        return {
            "success": True,
            "output_id": output_id,
            "file_size_kb": round(file_size, 2),
            "text_length": len(request.text),
            "language": language,
            "emotion": emotion,
            "download_url": f"/api/fish-speech/download/{output_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")


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
    ref_path = None
    try:
        synthesizer = get_synthesizer()

        if not isinstance(synthesizer.provider, FishSpeechProvider):
            raise HTTPException(
                status_code=400,
                detail="Fish Speech provider not active"
            )

        # Validate inputs
        text = validate_text_input(text, max_length=5000)
        language = validate_language_code(
            language,
            synthesizer.get_supported_languages()
        )
        emotion = validate_emotion(
            emotion,
            synthesizer.get_available_emotions()
        )

        # Validate reference audio with MIME type checking
        content, mime_type = await validate_audio_file(audio, MAX_REFERENCE_AUDIO_SIZE)

        # Save temporary reference audio with secure filename
        temp_id = str(uuid.uuid4())
        secure_ref_filename = generate_secure_filename(audio.filename or "reference.wav")
        ref_path = TEMP_DIR / secure_ref_filename

        with open(ref_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved temp reference: {secure_ref_filename} ({len(content)} bytes)")

        # Generate secure output path
        output_path = TEMP_DIR / f"{temp_id}_cloned.wav"

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

        file_size = Path(result_path).stat().st_size / 1024

        logger.info(f"Voice cloning complete: {temp_id} ({file_size:.1f} KB)")

        return {
            "success": True,
            "output_id": temp_id,
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
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail="Voice cloning failed")
    finally:
        # Always cleanup reference audio
        if ref_path and ref_path.exists():
            ref_path.unlink(missing_ok=True)


@router.get("/download/{output_id}")
def download_synthesized_audio(output_id: str):
    """Download synthesized audio file"""
    # Validate output_id format (UUID)
    try:
        uuid.UUID(output_id)
    except ValueError:
        raise HTTPException(400, "Invalid output ID format")

    # Try different suffixes
    for suffix in ["_synthesized.wav", "_cloned.wav"]:
        file_path = TEMP_DIR / f"{output_id}{suffix}"
        if file_path.exists():
            # Verify file is within temp directory (prevent path traversal)
            if not file_path.resolve().parent == TEMP_DIR.resolve():
                raise HTTPException(403, "Access denied")

            return FileResponse(
                path=file_path,
                filename=f"fish_speech_{output_id}.wav",
                media_type="audio/wav"
            )

    raise HTTPException(404, "Audio file not found or expired")


@router.get("/health")
def check_fish_speech_health():
    """Check Fish Speech API server health"""
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
            "message": "Fish Speech API is running"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": "Fish Speech API is not accessible"
        }
