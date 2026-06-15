import pytest
from engines.splitter.ffmpeg.builder import (
    sanitize_filename,
    format_ffmpeg_time,
    build_copy_command,
    build_reencode_command,
)


def test_sanitize_filename():
    assert sanitize_filename("valid_name") == "valid_name"
    assert sanitize_filename("invalid<name>") == "invalid_name_"
    assert sanitize_filename("name:with?special|chars") == "name_with_special_chars"
    assert sanitize_filename("  leading_and_trailing  ") == "leading_and_trailing"


def test_format_ffmpeg_time():
    assert format_ffmpeg_time(0) == "00:00:00"
    assert format_ffmpeg_time(45) == "00:00:45"
    assert format_ffmpeg_time(125) == "00:02:05"
    assert format_ffmpeg_time(3600) == "01:00:00"
    assert format_ffmpeg_time(3665) == "01:01:05"


def test_build_copy_command():
    cmd = build_copy_command("input.mp3", "output.mp3", 10, 20)
    assert "-ss" in cmd
    assert "00:00:10" in cmd
    assert "-to" in cmd
    assert "00:00:20" in cmd
    assert "copy" in cmd


def test_build_reencode_command():
    cmd = build_reencode_command("input.wav", "output.mp3", 0, 10, output_format="mp3", bitrate="192k")
    assert "-acodec" in cmd
    assert "libmp3lame" in cmd
    assert "-ab" in cmd
    assert "192k" in cmd
    assert "output.mp3" == cmd[-1]
