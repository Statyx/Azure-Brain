# Storytelling and Pacing Playbook

This is a repeatable **starting method**, not pre-approved narration. Tailor it to the
audience and the actual application, then follow the approval gate in
[instructions.md](instructions.md). Keep the language of the delivered video consistent.

## 1. Explain the use case before the first click

Answer five questions in ordinary language: **Who** is acting? **What** just happened?
**Why** does it matter? **What decision** must be made? **What** will the viewer see
the person do? Verify the scenario, dates, figures, names and sources against the product.
Avoid opening with a catalogue of tools or a claim that the audience cannot verify.

Use this adaptable narrative shape, not mandatory wording:

> As a [role], I need to [make a decision] because [business event or problem].
> I'll bring together [relevant evidence] to understand [the stakes] and decide
> [the next action].

Give this context enough time to be understood. In the observed demo, a longer
introduction was preferable to a rapid jump into the interface. Start on a composed,
legible view; as context permits, begin a natural first action during the explanation
rather than leaving an unrelated still on screen. Do not cut or accelerate that action
to fit the introduction.

## 2. Let the story pull the viewer through the work

For each step write three short parts, in the user's point of view where appropriate:

1. **Observation:** what is on screen and the important evidence or figure.
2. **Meaning:** why it matters for this particular use case.
3. **Next question:** what is still unknown and why the next source or action is needed.

Write the bridges **before** capture rather than adding generic filler later. For a wait,
choose one relevant purpose: interpret the last result, explain what the next source
adds, state why timing matters, prepare the choice, or explain why human approval is
necessary. Fit the words to the visible activity; never narrate a completed result before
it exists. A transition can lead the action, but an assertion about a particular card or
result requires that item to be visible while it is described.

Examples to adapt and approve, not claims about any product:

- “Now that I understand the gap, I need to know what the agreement says.”
- “That context shows what the team has already discussed and what still needs attention.”
- “With the evidence together, I can compare the options and choose the best next step.”
- “Before acting, I need the appropriate person to review the plan and its sources.”

For alternatives, show and describe each one in turn, explain its consequence and
trade-off, then show and justify the selected option. Do not move to a different card
while describing the previous one. For a human approval, show who approves, why approval
is needed, the relevant figures and sources, draft review, the requested action, and
confirmation as applicable. Never invent an actual message delivery.

## 3. Finish the story rather than stopping at the last click

After the final action and its confirmation, give the voice a distinct conclusion:
state **what the pieces achieved together**, the business outcome or next step, and why
it matters in the user's workflow. Do not promise an outcome not evidenced by the demo.
Keep the final composed image visible during the conclusion and for a readable hold
after it. Do not fade the first or last image to black.

## 4. Budget time from the actual words and actions

Build a cue sheet with each narration line's actual start/end, the frame where its
supporting result is visible, the relevant click/action start/end, and the planned
next transition. A **fully ready** marker is not necessarily the first visible frame.
Calibrate recording-script clock offsets before comparing them with video timestamps.

Measure each approved audio clip after conversion. Allow enough time for writing,
thinking, reading the choices and reviewing the draft; do not cut them to meet a
duration estimate. If the total exceeds the cap, ask whether to simplify the
approved story, make the take longer or change scope. Do not silently accelerate
the voice or interaction.

As a *review trigger*, flag gaps of **3 seconds or longer** without planned speech,
including the opening and tail. This is not a mandate to talk continuously: the
final hold, deliberate reading time, user-requested silence or a meaningful visible
action may justify a gap. Review every flag in context; prefer a concise approved
bridge over an empty wait when it adds meaning. Never insert narration over existing
words. Also inspect for silence **inside** a voice clip: declared clip boundaries
alone cannot detect it.

## 5. Fast path: preflight, preview, then render

1. Write and approve the full board and copy once; explicitly include the intended
   introduction, transitions, decision, approval and final conclusion.
2. Record a wide, natural-speed continuous take and measure interaction markers.
   Synthesize the chosen approved voice, measure its clips and build the cue sheet.
3. Use the local preflight below to flag planned narration gaps, narration overlapping
   speech, a named result not visible for its line, or a cut inside a recorded action.
   Optionally detect actual low-level audio gaps; neither markers nor silence detection
   prove what the audience can read or hear.
4. Review short excerpts around the difficult transitions and revise locally before
   rendering the whole film. Do not falsely claim a real-time viewing or listening
   review if only images, transcripts or signal measurements were inspected.
5. If the user later approves only an audio change and it fits the existing timeline,
   add the approved clips to a new mix and copy the already validated video stream.
   Verify stream identity and all added and preserved speech, then deliver a new file.
   Otherwise update the timeline and rerender the picture.

### Timeline preflight

Copy [examples/timeline.json](examples/timeline.json) into the production workspace and
replace its example values with **measured output-timeline seconds**. Speech entries
name a visual only when that visual must stay visible for the **whole** utterance.
Actions are protected intervals; cuts strictly inside them are errors. Long uncovered
intervals are warnings, including an intentional final hold: decide each one in context.

```powershell
python <agent-dir>\tools\check_timeline.py <timeline.json> --gap-threshold 3
python <agent-dir>\tools\check_timeline.py <timeline.json> --gap-threshold 3 --audio <narration.wav>
```

Replace placeholders with actual paths. The optional audio analysis runs FFmpeg
`silencedetect`; it detects low-level **signal**, not speech semantics, and a music bed
can hide silence. Check its warnings against the image and voice. The tool reports JSON;
invalid input or an FFmpeg failure is an error, unsafe cue/cut/overlap findings exit
nonzero, and gap warnings remain review items. It does not render, synthesize or publish.
When audio is supplied, its duration must cover the last declared speech and must not
exceed the video timeline; an intentionally silent closing hold can extend beyond audio.
Use a narration file aligned to timeline zero, not an unrelated mix or a music track.

To run the bundled example from the Azure-Brain repository root:

```powershell
$agent = Join-Path (Get-Location) 'Meta-Brain\agents\video-production-agent'
python (Join-Path $agent 'tools\check_timeline.py') (Join-Path $agent 'examples\timeline.json')
```

**Evidence:** The 2026-10-29 demo needed a longer use-case introduction, then five
approved bridges to address waits around context gathering, scenarios and approval.
The continuous version was 181.32 seconds; the five clips fit without shifting the
video stream. Its user described the resulting video as very good. Those specific
durations informed this method, not a universal target for other demos.
An independent preflight of that final mix used 38 transcribed speech intervals and
two protected action intervals; it reported no speech-overlap or cut errors and no
planned or detected signal gaps of at least three seconds. No visual intervals were
mapped in that check, which did not establish subjective pacing.
