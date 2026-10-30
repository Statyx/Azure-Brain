# Known Issues — video-production-agent

## 1. Video is technically valid but no longer follows the interaction

**Symptom:** Typing and progressive reasoning jump to completed answers, an approval
click disappears, or a tight crop hides the control needed to proceed.

**Root cause:** Captured segments were removed to hit a time target; zoom and crop
positions were checked against selected frames rather than the whole interaction.

**Fix:** Prefer a continuous, natural-speed recapture and a stable wide view. Preserve
the voice; budget time for the complete interaction and ask the user before relaxing
a hard duration target. Inspect the complete critical transitions and visible controls.

**Evidence:** A 2026-10-29 narrated demo export was 138.36 seconds, decodable and had
non-black endpoints, but its user rejected missing typing, reasoning and approval
actions. The prior 203.48-second source contained the omitted interactions. A later
continuous and retimed version lasted 181.32 seconds; the user described the resulting
video as very good. Measurements and extracted frames do not establish a human playback
review by the agent.

## 2. Smooth timestamps do not mean smooth on-screen motion

**Symptom:** The video appears to lag at some moments and rush at others despite
constant frame-rate timestamps. Cursor movement is nearly instantaneous.

**Root cause:** The edit changed interaction speed between 0.16x and 2.59x, duplicating
frames during slowdowns and compressing actions during speedups. Automated mouse steps
were issued without real delays.

**Fix:** Record timed pointer steps and let interactions play at 1x. Remove only
genuinely idle waiting, not active writing or reasoning. Recheck the movement itself
and keep camera changes restrained.

**Evidence:** In the same 2026-10-29 walkthrough, the source and edited video both had
regular 25 fps timestamps, while the edit's `setpts` factors and pointer code exposed
the speed changes. A later take used timed pointer movement and 1x interaction footage.

## 3. The next screen appears before the current explanation is finished

**Symptom:** A new source or scenario card is shown while the narrator still describes
the previous one; approval starts before the recommendation has been explained.

**Root cause:** Script estimates, capture markers and the actual recorded speech were
treated as interchangeable timelines. A `ready` marker can also be later than first
appearance, so it is not an exact visibility timestamp.

**Fix:** Measure narration, first-visible and ready states, and actual click times.
Create a cue map, keep the described item visible through its explanation and validate
the critical transitions after every change.

**Evidence:** In the 2026-10-29 initial continuous cut, the next source was clicked at
76.44 seconds while the prior explanation continued to about 83 seconds; scenario cards
changed before their associated narration ended. A subsequent retime checked markers
for source transitions, each option, approval, Send and the conclusion.

## 4. Filling long pauses risks changing an approved voice or picture

**Symptom:** A pacing revision adds speech but unexpectedly changes the approved voice,
cuts words, shifts the picture, or requires an unnecessary full video render.

**Root cause:** Generating a complete replacement narration or rerendering the entire
composition for a local audio edit changes more than the user requested. Measured
clip duration must include normalization and sample-rate conversion.

**Fix:** Obtain approval of each new line; synthesize only those clips using the same
voice and settings. Fit each complete clip and breathing room within an idle gap, check
the unchanged original PCM samples, then copy the video stream into a new MP4 if the
picture timeline is unchanged. Check stream hash and decoded speech cues.

**Evidence:** In the 2026-10-29 retime, five approved clips of 3.90, 5.30, 6.10,
4.75 and 5.70 seconds fit their existing gaps without moving the pictures. The original
PCM narration reconstructed byte-for-byte; the old and new compressed video streams
had the same SHA-256; sampled decoded speech correlations were 0.9999–1.0000.
These checks do not prove subjective naturalness or cover every possible codec.

## 5. Valid-looking video starts or ends on black

**Symptom:** The file's thumbnail or final paused frame shows black although the
duration and codecs are correct.

**Root cause:** A fade was placed on the first or final composed board, or the luminance
check silently accepted an empty sample set.

