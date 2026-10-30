# Interactive Demo Recipe - current reference

Use this recipe for narrated interactive workflows with progressive or atomic results
and a final confirmed action. It operationalizes the pacing corrections in
[instructions.md](instructions.md), rather than replacing earlier history with another
project-specific script. For other marketing/editing formats, retain the general
[storytelling playbook](storytelling_playbook.md) and [timeline checker](tools/check_timeline.py).

## Production path

1. **Approve the brief and exact board.** Establish audience, language, duration,
   narrator/delivery, claims and live/staged boundaries. Explain the business purpose
   and, where relevant, distinguish the authoritative platform from its access surface.
   Preserve approved voice clips byte-for-byte; changed wording requires new approval.
2. **Measure one native path.** The application adapter records coherent readable text,
   full writing, actual structured visibility, ready controls and full confirmation.
   Calibrate its clock against decoded frames. Record the end of the actual spoken
   purpose, not the end of a proposed text prefix or an estimated words-per-minute rate.
3. **Approve one representative audiovisual excerpt early.** Include a difficult
   launch, recognition and card transition. Written timings and green signal checks
   cannot establish that the rhythm feels right. Excerpt approval, authorization for
   remaining changed copy, and full-version playback feedback are separate decisions.
4. **Capture continuously at natural speed.** Finish the prior result explanation,
   introduce the next purpose, then change context/start its action. Let the remaining
   useful bridge accompany that same action. Observe readable support during the bridge
   when possible; after brief recognition, explain the current answer while it is still
   writing. Do not recover speed with an unintroduced next task, cuts or acceleration.
5. **Run blocking preflight before full export.** Map measured events into the contract
   below. Check both the metadata and aligned dry narration. Fix failures, not thresholds
   after the fact. Keep intentional option reading and draft review separate.
6. **Check the exported media, then review the experience.** Repeat against the final
   encoded audio, including unchanged bridges and the last action-to-closing transition.
   Check decode, format and non-black endpoints. Inspect boundary frames and obtain
   playback feedback without claiming signal checks are human listening/viewing.
7. **Deliver reproducible sources.** Preserve approved copy/voice provenance, capture,
   event adapter, composition, manifest, reports and a rebuild command. Independently
   verify retained source hashes, complete speech in the mix, capture continuity and
   reconstruction using [production_workflow.md](production_workflow.md). This checker
   does not establish those properties by itself.

## Application adapter boundary

Keep selectors, question text, product names, cue IDs, API/configuration, measured native
latencies and render/capture implementation in the consuming production workspace.
Do not fork the Brain checker or copy a previous application's latency constants.

The adapter supplies **observed output-timeline seconds**, not desired timestamps.
An app's committed DOM marker is not automatically coherent visible text or proof that
an off-screen card can be read. Inspect decoded frames and record claim-specific visible
support where necessary. The checker validates the supplied observations; it cannot
discover an omitted interaction, understand a claim, infer approval or certify a live call.

Schedule a launch near:

```text
bridge end + breathing space - observed action-to-readable latency - recognition
```

Never dispatch before the spoken-purpose gate. Keep observing the response while the
bridge plays; do not begin the readable-text wait only when its audio has finished.
Treat this as a scheduling estimate and retain actual-state guards.

## Measured contract, version 1

Start from [demo-accepted.json](examples/demo-accepted.json). It is **synthetic metadata**,
not an approved storyboard, recording, voice sample or universal timing profile.
[demo-rejected.json](examples/demo-rejected.json) differs in launch coverage: animated
typing does not excuse its 2.3-second gap, even though the older three-second warning
checker accepts it.

