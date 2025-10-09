"""
Coqui TTS Voice Synthesis Module
Generates natural-sounding speech from text
"""

from TTS.api import TTS
import torch
from pathlib import Path
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    """Professional TTS with multi-language and voice cloning support"""
    
    # Available TTS models by language
    TTS_MODELS = {
        "en": "tts_models/en/ljspeech/tacotron2-DDC",
        "es": "tts_models/es/mai/tacotron2-DDC",
        "fr": "tts_models/fr/mai/tacotron2-DDC",
        "de": "tts_models/de/thorsten/tacotron2-DDC",
        "multi": "tts_models/multilingual/multi-dataset/your_tts"  # Multilingual fallback
    }
    
    def __init__(self, default_model: Optional[str] = None):
        """
        Initialize TTS synthesizer
        
        Args:
            default_model: Specific TTS model to use
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.default_model = default_model or self.TTS_MODELS["en"]
        self.tts = None
        self.current_model = None
        
        logger.info(f"Initializing TTS on {self.device}")
    
    def load_model(self, model_name: Optional[str] = None):
        """Load TTS model"""
        model_name = model_name or self.default_model
        
        # Only reload if different model
        if self.tts is None or self.current_model != model_name:
            try:
                logger.info(f"Loading TTS model: {model_name}")
                
                self.tts = TTS(
                    model_name=model_name,
                    progress_bar=False,
                    gpu=(self.device == "cuda")
                )
                
                self.current_model = model_name
                logger.info("✅ TTS model loaded successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to load TTS model: {e}")
                # Fallback to multilingual model
                logger.info("⚠️  Trying multilingual fallback model...")
                self.tts = TTS(
                    model_name=self.TTS_MODELS["multi"],
                    progress_bar=False,
                    gpu=(self.device == "cuda")
                )
                self.current_model = self.TTS_MODELS["multi"]
        
        return self.tts
    
    def get_model_for_language(self, language: str) -> str:
        """Select appropriate TTS model for language"""
        return self.TTS_MODELS.get(language.lower(), self.TTS_MODELS["multi"])
    
    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0
    ) -> str:
        """
        Synthesize speech from text
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Target language code
            speaker: Speaker voice (if multi-speaker model)
            speed: Speech speed multiplier
        
        Returns:
            Path to generated audio file
        """
        try:
            if not text or not text.strip():
                raise ValueError("Empty text provided for synthesis")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Select model for language
            model_name = self.get_model_for_language(language)
            tts = self.load_model(model_name)
            
            logger.info(f"Synthesizing speech for '{language}'")
            logger.info(f"Text length: {len(text)} characters")
            
            # Generate speech
            if hasattr(tts, 'tts_to_file'):
                tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker=speaker,
                    language=language if "multilingual" in model_name else None
                )
            else:
                # Alternative method for different TTS versions
                wav = tts.tts(text=text, speaker=speaker)
                tts.save_wav(wav, output_path)
            
            if not Path(output_path).exists():
                raise FileNotFoundError("TTS failed to generate audio file")
            
            file_size = Path(output_path).stat().st_size / 1024  # KB
            logger.info(f"✅ Speech synthesis complete")
            logger.info(f"   Output: {Path(output_path).name}")
            logger.info(f"   Size: {file_size:.1f} KB")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Speech synthesis failed: {e}")
            raise RuntimeError(f"TTS error: {e}")

# Global instance
_synthesizer = None

def get_synthesizer() -> VoiceSynthesizer:
    """Get or create global synthesizer instance"""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = VoiceSynthesizer()
    return _synthesizer

def synthesize_speech(
    text: str,
    output_path: str,
    language: str = "en"
) -> str:
    """
    Convenience function for speech synthesis
    
    Args:
        text: Text to synthesize
        output_path: Output file path
        language: Target language
    
    Returns:
        Path to generated audio
    """
    synthesizer = get_synthesizer()
    return synthesizer.synthesize(text, output_path, language)
