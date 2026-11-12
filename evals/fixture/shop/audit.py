"""Audit trail."""
import json
import time

PATH = "audit.log"


def _stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def record(event, **data):
    line = json.dumps({"at": _stamp(), "event": event, **data})
    with open(PATH, "a") as f:
        f.write(line + "\n")
