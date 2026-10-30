"""Reusable demo gates: neutral lifecycle fixtures and independently generated media."""

import copy
import importlib.util
import json
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import ROOT


AGENT = ROOT / "Meta-Brain" / "agents" / "video-production-agent"
SCRIPT = AGENT / "tools" / "check_demo.py"
SPEC = importlib.util.spec_from_file_location("video_demo", SCRIPT)
demo = importlib.util.module_from_spec(SPEC)
with patch.object(sys, "path", [str(SCRIPT.parent), *sys.path]):
    SPEC.loader.exec_module(demo)

MEDIA_AVAILABLE = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
needs_media = pytest.mark.skipif(not MEDIA_AVAILABLE, reason="FFmpeg/FFprobe are not installed")


def example(name: str = "demo-accepted.json") -> dict:
    return json.loads((AGENT / "examples" / name).read_text(encoding="utf-8"))


def replace(data: dict, path: str, value: object) -> None:
    parts = path.split(".")
    target = data
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    key = int(parts[-1]) if isinstance(target, list) else parts[-1]
    target[key] = value


def audio_file(path: Path, data: dict, silence: tuple = ()) -> Path:
    rate = 8000
    samples = []
    for frame in range(round(data["duration"] * rate)):
        moment = frame / rate
        voiced = any(cue["start"] <= moment < cue["end"] for cue in data["speech"])
        muted = any(start <= moment < end for start, end in silence)
        samples.append(round(8000 * math.sin(2 * math.pi * 440 * moment)) if voiced and not muted else 0)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return path


def cli(tmp_path: Path, data: dict, *arguments: str) -> subprocess.CompletedProcess:
    source = tmp_path / "contract.json"
    source.write_text(json.dumps(data), encoding="utf-8")
    before = source.read_bytes()
    result = subprocess.run([sys.executable, str(SCRIPT), str(source), *arguments],
                            capture_output=True, text=True)
    assert source.read_bytes() == before
    return result


def test_accepted_fixture_and_legacy_checker_agree() -> None:
    data = example()
    before = copy.deepcopy(data)
    report = demo.check_demo(data)
    assert report["errors"] == []
    assert report["final_verified"] is False
    assert report["human_playback_review"] == "not_established"
    assert report["declared_claims_checked"] == 2
    assert data == before


def test_rejected_moving_launch_is_not_accepted_as_legacy_gap_warning() -> None:
    data = example("demo-rejected.json")
    assert demo.timeline.check_timeline(data, 3)["errors"] == []
    assert demo.timeline.check_timeline(data, 3)["planned_speech_gaps"] == []
    assert any("planned launch gap" in error for error in demo.check_demo(data)["errors"])


def test_profile_is_per_brief_not_a_hardcoded_launch_constant() -> None:
    data = example("demo-rejected.json")
    data["profile"]["launch_silence_cap_seconds"] = 2.5
    assert demo.check_demo(data)["errors"] == []


def test_current_recipe_is_loaded_from_behavior_driving_files() -> None:
    for name in ("README.md", "instructions.md", "production_workflow.md"):
        assert "[demo_recipe.md](demo_recipe.md)" in (AGENT / name).read_text(encoding="utf-8")
    recipe = (AGENT / "demo_recipe.md").read_text(encoding="utf-8")
    assert r"tools\check_demo.py" in recipe
    assert "application adapter" in recipe.lower()
    assert "human_playback_review: not_established" in recipe
    assert (AGENT / "instructions.md").stat().st_size < 20000


@pytest.mark.parametrize(("path", "value", "message"), [
    ("actions.0.start", 2.9, "before the spoken purpose"),
    ("steps.0.title_at", 3.9, "title changes"),
    ("speech.1.start", 2.9, "previous explanation"),
    ("steps.0.response.readable_at", 8.2, "readable recognition"),
    ("steps.0.response.writing_end", 8.35, "too late"),
    ("steps.0.claims.1.visible_at", 9.6, "visible supporting evidence"),
    ("steps.0.response.structured_at", 9.15, "visible supporting evidence"),
    ("steps.0.response.ready_at", 10, "protected action"),
    ("steps.1.response.confirmed_at", 16.2, "before full confirmation"),
    ("profile.closing_cap_seconds", 2, "Closing narration"),
    ("profile.duration_cap_seconds", 20, "Complete runtime"),
    ("profile.opening_cap_seconds", 4, "Opening before"),
    ("profile.confirmation_to_end_cap_seconds", 3, "Confirmation-to-end"),
    ("profile.confirmation_to_closing_cap_seconds", 0.05, "follow confirmation"),
    ("duration", 22, "Final hold"),
    ("steps.1.previous", "opening", "narrative chain"),
    ("cuts", [5], "interrupts action"),
    ("review_pauses", [{"id": "not-an-exemption", "start": 6, "end": 7}], "cannot exempt"),
])
def test_semantic_negative_controls(path: str, value: object, message: str) -> None:
    data = example()
    replace(data, path, value)
    assert any(message in error for error in demo.check_demo(data)["errors"])


