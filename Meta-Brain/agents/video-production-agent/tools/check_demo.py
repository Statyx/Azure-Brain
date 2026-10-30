"""Check measured interactive-demo handoffs and independently decoded launch silence."""

import argparse
import json
import math
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import check_timeline as timeline


PROFILE_KEYS = {
    "duration_cap_seconds", "opening_cap_seconds",
    "recognition_seconds", "progressive_lead_seconds", "launch_silence_cap_seconds",
    "closing_cap_seconds", "confirmation_to_closing_cap_seconds",
    "confirmation_to_end_cap_seconds", "final_hold_min_seconds", "final_hold_max_seconds",
    "gap_warning_seconds", "duration_tolerance_seconds", "silence_noise_db",
    "silence_min_seconds", "endpoint_min_luma", "endpoint_window_seconds",
}
FORMAT_KEYS = {"width", "height", "fps", "video_codec", "audio_codec",
               "audio_channels", "audio_sample_rate"}
EPSILON = 1e-6


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _entries(value: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return [_object(item, label) for item in value]


def _id(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _time(value: object, label: str, duration: float) -> float:
    number = timeline._number(value, label)
    if not 0 <= number <= duration:
        raise ValueError(f"{label} must be within the timeline")
    return number


def _reference(table: dict[str, Any], value: object, label: str) -> dict[str, Any]:
    key = _id(value, label)
    if key not in table:
        raise ValueError(f"{label} refers to an unknown ID: {key}")
    return table[key]


def _profile(value: object) -> dict[str, float]:
    raw = _object(value, "profile")
    if set(raw) != PROFILE_KEYS:
        raise ValueError(f"profile needs exactly these keys: {', '.join(sorted(PROFILE_KEYS))}")
    profile = {key: timeline._number(raw[key], f"profile.{key}") for key in PROFILE_KEYS}
    if any(value <= 0 for key, value in profile.items() if key != "silence_noise_db"):
        raise ValueError("profile limits must be positive")
    if not profile["silence_noise_db"] < 0:
        raise ValueError("silence_noise_db must be negative")
    if profile["silence_min_seconds"] > profile["launch_silence_cap_seconds"]:
        raise ValueError("silence_min_seconds must not exceed the launch silence cap")
    if profile["final_hold_min_seconds"] > profile["final_hold_max_seconds"]:
        raise ValueError("final hold minimum exceeds its maximum")
    if profile["endpoint_min_luma"] >= 255:
        raise ValueError("endpoint_min_luma must be below 255")
    return profile


def _format(value: object) -> dict[str, Any]:
    raw = _object(value, "format")
    if set(raw) != FORMAT_KEYS:
        raise ValueError(f"format needs exactly these keys: {', '.join(sorted(FORMAT_KEYS))}")
    for key in ("width", "height", "audio_channels", "audio_sample_rate"):
        number = timeline._number(raw[key], f"format.{key}")
        if number <= 0 or not number.is_integer():
            raise ValueError(f"format.{key} must be a positive integer")
    if timeline._number(raw["fps"], "format.fps") <= 0:
        raise ValueError("format.fps must be positive")
    for key in ("video_codec", "audio_codec"):
        _id(raw[key], f"format.{key}")
    return raw


def check_demo(data: object) -> dict[str, Any]:
    """Validate metadata; no media or human-review claim is made by this function."""
    data = _object(data, "demo")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if data.get("audio_content") not in ("voice_only", "mixed"):
        raise ValueError("audio_content must explicitly be voice_only or mixed")
    profile = _profile(data.get("profile"))
    _format(data.get("format"))
    report = timeline.check_timeline(data, profile["gap_warning_seconds"])
    duration = report["duration"]
    reviews = timeline._intervals(data.get("review_pauses"), "review_pauses", duration)
    speech = {item["id"]: item for item in data["speech"]}
    actions = {item["id"]: item for item in data["actions"]}
    steps = _entries(data.get("steps"), "steps")
    if not steps:
        raise ValueError("steps must contain every launch")
    errors = report["errors"]
    if duration > profile["duration_cap_seconds"] + EPSILON:
        errors.append("Complete runtime exceeds the brief's duration cap")
    launches = []
    seen = set()
    used_actions = set()
    chain = []
    previous_result = None
    previous_ready = None
    claim_count = 0
    budget_count = 0
    for step in steps:
        name = _id(step.get("id"), "step.id")
        if name in seen:
            raise ValueError(f"Duplicate step ID: {name}")
        seen.add(name)
        previous = _reference(speech, step.get("previous"), f"{name}.previous")
        bridge = _reference(speech, step.get("bridge"), f"{name}.bridge")
        result = _reference(speech, step.get("result"), f"{name}.result")
        action = _reference(actions, step.get("action"), f"{name}.action")
        if action["id"] in used_actions:
            raise ValueError(f"Action reused by multiple launches: {action['id']}")
        used_actions.add(action["id"])
        if previous_result is None:
            chain.append(previous["id"])
        elif previous["id"] != previous_result:
            errors.append(f"{name}: previous result does not continue the narrative chain")
        chain.extend((bridge["id"], result["id"]))
        previous_result = result["id"]
        purpose = _time(step.get("purpose_at"), f"{name}.purpose_at", duration)
        if not bridge["start"] <= purpose <= bridge["end"]:
            errors.append(f"{name}: spoken purpose must be inside its bridge")
        if previous["end"] > bridge["start"]:
            errors.append(f"{name}: bridge overlaps the previous explanation")
        if action["start"] < purpose:
            errors.append(f"{name}: action starts before the spoken purpose")
        if previous_ready is not None and action["start"] < previous_ready:
            errors.append(f"{name}: action interrupts the previous response before readiness")
        if "title_at" not in step:
            raise ValueError(f"{name}.title_at is required (null if no title changes)")
        if step["title_at"] is not None:
            title = _time(step["title_at"], f"{name}.title_at", duration)
            if title < purpose:
                errors.append(f"{name}: title changes before the spoken purpose")
        if bridge["end"] > result["start"]:
            errors.append(f"{name}: result narration overlaps its bridge")
        gap = result["start"] - bridge["end"]
        if gap > profile["launch_silence_cap_seconds"] + EPSILON:
            errors.append(f"{name}: planned launch gap exceeds the launch silence cap")

        response = _object(step.get("response"), f"{name}.response")
        mode = response.get("mode")
        if mode not in ("atomic", "progressive", "confirmation"):
            raise ValueError(f"{name}: response mode must be atomic, progressive or confirmation")
        if mode == "confirmation":
            ready = _time(response.get("confirmed_at"), f"{name}.confirmed_at", duration)
            readable = ready
            if step is not steps[-1]:
                raise ValueError("confirmation is reserved for the last launch")
            if result["start"] < ready:
                errors.append(f"{name}: closing starts before full confirmation")
        else:
            readable = _time(response.get("readable_at"), f"{name}.readable_at", duration)
            ready = _time(response.get("ready_at"), f"{name}.ready_at", duration)
            if readable > ready:
                errors.append(f"{name}: readable evidence follows full readiness")
            if result["start"] - readable + EPSILON < profile["recognition_seconds"]:
                errors.append(f"{name}: narration starts before readable recognition")
            if mode == "atomic" and result["start"] < ready:
                errors.append(f"{name}: atomic result is not fully ready for narration")
            if mode == "progressive":
                writing_end = _time(response.get("writing_end"), f"{name}.writing_end", duration)
                if not readable < writing_end <= ready:
                    errors.append(f"{name}: invalid progressive response lifecycle")
                if writing_end - result["start"] + EPSILON < profile["progressive_lead_seconds"]:
                    errors.append(f"{name}: narration starts too late during progressive writing")
        if not action["start"] <= readable <= ready <= action["end"]:
            errors.append(f"{name}: response evidence is outside its protected action")
        previous_ready = ready

        structured = response.get("structured_at")
        if structured is not None:
            structured = _time(structured, f"{name}.structured_at", duration)
            if not action["start"] <= structured <= ready:
                errors.append(f"{name}: structured visibility is outside its response lifecycle")
        if response.get("structured_lag_cap_seconds") is not None:
            limit = timeline._number(response["structured_lag_cap_seconds"], f"{name}.structured lag cap")
            if limit <= 0 or structured is None:
                raise ValueError(f"{name}: positive structured lag cap needs structured_at evidence")
            budget_count += 1
            if structured - result["start"] > limit + EPSILON:
                errors.append(f"{name}: structured details exceed their approved arrival budget")
        claims = _entries(step.get("claims"), f"{name}.claims")
        claim_count += len(claims)
        claim_ids = set()
        for claim in claims:
            claim_id = _id(claim.get("id"), f"{name}.claim.id")
            if claim_id in claim_ids:
                raise ValueError(f"{name}: duplicate claim ID: {claim_id}")
            claim_ids.add(claim_id)
            spoken = _time(claim.get("spoken_at"), f"{name}.{claim_id}.spoken_at", duration)
            visible = _time(claim.get("visible_at"), f"{name}.{claim_id}.visible_at", duration)
            kind = claim.get("kind")
            if kind not in ("text", "structured"):
                raise ValueError(f"{name}.{claim_id}: kind must be text or structured")
            if kind == "structured" and structured is None:
                raise ValueError(f"{name}.{claim_id}: structured_at evidence is required")
            support = structured if kind == "structured" else readable
            if visible < support or spoken < visible or not result["start"] <= spoken < result["end"]:
                errors.append(f"{name}.{claim_id}: claim precedes visible supporting evidence")
        launches.append({
            "id": name, "bridge_start": bridge["start"], "bridge_end": bridge["end"],
            "action_start": action["start"], "result_start": result["start"],
            "planned_gap_seconds": gap, "recognition_seconds": result["start"] - readable,
        })
        if any(pause["start"] < result["start"] and pause["end"] > action["start"] for pause in reviews):
            errors.append(f"{name}: a review pause cannot exempt launch silence")

    ordered = [item["id"] for item in sorted(speech.values(), key=lambda item: item["start"])]
    if chain != ordered:
        errors.append("Narrative chain must cover every speech cue exactly once; no extra recap")
    if launches[0]["action_start"] > profile["opening_cap_seconds"] + EPSILON:
        errors.append("Opening before the first action exceeds the brief's cap")
    closing = _object(data.get("closing"), "closing")
    cue = _reference(speech, closing.get("cue"), "closing.cue")
    if steps[-1]["response"]["mode"] != "confirmation" or cue["id"] != steps[-1]["result"]:
        raise ValueError("closing must reference the final confirmation launch's result")
    confirmed = steps[-1]["response"]["confirmed_at"]
    hold = duration - cue["end"]
    if cue["end"] - cue["start"] > profile["closing_cap_seconds"] + EPSILON:
        errors.append("Closing narration exceeds its approved duration cap")
    if cue["start"] - confirmed > profile["confirmation_to_closing_cap_seconds"] + EPSILON:
        errors.append("Closing does not follow confirmation directly")
    if duration - confirmed > profile["confirmation_to_end_cap_seconds"] + EPSILON:
        errors.append("Confirmation-to-end interval exceeds its cap")
    if not profile["final_hold_min_seconds"] - EPSILON <= hold <= profile["final_hold_max_seconds"] + EPSILON:
        errors.append("Final hold is outside its approved range")
    for pause in reviews:
        if any(pause["start"] < cut < pause["end"] for cut in data["cuts"]):
            errors.append(f"Cut interrupts deliberate review '{pause['id']}'")
    report.update({
        "launches": launches, "closing_hold_seconds": hold, "media_checks": [],
        "opening_seconds": launches[0]["action_start"],
        "declared_claims_checked": claim_count, "structured_budgets_checked": budget_count,
        "review_pauses": reviews,
        "final_verified": False, "human_playback_review": "not_established",
        "audio_content": data["audio_content"],
    })
    return report


def _run(arguments: list[str]) -> bytes:
    try:
        return subprocess.run(arguments, check=True, capture_output=True).stdout
    except FileNotFoundError as exc:
        raise ValueError(f"{arguments[0]} is required and was not found") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"{arguments[0]} failed: {detail}") from exc


def parse_silence(output: bytes, duration: float) -> list[dict[str, float]]:
    """Include trailing open silence; never truncate a gap at the nominal cue boundary."""
    gaps = []
    start = None
    previous_point = 0.0
    for kind, raw in re.findall(rb"lavfi\.silence_(start|end)=([^\s]+)", output):
        point = float(raw)
        if not math.isfinite(point) or not -EPSILON <= point <= duration + 0.1:
            raise ValueError("FFmpeg silence event is outside the decoded audio")
        point = max(0.0, min(point, duration))
        if point + EPSILON < previous_point:
            raise ValueError("FFmpeg silence events are not chronological")
        previous_point = point
        if kind == b"start":
            if start is not None:
                raise ValueError("FFmpeg emitted unpaired silence-start events")
            start = point
        else:
            if start is None or point < start:
                raise ValueError("FFmpeg emitted an invalid silence-end event")
            gaps.append({"start": start, "end": point, "duration": point - start})
            start = None
    if start is not None:
        gaps.append({"start": start, "end": duration, "duration": duration - start})
    return gaps


def check_launch_audio(
    launches: list[dict[str, Any]], gaps: list[dict[str, float]], cap: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    results = []
    errors = []
    for launch in launches:
        # Clip only the left edge: prior deliberate reading must not become launch silence.
        relevant = [
            gap["end"] - max(gap["start"], launch["bridge_start"])
            for gap in gaps
            if gap["start"] <= launch["result_start"] and gap["end"] >= launch["action_start"]
        ]
        largest = max(relevant, default=0.0)
        results.append({"id": launch["id"], "signal_silence_seconds": largest, "cap_seconds": cap})
        if largest > cap + EPSILON:
            errors.append(f"{launch['id']}: decoded launch silence {largest:.4f}s exceeds {cap:g}s")
    return results, errors


def _metadata_number(value: object, label: str) -> float:
    try:
        return timeline._number(float(value), label)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"FFprobe did not report a finite {label}") from exc


def _endpoint(path: Path, ending: bool, profile: dict[str, float]) -> dict[str, Any]:
    window = str(profile["endpoint_window_seconds"])
    seek = ["-sseof", f"-{window}"] if ending else ["-ss", "0"]
    output = _run([
        "ffmpeg", "-v", "error", "-xerror", *seek, "-i", str(path), "-t", window,
        "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
        "-an", "-f", "null", "-",
    ])
    samples = [float(value) for value in re.findall(rb"lavfi\.signalstats\.YAVG=([\d.]+)", output)]
    if not samples or not all(math.isfinite(value) for value in samples):
        raise ValueError("Endpoint luminance is empty or unmeasured")
    return {"samples": len(samples), "minimum_yavg": min(samples)}


def check_media(
    path: Path, data: dict[str, Any], report: dict[str, Any], *, video: bool,
) -> dict[str, Any]:
    path = path.resolve(strict=True)
    if not path.is_file():
        raise ValueError("Media must be a local file")
    info = _object(json.loads(_run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path),
    ])), "FFprobe output")
    streams = _entries(info.get("streams"), "FFprobe streams")
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    picture = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    if audio is None or (video and picture is None):
        raise ValueError("Required audio/video stream is missing")
    container = _object(info.get("format"), "FFprobe format")
    raw_length = audio.get("duration")
    if raw_length in (None, "N/A"):
        raw_length = container.get("duration")
    audio_length = _metadata_number(raw_length, "audio duration")
    if audio_length <= 0:
        raise ValueError("Audio duration must be positive")
    profile = _profile(data["profile"])
    tolerance = profile["duration_tolerance_seconds"]
    errors = []
    if audio_length + tolerance < max(cue["end"] for cue in data["speech"]):
        errors.append("Audio ends before the last declared speech")
    if audio_length > data["duration"] + tolerance:
        errors.append("Audio exceeds the timeline duration")
    output = _run([
        "ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:a:0", "-vn",
        "-af", f"silencedetect=noise={profile['silence_noise_db']:g}dB:"
        f"d={profile['silence_min_seconds']:g},ametadata=print:file=-",
        "-f", "null", "-",
    ])
    gaps = parse_silence(output, audio_length)
    launches, audio_errors = check_launch_audio(
        report["launches"], gaps, profile["launch_silence_cap_seconds"],
    )
    errors.extend(audio_errors)
    result = {"source": path.name, "kind": "video" if video else "narration",
              "audio_duration": audio_length, "launches": launches, "errors": errors}
    if video:
        expected = _format(data["format"])
        length = _metadata_number(container.get("duration"), "container duration")
        picture_length = _metadata_number(picture.get("duration"), "video duration")
        if any(abs(value - data["duration"]) > tolerance for value in (length, picture_length)):
            errors.append("Export duration does not match the timeline")
        if (picture.get("codec_name"), picture.get("width"), picture.get("height")) != (
            expected["video_codec"], expected["width"], expected["height"],
        ):
            errors.append("Export picture format does not match the brief")
        for key in ("r_frame_rate", "avg_frame_rate"):
            try:
                fps = float(Fraction(picture.get(key, "")))
            except (TypeError, ValueError, ZeroDivisionError) as exc:
                raise ValueError(f"FFprobe did not report a valid {key}") from exc
            if abs(fps - expected["fps"]) > 0.001:
                errors.append(f"Export {key} does not match the brief's frame rate")
        if (audio.get("codec_name"), audio.get("channels"),
            _metadata_number(audio.get("sample_rate"), "audio sample rate")) != (
            expected["audio_codec"], expected["audio_channels"], expected["audio_sample_rate"],
        ):
            errors.append("Export audio format does not match the brief")
        _run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"])
        result["full_decode"] = "passed"
        for key, ending in (("first_frames", False), ("last_frames", True)):
            result[key] = _endpoint(path, ending, profile)
            if result[key]["minimum_yavg"] < profile["endpoint_min_luma"]:
                errors.append(f"{key}: black endpoint or luminance below the brief's floor")
        result["duration"] = length
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--preflight", action="store_true", help="Never claims final verification")
    parser.add_argument("--narration", type=Path, help="Aligned dry narration, required with a music bed")
    parser.add_argument("--video", type=Path, help="Final local export; mandatory without --preflight")
    parser.add_argument("--output", type=Path, help="Optional UTF-8 JSON report")
    args = parser.parse_args(argv)
    try:
        if not args.preflight and args.video is None:
            raise ValueError("Final verification requires --video; use --preflight for metadata only")
        data = json.loads(args.contract.read_text(encoding="utf-8"))
        report = check_demo(data)
        if data["audio_content"] == "mixed" and args.video is not None and args.narration is None:
            raise ValueError("Mixed audio requires --narration: music can hide a voice gap")
        for path, is_video in ((args.narration, False), (args.video, True)):
            if path is not None:
                measured = check_media(path, data, report, video=is_video)
                report["media_checks"].append(measured)
                report["errors"].extend(measured["errors"])
        report["status"] = "failed" if report["errors"] else (
            "preflight_passed" if args.preflight else "mechanical_checks_passed"
        )
        report["final_verified"] = not args.preflight and not report["errors"]
        code = 1 if report["errors"] else 0
    except (OSError, ValueError) as exc:
        report = {"status": "invalid", "errors": [str(exc)], "final_verified": False,
                  "human_playback_review": "not_established"}
        code = 2
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        try:
            args.output.write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"Cannot persist report: {exc}", file=sys.stderr)
            return 2
    print(text, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
