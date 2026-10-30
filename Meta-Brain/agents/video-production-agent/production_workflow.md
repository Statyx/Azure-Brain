# Video Production Workflow

Read [instructions.md](instructions.md) first. Examples are local patterns, not permission
to transmit recordings, use a cloud service, install tools, send a message or publish.
For the narrative framework and preflight command, also read
[storytelling_playbook.md](storytelling_playbook.md).

## 1. Brief, board and provenance

- Define format (marketing story, demo walkthrough or both), target persona, business
  question, length, language, audience, channel and tone. Confirm the destination, voice,
  music preference, assets, source rights and privacy constraints.
- Build a table: **time | voice-over | visible action/frame | every on-screen text**.
  Show previews of the actual interface, and inventory intermediate loading/thinking
  text as well as results. Explicitly flag all numbers, dates, claims and logos.
- Track the approval of the entire board and each subsequent change. Do not synthesize
  or render until approved. Re-present only changed scenes when iterating.
- Prefer a presenter-style narrative: problem → observed result → why the next source
  is needed → alternatives → decision → human approval/action → outcome and conclusion.
  Include business context in the introduction, not just product names.
- Record which parts are live, prerecorded, staged, locally drawn or non-sending in
  presenter/distribution notes. Never infer a live integration from a realistic-looking UI.

## 2. Capture and framing

- Capture the actual product in a single continuous take when possible, in a stable,
  wide view, at a constant frame rate and **1x interaction speed**. Keep the cursor,
  typed questions, progressive responses, reasoning, scroll, choices, approval controls
  and final action visible when they matter. Hold long enough for a human to read them.
- Capture events with marker names and clock origin; measure or calibrate the offset
  between script startup and the first video frame. Record both *first visible* and
  *fully ready* states where timing matters.
- If browser automation creates the movement, space pointer steps over real time;
  merely asking for many steps can still deliver them almost instantaneously.
  Avoid camera movement while the application itself scrolls. A stable wide view is
  better than a dramatic zoom that hides the context or a bottom-edge button.
- Do not hide contradictory UI text with a brittle mask or a cut through the action.
  Surface the issue; present and obtain approval for a correction or a framing change.
- Choose pauses at genuinely idle moments. A single zero-crossing sample is not by
  itself evidence that a word, animation or user action is complete.

## 3. Narration and timeline

- When an automated narrator is requested, enumerate voices actually available to
  the chosen service. Offer comparable short samples of approved copy. Prefer a
  natural neural voice, without silently falling back to a robotic local voice.
  Once approved, retain the same voice, model, SSML settings and speaking rate for
  additions. If synthesis fails, report it rather than changing voices silently.
- A worked Azure AI Speech pattern was observed with an existing Foundry `AIServices`
  resource: acquire an Entra token in memory for `https://cognitiveservices.azure.com`
  using the configured tenant, then POST SSML to the resource's custom host at
  `/tts/cognitiveservices/v1`. The verified output format was
  `riff-24khz-16bit-mono-pcm`. Enumerate availability and verify access in the current
  resource; do not log tokens or assume another tenant/resource has the same access.
- Measure each generated WAV after normalization and resampling. A working stereo
  speech preparation used `loudnorm=I=-16:LRA=11:TP=-1.5`, 48 kHz, 16-bit PCM.
  These are targets, not a guarantee of matching perceived loudness; check the result.
  Use licensed/user-provided music only, or an explicitly identified generated bed,
  and keep it beneath the narration; no music is also a valid choice.
- Align measured speech to video actions and readable states, not guessed script lengths.
  Track each cue's start and end, current card, clicks, answer completion and conclusion.
  A bridge can introduce a decision or explain the need for approval during an existing
  idle gap. Fit the **whole** clip plus natural space; do not overlap other speech or
  truncate words. If it does not fit, propose a timing change and obtain approval.
- Preserve the original speech samples when adding pauses. Verify this by removing the
  inserted gaps from the PCM mix and comparing the reconstructed original byte-for-byte.
  That check proves sample preservation, not that every splice sounds natural.

