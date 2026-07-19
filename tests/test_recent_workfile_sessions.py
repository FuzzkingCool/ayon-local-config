"""Tests for recent workfile session persistence (Recent Work tray menu)."""

import json
import os

import pytest

from ayon_local_config.storage import (
    RECENT_WORKFILE_COUNT_DEFAULT,
    _recent_workfile_sessions_path,
    read_recent_workfile_sessions,
    recent_workfile_count,
    touch_recent_workfile_session,
)


@pytest.fixture
def session_config_dir(tmp_path, monkeypatch, request):
    config_dir = tmp_path / request.node.name
    monkeypatch.setenv("AYON_LOCAL_CONFIG_DIR", str(config_dir))
    monkeypatch.delenv("AYON_RECENT_FILES_COUNT", raising=False)
    return config_dir


def _session(
    workfile_path,
    *,
    project_name="demo_project",
    folder_path="/assets/hero",
    task_name="modeling",
    host_name="harmony",
):
    return {
        "project_name": project_name,
        "folder_path": folder_path,
        "task_name": task_name,
        "workfile_path": workfile_path,
        "host_name": host_name,
        "timestamp": "2026-07-16T10:00:00",
    }


def test_recent_workfile_count_default(session_config_dir):
    assert recent_workfile_count() == RECENT_WORKFILE_COUNT_DEFAULT


def test_recent_workfile_count_env_override(session_config_dir, monkeypatch):
    monkeypatch.setenv("AYON_RECENT_FILES_COUNT", "3")
    assert recent_workfile_count() == 3


def test_recent_workfile_count_invalid_env_falls_back(
    session_config_dir, monkeypatch
):
    monkeypatch.setenv("AYON_RECENT_FILES_COUNT", "not-a-number")
    assert recent_workfile_count() == RECENT_WORKFILE_COUNT_DEFAULT


def test_read_recent_workfile_sessions_missing_file(session_config_dir):
    assert read_recent_workfile_sessions() == []


def test_touch_and_read_recent_workfile_sessions(session_config_dir):
    first = _session("P:/demo/assets/hero/hero_model_v001.harmony")
    second = _session("P:/demo/assets/hero/hero_model_v002.harmony")

    assert touch_recent_workfile_session(first) is True
    assert touch_recent_workfile_session(second) is True

    sessions = read_recent_workfile_sessions()
    assert len(sessions) == 2
    assert sessions[0]["workfile_path"] == second["workfile_path"]
    assert sessions[1]["workfile_path"] == first["workfile_path"]

    path = _recent_workfile_sessions_path()
    assert os.path.isfile(path)
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    assert isinstance(raw, list)
    assert len(raw) == 2


def test_touch_recent_workfile_sessions_dedupes_by_path(session_config_dir):
    first = _session("P:/demo/assets/hero/hero_model_v001.harmony")
    second = _session("P:/demo/assets/hero/hero_model_v002.harmony")

    touch_recent_workfile_session(first)
    touch_recent_workfile_session(second)
    touch_recent_workfile_session(first)

    sessions = read_recent_workfile_sessions()
    assert len(sessions) == 2
    assert sessions[0]["workfile_path"] == first["workfile_path"]
    assert sessions[1]["workfile_path"] == second["workfile_path"]


def test_touch_recent_workfile_sessions_respects_env_cap(
    session_config_dir, monkeypatch
):
    monkeypatch.setenv("AYON_RECENT_FILES_COUNT", "3")

    for index in range(5):
        touch_recent_workfile_session(
            _session(f"P:/demo/assets/hero/hero_model_v{index:03d}.harmony")
        )

    sessions = read_recent_workfile_sessions()
    assert len(sessions) == 3
    assert sessions[0]["workfile_path"].endswith("v004.harmony")
    assert sessions[2]["workfile_path"].endswith("v002.harmony")


def test_touch_recent_workfile_session_skips_empty_path(session_config_dir):
    assert touch_recent_workfile_session(_session("")) is False
    assert read_recent_workfile_sessions() == []
