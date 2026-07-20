"""CLI behavior via cli.main() (no subprocesses)."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from battwin import StateSnapshot, load, save
from battwin.cli import main

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "cr2032.twin.json"


def test_init_then_validate_then_show(tmp_path: Path, capsys) -> None:
    out = tmp_path / "new.twin.json"
    assert main(["init", "--label", "Bench cell", "--chemistry", "LFP", "-o", str(out)]) == 0
    assert out.exists()

    assert main(["validate", str(out)]) == 0
    assert main(["show", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "Bench cell" in printed


def test_validate_reports_problems(tmp_path: Path, capsys) -> None:
    doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    del doc["identity"]
    bad = tmp_path / "bad.twin.json"
    bad.write_text(json.dumps(doc), encoding="utf-8")

    assert main(["validate", str(bad)]) == 1
    assert "INVALID" in capsys.readouterr().out


def test_hash_prints_content_hash(capsys) -> None:
    assert main(["hash", str(EXAMPLE)]) == 0
    assert capsys.readouterr().out.strip().startswith("sha256:")


def test_diff_intact_and_broken_chain(tmp_path: Path, capsys) -> None:
    v1 = load(EXAMPLE)
    v2 = v1.next_version(
        state=StateSnapshot(as_of=datetime(2026, 7, 9, tzinfo=timezone.utc), state_of_charge=0.4)
    )
    a, b = tmp_path / "v1.twin.json", tmp_path / "v2.twin.json"
    save(v1, a)
    save(v2, b)

    assert main(["diff", str(a), str(b)]) == 0
    out = capsys.readouterr().out
    assert "state" in out and "intact" in out

    # break the chain: re-point v2 at a bogus predecessor
    doc = json.loads(b.read_text(encoding="utf-8"))
    doc["version"]["previous"] = "sha256:" + "0" * 64
    b.write_text(json.dumps(doc), encoding="utf-8")
    assert main(["diff", str(a), str(b)]) == 1
    assert "BROKEN" in capsys.readouterr().out


def test_missing_file_is_a_clean_error(capsys) -> None:
    assert main(["show", "no-such-file.twin.json"]) == 2
    assert "error:" in capsys.readouterr().err


def test_schema_command_prints_packaged_schema(capsys) -> None:
    assert main(["schema"]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert schema["title"] == "Battery Twin Envelope"


def test_context_command_prints_packaged_context(capsys) -> None:
    assert main(["context"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["@context"]["bte"] == "https://w3id.org/battinfo/twin#"


def test_validate_directory_is_a_clean_error(tmp_path: Path, capsys) -> None:
    assert main(["validate", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert err.strip().count("\n") == 0  # one line, no traceback


def test_validate_binary_file_is_a_clean_error(tmp_path: Path, capsys) -> None:
    binary = tmp_path / "not-json.bin"
    binary.write_bytes(b"\x89PNG\r\n\x1a\n\x00\xff\xfe\x00garbage")
    assert main(["validate", str(binary)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert err.strip().count("\n") == 0  # one line, no traceback


def test_diff_different_twins_reported(tmp_path: Path, capsys) -> None:
    a, b = tmp_path / "a.twin.json", tmp_path / "b.twin.json"
    assert main(["init", "--label", "Cell A", "--id", "urn:bte:cell-a", "-o", str(a)]) == 0
    assert main(["init", "--label", "Cell B", "--id", "urn:bte:cell-b", "-o", str(b)]) == 0
    capsys.readouterr()

    assert main(["diff", str(a), str(b)]) == 1
    assert "different twins" in capsys.readouterr().out


# --- FIX 4: `python -m battwin` runs the CLI like the console script -------


def test_python_m_entrypoint_runs_cli() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "battwin", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "battwin" in result.stdout
