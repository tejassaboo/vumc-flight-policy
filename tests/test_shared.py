"""The tools and the verifier share their logic byte for byte (the verifier may not import src/)."""

import pytest

from plugin_spec import ROOT

SHARED = ["world.py", "scenarios.py", "guide.py", "answer.py", "rules.py"]


@pytest.mark.parametrize("name", SHARED)
def test_byte_identical(name):
    assert (ROOT / "src" / "plugin" / name).read_bytes() == (ROOT / "verifier" / name).read_bytes(), name
