"""
Fish Speech (OpenAudio S1) TTS Provider
State-of-the-art TTS with voice cloning and emotion support
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import soundfile as sf
import numpy as np
from .base import TTSProvider

logger = logging.getLogger(__name__)


class FishSpeechProvider(TTSProvider):
    """
    Fish Speech TTS Provider

    Features:
    - Voice cloning from reference audio
    - Emotion and tone markers (angry, sad, excited, whispering, etc.)
    - Streaming and non-streaming modes
    - Multilingual support (English, Chinese, Japanese)
    - SOTA quality (WER: 0.008, CER: 0.004)
    - #1 on TTS-Arena2 benchmark
    """

    # Supported emotion markers
    EMOTION_MARKERS = [
        "neutral",
        "happy",
        "sad",
        "angry",
        "fearful",
        "disgusted",
        "surprised",
        "excited",
        "whispering",
        "shouting"
    ]

    # Language codes mapping
    LANGUAGE_MAP = {
        "en": "english",
        "zh": "chinese",
        "ja": "japanese",
        "zh-CN": "chinese",
        "zh-TW": "chinese",
        "en-US": "english",
        "en-GB": "english"
    }

    def __init__(
        self,
        device: str = "cuda",
        api_url: str = "http://localhost:8080",
        model: str = "s1-mini",
        compile_mode: bool = False,
        max_new_tokens: int = 1024,
        top_p: float = 0.7,
        temperature: float = 0.7,
        repetition_penalty: float = 1.2
    ):
        """
        Initialize Fish Speech TTS provider

        Args:
            device: Computation device (cuda/cpu)
            api_url: Fish Speech API server URL
            model: Model variant (s1 or s1-mini)
            compile_mode: Enable torch.compile for faster inference
            max_new_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            temperature: Sampling temperature
            repetition_penalty: Repetition penalty factor
        """
        super().__init__(device)
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.compile_mode = compile_mode
        self.max_new_tokens = max_new_tokens
        self.top_p = top_p
        self.temperature = temperature
        self.repetition_penalty = repetition_penalty
        self.reference_voices: Dict[str, str] = {}

        logger.info(f"Initialized Fish Speech TTS ({model}) on {device}")
        logger.info(f"API URL: {self.api_url}")

    def load_model(self, model_name: Optional[str] = None) -> Any:
        """
        Fish Speech models are loaded on the server side
        This method validates the API connection
        """
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=5
            )
            if response.status_code == 200:
                logger.info("Fish Speech API connection validated")
                return True
            else:
                raise ConnectionError(f"API health check failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Fish Speech API: {e}")
            raise ConnectionError(
                f"Fish Speech API not available at {self.api_url}. "
                "Please ensure the Fish Speech server is running."
            )

    def add_reference_voice(
        self,
        voice_id: str,
        audio_path: str,
        text: Optional[str] = None
    ) -> bool:
        """
        Add a reference voice for voice cloning

        Args:
            voice_id: Unique identifier for the voice
            audio_path: Path to reference audio file
            text: Optional transcript of the reference audio

        Returns:
            True if successful
        """
        try:
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Reference audio not found: {audio_path}")

            with open(audio_path, 'rb') as f:
                files = {'audio': f}
                data = {'voice_id': voice_id}
                if text:
                    data['text'] = text

                response = requests.post(
                    f"{self.api_url}/v1/references/add",
                    files=files,
                    data=data,
                    timeout=30
                )

            if response.status_code == 200:
                self.reference_voices[voice_id] = audio_path
                logger.info(f"Reference voice '{voice_id}' added successfully")
                return True
            else:
                logger.error(f"Failed to add reference voice: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error adding reference voice: {e}")
            return False

    def list_reference_voices(self) -> List[Dict[str, Any]]:
        """
        List available reference voices

        Returns:
            List of reference voice information
        """
        try:
            response = requests.get(
                f"{self.api_url}/v1/references/list",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to list reference voices: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing reference voices: {e}")
            return []

    def _format_text_with_emotion(self, text: str, emotion: Optional[str] = None) -> str:
        """
        Format text with emotion markers

        Args:
            text: Input text
            emotion: Emotion marker

        Returns:
            Formatted text with emotion tags
        """
        if emotion and emotion.lower() in self.EMOTION_MARKERS:
            return f"[{emotion.lower()}]{text}[/{emotion.lower()}]"
        return text

    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0,
        emotion: Optional[str] = None,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        streaming: bool = False,
        **kwargs
    ) -> str:
        """
        Synthesize speech using Fish Speech

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Target language code
            speaker: Reference voice ID (if using pre-registered voice)
            speed: Speech speed multiplier
            emotion: Emotion marker (angry, sad, excited, etc.)
            reference_audio: Path to reference audio for voice cloning
            reference_text: Transcript of reference audio
            streaming: Enable streaming mode
            **kwargs: Additional parameters

        Returns:
            Path to generated audio file
        """
        try:
            if not text or not text.strip():
                raise ValueError("Empty text provided for synthesis")

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Format text with emotion markers
            formatted_text = self._format_text_with_emotion(text, emotion)

            # Map language code
            lang = self.LANGUAGE_MAP.get(language.lower(), "english")

            logger.info(f"Synthesizing speech using Fish Speech TTS")
            logger.info(f"Language: {lang}, Text length: {len(text)} characters")
            if emotion:
                logger.info(f"Emotion: {emotion}")

            # Prepare request payload
            payload = {
                "text": formatted_text,
                "language": lang,
                "streaming": streaming,
                "max_new_tokens": self.max_new_tokens,
                "top_p": self.top_p,
                "temperature": self.temperature,
                "repetition_penalty": self.repetition_penalty
            }

            # Add reference voice if specified
            files = None
            if reference_audio and Path(reference_audio).exists():
                files = {'reference_audio': open(reference_audio, 'rb')}
                if reference_text:
                    payload['reference_text'] = reference_text
                logger.info(f"Using reference audio for voice cloning")
            elif speaker and speaker in self.reference_voices:
                payload['voice_id'] = speaker
                logger.info(f"Using registered voice: {speaker}")

            # Make API request
            if streaming:
                audio_data = self._synthesize_streaming(payload, files)
            else:
                audio_data = self._synthesize_non_streaming(payload, files)

            # Close file handle if opened
            if files:
                files['reference_audio'].close()

            # Save audio to file
            if isinstance(audio_data, bytes):
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
            elif isinstance(audio_data, np.ndarray):
                sf.write(output_path, audio_data, 24000)  # Fish Speech default sample rate
            else:
                raise ValueError(f"Unexpected audio data type: {type(audio_data)}")

            if not Path(output_path).exists():
                raise FileNotFoundError("TTS failed to generate audio file")

            file_size = Path(output_path).stat().st_size / 1024
            logger.info(f"Fish Speech synthesis complete ({file_size:.1f} KB)")

            return output_path

        except Exception as e:
            logger.error(f"Fish Speech TTS synthesis failed: {e}")
            raise RuntimeError(f"Fish Speech TTS error: {e}")

    def _synthesize_non_streaming(
        self,
        payload: Dict[str, Any],
        files: Optional[Dict] = None
    ) -> bytes:
        """
        Non-streaming synthesis

        Args:
            payload: Request payload
            files: Optional file attachments

        Returns:
            Audio data as bytes
        """
        try:
            response = requests.post(
                f"{self.api_url}/v1/tts",
                json=payload if not files else None,
                data=payload if files else None,
                files=files,
                timeout=60
            )

            if response.status_code == 200:
                return response.content
            else:
                raise RuntimeError(f"API request failed: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request error: {e}")

    def _synthesize_streaming(
        self,
        payload: Dict[str, Any],
        files: Optional[Dict] = None
    ) -> bytes:
        """
        Streaming synthesis

        Args:
            payload: Request payload
            files: Optional file attachments

        Returns:
            Audio data as bytes
        """
        try:
            audio_chunks = []

            with requests.post(
                f"{self.api_url}/v1/tts",
                json=payload if not files else None,
                data=payload if files else None,
                files=files,
                stream=True,
                timeout=60
            ) as response:
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            audio_chunks.append(chunk)
                else:
                    raise RuntimeError(f"API request failed: {response.status_code}")

            return b''.join(audio_chunks)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Streaming API request error: {e}")

    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return ["en", "zh", "ja", "zh-CN", "zh-TW", "en-US", "en-GB"]

    def get_available_emotions(self) -> List[str]:
        """Get available emotion markers"""
        return self.EMOTION_MARKERS.copy()

    def cleanup(self):
        """Clean up Fish Speech resources"""
        self.reference_voices.clear()
        logger.info("Fish Speech provider cleaned up")
