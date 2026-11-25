"""The bundled handbook is the frozen file, byte for byte."""

import hashlib
import json

import pytest

from plugin_spec import FROZEN_SHA256SUMS, ROOT

POLICY = ROOT / "src" / "plugin" / "data" / "policy.txt"
FACTS = json.loads((ROOT / "src" / "plugin" / "data" / "handbook.json").read_text(encoding="utf-8"))


def test_policy_hash_is_pinned():
    assert hashlib.sha256(POLICY.read_bytes()).hexdigest() == FACTS["sha256"]


def test_policy_matches_the_frozen_sha256sums():
    if not FROZEN_SHA256SUMS.is_file():
        pytest.skip(f"{FROZEN_SHA256SUMS} is not on this machine")
    sums = dict(reversed(line.split(maxsplit=1)) for line in FROZEN_SHA256SUMS.read_text().splitlines() if line.strip())
    assert sums[FACTS["frozen_file"]] == hashlib.sha256(POLICY.read_bytes()).hexdigest()


def test_word_and_line_counts():
    text = POLICY.read_text(encoding="utf-8")
    assert len(text.split()) == FACTS["words"]
    assert len(text.splitlines()) == FACTS["lines"]


def test_only_the_bundled_path_holds_the_handbook():
    # Stock NanoAgent rejects a root policy.txt (Q2): the handbook lives only under src/plugin/data.
    assert not (ROOT / "policy.txt").exists()