**Fix:** Keep both composed endpoint boards visible. Use `signalstats` with
`metadata=print:file=-`, reject empty measurements and check the minimum luminance
over the endpoint windows. See the existing
[project-presentation evidence](../project-presentation-agent/known_issues.md#problem-a-teaser-ends-on-black-throwing-away-its-closing-message).

**Evidence:** The earlier teaser recorded in that entry faded to black despite being
otherwise valid; after removing the fade, the final window measured constant non-black
luminance. The later 181.32-second demo had minimum endpoint YAVG values above 20.

## 6. Azure Speech authentication or endpoint is assumed rather than checked

**Symptom:** A resource lists plausible voices but synthesis fails, or the wrong tenant
is used.

**Root cause:** Voice listing alone does not establish synthesis access. A multi-tenant
CLI session may return a token for the wrong tenant, and endpoint and authentication
capabilities vary by resource.

**Fix:** Verify the actual configured tenant and resource, use an in-memory Entra token
for the Cognitive Services audience, and call that resource's custom `/tts` endpoint.
Enumerate the current voices; report failures without exposing tokens or silently
switching to a lower-quality narrator.

**Evidence:** On 2026-10-29, five clips were synthesized using the existing Foundry
`AIServices` resource, a tenant-targeted Entra token and its custom
`/tts/cognitiveservices/v1` endpoint. The working format and delivery settings are
recorded in [production_workflow.md](production_workflow.md); this is not proof of
availability for other resources.

## 7. A capture composition makes an otherwise working app lose Web Crypto

**Symptom:** A localhost application works in a normal browser page but renders no
controls when embedded in a Playwright composition. MSAL reports
`crypto_nonexistent`.

**Root cause:** In the observed recording setup, `page.set_content()` left the parent
at an opaque `about:blank` origin. The embedded localhost app consequently reported
`isSecureContext === false` and had no `crypto.subtle`. A localhost child URL alone
did not establish a trustworthy ancestor context.

**Fix:** Serve the capture composition from the same localhost origin as the app.
A Playwright route can fulfill a dedicated composition URL with the wrapper HTML;
navigate to that URL before loading the app iframe. Keep normal browser security
enabled, and assert both the app opener and `isSecureContext && !!crypto.subtle`
before starting the timed recording. A title band outside the iframe can then reserve
space without covering app controls or changing application code.

**Evidence:** A 2026-10-30 browser probe reproduced `crypto_nonexistent` and zero
embedded buttons with the `about:blank` parent; direct navigation exposed the app
opener. A paired probe measured `{secure: false, webCrypto: false}` before the change
and `{secure: true, webCrypto: true}` with the same-origin parent, where the expected
opener became visible. This verifies that local capture setup, not arbitrary remote
embedding or a production authentication flow.

## 8. Storyboard estimates become dead-air minimum durations

**Symptom:** A technically valid walkthrough sits silently on a completed result for
several seconds before continuing. A green timeline preflight does not reject the
empty wait because its speech-gap findings are warnings.

**Root cause:** The observed capture waited for fixed storyboard end times after the
measured narration and required interaction had already finished. Optional source
metadata visits were also serialized after narration. Treating every warning as
"reading time" preserved dead air rather than the flow of work.

**Fix:** Schedule from measured speech and observed UI states, not minimum scene
deadlines. Let useful actions accompany the existing approved words. The next question
may start typing while the previous result remains visible and its explanation ends;
do not hide that result or assert new figures before their supporting text appears.
Distinguish a visible supporting summary from a fully committed result card. Omit
optional metadata detours when they add no evidence needed by the spoken story.

Add a regression check for intervals that are both silent and visually idle. Calibrate
it against the rejected passage and against genuine typing and answer writing:
codec noise can defeat a naive freeze detector, while a coarse mean-difference
threshold can mistake a few changing letters for a frozen screen. In the observed
1080p H.264 export, comparing adjacent grayscale frames, ignoring pixel differences
of 40/255 or less and requiring 99.999% unchanged pixels in the chat/input crop caught
the idle passage without flagging the active controls. These are calibrated example
parameters, not universal thresholds. Only the explicit closing hold was exempt,
including up to 250 ms of trailing silence in the normalized final voice clip.

**Evidence:** On 2026-10-30, the rejected 303.375-second recording had an 8.3105-second
silent, idle overlap after the Fabric explanation. The revised continuous recording
was 219.109 seconds at 1x, with no active-interaction cuts and no detected interior
silent/idle overlap of at least 2.8 seconds. The next question began before the prior
explanation ended, leaving zero idle time after Fabric. All 17 original voice clips
were preserved; decoded AAC correlations for their sampled windows were at least
0.999798. The typing and answer-writing negative controls were not classified as idle.
These signal, event and frame checks do not establish a human playback review.

**Correction (2026-10-30, after viewer review):** The earlier permission to start the
next question while explaining the current result is not a suitable default. The
viewer rejected that revision: work-context activity had started while the voice was
still explaining contract obligations. Detecting motion and eliminating silent freezes
does not establish narrative coherence.

Use the strict order **finish the current explanation -> introduce the next experience
and its purpose -> begin that experience's visible action**. Keep the current result
visible until its explanation ends. Introduce the next engine before changing its
title/colour or typing its question. A bridge can continue over the new action after
that introduction; the previous result explanation cannot. Replace an existing weak
bridge rather than stacking a new bridge onto it. Do not recover speed by anticipating
the next task or accelerating the recording.

For precise handoffs, the Speech SDK's word-boundary events can measure the end of the
approved introducing phrase in the actual synthesized clip. With a custom endpoint,
construct `SpeechConfig(endpoint=...)`, then set `authorization_token` separately:
passing both `auth_token` and `endpoint` to its constructor raises
`ValueError: cannot specify both auth_token and endpoint or host when constructing SpeechConfig`.
The observed custom-subdomain synthesis endpoint used the
`/tts/cognitiveservices/websocket/v1` path. This successfully preserved the approved
NeuralHD voice and default delivery while yielding word timings for all new bridges.

**Evidence:** The new capture finished the contract explanation at 82.83 seconds,
began the work-context bridge at 83.30 seconds and started its next action at
87.42 seconds, after the measured engine introduction. All eight handoffs had this
order. Four negative controls were rejected: next action before the previous
explanation ends, next title before its introduction, bridge overlapping the previous
explanation, and an added narrated confirmation recap. The shortened ending proceeded
from full confirmation directly to one approved closing sentence, with an approximately
1.8-second final image rather than the previous five-second hold.

**Clarification (2026-10-30, progressive reply recognition):** The corrected handoff
order remains mandatory, but it does not mean waiting for the **current** answer to
finish writing before explaining it. The viewer requested earlier commentary, then
clarified that the first readable content should register briefly before the voice starts.

In the observed UI, only the assistant summary streams. Reflection, option/person cards
and the email draft appear on commit after writing; the atomic report does not stream.
The committed-message selector therefore cannot identify first readable text. Observe a
coherent partial prefix, allow recognition time, verify it is still partial, then start
the current-result narration. Record full writing, actual DOM commit and ready controls
separately. Frame-polled commit detection avoids mistaking an assertion's polling delay
for UI latency. Verify encoded images too; DOM timing alone is not a visibility proof.

Do not introduce unseen structured details merely because the summary is visible. Use
claim-specific card-arrival budgets and keep the first option in focus before its
detailed explanation. Preserve the prior-result/next-purpose/action ordering, explicit
human decision and draft review, and short confirmation-to-closing sequence.

**Evidence:** The revised continuous take was 257.66 seconds at 1x. All six non-atomic
replies began narration after 0.625-0.828 seconds of readable-text recognition and
before writing ended, with leads of 0.328-5.531 seconds. The public-context, option and
draft cards committed 0.797, 1.406 and 1.735 seconds after their commentary started.
Seven negative controls rejected premature actions/titles, overlapping bridges, an
extra confirmation recap, waiting for writing completion, speaking before recognition
and late structured details. The seventeen previously approved voice clips were reused;
no narration wording, voice delivery or application source was changed.

**Correction (2026-10-30, silence during animated launches):** The preceding green
257.66-second revision still failed viewer review. After introductory speech, native
typing/thinking continued for roughly 6-11 seconds without narration. The motion guard
accepted those intervals because they were not frozen. Progressive result narration
alone therefore did not fix the launch-to-result handoff.

**Root cause:** The bridge named its purpose late, then the capture mostly finished
that bridge before dispatching or observing the native launch. The next explanation
correctly waited for readable evidence, but almost all question entry, retrieval and
early reveal happened in silence. Beginning the readable-text wait after bridge
completion also prevented useful overlap with the bridge's own approved words.

**Fix:** Replace the affected bridge with approved purpose-first copy. Finish the prior
result, introduce the current purpose, then dispatch its action while the rest of the
bridge explains the current check. Measure native action-to-readable latency and the
actual spoken gate. Observe coherent visible text during bridge playback; preserve
brief recognition and start its explanation before writing finishes. Keep structured
details and human decisions gated separately. Do not repair this with faster speech,
faster footage, cuts through interactions or premature next-task activity.

Add a separate decoded-audio launch-silence guard, independent of screen motion.
The worked acceptance cap was 1.5 seconds at introduction/result boundaries, not at
deliberate reading/review pauses. Require it to reject the known moving/loading failure
that the old silent/static guard accepted. Review a short audiovisual trial when the
viewer says the feeling cannot be judged from text; do not treat trial approval as
authorization to change all remaining copy.

**Evidence:** The old comparison boundary contained 11.0259 seconds of measured
decoded-audio silence despite an empty silent/static failure list. The authorized
42.36-second continuous trial reduced launch silence to 0.4125 seconds, retained
0.64 seconds of visible-text recognition and started explanation 0.875 seconds before
writing ended. Cards committed 1.391 seconds after speech began, before the
option-specific details needed them. The original result clip's SHA-256 was unchanged;
both sampled AAC correlations exceeded 0.99998. The viewer replied "parfait", then
explicitly authorized the complete extension. The trial's measured signals and viewer
approval do not constitute a full-version real-time playback review.
