"""The bundled scenarios and handbook facts of the original-handbook template, shared byte for byte by the
tools (src/plugin/scenarios.py) and the verifier (verifier/scenarios.py). Both read the files under
src/plugin/data, found from this file's own folder."""

import dataclasses
import json
import typing
from enum import Enum
from functools import cache
from pathlib import Path

from contract import Airport, Scenario, Trip

from .world import airport

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" if (HERE / "data").is_dir() else HERE.parent / "src" / "plugin" / "data"
SCALARS = (str, int, bool)


@cache
def read_data(name):
    return (DATA / name).read_text(encoding="utf-8")


def scenario(name):
    """A fresh copy of one scenario's JSON, by id (a contract.Scenario member or its value)."""
    value = Scenario(name).value
    data = json.loads(read_data(f"scenarios/{value}.json"))
    # The handbook's default number of background offers per search (handbook.json "background_offers"),
    # used where the scenario and its search set none.
    data["world"]["handbook_background"] = handbook()["background_offers"]
    return data


def scenario_ids():
    return [member.value for member in Scenario]


def handbook():
    """The handbook facts: id, slug, frozen file sha256, words, source."""
    return json.loads(read_data("handbook.json"))


def currency():
    return handbook()["currency"]


def policy_text():
    return read_data("policy.txt")


def build(kind, value, where="value"):
    """``value`` (plain JSON) built strictly into the contract type ``kind``: every field present, none
    extra, no bool for an int. The verifier may not import slimconfig, so both sides use this."""
    if isinstance(kind, type) and isinstance(value, kind) and not isinstance(value, SCALARS):
        return value
    if kind is Airport and isinstance(value, str):
        return airport(value)
    if typing.get_origin(kind) is list:
        if not isinstance(value, list):
            raise ValueError(f"{where}: expected a list")
        item = typing.get_args(kind)[0]
        return [build(item, entry, f"{where}[{index}]") for index, entry in enumerate(value)]
    if isinstance(kind, type) and issubclass(kind, Enum):
        return kind(value)
    if dataclasses.is_dataclass(kind):
        if not isinstance(value, dict):
            raise ValueError(f"{where}: expected an object")
        hints = typing.get_type_hints(kind)
        names = [field.name for field in dataclasses.fields(kind)]
        if sorted(value) != sorted(names):
            raise ValueError(f"{where}: fields {sorted(value)} are not {sorted(names)}")
        return kind(**{name: build(hints[name], value[name], f"{where}.{name}") for name in names})
    if kind in SCALARS:
        if type(value) is not kind:
            raise ValueError(f"{where}: expected {kind}, got {value!r}")
        return value
    raise ValueError(f"{where}: unsupported type {kind}")


def trip_record(scenario_data):
    """The scenario's trip as a contract.Trip: any field the contract types as an Airport may be written as
    an airport code in the scenario JSON, and is expanded to the airport."""
    return build(Trip, scenario_data["trip"], "trip")
