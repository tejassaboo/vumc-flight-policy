"""The deterministic verifier. An unknown tool or task id, or anything a check did not expect, is a failed
verdict, never an exception: a verifier that raises leaves the run with no verdict."""

from contract import Task, Tool

from . import booking, tools
from .checks import UNEXPECTED, result

# A tool task's output is its one tool's output.
TOOL_TASKS = {Task.BOOKING_REQUIREMENTS: Tool.BOOKING_REQUIREMENTS, Task.SEARCH_FLIGHTS: Tool.SEARCH_FLIGHTS}


def verify_input(tool, value):
    try:
        return tools.verify_input(Tool(tool), value)
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}")


def verify_output(tool, input_value, output_value, workspace):
    try:
        return tools.verify_output(Tool(tool), input_value, output_value)
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}")


def verify_task(task, arguments, output, reference, workspace):
    try:
        kind = Task(task)
        if kind == Task.BOOK_FLIGHT:
            return booking.verify_task(arguments, output, reference, workspace)
        return tools.verify_output(TOOL_TASKS[kind], arguments, output)
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}", score=0.0)