@pytest.mark.parametrize(("path", "value"), [
    ("schema_version", True),
    ("audio_content", None),
    ("duration", float("nan")),
    ("steps", []),
    ("steps.0.id", "send"),
    ("steps.0.purpose_at", True),
    ("steps.0.title_at", "unknown"),
    ("steps.0.result", "missing"),
    ("steps.0.response.mode", "unknown"),
    ("steps.0.response.readable_at", -1),
    ("steps.0.claims", None),
    ("steps.0.claims.1.kind", "unknown"),
    ("steps.0.response.structured_at", None),
    ("profile.silence_min_seconds", 2),
    ("profile.silence_noise_db", float("inf")),
    ("profile.launch_silence_cap_seconds", False),
    ("profile.final_hold_min_seconds", 3),
    ("format.width", 0),
    ("format.fps", True),
])
def test_invalid_or_missing_evidence_is_not_a_pass(path: str, value: object) -> None:
    data = example()
    replace(data, path, value)
    with pytest.raises(ValueError):
        demo.check_demo(data)


def test_atomic_result_does_not_require_progressive_writing() -> None:
    data = example()
    data["steps"][0]["response"] = {
        "mode": "atomic", "readable_at": 7.6, "structured_at": 7.6, "ready_at": 8,
    }
    assert demo.check_demo(data)["errors"] == []
    data["steps"][0]["response"]["ready_at"] = 8.5
    assert any("atomic result" in error for error in demo.check_demo(data)["errors"])


def test_structured_arrival_budget_is_explicit_not_a_claim_timestamp() -> None:
    data = example()
    data["steps"][0]["response"]["structured_lag_cap_seconds"] = 0.6
    report = demo.check_demo(data)
    assert report["structured_budgets_checked"] == 1
    assert any("arrival budget" in error for error in report["errors"])


def test_next_action_cannot_interrupt_the_previous_unfinished_response() -> None:
    data = example()
    data["steps"][0]["response"]["ready_at"] = 15.2
    data["actions"][0]["end"] = 15.2
    assert any("interrupts the previous response" in error for error in demo.check_demo(data)["errors"])


def test_unmapped_confirmation_recap_is_rejected() -> None:
    data = example()
    data["speech"].append({"id": "extra-recap", "start": 15.1, "end": 15.9})
    assert any("no extra recap" in error for error in demo.check_demo(data)["errors"])


def test_deliberate_reading_does_not_waive_launches_or_allow_cuts() -> None:
    data = example()
    data["review_pauses"] = [{"id": "read-options", "start": 10, "end": 12}]
    assert demo.check_demo(data)["errors"] == []
    data["cuts"] = [11]
    assert any("deliberate review" in error for error in demo.check_demo(data)["errors"])


def test_cli_modes_and_persisted_json_are_truthful(tmp_path: Path) -> None:
    result = cli(tmp_path, example(), "--preflight", "--output", str(tmp_path / "report.json"))
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["status"] == "preflight_passed" and not report["final_verified"]
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == report
    assert not (tmp_path / "report.json").read_bytes().startswith(b"\xef\xbb\xbf")
    result = cli(tmp_path, example())
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid"
    assert cli(tmp_path, example("demo-rejected.json"), "--preflight").returncode == 1


def test_music_cannot_hide_missing_dry_voice_evidence(tmp_path: Path) -> None:
    data = example()
    data["audio_content"] = "mixed"
    result = cli(tmp_path, data, "--video", str(tmp_path / "not-even-opened.mp4"))
    assert result.returncode == 2
    assert "music can hide" in json.loads(result.stdout)["errors"][0]
    assert cli(tmp_path, data, "--preflight").returncode == 0


