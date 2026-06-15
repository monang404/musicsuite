import os
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from engines.splitter.service import SplitterService
from engines.splitter.models.exceptions import SplitError
from engines.timestamp.models.track import Track


@pytest.fixture
def service():
    srv = SplitterService()
    srv.check_ffmpeg = MagicMock(return_value=True)
    return srv


@pytest.fixture
def sample_tracks():
    return [
        Track(index=1, start_seconds=0, end_seconds=10, title="Song 1", raw_line="00:00 Song 1", line_number=1),
        Track(index=2, start_seconds=10, end_seconds=20, title="Song 2", raw_line="00:10 Song 2", line_number=2),
    ]


@patch("engines.splitter.service.export_song_segment")
def test_split_audio_success(mock_export, service, sample_tracks, tmp_path):
    source = tmp_path / "source.mp3"
    source.write_text("dummy")
    
    output_dir = tmp_path / "output"
    
    result = service.split_audio(
        source_file=source,
        songs=sample_tracks,
        output_dir=output_dir,
        output_format="mp3",
        naming_pattern="{index:02d} {title}"
    )
    
    assert len(result) == 2
    assert "01 Song 1.mp3" in result[0]
    assert "02 Song 2.mp3" in result[1]
    assert mock_export.call_count == 2


def test_split_audio_missing_source(service, sample_tracks, tmp_path):
    with pytest.raises(SplitError) as exc:
        service.split_audio(
            source_file=tmp_path / "nonexistent.mp3",
            songs=sample_tracks,
            output_dir=tmp_path
        )
    assert "tidak ditemukan" in str(exc.value)


def test_split_audio_ffmpeg_missing(service, sample_tracks, tmp_path):
    service.check_ffmpeg.return_value = False
    source = tmp_path / "source.mp3"
    source.write_text("dummy")
    
    with pytest.raises(SplitError) as exc:
        service.split_audio(
            source_file=source,
            songs=sample_tracks,
            output_dir=tmp_path
        )
    assert "FFmpeg tidak ditemukan" in str(exc.value)


@patch("engines.splitter.service.export_song_segment")
def test_split_audio_cancel(mock_export, service, sample_tracks, tmp_path):
    source = tmp_path / "source.mp3"
    source.write_text("dummy")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    cancel_mock = MagicMock(side_effect=[False, True])  # Cancel on the second song
    
    with pytest.raises(SplitError) as exc:
        service.split_audio(
            source_file=source,
            songs=sample_tracks,
            output_dir=output_dir,
            cancel_check=cancel_mock
        )
    assert "cancelled by user" in str(exc.value).lower()