| Field | Required meaning |
|---|---|
| `schema_version`, `duration` | Version `1`, positive finite complete film length. |
| `audio_content` | Explicit `voice_only` or `mixed`. Checking a mixed export requires an aligned dry narration track as well. This declaration is not automatic content recognition. |
| `speech`, `visuals`, `actions`, `cuts` | Existing timeline-checker intervals; unique IDs, finite times. Actions protect native interactions. Link a speech cue's `visual` only if that visual covers the whole cue. |
| `steps` | Ordered nonempty launches. Each names `previous`, `bridge`, `result` speech and one `action`; the chain covers every speech cue exactly once. Extra protected actions are allowed. Never omit a bridge, an unchanged launch or a narrated recap to make the check pass. |
| `purpose_at`, `title_at` | End of spoken introducing purpose, and actual context/title change. Explicit `null` title means no change. Both title and action wait for the purpose. |
| `response.mode: progressive` | `readable_at`, `writing_end`, `ready_at`; recognition before result narration and configured lead before writing ends. |
| `response.mode: atomic` | `readable_at`, `ready_at`; the complete result is ready before narration. Do not invent a streaming lifecycle. |
| `response.mode: confirmation` | Final launch only, with observed full `confirmed_at`. Its result cue is the short closing, not another confirmation recap. |
| `response.structured_at` | Actual structured-detail visibility when relevant. It may differ from both writing end and control readiness. |
| `response.structured_lag_cap_seconds` | Optional approved arrival budget relative to result narration, requiring `structured_at`. This is a bounded card-arrival check, **not** a measured word/claim timestamp. |
| `claims` | Explicit list per step, empty only when no additional claim is instrumented. Each has a unique `id`, `kind` (`text` or `structured`), `spoken_at` and supporting `visible_at`. Structured claims also require `structured_at`. Reported claim counts expose coverage; the tool cannot know which spoken claims were omitted. |
| `review_pauses` | Explicit intervals for deliberate reading/review, empty when absent. Cuts inside them fail. They cannot overlap or exempt a launch. |
| `closing.cue` | Final confirmation launch's result; no extra unlinked speech cue. |
| `format` | Agreed width, height, numeric fps, video/audio codec names, channels and sample rate. |
| `profile` | All named limits in the example, agreed for this brief. No universal scene count, customer, voice, selector or UI latency is embedded in the tool. |

Use the profile to choose total-runtime and opening-to-first-action caps, recognition,
progressive lead, launch silence, short-closing, confirmation-to-closing/end and
final-hold limits. A next action must also wait for the prior response's readiness.
Also declare gap-warning, duration
tolerance, silence-detector sensitivity/minimum duration and endpoint-luminance/window
settings. Detector minimum duration cannot exceed the launch cap.

**A launch silence cap cannot be waived by animated UI.** The legacy three-second
gap warning is editorial context, not an exemption from the selected hard cap. The
checker decodes the complete audio, so silence inside a bridge and a long silent tail
cannot hide behind nominal clip ends. It tests silence intersecting the current launch,
from action start through result onset; prior reading time is clipped at bridge start.
Trailing open silence is measured to EOF, not silently discarded.

## Commands

Python 3.12+ and local FFmpeg/FFprobe are sufficient; no cloud calls or new packages.
From the Azure-Brain repository root:

```powershell
$agent = Join-Path (Get-Location) 'Meta-Brain\agents\video-production-agent'
python (Join-Path $agent 'tools\check_demo.py') (Join-Path $agent 'examples\demo-accepted.json') --preflight
python (Join-Path $agent 'tools\check_demo.py') (Join-Path $agent 'examples\demo-rejected.json') --preflight
```

The second command must exit `1`. For a real production's measured contract:

```powershell
python (Join-Path $agent 'tools\check_demo.py') <contract.json> --preflight --narration <aligned-dry-voice.wav> --output <preflight-report.json>
python (Join-Path $agent 'tools\check_demo.py') <contract.json> --video <final.mp4> --narration <aligned-dry-voice.wav> --output <final-report.json>
```

Paths are local. Narration starts at timeline zero and covers every declared cue; it
may end before the silent final image hold. With a music bed, supply the aligned **dry**
voice too: low-level signal detection is not speech recognition, and music can hide a
voice gap. Both supplied tracks are checked. Separately verify speech preservation
and actual cue alignment in the export; the tool does not correlate source speech.

Exit `0` means the requested mechanical stage passed, `1` means measured/declared guards
failed, and `2` means invalid/missing evidence or a tool/IO failure. JSON is UTF-8 without
BOM. `--preflight` always reports `final_verified: false`; final checking requires
`--video`. Even a passing final report states `human_playback_review: not_established`.
Do not use these reports as proof of natural pacing, legibility, provenance, source
preservation, 1x playback or authorization.

## Regression evidence

[test_video_demo.py](../../tests/test_video_demo.py) exercises accepted progressive and
atomic lifecycles; rejected action/title/bridge order, recognition, writing, hidden
details, extra recap, confirmation and long ending; malformed/missing evidence; real
synthetic-audio gaps despite valid metadata; internal bridge silence; deliberate reading;
EOF silence; unavailable/failed tools; and decoded white/black endpoints and format.
The existing timeline checker and its tests are retained unchanged.

**Observed reuse proof (2026-10-30):** An external application adapter mapped a retained
production into this contract. Its eight launches passed against both the full encoded
movie and dry narration; maximum decoded launch silence was 1.287896 seconds. Seven
semantic mutations failed their expected gates. The same generic audio guard rejected
the actual 11.025917-second animated-loading silence accepted by the older motion check.
Legacy result clips lacked word events: their three structured-arrival budgets were
checked using inspected card/shell frames, without inventing claim-level word timings
or claiming another human playback review. Application evidence remains outside the Brain.
