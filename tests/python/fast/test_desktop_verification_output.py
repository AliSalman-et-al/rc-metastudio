import io

import pytest

from scripts.verify_rcms import _print_failure_transcripts


@pytest.mark.parametrize("encoding", ["cp1252", "ascii"])
def test_failed_desktop_transcripts_survive_console_encoding(monkeypatch, tmp_path, encoding):
    raw = "AssertionError: τ² … Ω\n".encode("utf-8")
    for name in ("stdout.log", "stderr.log"):
        (tmp_path / name).write_bytes(raw)
    output = io.BytesIO()
    console = io.TextIOWrapper(output, encoding=encoding, newline="\n")
    monkeypatch.setattr("sys.stdout", console)

    _print_failure_transcripts(tmp_path)

    console.flush()
    displayed = output.getvalue().decode(encoding)
    assert "AssertionError:" in displayed
    assert raw.decode("utf-8").encode(encoding, errors="backslashreplace").decode(encoding) in displayed
    assert all((tmp_path / name).read_bytes() == raw for name in ("stdout.log", "stderr.log"))
