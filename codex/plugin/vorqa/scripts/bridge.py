#!/usr/bin/env python3
"""Explicit bridge to an existing AVRL workspace; not a plugin installer.

A workspace's controller must match this adapter's pinned source digest and have a specs/ tree.
Controller actions are allowlisted and require an explicit caller; summaries never claim verified PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time

SLUG = re.compile(r"[a-z][a-z0-9-]{1,48}\Z")
TIMEOUT = 12
MAX_CONTROLLER_BYTES = 256 * 1024
MAX_CONTROLLER_SUMMARY = 2048
MAX_CONTROLLER_CAPTURE_BYTES = 64 * 1024
CONTROLLER_TIMEOUT = 900
QUICK_CONTROLLER_TIMEOUT = 30
CONTROLLER_COMMANDS = frozenset({"approve", "blind", "complete", "release-attest", "review", "round", "status", "verify"})
INTERACTIVE_COMMANDS = frozenset({"approve", "release-attest"})
MUTATING_CONTROLLER_COMMANDS = frozenset({"blind", "complete", "review", "round", "verify"})
# Pinned to claude/implementation/scripts/avrl.py at PR #14 head 9175b210ea98d4a06606b1c3ea17da6b2936ec25.
TRUSTED_CONTROLLER_SHA256 = "db6a055f7f944c7925156890e19bcab7506b3281f51c26878c61845ad14cd0b2"
TRUSTED_TRACE_EVENTS_SHA256 = "3e957a79077e3b905017640de545464905e9eea208b7797236c6ae249367b35e"
STATUSES = frozenset({"draft", "in-review", "awaiting-approval", "approved", "building", "verifying", "reviewing", "rethink", "paused", "failed", "completed"})
RISKS = frozenset({"low", "medium", "high"})


def emit(kind: str, **fields: object) -> None:
    print(json.dumps({"bridge_schema": 1, "kind": kind, **fields}, sort_keys=True))


def inspect_workspace(root: Path) -> tuple[bool, str]:
    """Reject incomplete, non-root, or symlinked controllers before execution."""
    if not root.is_dir():
        return False, "workspace_missing"
    scripts = root / "scripts"
    specs = root / "specs"
    controller = scripts / "avrl.py"
    if (scripts.is_symlink() or specs.is_symlink() or not controller.is_file()
            or controller.is_symlink() or not specs.is_dir()
            or not controller.resolve().is_relative_to(root)):
        return False, "controller_not_installed"
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True, timeout=TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False, "git_unavailable"
    if result.returncode or Path(result.stdout.strip()).resolve() != root:
        return False, "not_git_root"
    return True, "controller_present"


def read_script_bytes(root: Path, filename: str) -> bytes | None:
    """Read a bounded regular script without following its file or scripts-dir symlink."""
    scripts = root / "scripts"
    try:
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        if os.name == "posix" and hasattr(os, "O_DIRECTORY") and os.open in os.supports_dir_fd:
            directory = os.open(scripts, os.O_RDONLY | os.O_DIRECTORY | nofollow)
            try:
                descriptor = os.open(filename, os.O_RDONLY | nofollow, dir_fd=directory)
            finally:
                os.close(directory)
        else:
            descriptor = os.open(scripts / filename, os.O_RDONLY | nofollow)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_CONTROLLER_BYTES:
                return None
            source = stream.read(MAX_CONTROLLER_BYTES + 1)
    except OSError:
        return None
    if len(source) > MAX_CONTROLLER_BYTES:
        return None
    return source


def trusted_controller_source(root: Path) -> bytes | None:
    """Read and pin the exact controller bytes before executing them in isolation."""
    source = read_script_bytes(root, "avrl.py")
    if source is None or hashlib.sha256(source).hexdigest() != TRUSTED_CONTROLLER_SHA256:
        return None
    return source


def trusted_trace_events_source(root: Path) -> bytes | None:
    """Return the pinned helper bytes dynamically loaded by state transitions."""
    source = read_script_bytes(root, "trace_events.py")
    if source is None or hashlib.sha256(source).hexdigest() != TRUSTED_TRACE_EVENTS_SHA256:
        return None
    return source


def observed_status(root: Path, feature: str) -> tuple[bool, str, dict[str, object]]:
    if not SLUG.fullmatch(feature):
        return False, "invalid_feature", {}
    ready, reason = inspect_workspace(root)
    if not ready:
        return False, reason, {}
    source = trusted_controller_source(root)
    if source is None:
        return False, "untrusted_controller", {}
    exit_code, stdout, _stderr, failure = execute_pinned_controller(
        root, source, None, ["status", feature, "--json"], timeout_seconds=TIMEOUT
    )
    if failure:
        return False, failure, {}
    if exit_code:
        return False, "controller_rejected", {}
    try:
        state = json.loads(stdout.decode("utf-8"))
    except (TypeError, ValueError):
        return False, "malformed_controller_response", {}
    if not isinstance(state, dict) or state.get("feature") != feature:
        return False, "mismatched_controller_response", {}
    status = state.get("status")
    risk = state.get("risk")
    if not isinstance(status, str) or status not in STATUSES or not isinstance(risk, str) or risk not in RISKS:
        return False, "malformed_controller_response", {}
    if any(type(state.get(key)) is not int or not 0 <= state[key] <= 100
           for key in ("round", "max_rounds")):
        return False, "malformed_controller_response", {}
    public = {key: state[key] for key in ("feature", "status", "risk", "round", "max_rounds")
              if key in state and isinstance(state[key], (str, int)) and not isinstance(state[key], bool)}
    return True, "observed_unverified", public


def controller_summary(command: str, stdout: bytes, stderr: bytes, exit_code: int) -> str | None:
    """Return a bounded allowlisted summary, never controller logs or raw test output."""
    if exit_code:
        message = ""
        for line in stderr.decode("utf-8", "replace").splitlines():
            if line.startswith("AVRL ERROR:"):
                message = line.removeprefix("AVRL ERROR:").strip()
                break
        if message.startswith("Completion denied:"):
            return "rejected: completion_denied"
        if re.fullmatch(r"No state for [a-z][a-z0-9-]{1,48}; run init", message):
            return "rejected: feature_not_initialized"
        if message == "Approval absent/expired/tampered; re-approve after changing eval":
            return "rejected: approval_missing_or_stale"
        if re.fullmatch(r"Cannot start round from [a-z-]+", message):
            return "rejected: round_transition_denied"
        if message == "Verify only during active building/verifying":
            return "rejected: verify_transition_denied"
        return "controller rejected transition"

    lines = stdout.decode("utf-8", "replace").splitlines()
    if command == "status":
        try:
            state = json.loads("\n".join(lines))
        except (TypeError, ValueError):
            return None
        if (not isinstance(state, dict) or not isinstance(state.get("feature"), str)
                or not isinstance(state.get("status"), str) or state.get("status") not in STATUSES
                or not isinstance(state.get("risk"), str) or state.get("risk") not in RISKS
                or any(type(state.get(key)) is not int or not 0 <= state[key] <= 100
                       for key in ("round", "max_rounds"))
                or state["round"] > state["max_rounds"]):
            return None
        return (f"feature={state['feature']} status={state['status']} risk={state['risk']} "
                f"round={state['round']}/{state['max_rounds']}")
    if command == "round":
        match = re.fullmatch(r"Round (\d+) started; delegate builder", " ".join(lines))
        return f"round_started={match.group(1)}" if match else None
    if command == "verify":
        checks = []
        for line in lines:
            match = re.match(r"([A-Za-z0-9_.-]{1,80}) (PASS|FAIL) ", line)
            if match:
                checks.append(f"{match.group(1)}:{match.group(2)}")
        return ("checks=" + ",".join(checks))[:MAX_CONTROLLER_SUMMARY] if checks else None
    if command == "review":
        match = re.fullmatch(r"Reviewer recorded: (pass|fail) status: (reviewing|rethink)", " ".join(lines))
        return f"review={match.group(1)} status={match.group(2)}" if match else None
    if command == "blind":
        match = re.fullmatch(r"Blind QA result: (pass|fail)", " ".join(lines))
        return f"blind_qa={match.group(1)}" if match else None
    if command == "complete":
        match = re.fullmatch(r"COMPLETED ([a-z][a-z0-9-]{1,48}) ([0-9a-f]{40,64})", " ".join(lines))
        return f"completed={match.group(1)} sha={match.group(2)}" if match else None
    if command == "approve":
        match = re.search(r"Approval attested (\d+) / (\d+)", " ".join(lines))
        return f"approval_count={match.group(1)}/{match.group(2)}" if match else None
    if command == "release-attest":
        match = re.search(r"Release approvals: (\d+) required: (\d+)", " ".join(lines))
        return f"release_approvals={match.group(1)}/{match.group(2)}" if match else None
    return None


def stop_controller_process(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "posix":
            # The controller can leave descendants holding the captured pipes open.
            os.killpg(process.pid, signal.SIGKILL)
        elif process.poll() is None:
            process.kill()
    except ProcessLookupError:
        pass
    process.wait()


def execute_pinned_controller(root: Path, source: bytes, trace_source: bytes | None,
                              controller_args: list[str], timeout_seconds: float | None = None
                              ) -> tuple[int | None, bytes, bytes, str | None]:
    """Execute the validated source with bounded output capture and process-tree cleanup."""
    runner = ("import importlib.util\n"
              "import os\n"
              "import sys\n"
              "root = sys.argv[1]\n"
              "controller_args = sys.argv[2:]\n"
              "def read_exactly(size):\n"
              "    data = bytearray()\n"
              "    while len(data) < size:\n"
              "        chunk = sys.stdin.buffer.read(size - len(data))\n"
              "        if not chunk: raise SystemExit(2)\n"
              "        data.extend(chunk)\n"
              "    return bytes(data)\n"
              "def read_blob():\n"
              "    size = int.from_bytes(read_exactly(4), 'big')\n"
              "    if size > 262144: raise SystemExit(2)\n"
              "    return read_exactly(size)\n"
              "source = read_blob()\n"
              "trace_source = read_blob()\n"
              "source_name = root + '/scripts/.codex-verified-avrl.py'\n"
              "trace_path = os.path.normpath(root + '/scripts/trace_events.py')\n"
              "original_spec = importlib.util.spec_from_file_location\n"
              "class PinnedTraceLoader:\n"
              "    def create_module(self, spec): return None\n"
              "    def exec_module(self, module):\n"
              "        exec(compile(trace_source, trace_path, 'exec'), module.__dict__)\n"
              "def pinned_spec(name, location, *args, **kwargs):\n"
              "    if name == '_avrl_trace':\n"
              "        if trace_path is None or os.path.normpath(os.fspath(location)) != trace_path:\n"
              "            raise ImportError('unapproved AVRL trace module path')\n"
              "        return importlib.util.spec_from_loader(name, PinnedTraceLoader(), origin=trace_path)\n"
              "    return original_spec(name, location, *args, **kwargs)\n"
              "importlib.util.spec_from_file_location = pinned_spec\n"
              "sys.argv = ['avrl.py', *controller_args]\n"
              "exec(compile(source, source_name, 'exec'), {'__file__': source_name, '__name__': '__main__'})\n")
    try:
        process = subprocess.Popen(
            [sys.executable, "-I", "-c", runner, str(root), *controller_args],
            cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0, start_new_session=(os.name == "posix")
        )
    except OSError:
        return None, b"", b"", "controller_unavailable"

    selector = selectors.DefaultSelector()
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    total = 0
    timeout = timeout_seconds or (
        CONTROLLER_TIMEOUT if controller_args and controller_args[0] == "verify"
        else QUICK_CONTROLLER_TIMEOUT
    )
    deadline = time.monotonic() + timeout
    try:
        assert process.stdin is not None
        trace_bytes = trace_source or b""
        process.stdin.write(len(source).to_bytes(4, "big") + source
                            + len(trace_bytes).to_bytes(4, "big") + trace_bytes)
        process.stdin.close()
        assert process.stdout is not None and process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, timeout)
            for key, _ in selector.select(min(remaining, 0.1)):
                chunk = os.read(key.fileobj.fileno(), 4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                if total + len(chunk) > MAX_CONTROLLER_CAPTURE_BYTES:
                    stop_controller_process(process)
                    return None, b"", b"", "controller_output_too_large"
                total += len(chunk)
                buffer = captured[key.data]
                buffer.extend(chunk)
        exit_code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        stop_controller_process(process)
        return None, b"", b"", "controller_timeout"
    except (BrokenPipeError, OSError):
        stop_controller_process(process)
        return None, b"", b"", "controller_unavailable"
    finally:
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
    return exit_code, bytes(captured["stdout"]), bytes(captured["stderr"]), None


def run_controller(root: Path, controller_args: list[str]) -> tuple[int, str, dict[str, object]]:
    if controller_args and controller_args[0] == "--":
        controller_args = controller_args[1:]
    command = controller_args[0] if controller_args else ""
    fields: dict[str, object] = {"command": command or "unknown"}
    if command not in CONTROLLER_COMMANDS or "--help" in controller_args or "-h" in controller_args:
        return 2, "unsupported_controller_command", fields
    if len(controller_args) < 2 or not SLUG.fullmatch(controller_args[1]):
        return 2, "invalid_feature", fields
    if command in INTERACTIVE_COMMANDS:
        return 2, "operator_handoff_required", fields
    ready, reason = inspect_workspace(root)
    if not ready:
        return 2, reason, fields
    source = trusted_controller_source(root)
    if source is None:
        return 2, "untrusted_controller", fields

    trace_source = None
    if command in MUTATING_CONTROLLER_COMMANDS:
        trace_source = trusted_trace_events_source(root)
        if trace_source is None:
            return 2, "untrusted_controller_dependency", fields

    exit_code, output, error, failure = execute_pinned_controller(root, source, trace_source, controller_args)
    if failure:
        return 2, failure, fields
    assert exit_code is not None

    summary = controller_summary(command, output, error, exit_code)
    if summary is None:
        return 2, "malformed_controller_response", fields
    fields.update({"exit_code": exit_code, "summary": summary})
    return ((0, "controller_command_succeeded", fields) if exit_code == 0
            else (2, "controller_rejected", fields))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("probe")
    status = actions.add_parser("status")
    status.add_argument("--feature", required=True)
    controller = actions.add_parser("controller")
    controller.add_argument("controller_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        root = args.workspace.expanduser().resolve()
    except (OSError, RuntimeError):
        emit(args.action, available=False, reason="workspace_resolution_failed")
        return 2
    if args.action == "probe":
        ready, reason = inspect_workspace(root)
        emit("probe", available=ready, reason=reason)
        return 0 if ready else 2
    if args.action == "controller":
        code, reason, fields = run_controller(root, args.controller_args)
        emit("controller", available=code == 0, reason=reason, **fields)
        return code
    ok, reason, fields = observed_status(root, args.feature)
    emit("status", available=ok, reason=reason, **fields)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
