#!/usr/bin/env python
"""Build the Azure-Brain teaser: 10 typographic boards -> 1920x1080 silent MP4.

Why this file exists
--------------------
The reference teaser (``Fab-Marketing-Campaign/marketing/teaser-c360.mp4``) was produced
outside its repository and cannot be re-cut when a label changes. That is the drift this
script avoids: the boards, the copy and the render are all here, so a wording change is a
re-run, not an archaeology exercise.

Matches the reference format exactly: 1920x1080, h264, 30 fps, **no audio track**.
The reference carries everything typographically; so does this.

    python build_teaser.py --boards    # render the 10 PNG boards only
    python build_teaser.py --render    # boards -> mp4
    python build_teaser.py --all
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
BOARDS = HERE / "boards"
OUT_MP4 = HERE / "teaser-azure-brain-en.mp4"


def _tool(name: str) -> str:
    """Resolve ffmpeg/ffprobe without depending on the shell's PATH.

    winget writes its shims to a Links directory and tells you to restart the shell; a
    long-lived session never does, so a freshly-installed ffmpeg is invisible to
    ``shutil.which`` until the process is replaced. Look it up on disk instead of failing
    with a bare WinError 2.
    """
    import shutil

    found = shutil.which(name)
    if found:
        return found
    candidates = [
        pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe",
        pathlib.Path(r"C:\ProgramData\chocolatey\bin") / f"{name}.exe",
        pathlib.Path(os.environ.get("USERPROFILE", "")) / "scoop" / "shims" / f"{name}.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    machine = os.environ.get("PATH", "")
    for root in (pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",):
        if root.exists():
            hit = next(root.rglob(f"{name}.exe"), None)
            if hit:
                return str(hit)
    sys.exit(f"{name} not found (PATH={machine[:120]}...) — install it, e.g. winget install Gyan.FFmpeg")

DEMO = pathlib.Path(
    os.environ.get("FABRIC_DEMO_ROOT") or HERE.parent.parent
)
# Same repo: always correct wherever the checkout lives.
PROOF = HERE.parent / "docs" / "proof"
# Different repo. Defaults to the sibling checkout next to Azure-Brain; set
# FABRIC_DEMO_ROOT if the two repos are not siblings.
SHOTS = DEMO / "Fab-Marketing-Campaign" / "marketing" / "screenshots"

W, H = 1920, 1080
FPS = 30
XFADE = 0.5         # crossfade between boards

# Per-board hold, in seconds. Kept on the board rather than in a parallel list so that
# cutting a board cannot silently shift every duration after it.
#
# The rhythm is deliberate and uneven: the setup (2-4) is tightened so the brain reveal
# lands at ~15 s instead of ~24 s, the reveal itself (5) gets air, and the last board is
# the longest because nothing fades after it.
# Total = sum(hold) - 9 * XFADE = 44.6 - 4.5 = 40.1 s

# Each board: kicker, line 1 (white), line 2 (accent), subtitle, background, dim preset.
# `dim` is chosen per source: the instruction-file shots are already dark, the app shots
# are light and need to lose more, or the white type stops being legible over them.
SCENES = [
    dict(
        kicker="AZURE-BRAIN",
        l1="What you learn building",
        l2="is always lost.",
        hold=5.2,
        sub="The next project relearns it from scratch.",
        bg=PROOF / "02-instructions.png",
        dim="dark",
        pos="center top",
    ),
    dict(
        kicker="TWO PROJECTS",
        l1="Retail. Telco.",
        l2="Nothing in common.",
        hold=3.8,
        sub="Different data, different jobs, different questions.",
        bg=PROOF / "04-portal.png",
        dim="light",
        pos="center center",
    ),
    dict(
        kicker="CUSTOMER 360 · MICROSOFT FABRIC",
        l1="A cockpit for",
        l2="customer knowledge.",
        hold=4.2,
        sub="Lakehouse, Direct Lake, ontology — four assistants that show where they looked.",
        # `center top` because these app captures are content in the upper half and empty
        # white below; centred, the frame filled with the blank part and the board read as
        # a grey wash with no product in it.
        bg=SHOTS / "v2-retention.png",
        dim="light",
        pos="center top",
        zoom=1.22,
    ),
    dict(
        kicker="NETWORK OPERATIONS · MICROSOFT FABRIC",
        l1="Detect. Diagnose.",
        l2="Impact.",
        hold=3.8,
        sub="A PFC storm on a switch in Lille, traced through the graph to the customers it hits.",
        bg=None,                      # no capture exists for this project yet
        dim="none",
        pos="center center",
    ),
    dict(
        kicker="THE SAME BRAIN",
        l1="Same agents.",
        l2="Same instruction files.",
        hold=5.0,
        sub="Both were built by reading the same knowledge base.",
        bg=PROOF / "02-instructions.png",
        dim="dark",
        pos="center center",
    ),
    dict(
        kicker="AZURE-BRAIN",
        l1="No application.",
        l2="Nothing to run.",
        hold=4.0,
        sub="42 agents across 5 brains — only what an agent needs to know before it acts.",
        # Deliberately no capture: this is the one claim the board can *demonstrate* rather
        # than illustrate. Putting a deployed architecture behind "nothing to run" would have
        # argued against the line it sits under.
        bg=None,
        dim="none",
        pos="center center",
        alt_base=True,
    ),
    dict(
        kicker="WHY THE RULES EXIST",
        l1="Every rule",
        l2="encodes an incident.",
        hold=4.0,
        sub="Nothing is marked verified without a trace behind it.",
        bg=PROOF / "02-instructions.png",
        dim="dark",
        pos="center bottom",
        zoom=1.45,
    ),
    dict(
        kicker="THE INDUSTRY IS AN AXIS",
        l1="The tables change.",
        l2="The rules don't.",
        hold=4.0,
        sub="Retail: a starter kit plus an ontology module. Telco: graph and real time.",
        bg=PROOF / "03-ontology.png",
        dim="light",
        pos="center center",
    ),
    dict(
        # No trailing em dash: it is a break opportunity, so it wrapped onto a line of its
        # own and the board read as three lines with an orphan rule in the middle.
        kicker="SHOW, DON'T ASSERT",
        l1="A question in plain language,",
        l2="and the query it ran.",
        hold=4.8,
        sub="The answer names its source, next to the report the number comes from.",
        bg=PROOF / "01-agent-and-report.png",
        dim="light",
        pos="center center",
    ),
    dict(
        kicker="AZURE-BRAIN",
        l1="What you learned.",
        l2="Reusable.",
        # Longest hold: nothing fades after this board, so it is the frame the viewer is
        # left on when playback stops.
        hold=5.8,
        sub="github.com/Statyx/Azure-Brain",
        bg=PROOF / "social-card.png",
        dim="light",
        pos="center center",
    ),
]

DIM = {
    # The point of keeping a real screenshot behind the type is that it stays *readable as a
    # product*. Dimmed to .40 it was indistinguishable from a texture, which is the same as
    # having no proof on screen at all.
    "dark": "brightness(.46) saturate(.85) contrast(1.02)",
    "light": "brightness(.55) saturate(.55) contrast(1.04)",
    "none": "none",
}

_TPL = """<!doctype html>
<html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:{W}px; height:{H}px; overflow:hidden; background:#080b14; }}
  .board {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; }}

  /* Base wash: on the one board with no capture behind it, this IS the visual, so it has to
     carry weight on its own rather than read as flat black. */
  .base {{ position:absolute; inset:0;
    background:
      radial-gradient(1500px 1000px at 74% 22%, rgba(84,132,235,.42), transparent 60%),
      radial-gradient(1200px 900px at 16% 86%, rgba(140,104,238,.34), transparent 58%),
      radial-gradient(900px 900px at 96% 96%, rgba(58,96,190,.26), transparent 62%),
      linear-gradient(155deg, #101a2f 0%, #0a0f1c 58%, #0c1020 100%); }}
  /* Second no-capture board: same palette, mirrored, so the two "empty" boards don't read
     as the same slide shown twice. */
  .base.alt {{
    background:
      radial-gradient(1400px 1050px at 22% 26%, rgba(140,104,238,.38), transparent 60%),
      radial-gradient(1300px 950px at 82% 80%, rgba(84,132,235,.36), transparent 58%),
      radial-gradient(950px 950px at 8% 96%, rgba(58,96,190,.24), transparent 62%),
      linear-gradient(198deg, #141428 0%, #0a0f1c 56%, #0b1224 100%); }}

  .bg {{ position:absolute; inset:0; width:100%; height:100%;
    object-fit:cover; object-position:{POS};
    filter:{DIMF}; transform:scale({ZOOM}); transform-origin:center; }}

  /* Directional scrim so the left third -- where the type sits -- stays the darkest area. */
  .scrim {{ position:absolute; inset:0;
    background:
      linear-gradient(100deg, rgba(8,11,20,.93) 0%, rgba(8,11,20,.80) 42%,
                      rgba(8,11,20,.55) 72%, rgba(8,11,20,.48) 100%),
      radial-gradient(120% 100% at 50% 50%, transparent 42%, rgba(4,6,12,.55) 100%); }}
  /* Without a capture there is nothing to knock back, and the full scrim just erased the
     gradient underneath. */
  .scrim.noimg {{
    background:
      linear-gradient(100deg, rgba(8,11,20,.62) 0%, rgba(8,11,20,.34) 46%,
                      rgba(8,11,20,.10) 78%, rgba(8,11,20,0) 100%),
      radial-gradient(125% 105% at 46% 50%, transparent 46%, rgba(4,6,12,.52) 100%); }}

  .copy {{ position:absolute; inset:0; display:flex; flex-direction:column;
    justify-content:center; align-items:flex-start; padding:0 150px;
    font-family:'Segoe UI Variable Display','Segoe UI',Inter,system-ui,sans-serif;
    -webkit-font-smoothing:antialiased; }}

  .kicker {{ font-size:28px; font-weight:700; letter-spacing:.20em; text-transform:uppercase;
    color:#5b9cf8; margin-bottom:34px; }}

  h1 {{ font-size:104px; font-weight:800; line-height:1.06; letter-spacing:-.021em;
    color:#fff; max-width:1500px; }}
  h1 .l2 {{ display:block;
    background:linear-gradient(96deg,#6ea8ff 0%,#9db4ff 46%,#b79cf9 100%);
    -webkit-background-clip:text; background-clip:text; color:transparent; }}

  .sub {{ margin-top:34px; font-size:36px; font-weight:400; line-height:1.36;
    color:rgba(255,255,255,.74); max-width:1180px; }}
</style></head><body>
  <div class="board">
    <div class="base{BASEMOD}"></div>
    {IMG}
    <div class="scrim{SCRIMMOD}"></div>
    <div class="copy">
      <div class="kicker">{KICKER}</div>
      <h1><span class="l1">{L1}</span><span class="l2">{L2}</span></h1>
      <p class="sub">{SUB}</p>
    </div>
  </div>
</body></html>"""


def _data_uri(p: pathlib.Path) -> str:
    # Playwright renders file:// image srcs as empty boxes in set_content(), so every board
    # has to be a self-contained document.
    if not p.exists():
        sys.exit(
            f"missing background: {p}\n"
            "The app screenshots live in the Fab-Marketing-Campaign checkout. Set "
            "FABRIC_DEMO_ROOT to the folder holding both repos if they are not siblings."
        )
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html_for(scene: dict) -> str:
    """Inline the background as a data URI.

    A ``file://`` src would be subject to the page's origin rules and silently render an
    empty box; embedding removes the whole class of problem and makes each board a single
    self-contained document.
    """
    img = ""
    if scene["bg"] is not None:
        if not scene["bg"].exists():
            sys.exit(f"missing background: {scene['bg']}")
        img = f'<img class="bg" src="{_data_uri(scene["bg"])}">'
    return _TPL.format(
        W=W, H=H,
        POS=scene.get("pos", "center center"),
        DIMF=DIM[scene["dim"]],
        ZOOM=scene.get("zoom", 1.0),
        IMG=img,
        SCRIMMOD="" if img else " noimg",
        BASEMOD=" alt" if scene.get("alt_base") else "",
        KICKER=_esc(scene["kicker"]),
        L1=_esc(scene["l1"]),
        L2=_esc(scene["l2"]),
        SUB=_esc(scene["sub"]),
    )


def build_boards() -> list[pathlib.Path]:
    from playwright.sync_api import sync_playwright

    BOARDS.mkdir(parents=True, exist_ok=True)
    out: list[pathlib.Path] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, scene in enumerate(SCENES, start=1):
            page.set_content(html_for(scene), wait_until="load")
            page.wait_for_timeout(180)          # let the gradient text settle before capture
            dst = BOARDS / f"board-{i:02d}.png"
            page.screenshot(path=str(dst))
            out.append(dst)
            print(f"  board {i:02d}  {scene['l1']} / {scene['l2']}")
        browser.close()
    return out


def contact_sheet() -> pathlib.Path:
    """A 2x5 montage of every board.

    Reviewing boards one file at a time hides the thing that actually goes wrong in a
    typographic cut: repetition. Seeing all ten at once is how you notice that three of them
    share a background.
    """
    boards = sorted(BOARDS.glob("board-*.png"))
    if not boards:
        sys.exit("no boards -- run --boards first")
    dst = HERE / "contact-sheet.png"
    cmd: list[str] = [_tool("ffmpeg"), "-y"]
    for b in boards:
        cmd += ["-i", str(b)]
    n = len(boards)
    chain = [f"[{i}:v]scale=640:360,drawbox=0:0:640:360:0x5b9cf8@0.5:t=2[c{i}]" for i in range(n)]
    chain.append("".join(f"[c{i}]" for i in range(n)) + f"xstack=inputs={n}:layout="
                 + "|".join(f"{(i % 5) * 640}_{(i // 5) * 360}" for i in range(n)) + "[out]")
    cmd += ["-filter_complex", ";".join(chain), "-map", "[out]", "-frames:v", "1", str(dst)]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"contact sheet -> {dst}")
    return dst


def render() -> None:
    """Concatenate the boards with crossfades.

    Two frames matter more than the rest, and both must be a composed board, never black:

    - **Frame 0** carries no ``fade=t=in``: it becomes the poster used by Explorer, Teams,
      PowerPoint and link previews. A black first frame makes the link look broken.
    - **The last frame** carries no ``fade=t=out``: playback stops on it, and it is what a
      paused player, a looping embed or an end card leaves on screen. Fading to black
      throws away the closing message and ends the piece on nothing.
    """
    boards = sorted(BOARDS.glob("board-*.png"))
    if len(boards) != len(SCENES):
        sys.exit(f"expected {len(SCENES)} boards, found {len(boards)} -- run --boards first")

    holds = [float(s["hold"]) for s in SCENES]

    cmd: list[str] = [_tool("ffmpeg"), "-y"]
    for b, hold in zip(boards, holds):
        cmd += ["-loop", "1", "-t", str(hold), "-i", str(b)]

    chain: list[str] = []
    for i in range(len(boards)):
        chain.append(f"[{i}:v]scale={W}:{H},setsar=1,fps={FPS},format=yuv420p[v{i}]")

    prev, offset = "v0", holds[0] - XFADE
    for i in range(1, len(boards)):
        label = f"x{i}"
        chain.append(
            f"[{prev}][v{i}]xfade=transition=fade:duration={XFADE}:offset={offset:.3f}[{label}]"
        )
        prev = label
        offset += holds[i] - XFADE

    # No trailing fade: the last board is held to the final frame.
    chain.append(f"[{prev}]null[vout]")

    cmd += [
        "-filter_complex", ";".join(chain),
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-an",                                  # the reference teaser has no audio track
        str(OUT_MP4),
    ]
    subprocess.run(cmd, check=True)

    # Verify the artefact, not the exit code.
    probe = subprocess.run(
        [_tool("ffprobe"), "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-show_entries", "format=duration", "-of", "default=nw=1", str(OUT_MP4)],
        capture_output=True, text=True, check=True,
    )
    first = HERE / "first-frame.png"
    subprocess.run([_tool("ffmpeg"), "-y", "-i", str(OUT_MP4), "-frames:v", "1", "-q:v", "2",
                    str(first)], check=True, capture_output=True)

    # Extract the last frame too, and assert it is not black. A trailing fade is easy to
    # reintroduce by accident and invisible in every check that only looks at duration.
    last = HERE / "last-frame.png"
    subprocess.run([_tool("ffmpeg"), "-y", "-sseof", "-0.2", "-i", str(OUT_MP4),
                    "-update", "1", "-q:v", "2", str(last)], check=True, capture_output=True)
    lum = subprocess.run(
        [_tool("ffmpeg"), "-v", "error", "-sseof", "-0.2", "-i", str(OUT_MP4),
         "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
         "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    # `file=-` is required: metadata=print logs at info level, so `-v error` swallows it and
    # the guard silently measures nothing.
    yavg = [
        float(line.split("=")[-1])
        for line in lum.stdout.splitlines()
        if "YAVG" in line
    ]
    if not yavg:
        sys.exit("could not measure the last frame's luminance — guard cannot be trusted")
    # min, not max: a fade darkens the *final* frames, so the darkest sample in the tail
    # window is what gives it away. Full black in limited-range YUV sits at 16.
    if min(yavg) < 20:
        sys.exit(f"last frame is black (YAVG={min(yavg):.1f}) — a trailing fade crept back in")

    print(f"\n{OUT_MP4}\n{probe.stdout.strip()}\n"
          f"first frame -> {first} (must show board 1)\n"
          f"last frame  -> {last} (board {len(boards)}, YAVG={min(yavg):.1f}, not black)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.boards or a.all:
        build_boards()
    if a.sheet or a.all:
        contact_sheet()
    if a.render or a.all:
        render()
    if not (a.boards or a.sheet or a.render or a.all):
        ap.print_help()