## 4. Local composition and audio-only iteration

- A local HTML/CSS/GSAP composition with HyperFrames was used successfully for a
  continuous walkthrough. In the observed version, trimmed media uses
  `data-media-start`; GSAP timelines are paused and registered under
  `window.__timelines[compositionId]`. Check the installed version's CLI and avoid
  unrequested uploads or cloud rendering. With constrained resources, one worker
  reduced contention. Inspect short critical excerpts before a full render.
- If only narration changes and the approved pictures and timings remain untouched,
  combine the existing video stream with the new audio. For example, with FFmpeg:

  ```powershell
  ffmpeg -i <reference-video> -i <new-mix.wav> -map 0:v:0 -map 1:a:0 -map_metadata 0 -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart <new-output.mp4>
  ```

  Replace placeholders with actual arguments; write to a new path and do not overwrite
  the reference. Confirm the mix fits the visual timeline and the final duration before
  delivery. If pictures or timings must change, an audio-only remux is not sufficient.
- Compare compressed **video stream** hashes of reference and output with the same
  FFmpeg `-map 0:v:0 -c:v copy -f hash -hash sha256` method. Container-file hashes
  differ when audio changes and do not prove whether the picture changed.

## 5. Verification and handoff

1. Use `ffprobe` to check duration, video and audio codecs, dimensions, frame rate,
   sample rate and channels; compare against the agreed output requirements.
2. Decode the whole file with FFmpeg in error-fail mode. Check first and last image
   windows with `signalstats,metadata=print:file=-`; fail on **no samples** or
   `min(YAVG) < 20`. A last-frame fade to black erases the closing message.
3. Inspect sequential images around each cue and note the limits of still-image review.
   Verify title/caption timing, controls, cursor, continuous writing and reasoning,
   each described card, approval, final action and conclusion. Ask a person to review
   actual playback when available; automated checks are not a substitute.
4. Compare the prepared WAV with decoded AAC at representative old and new speech
   windows; detect missing, shifted, clipped or overlapping speech. Correlation is
   useful evidence of matching samples, not proof of intelligibility or pleasant pacing.
5. Deliver the agreed MP4 and retain a reproducible package: approved copy, raw
   recording, event markers and their clock origin, voice clips, editable timing/
   composition, scripts, dependency versions, instructions and validation. Exclude
   secrets, tenant IDs, private config and regenerable bulky intermediates. Rebuild
   from the extracted package when practical.

For GitHub README embedding, defer to
[project-presentation-agent](../project-presentation-agent/visual_presentation.md).

## 6. Reusable response-recognition and handoff contract

Apply this procedure alongside sections 1-5, not as permission to anticipate the next task.

1. Freeze approved copy, voice settings and native UI inventory. For a timing-only
   revision, hash the existing voice clips and reuse them rather than synthesizing again.
2. Read the actual response lifecycle before choosing a narration trigger. Establish
   whether the answer is atomic, progressively written, or a written summary followed
   by cards. Distinguish the first readable evidence, writing end, card commit and
   interactive readiness; do not map them all to `ready`.
3. Finish the preceding result explanation and introduce the next purpose before its
   title/colour/action. Measure an introduction from actual speech word timings when
   available. Do not start the next question under the previous result explanation.
4. For the current progressive reply, observe a coherent prefix in the visible UI.
   Allow a brief recognition interval, then recheck that writing is still in progress
   before starting its approved explanation. Record the observed writing end separately.
   The worked capture used 0.6 seconds, or 0.8 seconds for a short public-context summary.
   Atomic reports instead need their own readable-result gate.
5. Budget structured-card arrival against the **spoken clauses that need its details**.
   A known fact or a generic opening may accompany the remaining reveal, but a summary
   alone cannot justify unseen recipients, figures or option-specific fields. Keep
   comparison focus aligned with each option and leave approval/draft review explicit.
