"""Shared fixtures and helpers for the Azure-Brain umbrella test suite.

This module is the SINGLE SOURCE OF TRUTH for:
  * which brains are covered (`BRAINS`)
  * how agents are discovered on disk (`agent_dirs`) — depth-aware
  * which catalog entries are expected to exist on disk (`catalog_agent_names`)

Agent folder layout differs per brain:
  Fabric-Brain / Meta-Brain / Foundry-Brain / Apps-Brain : agents/<agent>/             (flat)
  Database-Brain                                         : agents/<NN-domain>/<agent>/ (nested by domain)

`agent_dirs()` handles both: a directory directly under `agents/` is treated as an
agent when it contains `instructions.md`, otherwise as a domain folder whose
children are agents.

Catalog entries carry an optional `status` (`active` / `planned` / `deprecated`).
Only `active` entries (or entries with no status, which is the Fabric/Meta
convention) are required to exist on disk.
"""
import pathlib

import yaml

# ROOT = Azure-Brain umbrella (parent of every brain)
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

BRAINS = ["Fabric-Brain", "Meta-Brain", "Database-Brain", "Foundry-Brain", "Apps-Brain"]

# Catalog statuses that must have a matching folder on disk.
IMPLEMENTED_STATUSES = {"active"}

_PRIVATE_PREFIXES = ("_", ".")


def agents_dir(brain: str) -> pathlib.Path:
    return ROOT / brain / "agents"


def catalog_path(brain: str) -> pathlib.Path:
    return agents_dir(brain) / "_catalog.yaml"


def load_catalog(brain: str) -> dict:
    return yaml.safe_load(catalog_path(brain).read_text(encoding="utf-8"))


def _visible_subdirs(path: pathlib.Path):
    return sorted(d for d in path.iterdir()
                  if d.is_dir() and not d.name.startswith(_PRIVATE_PREFIXES))


def agent_dirs(brain: str) -> list[pathlib.Path]:
    """Every agent folder in a brain, whatever the nesting depth."""
    ad = agents_dir(brain)
    if not ad.exists():
        return []
    out: list[pathlib.Path] = []
    for entry in _visible_subdirs(ad):
        if (entry / "instructions.md").exists():
            out.append(entry)              # flat agent
        else:
            out.extend(_visible_subdirs(entry))   # domain folder → nested agents
    return out


def all_agent_dirs() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for brain in BRAINS:
        out.extend(agent_dirs(brain))
    return out


def agent_id(path: pathlib.Path) -> str:
    """Stable, readable pytest id: '<Brain>/<agent>' or '<Brain>/<domain>/<agent>'."""
    return str(path.relative_to(ROOT)).replace("\\", "/").replace("/agents/", "/")


def folder_agent_names(brain: str) -> set[str]:
    return {d.name for d in agent_dirs(brain)}


def catalog_entries(brain: str) -> list[dict]:
    entries: list[dict] = []
    for domain in load_catalog(brain).get("domains", {}).values():
        entries.extend(domain.get("agents", []))
    return entries


def catalog_agent_names(brain: str, implemented_only: bool = True) -> set[str]:
    """Agent names from the catalog.

    When `implemented_only`, keep entries whose status is in IMPLEMENTED_STATUSES.
    Entries with no `status` key are treated as implemented (Fabric/Meta convention).
    """
    names = set()
    for agent in catalog_entries(brain):
        status = agent.get("status")
        if implemented_only and status is not None and status not in IMPLEMENTED_STATUSES:
            continue
        names.add(agent["name"])
    return names
