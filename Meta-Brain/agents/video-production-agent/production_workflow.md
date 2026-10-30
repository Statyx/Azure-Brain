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
