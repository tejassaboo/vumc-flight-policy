"""Two identical verifier runs: the same verdicts twice in one process (as NanoAgent's helper calls it) and
across two fresh `python -I` processes (different hash seeds)."""

import json
import subprocess
import sys

import verifier
from contract import Task
from helpers import build_task_input, reference, right_answer, scenarios
from plugin_spec import ROOT

SCRIPT = """
import json, sys
sys.path[:0] = [sys.argv[1], sys.argv[1] + "/src"]
import verifier
from contract import Task
sys.path.insert(0, sys.argv[1] + "/tests")
from helpers import build_task_input, reference, right_answer, scenarios
out = {}
for data in scenarios():
    key = reference(data)
    out[data["id"]] = [verifier.verify_task(Task.BOOK_FLIGHT.value, build_task_input(data), right_answer(key), key, "."),
                       verifier.verify_task(Task.BOOK_FLIGHT.value, build_task_input(data), right_answer(key), None, ".")]
print(json.dumps(out, sort_keys=True, default=lambda value: getattr(value, "value", str(value))))
"""


def test_two_calls_in_one_process_agree():
    for data in scenarios():
        key = reference(data)
        first = verifier.verify_task(Task.BOOK_FLIGHT.value, build_task_input(data), right_answer(key), key, ".")
        second = verifier.verify_task(Task.BOOK_FLIGHT.value, build_task_input(data), right_answer(key), key, ".")
        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_two_fresh_processes_agree():
    runs = []
    for seed in ("1", "2"):
        completed = subprocess.run([sys.executable, "-I", "-c", SCRIPT, str(ROOT)], capture_output=True, text=True,
                                   check=True, env={"PYTHONHASHSEED": seed})
        runs.append(completed.stdout)
    assert runs[0] == runs[1] and runs[0].strip()
