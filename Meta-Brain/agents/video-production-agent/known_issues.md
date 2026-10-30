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
