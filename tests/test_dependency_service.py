import unittest
from unittest.mock import patch, MagicMock
from services.dependency_service import DependencyService

class TestDependencyService(unittest.TestCase):
    def setUp(self):
        self.service = DependencyService()

    @patch('subprocess.run')
    def test_check_ffmpeg_success(self, mock_run):
        # Setup mock for successful run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.service.check_ffmpeg()
        
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["ffmpeg", "-version"],
            stdout=-1, # subprocess.PIPE is -1
            stderr=-1,
            text=True,
            shell=False,
            check=False
        )

    @patch('subprocess.run')
    def test_check_ffmpeg_failure(self, mock_run):
        # Setup mock for failed run (e.g., non-zero exit code)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = self.service.check_ffmpeg()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_check_ffmpeg_not_found(self, mock_run):
        # Setup mock for FileNotFoundError
        mock_run.side_effect = FileNotFoundError

        result = self.service.check_ffmpeg()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_check_ytdlp_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.service.check_ytdlp()
        
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["yt-dlp", "--version"],
            stdout=-1,
            stderr=-1,
            text=True,
            shell=False,
            check=False
        )

    @patch('subprocess.run')
    def test_check_ytdlp_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError

        result = self.service.check_ytdlp()
        self.assertFalse(result)

    @patch('services.dependency_service.DependencyService.check_ffmpeg')
    @patch('services.dependency_service.DependencyService.check_ytdlp')
    def test_get_dependency_status(self, mock_ytdlp, mock_ffmpeg):
        mock_ffmpeg.return_value = True
        mock_ytdlp.return_value = False

        status = self.service.get_dependency_status()
        
        self.assertEqual(status, {
            "ffmpeg": True,
            "ytdlp": False
        })
        mock_ffmpeg.assert_called_once()
        mock_ytdlp.assert_called_once()

if __name__ == '__main__':
    unittest.main()
