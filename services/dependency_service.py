import subprocess
import logging

class DependencyService:
    """
    Service responsible for verifying system-level dependencies required
    by the Music Suite application, primarily ffmpeg and yt-dlp.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_ffmpeg(self) -> bool:
        """
        Verifies if ffmpeg is available in the system PATH.
        Returns:
            bool: True if available, False otherwise.
        """
        try:
            # We use creationflags=subprocess.CREATE_NO_WINDOW on Windows to prevent popping up console windows, 
            # but for cross-platform compatibility we can omit it unless required.
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.warning("ffmpeg not found in system PATH.")
            return False
        except Exception as e:
            self.logger.error(f"Error checking ffmpeg: {e}")
            return False

    def check_ytdlp(self) -> bool:
        """
        Verifies if yt-dlp is available in the system PATH.
        Returns:
            bool: True if available, False otherwise.
        """
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.warning("yt-dlp not found in system PATH.")
            return False
        except Exception as e:
            self.logger.error(f"Error checking yt-dlp: {e}")
            return False

    def get_dependency_status(self) -> dict:
        """
        Returns the overall dependency status for core tools.
        Returns:
            dict: A dictionary mapping dependency names to boolean availability.
        """
        return {
            "ffmpeg": self.check_ffmpeg(),
            "ytdlp": self.check_ytdlp()
        }
