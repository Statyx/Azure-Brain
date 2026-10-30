"""Review measured narration, visual, action and optional audio-silence timings."""

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _intervals(value, label, duration):
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    result = []
    seen = set()
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError(f"{label} entries must be objects")
        name = entry.get("id")
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError(f"{label} entries require unique, nonempty IDs")
        start = _number(entry.get("start"), f"{label}.{name}.start")
        end = _number(entry.get("end"), f"{label}.{name}.end")
        if not 0 <= start < end <= duration:
            raise ValueError(f"{label}.{name} must satisfy 0 <= start < end <= duration")
        seen.add(name)
        result.append({**entry, "start": start, "end": end})
    return result


def check_timeline(data, threshold):
    if not isinstance(data, dict):
        raise ValueError("timeline must be a JSON object")
    duration = _number(data.get("duration"), "duration")
    threshold = _number(threshold, "gap threshold")
    if duration <= 0 or threshold <= 0:
        raise ValueError("duration and gap threshold must be positive")
    speech = sorted(_intervals(data.get("speech"), "speech", duration), key=lambda x: x["start"])
    if not speech:
        raise ValueError("speech must contain at least one measured interval")
    visuals = {item["id"]: item for item in _intervals(data.get("visuals"), "visuals", duration)}
    actions = _intervals(data.get("actions"), "actions", duration)
    if not isinstance(data.get("cuts"), list):
        raise ValueError("cuts must be a list")
    cuts = [_number(value, "cut") for value in data["cuts"]]
    if any(not 0 <= cut <= duration for cut in cuts):
        raise ValueError("cuts must be within the timeline")

    errors = []
    gaps = []
    previous_end = 0.0
    previous_id = None
    for line in speech:
        start, end = line["start"], line["end"]
        if start < previous_end:
            errors.append(f"Speech '{line['id']}' overlaps '{previous_id}'")
        elif start - previous_end >= threshold:
            gaps.append({"start": previous_end, "end": start, "duration": start - previous_end})
        if end > previous_end:
            previous_end, previous_id = end, line["id"]
        visual_id = line.get("visual")
        if visual_id is not None:
            if not isinstance(visual_id, str) or visual_id not in visuals:
                raise ValueError(f"speech.{line['id']} refers to an unknown visual")
            visual = visuals[visual_id]
            if visual["start"] > start or visual["end"] < end:
                errors.append(f"Visual '{visual_id}' does not cover speech '{line['id']}'")
    if duration - previous_end >= threshold:
        gaps.append({"start": previous_end, "end": duration, "duration": duration - previous_end})
    for action in actions:
        for cut in cuts:
            if action["start"] < cut < action["end"]:
                errors.append(f"Cut at {cut:g}s interrupts action '{action['id']}'")
    return {"duration": duration, "errors": errors, "planned_speech_gaps": gaps}


def measure_audio_gaps(path, threshold):
    command = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", f"silencedetect=noise=-40dB:d={threshold:g}", "-f", "null", "-",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise ValueError("FFmpeg is required for --audio and was not found") from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"FFmpeg audio analysis failed: {exc.stderr.strip()}") from exc
    events = re.findall(r"silence_(start|end):\s*([0-9]+(?:\.[0-9]+)?)", result.stderr)
    gaps = []
    start = None
    for kind, value in events:
        time = float(value)
        if kind == "start":
            if start is not None:
                raise ValueError("FFmpeg produced unpaired silence-start events")
            start = time
        else:
            if start is None or time < start:
                raise ValueError("FFmpeg produced an invalid silence-end event")
            gaps.append({"start": start, "end": time, "duration": time - start})
            start = None
    if start is not None:
        raise ValueError("FFmpeg did not report the end of a detected silence")
    return gaps


def audio_duration(path):
    command = [
        "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
        "stream=duration:format=duration", "-of", "json", str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise ValueError("FFprobe is required for --audio and was not found") from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"FFprobe audio inspection failed: {exc.stderr.strip()}") from exc
    info = json.loads(result.stdout)
    streams = info.get("streams", [])
    if not streams:
        raise ValueError("The supplied file has no audio stream")
    raw_duration = streams[0].get("duration")
    if raw_duration in (None, "N/A"):
        raw_duration = info.get("format", {}).get("duration")
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError) as exc:
        raise ValueError("FFprobe did not report an audio duration") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("FFprobe reported an invalid audio duration")
    return duration


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timeline", type=Path)
    parser.add_argument("--gap-threshold", type=float, default=3.0)
    parser.add_argument("--audio", type=Path, help="Optional narration file for signal-silence detection")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.timeline.read_text(encoding="utf-8"))
        report = check_timeline(data, args.gap_threshold)
        if args.audio is not None:
            length = audio_duration(args.audio)
            report["audio_duration"] = length
            last_speech = max(line["end"] for line in data["speech"])
            if length > report["duration"] + 0.05:
                report["errors"].append("Audio lasts longer than the video timeline")
            if length + 0.05 < last_speech:
                report["errors"].append("Audio ends before the last planned speech")
            report["audio_signal_gaps"] = measure_audio_gaps(args.audio, args.gap_threshold)
    except (OSError, ValueError) as exc:
        print(f"Timeline preflight failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
