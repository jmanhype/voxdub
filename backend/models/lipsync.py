"""
Wav2Lip Lip Synchronization Module
Syncs lip movements with dubbed audio for realistic results
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LipSyncProcessor:
    """Professional Wav2Lip integration with error handling"""
    
    def __init__(self, wav2lip_path: Optional[Path] = None):
        """
        Initialize Wav2Lip processor
        
        Args:
            wav2lip_path: Path to Wav2Lip repository
        """
        self.wav2lip_path = wav2lip_path or Path("Wav2Lip")
        self.checkpoint_path = self.wav2lip_path / "checkpoints" / "wav2lip_gan.pth"
        self.inference_script = self.wav2lip_path / "inference.py"
        
        self._validate_setup()
    
    def _validate_setup(self):
        """Validate Wav2Lip installation"""
        if not self.wav2lip_path.exists():
            raise FileNotFoundError(
                f"Wav2Lip directory not found at {self.wav2lip_path}. "
                "Please clone the repository first."
            )
        
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"Wav2Lip checkpoint not found at {self.checkpoint_path}. "
                "Please download wav2lip_gan.pth and place it in Wav2Lip/checkpoints/"
            )
        
        if not self.inference_script.exists():
            raise FileNotFoundError(
                f"Wav2Lip inference script not found at {self.inference_script}"
            )
        
        logger.info("✅ Wav2Lip setup validated")
    
    def sync_lips(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        face_det_batch_size: int = 16,
        wav2lip_batch_size: int = 128,
        resize_factor: int = 1,
        crop_params: Optional[str] = None,
        box: Optional[str] = None,
        rotate: bool = False,
        nosmooth: bool = False
    ) -> str:
        """
        Synchronize lips with audio using Wav2Lip
        
        Args:
            video_path: Path to input video
            audio_path: Path to dubbed audio
            output_path: Path for output video
            face_det_batch_size: Batch size for face detection
            wav2lip_batch_size: Batch size for lip sync
            resize_factor: Video resize factor (1 = original)
            crop_params: Face crop parameters (optional)
            box: Bounding box coordinates (optional)
            rotate: Rotate video if needed
            nosmooth: Disable temporal smoothing
        
        Returns:
            Path to lip-synced video
        """
        try:
            # Validate inputs
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video not found: {video_path}")
            
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio not found: {audio_path}")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            logger.info("🎬 Starting Wav2Lip lip synchronization...")
            logger.info(f"   Video: {Path(video_path).name}")
            logger.info(f"   Audio: {Path(audio_path).name}")
            
            # Build command
            cmd = [
                sys.executable,  # Use current Python interpreter
                str(self.inference_script),
                "--checkpoint_path", str(self.checkpoint_path),
                "--face", str(video_path),
                "--audio", str(audio_path),
                "--outfile", str(output_path),
                "--face_det_batch_size", str(face_det_batch_size),
                "--wav2lip_batch_size", str(wav2lip_batch_size),
                "--resize_factor", str(resize_factor)
            ]
            
            # Add optional parameters
            if crop_params:
                cmd.extend(["--crop", crop_params])
            if box:
                cmd.extend(["--box", box])
            if rotate:
                cmd.append("--rotate")
            if nosmooth:
                cmd.append("--nosmooth")
            
            # Execute Wav2Lip
            logger.info("⏳ Processing (this may take a few minutes)...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.wav2lip_path)  # Run from Wav2Lip directory
            )
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"❌ Wav2Lip failed with exit code {result.returncode}")
                logger.error(f"Error output: {error_msg}")
                raise RuntimeError(f"Wav2Lip processing failed: {error_msg}")
            
            # Verify output
            if not Path(output_path).exists():
                raise FileNotFoundError(
                    f"Wav2Lip completed but output file not found: {output_path}"
                )
            
            file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✅ Lip synchronization complete!")
            logger.info(f"   Output: {Path(output_path).name}")
            logger.info(f"   Size: {file_size:.1f} MB")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Lip sync failed: {e}")
            raise RuntimeError(f"Lip synchronization error: {e}")
    
    def get_system_info(self) -> Dict:
        """Get Wav2Lip system information"""
        return {
            "wav2lip_path": str(self.wav2lip_path),
            "checkpoint_exists": self.checkpoint_path.exists(),
            "checkpoint_path": str(self.checkpoint_path),
            "inference_script_exists": self.inference_script.exists()
        }

# Global instance
_lip_sync_processor = None

def get_lip_sync_processor() -> LipSyncProcessor:
    """Get or create global lip sync processor"""
    global _lip_sync_processor
    if _lip_sync_processor is None:
        _lip_sync_processor = LipSyncProcessor()
    return _lip_sync_processor

def sync_lips(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Convenience function for lip synchronization
    
    Args:
        video_path: Input video path
        audio_path: Dubbed audio path
        output_path: Output video path
    
    Returns:
        Path to lip-synced video
    """
    processor = get_lip_sync_processor()
    return processor.sync_lips(video_path, audio_path, output_path)
