"""Exercise video cue, action and silence preflight using local synthetic data."""

import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import wave

import pytest

from conftest import ROOT


AGENT = ROOT / "Meta-Brain" / "agents" / "video-production-agent"
SCRIPT = AGENT / "tools" / "check_timeline.py"
SPEC = importlib.util.spec_from_file_location("video_timeline", SCRIPT)
timeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(timeline)


def example():
    return json.loads((AGENT / "examples" / "timeline.json").read_text(encoding="utf-8"))


def test_example_has_no_errors_or_long_gaps():
    report = timeline.check_timeline(example(), 3)
    assert report["errors"] == []
    assert report["planned_speech_gaps"] == []


def test_gaps_at_threshold_are_reported_with_opening_and_tail():
    data = {"duration": 12, "speech": [{"id": "line", "start": 3, "end": 9}],
            "visuals": [], "actions": [], "cuts": []}
    gaps = timeline.check_timeline(data, 3)["planned_speech_gaps"]
    assert gaps == [{"start": 0.0, "end": 3.0, "duration": 3.0},
                    {"start": 9.0, "end": 12.0, "duration": 3.0}]


def test_overlapping_speech_wrong_visual_and_cut_inside_action_are_errors():
    data = example()
    data["speech"][2]["start"] = 9.9
    data["cuts"].append(9)
    report = timeline.check_timeline(data, 3)
    assert any("overlaps" in error for error in report["errors"])
    assert any("does not cover" in error for error in report["errors"])
    assert any("interrupts action 'writing'" in error for error in report["errors"])


def test_action_boundary_is_not_a_cut_inside_the_action():
    data = example()
    data["cuts"].extend([8.0, 11.0])
    assert timeline.check_timeline(data, 3)["errors"] == []


@pytest.mark.parametrize("value", [True, float("nan"), -1])
def test_invalid_duration_is_rejected(value):
    data = example()
    data["duration"] = value
    with pytest.raises(ValueError):
        timeline.check_timeline(data, 3)


def test_cli_reports_unsafe_timing(tmp_path):
    data = example()
    data["cuts"].append(9)
    source = tmp_path / "timeline.json"
    source.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), str(source)],
                            text=True, capture_output=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["errors"]


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_audio_silence_is_measured(tmp_path):
    path = tmp_path / "audio.wav"
    rate = 8000
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(struct.pack("<h", 8000) * rate)
        audio.writeframes(b"\0\0" * (rate * 4))
        audio.writeframes(struct.pack("<h", 8000) * rate)
    gaps = timeline.measure_audio_gaps(path, 3)
    assert len(gaps) == 1
    assert gaps[0]["start"] == pytest.approx(1, abs=0.01)
    assert gaps[0]["end"] == pytest.approx(5, abs=0.01)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_audio_silence_threshold_distinguishes_short_and_long_gaps(tmp_path):
    path = tmp_path / "threshold.wav"
    rate = 8000
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        voice = struct.pack("<h", 8000) * rate
        audio.writeframes(voice)
        audio.writeframes(b"\0\0" * (rate * 299 // 100))
        audio.writeframes(voice)
        audio.writeframes(b"\0\0" * (rate * 3))
        audio.writeframes(voice)
    gaps = timeline.measure_audio_gaps(path, 3)
    assert len(gaps) == 1
    assert gaps[0]["start"] == pytest.approx(4.99, abs=0.01)
    assert gaps[0]["end"] == pytest.approx(7.99, abs=0.01)


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="FFmpeg and FFprobe are not installed",
)
def test_cli_rejects_audio_that_ends_before_planned_speech(tmp_path):
    audio_path = tmp_path / "short.wav"
    with wave.open(str(audio_path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0\0" * 8000)
    source = tmp_path / "timeline.json"
    source.write_text(json.dumps(example()), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source), "--audio", str(audio_path)],
        text=True, capture_output=True,
    )
    assert result.returncode == 1
    assert "Audio ends before the last planned speech" in json.loads(result.stdout)["errors"]
