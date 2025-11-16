"""
Voice Synthesis Module
Supports multiple TTS providers: Coqui TTS and Fish Audio
Generates natural-sounding speech from text
"""

from TTS.api import TTS
import torch
from pathlib import Path
from typing import Optional, List, Literal
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fish Audio imports (optional)
try:
    from fishaudio import FishAudio, AsyncFishAudio
    from fishaudio.types import TTSConfig, Prosody
    from fishaudio.exceptions import (
        AuthenticationError,
        RateLimitError,
        ValidationError,
        FishAudioError
    )
    FISH_AUDIO_AVAILABLE = True
    logger.info("✅ Fish Audio SDK available")
except ImportError:
    FISH_AUDIO_AVAILABLE = False
    logger.warning("⚠️  Fish Audio SDK not installed. Only Coqui TTS available.")

class FishAudioSynthesizer:
    """Fish Audio TTS provider with advanced voice cloning"""

    # Language support mapping
    LANGUAGE_SUPPORT = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "hi": "Hindi",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "pt": "Portuguese",
        "ru": "Russian",
        "ar": "Arabic",
        "it": "Italian"
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Fish Audio synthesizer

        Args:
            api_key: Fish Audio API key (or use FISH_API_KEY env var)
        """
        if not FISH_AUDIO_AVAILABLE:
            raise ImportError(
                "Fish Audio SDK not installed. Install with: pip install fish-audio-sdk"
            )

        self.api_key = api_key or os.getenv("FISH_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Fish Audio API key required. Set FISH_API_KEY env var or pass api_key parameter. "
                "Get your key at: https://fish.audio/app/api-keys"
            )

        self.client = FishAudio(api_key=self.api_key)
        logger.info("✅ Fish Audio client initialized")

    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        reference_id: Optional[str] = None,
        speed: float = 1.0,
        volume: int = 0,
        audio_format: str = "wav"
    ) -> str:
        """
        Synthesize speech using Fish Audio

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Target language code
            reference_id: Fish Audio voice reference ID
            speed: Speech speed multiplier (0.5 - 2.0)
            volume: Volume adjustment in dB (-20 to 20)
            audio_format: Output format ('wav' or 'mp3')

        Returns:
            Path to generated audio file
        """
        try:
            if not text or not text.strip():
                raise ValueError("Empty text provided for synthesis")

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"🐟 Fish Audio: Synthesizing speech for '{language}'")
            logger.info(f"   Text length: {len(text)} characters")
            logger.info(f"   Speed: {speed}x, Volume: {volume}dB")

            # Configure TTS settings
            config = TTSConfig(
                format=audio_format,
                prosody=Prosody(speed=speed, volume=volume),
                latency="balanced"
            )

            # Generate speech
            if reference_id:
                logger.info(f"   Using voice reference: {reference_id}")
                audio_data = self.client.tts.convert(
                    text=text,
                    reference_id=reference_id,
                    config=config
                )
            else:
                # Use default voice for language
                audio_data = self.client.tts.convert(
                    text=text,
                    config=config
                )

            # Save audio file
            with open(output_path, 'wb') as f:
                f.write(audio_data)

            if not Path(output_path).exists():
                raise FileNotFoundError("Fish Audio failed to generate audio file")

            file_size = Path(output_path).stat().st_size / 1024  # KB
            logger.info(f"✅ Fish Audio synthesis complete")
            logger.info(f"   Output: {Path(output_path).name}")
            logger.info(f"   Size: {file_size:.1f} KB")

            return output_path

        except AuthenticationError as e:
            logger.error(f"❌ Fish Audio authentication failed: {e}")
            raise RuntimeError(
                "Fish Audio API key invalid. Get your key at: https://fish.audio/app/api-keys"
            )
        except RateLimitError as e:
            logger.error(f"❌ Fish Audio rate limit exceeded: {e}")
            raise RuntimeError("Fish Audio rate limit exceeded. Please try again later.")
        except ValidationError as e:
            logger.error(f"❌ Fish Audio validation error: {e}")
            raise RuntimeError(f"Invalid parameters for Fish Audio: {e}")
        except FishAudioError as e:
            logger.error(f"❌ Fish Audio error: {e}")
            raise RuntimeError(f"Fish Audio TTS error: {e}")
        except Exception as e:
            logger.error(f"❌ Fish Audio synthesis failed: {e}")
            raise RuntimeError(f"Speech synthesis error: {e}")

    def get_account_info(self) -> dict:
        """Get Fish Audio account credits and usage"""
        try:
            credits = self.client.account.get_credits()
            return {
                "provider": "fish_audio",
                "credits": credits,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {"provider": "fish_audio", "status": "error", "error": str(e)}


class CoquiVoiceSynthesizer:
    """Coqui TTS provider with multi-language support"""

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
        Initialize Coqui TTS synthesizer

        Args:
            default_model: Specific TTS model to use
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.default_model = default_model or self.TTS_MODELS["en"]
        self.tts = None
        self.current_model = None

        logger.info(f"Initializing Coqui TTS on {self.device}")
    
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
                logger.info("✅ Coqui TTS model loaded successfully")

            except Exception as e:
                logger.error(f"❌ Failed to load Coqui TTS model: {e}")
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
        """Select appropriate Coqui TTS model for language"""
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
            logger.error(f"❌ Coqui TTS synthesis failed: {e}")
            raise RuntimeError(f"TTS error: {e}")


class VoiceSynthesizer:
    """
    Unified Voice Synthesizer supporting multiple TTS providers
    Automatically selects best available provider or uses specified one
    """

    def __init__(
        self,
        provider: Literal["auto", "fish_audio", "coqui"] = "auto",
        fish_api_key: Optional[str] = None
    ):
        """
        Initialize voice synthesizer with provider selection

        Args:
            provider: TTS provider ("auto", "fish_audio", "coqui")
            fish_api_key: Fish Audio API key (required if provider is "fish_audio")
        """
        self.provider = provider
        self.fish_synthesizer = None
        self.coqui_synthesizer = None

        # Initialize based on provider selection
        if provider == "fish_audio":
            if not FISH_AUDIO_AVAILABLE:
                raise ImportError(
                    "Fish Audio requested but not installed. "
                    "Install with: pip install fish-audio-sdk"
                )
            self.fish_synthesizer = FishAudioSynthesizer(api_key=fish_api_key)
            logger.info("🐟 Using Fish Audio as TTS provider")

        elif provider == "coqui":
            self.coqui_synthesizer = CoquiVoiceSynthesizer()
            logger.info("🎤 Using Coqui TTS as provider")

        elif provider == "auto":
            # Auto-select: prefer Fish Audio if available and configured
            if FISH_AUDIO_AVAILABLE and (fish_api_key or os.getenv("FISH_API_KEY")):
                try:
                    self.fish_synthesizer = FishAudioSynthesizer(api_key=fish_api_key)
                    logger.info("🐟 Auto-selected Fish Audio as TTS provider")
                except Exception as e:
                    logger.warning(f"⚠️  Fish Audio initialization failed: {e}")
                    logger.info("🎤 Falling back to Coqui TTS")
                    self.coqui_synthesizer = CoquiVoiceSynthesizer()
            else:
                self.coqui_synthesizer = CoquiVoiceSynthesizer()
                logger.info("🎤 Auto-selected Coqui TTS as provider")
        else:
            raise ValueError(f"Invalid provider: {provider}. Choose 'auto', 'fish_audio', or 'coqui'")

    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        **kwargs
    ) -> str:
        """
        Synthesize speech using configured provider

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Target language code
            **kwargs: Provider-specific parameters
                Fish Audio: reference_id, speed, volume, audio_format
                Coqui: speaker, speed

        Returns:
            Path to generated audio file
        """
        if self.fish_synthesizer:
            return self.fish_synthesizer.synthesize(
                text=text,
                output_path=output_path,
                language=language,
                **kwargs
            )
        elif self.coqui_synthesizer:
            return self.coqui_synthesizer.synthesize(
                text=text,
                output_path=output_path,
                language=language,
                **kwargs
            )
        else:
            raise RuntimeError("No TTS provider initialized")

    def get_provider_info(self) -> dict:
        """Get information about active provider"""
        if self.fish_synthesizer:
            return {
                "provider": "fish_audio",
                "features": ["voice_cloning", "multi_language", "cloud_based"],
                "account": self.fish_synthesizer.get_account_info()
            }
        elif self.coqui_synthesizer:
            return {
                "provider": "coqui",
                "features": ["multi_language", "local_processing"],
                "device": self.coqui_synthesizer.device,
                "current_model": self.coqui_synthesizer.current_model
            }
        else:
            return {"provider": "none", "status": "not_initialized"}


# Global singleton cache (stateless - only caches default provider from env)
_synthesizer = None

def get_synthesizer(
    provider: Optional[Literal["auto", "fish_audio", "coqui"]] = None,
    fish_api_key: Optional[str] = None
) -> VoiceSynthesizer:
    """
    Get or create synthesizer instance (stateless)

    If a provider is specified, creates a new instance for that request.
    Otherwise, returns a cached instance using the TTS_PROVIDER env var.

    Args:
        provider: Provider for this request (creates new instance if specified)
        fish_api_key: Fish Audio API key

    Returns:
        VoiceSynthesizer instance
    """
    global _synthesizer

    # If provider is explicitly specified, create a fresh instance for this request
    if provider is not None:
        return VoiceSynthesizer(provider=provider, fish_api_key=fish_api_key)

    # Otherwise, use global singleton with default from environment
    if _synthesizer is None:
        default_provider = os.getenv("TTS_PROVIDER", "auto")
        _synthesizer = VoiceSynthesizer(provider=default_provider, fish_api_key=fish_api_key)
    return _synthesizer

def synthesize_speech(
    text: str,
    output_path: str,
    language: str = "en",
    provider: Optional[Literal["auto", "fish_audio", "coqui"]] = None,
    **kwargs
) -> str:
    """
    Convenience function for speech synthesis

    Args:
        text: Text to synthesize
        output_path: Output file path
        language: Target language
        provider: Override default provider
        **kwargs: Provider-specific parameters

    Returns:
        Path to generated audio
    """
    synthesizer = get_synthesizer(provider=provider)
    return synthesizer.synthesize(text, output_path, language, **kwargs)
