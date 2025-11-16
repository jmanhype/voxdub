from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
import asyncio
from datetime import datetime

# Import our models
from models.transcription import transcribe_audio
from models.translation import translate_text
from models.voice_synthesis import synthesize_speech, set_tts_provider, get_synthesizer
from models.lipsync import sync_lips
from utils.video_processor import extract_audio, merge_audio_video
from utils.file_handler import cleanup_temp_files, ensure_directories

app = FastAPI(
    title="VoxDub - AI Video Dubbing API",
    description="Professional AI-powered video dubbing with lip-sync",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
TEMP_DIR = Path("temp")

# Job tracking (in production, use Redis or database)
jobs = {}

class JobStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@app.on_event("startup")
async def startup_event():
    """Initialize directories and models on startup"""
    ensure_directories()
    print("=" * 60)
    print("🎬 VoxDub AI Video Dubbing System")
    print("=" * 60)
    print("✅ Directories initialized")
    print("✅ Server ready to accept requests")
    print("=" * 60)

@app.get("/")
def read_root():
    return {
        "service": "VoxDub API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "health": "/api/health",
            "dub": "/api/dub (POST)",
            "status": "/api/status/{job_id} (GET)",
            "download": "/api/download/{job_id} (GET)",
            "languages": "/api/languages (GET)",
            "docs": "/docs"
        }
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint with TTS provider info"""
    try:
        synthesizer = get_synthesizer()
        tts_info = synthesizer.get_provider_info()
    except Exception:
        tts_info = {"provider": "unknown", "status": "not_initialized"}

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whisper": "ready",
            "nllb_translation": "ready",
            "tts": tts_info,
            "wav2lip": "ready",
            "ffmpeg": "ready"
        }
    }

@app.get("/api/languages")
def get_supported_languages():
    """Return comprehensive list of supported languages"""
    return {
        "languages": [
            {"code": "en", "name": "English", "native": "English"},
            {"code": "es", "name": "Spanish", "native": "Español"},
            {"code": "fr", "name": "French", "native": "Français"},
            {"code": "de", "name": "German", "native": "Deutsch"},
            {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
            {"code": "zh", "name": "Chinese", "native": "中文"},
            {"code": "ja", "name": "Japanese", "native": "日本語"},
            {"code": "ko", "name": "Korean", "native": "한국어"},
            {"code": "pt", "name": "Portuguese", "native": "Português"},
            {"code": "ru", "name": "Russian", "native": "Русский"},
            {"code": "ar", "name": "Arabic", "native": "العربية"},
            {"code": "it", "name": "Italian", "native": "Italiano"}
        ]
    }

@app.get("/api/tts/providers")
def get_tts_providers():
    """Get available TTS providers and current selection"""
    try:
        synthesizer = get_synthesizer()
        provider_info = synthesizer.get_provider_info()

        return {
            "providers": {
                "fish_audio": {
                    "name": "Fish Audio",
                    "features": ["voice_cloning", "multi_language", "cloud_based", "high_quality"],
                    "requires_api_key": True,
                    "available": provider_info.get("provider") == "fish_audio"
                },
                "coqui": {
                    "name": "Coqui TTS",
                    "features": ["multi_language", "local_processing", "offline"],
                    "requires_api_key": False,
                    "available": True
                }
            },
            "current": provider_info
        }
    except Exception as e:
        return {
            "providers": {
                "fish_audio": {"name": "Fish Audio", "available": False, "requires_api_key": True},
                "coqui": {"name": "Coqui TTS", "available": True, "requires_api_key": False}
            },
            "current": {"provider": "unknown", "error": str(e)}
        }

@app.post("/api/tts/provider")
def set_tts_provider_endpoint(provider: str):
    """
    Set the preferred TTS provider

    Args:
        provider: "auto", "fish_audio", or "coqui"
    """
    if provider not in ["auto", "fish_audio", "coqui"]:
        raise HTTPException(400, "Invalid provider. Choose 'auto', 'fish_audio', or 'coqui'")

    try:
        set_tts_provider(provider)
        return {
            "success": True,
            "message": f"TTS provider set to: {provider}",
            "provider": provider
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to set TTS provider: {str(e)}")

async def process_video_job(job_id: str, video_path: Path, target_language: str, tts_provider: Optional[str] = None):
    """Background task for video processing with TTS provider support"""
    try:
        # Update status
        jobs[job_id]["status"] = JobStatus.PROCESSING
        jobs[job_id]["progress"] = 0

        # Step 1: Extract audio (10%)
        jobs[job_id]["current_step"] = "Extracting audio..."
        audio_path = TEMP_DIR / f"{job_id}_audio.wav"
        extract_audio(str(video_path), str(audio_path))
        jobs[job_id]["progress"] = 20

        # Step 2: Transcribe (20%)
        jobs[job_id]["current_step"] = "Transcribing speech..."
        transcription = transcribe_audio(str(audio_path))
        source_lang = transcription["language"]
        source_text = transcription["text"]
        jobs[job_id]["source_language"] = source_lang
        jobs[job_id]["progress"] = 40

        # Step 3: Translate (30%)
        jobs[job_id]["current_step"] = "Translating text..."
        translated_text = translate_text(source_text, source_lang, target_language)
        jobs[job_id]["progress"] = 60

        # Step 4: Synthesize speech (40%)
        jobs[job_id]["current_step"] = "Generating new speech..."
        new_audio_path = TEMP_DIR / f"{job_id}_dubbed.wav"

        # Use specified TTS provider or auto
        synthesize_speech(
            translated_text,
            str(new_audio_path),
            target_language,
            provider=tts_provider
        )

        # Store which provider was actually used
        synthesizer = get_synthesizer(provider=tts_provider)
        provider_info = synthesizer.get_provider_info()
        jobs[job_id]["tts_provider_used"] = provider_info.get("provider", "unknown")

        jobs[job_id]["progress"] = 80

        # Step 5: Lip sync (50%)
        jobs[job_id]["current_step"] = "Syncing lips..."
        output_path = OUTPUT_DIR / f"{job_id}_final.mp4"
        sync_lips(str(video_path), str(new_audio_path), str(output_path))
        jobs[job_id]["progress"] = 100

        # Success!
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["current_step"] = "Complete!"
        jobs[job_id]["output_file"] = str(output_path)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

        # Cleanup temp files
        audio_path.unlink(missing_ok=True)
        new_audio_path.unlink(missing_ok=True)
        video_path.unlink(missing_ok=True)

    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["failed_at"] = datetime.now().isoformat()
        print(f"❌ Job {job_id} failed: {e}")

@app.post("/api/dub")
async def dub_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="Video file to dub"),
    target_language: str = Form(..., description="Target language code (e.g., 'es', 'fr')"),
    tts_provider: Optional[str] = Form(None, description="TTS provider: 'auto', 'fish_audio', 'coqui'")
):
    """
    Main endpoint for video dubbing
    Creates a background job and returns job_id for status tracking

    Args:
        video: Video file to dub
        target_language: Target language code
        tts_provider: Optional TTS provider override (auto, fish_audio, coqui)
    """
    try:
        # Validate file
        if not video.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(400, "Only video files are supported (.mp4, .avi, .mov, .mkv)")

        # Validate TTS provider
        if tts_provider and tts_provider not in ["auto", "fish_audio", "coqui"]:
            raise HTTPException(400, "Invalid TTS provider. Choose 'auto', 'fish_audio', or 'coqui'")

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Save uploaded video
        video_path = UPLOAD_DIR / f"{job_id}_{video.filename}"
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Initialize job tracking
        jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.QUEUED,
            "filename": video.filename,
            "target_language": target_language,
            "tts_provider": tts_provider or "auto",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "current_step": "Queued..."
        }

        # Add to background tasks
        background_tasks.add_task(process_video_job, job_id, video_path, target_language, tts_provider)

        return {
            "success": True,
            "job_id": job_id,
            "message": "Video uploaded successfully. Processing started.",
            "status_url": f"/api/status/{job_id}",
            "download_url": f"/api/download/{job_id}",
            "tts_provider": tts_provider or "auto"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/status/{job_id}")
def get_job_status(job_id: str):
    """Get processing status of a job"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    return jobs[job_id]

@app.get("/api/download/{job_id}")
def download_result(job_id: str):
    """Download the final dubbed video"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(400, f"Job not completed. Current status: {job['status']}")
    
    output_file = Path(job["output_file"])
    
    if not output_file.exists():
        raise HTTPException(404, "Output file not found")
    
    return FileResponse(
        path=output_file,
        filename=f"dubbed_{job['filename']}",
        media_type="video/mp4"
    )

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎬 VoxDub - Professional AI Video Dubbing System")
    print("=" * 60)
    print("✅ Server: http://localhost:8000")
    print("✅ API Documentation: http://localhost:8000/docs")
    print("✅ Health Check: http://localhost:8000/api/health")
    print("✅ Supported Languages: http://localhost:8000/api/languages")
    print("=" * 60)
    print("📊 Features:")
    print("   • Whisper AI Speech Recognition")
    print("   • NLLB Neural Translation")
    print("   • Coqui TTS Voice Synthesis")
    print("   • Wav2Lip Lip Synchronization")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
