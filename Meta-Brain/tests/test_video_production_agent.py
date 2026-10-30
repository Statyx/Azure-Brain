"""Guard the video agent's discoverability and essential production gates."""

from conftest import ROOT, catalog_entries


AGENT = ROOT / "Meta-Brain" / "agents" / "video-production-agent"


def test_video_agent_is_catalogued_and_routed():
    names = {entry["name"] for entry in catalog_entries("Meta-Brain")}
    assert "video-production-agent" in names
    routing = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "narrated product, marketing or screen-recorded demo video" in routing
    assert "`video-production-agent` | Meta" in routing


def test_video_agent_requires_approval_and_continuity():
    instructions = (AGENT / "instructions.md").read_text(encoding="utf-8")
    assert "Before generating voice audio or rendering the final video" in instructions
    assert "Wait for explicit user approval" in instructions
    assert "Do not cut through typing" in instructions
    assert "synthesize only approved additions" in instructions.lower()
    assert "never claim to have watched or listened" in instructions.lower()


def test_video_agent_records_audio_only_and_quality_gates():
    workflow = (AGENT / "production_workflow.md").read_text(encoding="utf-8")
    assert "-c:v copy" in workflow
    assert "video stream" in workflow
    assert "fail on **no samples**" in workflow
    assert "min(YAVG) < 20" in workflow
    assert "byte-for-byte" in workflow
    assert "automated checks are not a substitute" in workflow
