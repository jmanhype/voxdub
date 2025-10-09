"""
Video Processing Utilities using FFmpeg
Handles video/audio extraction, merging, and manipulation
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """Professional FFmpeg-based video processing"""
    
    def __init__(self):
        """Initialize video processor and validate FFmpeg"""
        self._validate_ffmpeg()
    
    def _validate_ffmpeg(self):
        """Check if FFmpeg is installed"""
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg and add it to PATH."
            )
        
        # Check FFmpeg version
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            version_line = result.stdout.split('\n')[0]
            logger.info(f"✅ {version_line}")
        except Exception as e:
            logger.warning(f"Could not check FFmpeg version: {e}")
    
    def extract_audio(
        self,
        video_path: str,
        audio_output_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
        audio_format: str = "wav"
    ) -> str:
        """
        Extract audio from video file
        
        Args:
            video_path: Input video file
            audio_output_path: Output audio file path
            sample_rate: Audio sample rate (Hz)
            channels: Number of audio channels (1=mono, 2=stereo)
            audio_format: Output audio format
        
        Returns:
            Path to extracted audio
        """
        try:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video not found: {video_path}")
            
            # Ensure output directory exists
            Path(audio_output_path).parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🎵 Extracting audio from video...")
            logger.info(f"   Input: {Path(video_path).name}")
            
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le" if audio_format == "wav" else "libmp3lame",
                "-ar", str(sample_rate),
                "-ac", str(channels),
                audio_output_path,
                "-y"  # Overwrite output
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not Path(audio_output_path).exists():
                raise FileNotFoundError("Audio extraction failed")
            
            file_size = Path(audio_output_path).stat().st_size / 1024  # KB
            logger.info(f"✅ Audio extracted successfully")
            logger.info(f"   Output: {Path(audio_output_path).name}")
            logger.info(f"   Size: {file_size:.1f} KB")
            
            return audio_output_path
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"❌ FFmpeg audio extraction failed: {error_msg}")
            raise RuntimeError(f"Audio extraction error: {error_msg}")
    
    def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        video_codec: str = "copy",
        audio_codec: str = "aac"
    ) -> str:
        """
        Merge audio with video
        
        Args:
            video_path: Input video file
            audio_path: Input audio file
            output_path: Output video path
            video_codec: Video codec ('copy' preserves original)
            audio_codec: Audio codec for output
        
        Returns:
            Path to merged video
        """
        try:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video not found: {video_path}")
            
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio not found: {audio_path}")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            logger.info("🎬 Merging audio with video...")
            
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", video_codec,
                "-c:a", audio_codec,
                "-map", "0:v:0",  # Video from first input
                "-map", "1:a:0",  # Audio from second input
                "-shortest",  # Match shortest stream
                output_path,
                "-y"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not Path(output_path).exists():
                raise FileNotFoundError("Video merging failed")
            
            file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✅ Audio and video merged successfully")
            logger.info(f"   Output: {Path(output_path).name}")
            logger.info(f"   Size: {file_size:.1f} MB")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"❌ FFmpeg merge failed: {error_msg}")
            raise RuntimeError(f"Video merge error: {error_msg}")
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Get video file information
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dictionary with video metadata
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            return json.loads(result.stdout)
            
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}

# Global instance
_video_processor = None

def get_video_processor() -> VideoProcessor:
    """Get or create global video processor"""
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor

def extract_audio(video_path: str, audio_output_path: str) -> str:
    """Convenience function for audio extraction"""
    processor = get_video_processor()
    return processor.extract_audio(video_path, audio_output_path)

def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Convenience function for audio/video merging"""
    processor = get_video_processor()
    return processor.merge_audio_video(video_path, audio_path, output_path)
