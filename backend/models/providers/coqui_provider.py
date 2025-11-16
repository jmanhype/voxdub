"""
Coqui TTS Provider
Original TTS implementation wrapped as a provider
"""

from TTS.api import TTS
import torch
from pathlib import Path
from typing import Optional, List, Dict
import logging
from .base import TTSProvider

logger = logging.getLogger(__name__)


class CoquiTTSProvider(TTSProvider):
    """Coqui TTS implementation"""

    # Available TTS models by language
    TTS_MODELS = {
        "en": "tts_models/en/ljspeech/tacotron2-DDC",
        "es": "tts_models/es/mai/tacotron2-DDC",
        "fr": "tts_models/fr/mai/tacotron2-DDC",
        "de": "tts_models/de/thorsten/tacotron2-DDC",
        "multi": "tts_models/multilingual/multi-dataset/your_tts"
    }

    def __init__(self, device: str = "cuda", default_model: Optional[str] = None):
        """Initialize Coqui TTS provider"""
        super().__init__(device)
        self.default_model = default_model or self.TTS_MODELS["en"]
        self.tts = None
        self.current_model = None
        logger.info(f"Initialized Coqui TTS on {self.device}")

    def load_model(self, model_name: Optional[str] = None):
        """Load Coqui TTS model"""
        model_name = model_name or self.default_model

        # Only reload if different model
        if self.tts is None or self.current_model != model_name:
            try:
                logger.info(f"Loading Coqui TTS model: {model_name}")

                self.tts = TTS(
                    model_name=model_name,
                    progress_bar=False,
                    gpu=(self.device == "cuda")
                )

                self.current_model = model_name
                logger.info("Coqui TTS model loaded successfully")

            except Exception as e:
                logger.error(f"Failed to load Coqui TTS model: {e}")
                # Fallback to multilingual model
                logger.info("Trying multilingual fallback model...")
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
        speed: float = 1.0,
        **kwargs
    ) -> str:
        """Synthesize speech using Coqui TTS"""
        try:
            if not text or not text.strip():
                raise ValueError("Empty text provided for synthesis")

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Select model for language
            model_name = self.get_model_for_language(language)
            tts = self.load_model(model_name)

            logger.info(f"Synthesizing speech for '{language}' using Coqui TTS")
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
                wav = tts.tts(text=text, speaker=speaker)
                tts.save_wav(wav, output_path)

            if not Path(output_path).exists():
                raise FileNotFoundError("TTS failed to generate audio file")

            file_size = Path(output_path).stat().st_size / 1024
            logger.info(f"Speech synthesis complete ({file_size:.1f} KB)")

            return output_path

        except Exception as e:
            logger.error(f"Coqui TTS synthesis failed: {e}")
            raise RuntimeError(f"Coqui TTS error: {e}")

    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return list(self.TTS_MODELS.keys())

    def cleanup(self):
        """Clean up Coqui TTS resources"""
        if self.tts is not None:
            del self.tts
            self.tts = None
            self.current_model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