6. Observe timing-sensitive state changes with sufficiently frequent polling. In the
   worked browser capture, frame-polled DOM commitment avoided counting an assertion
   retry delay as late card arrival. A DOM event is still not the first encoded frame:
   calibrate the raw capture offset and inspect decoded image sequences at the cue.
7. Preserve natural interaction speed and approved speech. Remove fixed storyboard
   minimum waits, not meaningful recognition or review time. Do not use a motion-only
   guard as proof of coherent transitions. After full confirmation, retain only the
   approved short closing and its intentional composed hold.
8. Before delivery, reject deliberate regressions: early next action, early title,
   overlapping bridge, extra post-confirmation recap, commentary after writing,
   commentary before recognition, and late structured details. Also check the rendered
   audio, endpoints and calibrated silent/static detector; review long speech gaps in
   their actual UI context rather than treating every gap as either an error or reading time.

**Evidence (2026-10-30):** A continuous 257.66-second capture retained all seventeen
approved voice clips. Its six progressively written answers started commentary
0.625-0.828 seconds after observed readable text, with 0.328-5.531 seconds of writing
still remaining. The atomic report was handled separately. Seven intentionally invalid
fixtures were rejected by their expected semantic guards; the timeline preflight passed.
This establishes the measured event contract, not a human real-time playback review.

## 7. Cover the current launch, not merely its static waits

This corrects an incomplete acceptance criterion in section 6: visible motion does not
make a long post-introduction speech gap acceptable.

1. Measure the spoken purpose gate, the complete normalized bridge, and native
   action-to-readable latency, including pointer motion, picker, typing and retrieval.
2. Introduce the current purpose before its title/action, but let the remaining bridge
   explain what is being checked while that same operation runs.
3. Schedule dispatch near `bridge_end + breathing_space - launch_latency - recognition`,
   never before the actual spoken-purpose gate. Use observed latency and retain
   real-time state checks; do not assume every question or session has identical timing.
4. Observe a coherent visible prefix during bridge playback. Start result commentary
   after both the bridge and recognition interval, while writing is still in progress.
   If a short bridge cannot cover the lifecycle, obtain approval for replacement copy;
   do not silently accelerate the voice/UI or start an unintroduced next task.
5. Before full export, build the PCM timeline and short transition excerpts. Check
   launch silence independently of screen motion, then repeat against the encoded audio.
   Include unchanged bridges and the sending-to-closing transition in the measured set.
6. Preserve deliberate option-reading and human-review intervals separately. Positioning
   a pointer under the completed draft review can remove avoidable post-intro travel;
   clicking still waits for the spoken sending introduction and closing for confirmation.
7. Prove the guard rejects a known moving/loading passage with excessive speech silence,
   even when the previous silent/static guard accepted it. Do not waive it as animated UI.
8. Use a short audiovisual trial when the viewer cannot assess written timing. Record
   trial approval, full-production authorization and full-version feedback separately.

**Evidence (2026-10-30):** The old motion guard accepted 11.0259 seconds of active-loading
speech silence. A 42.36-second continuous comparison trial had 0.4125 seconds at the
same narrative boundary, below its proposed 1.5-second cap. Recognition was 0.64 seconds;
explanation began 0.875 seconds before writing ended and option cards arrived 1.391
seconds after commentary started. Both encoded-audio sample correlations exceeded
0.99998. The viewer approved the excerpt and separately authorized the extension.
Mechanical checks and that bounded viewer feedback are not full-version human review.

## 8. Reusable implementation - 2026-10-30

The current operational entry point is [demo_recipe.md](demo_recipe.md), not a copy of
an earlier production's scripts. [check_demo.py](tools/check_demo.py) reuses the timeline
checker and adds project-neutral lifecycle, recognition, visibility, short-ending and
independently decoded launch-audio gates. It also checks final format, full decode and
non-black endpoints. Use the neutral examples and regression tests before mapping a
new application's measured events; do not encode selectors or scene counts in the tool.
Approval, source-speech preservation, actual 1x continuity and rebuild remain separate
requirements of the workflow above.