@pytest.mark.parametrize("output", [
    b"lavfi.silence_end=2",
    b"lavfi.silence_start=1\nlavfi.silence_start=2",
    b"lavfi.silence_start=2\nlavfi.silence_end=1",
    b"lavfi.silence_start=nan",
    b"lavfi.silence_start=garbage",
    b"lavfi.silence_start=21",
    b"lavfi.silence_start=2\nlavfi.silence_end=3\nlavfi.silence_start=1",
])
def test_malformed_audio_events_fail_closed(output: bytes) -> None:
    with pytest.raises(ValueError):
        demo.parse_silence(output, 20.5)


def test_trailing_silence_is_measured_to_eof() -> None:
    assert demo.parse_silence(b"lavfi.silence_start=16", 20.5) == [
        {"start": 16, "end": 20.5, "duration": 4.5},
    ]


@needs_media
def test_audio_passes_and_intentional_reading_is_not_a_launch(tmp_path: Path) -> None:
    data = example()
    data["review_pauses"] = [{"id": "read-options", "start": 10, "end": 12}]
    audio = audio_file(tmp_path / "good.wav", data, ((10, 12),))
    result = cli(tmp_path, data, "--preflight", "--narration", str(audio))
    report = json.loads(result.stdout)
    assert result.returncode == 0, report
    assert len(report["media_checks"][0]["launches"]) == len(data["steps"])
    assert report["media_checks"][0]["launches"][1]["signal_silence_seconds"] == pytest.approx(1.1, abs=0.01)


@needs_media
def test_decoded_audio_rejects_bad_launch_despite_valid_cue_metadata(tmp_path: Path) -> None:
    data = example()
    assert demo.check_demo(data)["errors"] == []
    audio = audio_file(tmp_path / "bad.wav", data, ((6, 8.3),))
    result = cli(tmp_path, data, "--preflight", "--narration", str(audio))
    report = json.loads(result.stdout)
    assert result.returncode == 1, report
    assert any("decoded launch silence" in error for error in report["errors"])
    assert report["media_checks"][0]["launches"][0]["signal_silence_seconds"] == pytest.approx(2.3, abs=0.01)


@needs_media
def test_internal_bridge_silence_is_checked_without_waiting_for_its_end(tmp_path: Path) -> None:
    data = example()
    audio = audio_file(tmp_path / "internal.wav", data, ((5, 7),))
    result = cli(tmp_path, data, "--preflight", "--narration", str(audio))
    assert result.returncode == 1
    assert any("decoded launch silence" in error for error in json.loads(result.stdout)["errors"])


def test_missing_tool_and_endpoint_measurement_are_errors() -> None:
    with patch.object(demo.subprocess, "run", side_effect=FileNotFoundError):
        with pytest.raises(ValueError, match="required"):
            demo._run(["ffmpeg"])
    with patch.object(demo.subprocess, "run",
                      side_effect=subprocess.CalledProcessError(1, ["ffmpeg"], stderr=b"decode failed")):
        with pytest.raises(ValueError, match="decode failed"):
            demo._run(["ffmpeg"])
    with patch.object(demo, "_run", return_value=b""):
        with pytest.raises(ValueError, match="empty or unmeasured"):
            demo._endpoint(Path("movie.mp4"), False, example()["profile"])


@needs_media
@pytest.mark.parametrize("colour", ["white", "black"])
def test_final_export_decode_format_and_endpoints(tmp_path: Path, colour: str) -> None:
    data = example()
    data["format"].update({"width": 160, "height": 90})
    audio = audio_file(tmp_path / "voice.wav", data)
    movie = tmp_path / "movie.mp4"
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c={colour}:s=160x90:r=25",
        "-i", str(audio), "-t", str(data["duration"]), "-c:v", "libx264",
        "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-ar", "48000", "-ac", "2", str(movie),
    ], check=True, capture_output=True)
    result = cli(tmp_path, data, "--video", str(movie), "--narration", str(audio))
    report = json.loads(result.stdout)
    assert result.returncode == (0 if colour == "white" else 1), report
    assert report["final_verified"] is (colour == "white")
    assert report["media_checks"][1]["full_decode"] == "passed"
    assert report["human_playback_review"] == "not_established"
    if colour == "black":
        assert any("black endpoint" in error for error in report["errors"])
    else:
        data["format"]["width"] = 320
        result = cli(tmp_path, data, "--video", str(movie))
        assert result.returncode == 1
        assert any("picture format" in error for error in json.loads(result.stdout)["errors"])
