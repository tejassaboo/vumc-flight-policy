"""Id check: a new plugin id, never a published one, the same everywhere it is written."""

import json
import tomllib

import yaml

from plugin_spec import PUBLISHED_IDS, ROOT


def manifest():
    return yaml.safe_load((ROOT / "nanoagent.yaml").read_text(encoding="utf-8"))


def test_id_is_new_and_consistent():
    data = manifest()
    plugin_id = data["id"]
    assert plugin_id not in PUBLISHED_IDS, f"{plugin_id} is a published id"
    assert ROOT.name == plugin_id
    handbook = json.loads((ROOT / "src/plugin/data/handbook.json").read_text(encoding="utf-8"))
    assert handbook["id"] == plugin_id and handbook["name"] == data["name"]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["name"] == f"nanoagent-{plugin_id}"
    assert project["version"] == data["version"]
    assert (ROOT / "README.md").read_text(encoding="utf-8").split("\n")[0] == f"# {data['name']}"
