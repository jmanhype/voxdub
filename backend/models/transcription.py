"""
Whisper AI Speech-to-Text Transcription Module
Handles audio transcription with multiple model sizes and GPU support
"""

import whisper
import torch
import warnings
from pathlib import Path
from typing import Dict, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore")

class WhisperTranscriber:
    """Professional Whisper transcription with caching and GPU support"""
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        """
        Initialize Whisper model
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to use (cuda/cpu). Auto-detected if None
        """
        self.model_size = model_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        
        logger.info(f"Initializing Whisper with device: {self.device}")
        
    def load_model(self):
        """Load Whisper model with error handling"""
        if self.model is None:
            try:
                logger.info(f"Loading Whisper '{self.model_size}' model...")
                self.model = whisper.load_model(self.model_size, device=self.device)
                logger.info(f"✅ Whisper model loaded successfully on {self.device}")
            except Exception as e:
                logger.error(f"❌ Failed to load Whisper model: {e}")
                raise RuntimeError(f"Whisper model loading failed: {e}")
        
        return self.model
    
    def transcribe(
        self, 
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict:
        """
        Transcribe audio file with comprehensive output
        
        Args:
            audio_path: Path to audio file
            language: Source language code (auto-detected if None)
            task: 'transcribe' or 'translate' (to English)
        
        Returns:
            Dictionary with transcription results
        """
        try:
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            model = self.load_model()
            
            logger.info(f"Transcribing audio: {Path(audio_path).name}")
            
            # Transcribe with options
            result = model.transcribe(
                audio_path,
                language=language,
                task=task,
                fp16=(self.device == "cuda"),  # Use FP16 on GPU
                verbose=False
            )
            
            # Extract key information
            transcription_data = {
                "text": result["text"].strip(),
                "language": result["language"],
                "segments": [
                    {
                        "id": seg["id"],
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
                    }
                    for seg in result.get("segments", [])
                ],
                "word_count": len(result["text"].split()),
                "duration": result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0
            }
            
            logger.info(f"✅ Transcription complete: {len(transcription_data['segments'])} segments")
            logger.info(f"   Language: {transcription_data['language']}")
            logger.info(f"   Words: {transcription_data['word_count']}")
            
            return transcription_data
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise RuntimeError(f"Transcription error: {e}")

# Global instance
_transcriber = None

def get_transcriber(model_size: str = "base") -> WhisperTranscriber:
    """Get or create global transcriber instance"""
    global _transcriber
    if _transcriber is None:
        _transcriber = WhisperTranscriber(model_size=model_size)
    return _transcriber

def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict:
    """
    Convenience function for transcription
    
    Args:
        audio_path: Path to audio file
        language: Source language (auto-detected if None)
    
    Returns:
        Transcription results dictionary
    """
    transcriber = get_transcriber()
    return transcriber.transcribe(audio_path, language=language)
