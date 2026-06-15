from unittest.mock import patch, MagicMock
import pytest
from engines.splitter.exporters.ffmpeg_exporter import export_song_segment
from engines.splitter.models.exceptions import SplitError


@patch("engines.splitter.exporters.ffmpeg_exporter.run_ffmpeg_export")
def test_export_song_segment_copy_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    
    # Matching formats allow copy attempt
    export_song_segment("source.mp3", "output.mp3", 0, 10, "Test Track", "mp3")
    
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "copy" in cmd


@patch("engines.splitter.exporters.ffmpeg_exporter.run_ffmpeg_export")
def test_export_song_segment_reencode_fallback(mock_run):
    # First call (copy) fails, second call (reencode) succeeds
    mock_run.side_effect = [
        MagicMock(returncode=1),
        MagicMock(returncode=0)
    ]
    
    export_song_segment("source.mp3", "output.mp3", 0, 10, "Test Track", "mp3")
    
    assert mock_run.call_count == 2
    cmd2 = mock_run.call_args_list[1][0][0]
    assert "libmp3lame" in cmd2


@patch("engines.splitter.exporters.ffmpeg_exporter.run_ffmpeg_export")
def test_export_song_segment_different_formats(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    
    # Different formats should skip copy attempt
    export_song_segment("source.wav", "output.mp3", 0, 10, "Test Track", "mp3")
    
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "libmp3lame" in cmd


@patch("engines.splitter.exporters.ffmpeg_exporter.run_ffmpeg_export")
def test_export_song_segment_failure(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr="ffmpeg error")
    
    with pytest.raises(SplitError) as exc:
        export_song_segment("source.wav", "output.mp3", 0, 10, "Test Track", "mp3")
        
    assert "Gagal memproses lagu" in str(exc.value)
