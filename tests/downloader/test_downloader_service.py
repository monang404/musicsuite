import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from engines.downloader.service import DownloaderService
from engines.downloader.models.exceptions import DownloadError

@patch("engines.downloader.providers.youtube.yt_dlp.YoutubeDL")
def test_get_video_info_success(mock_ytdl):
    mock_instance = MagicMock()
    mock_ytdl.return_value.__enter__.return_value = mock_instance
    
    mock_instance.extract_info.return_value = {
        "title": "Test Audio",
        "duration": 120,
        "thumbnail": "http://example.com/thumb.jpg",
        "id": "12345",
        "description": "Test description",
        "chapters": [],
    }
    
    result = DownloaderService.get_video_info("http://youtube.com/watch?v=12345")
    
    assert result["title"] == "Test Audio"
    assert result["duration"] == 120
    mock_instance.extract_info.assert_called_once_with("http://youtube.com/watch?v=12345", download=False)

@patch("engines.downloader.providers.youtube.yt_dlp.YoutubeDL")
def test_get_video_info_error(mock_ytdl):
    mock_instance = MagicMock()
    mock_ytdl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.side_effect = Exception("Failed")
    
    with pytest.raises(DownloadError) as exc_info:
        DownloaderService.get_video_info("http://youtube.com/watch?v=12345")
    
    assert "Gagal mengambil info video" in str(exc_info.value)

@patch("engines.downloader.providers.youtube.yt_dlp.YoutubeDL")
@patch("engines.downloader.providers.youtube.Path.exists")
def test_download_audio_success(mock_exists, mock_ytdl, tmp_path):
    mock_instance = MagicMock()
    mock_ytdl.return_value.__enter__.return_value = mock_instance
    
    mock_instance.extract_info.return_value = {
        "title": "Test Audio"
    }
    
    mock_exists.return_value = True
    
    # Run download
    out_dir = tmp_path / "downloads"
    out_dir.mkdir()
    
    result = DownloaderService.download_audio("http://youtube.com/watch?v=12345", output_dir=out_dir)
    
    expected_path = str(out_dir / "Test Audio.mp3")
    assert result == expected_path
    mock_instance.extract_info.assert_called_once()
