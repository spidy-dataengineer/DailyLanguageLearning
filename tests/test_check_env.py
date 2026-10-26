"""check-env reports names + lengths only and fails when a required variable is missing."""
import json

import pytest

from constants import REQUIRED_ENV
from daily_notion import check_env


def test_all_present(monkeypatch, capsys):
    for name in REQUIRED_ENV:
        monkeypatch.setenv(name, "x" * 7)
    check_env()
    out = json.loads(capsys.readouterr().out)
    assert out == {"ok": True, "missing": [], "present": {name: 7 for name in REQUIRED_ENV}}


def test_missing_name_is_reported_and_exit_is_nonzero(monkeypatch, capsys):
    for name in REQUIRED_ENV:
        monkeypatch.setenv(name, "secret-value")
    monkeypatch.delenv("NOTION_DB_ID_ZH")
    with pytest.raises(SystemExit) as exc:
        check_env()
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert json.loads(out)["missing"] == ["NOTION_DB_ID_ZH"]
    assert "secret-value" not in out


def test_empty_value_counts_as_missing(monkeypatch, capsys):
    for name in REQUIRED_ENV:
        monkeypatch.setenv(name, "v")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "")
    with pytest.raises(SystemExit):
        check_env()
    assert json.loads(capsys.readouterr().out)["missing"] == ["DISCORD_WEBHOOK_URL"]
