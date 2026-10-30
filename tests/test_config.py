import pytest

from app.config import ConfigError, Settings, _int_env, validate_settings


def _settings(tmp_path, **kw):
    return Settings(**{"anthropic_api_key": "k", "canvas_base_url": None, "canvas_token": None,
                       "data_dir": tmp_path, "offline": False, "max_revisions": 2, **kw})  # fmt: skip


def test_valid_settings_pass(tmp_path):
    validate_settings(_settings(tmp_path))


def test_missing_key_is_named_but_offline_is_fine(tmp_path):
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        validate_settings(_settings(tmp_path, anthropic_api_key=None))
    validate_settings(_settings(tmp_path, anthropic_api_key=None, offline=True))


def test_reports_every_problem_at_once(tmp_path):
    bad = _settings(tmp_path, anthropic_api_key=None, max_revisions=-1, canvas_token="secret-token")
    with pytest.raises(ConfigError) as err:
        validate_settings(bad)
    text = str(err.value)
    assert "ANTHROPIC_API_KEY" in text and "HARNESS_MAX_REVISIONS" in text and "CANVAS_BASE_URL" in text
    assert "secret-token" not in text


def test_bad_data_dir(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(ConfigError, match="HARNESS_DATA_DIR"):
        validate_settings(_settings(blocker / "sub"))


def test_non_numeric_int_env_is_clear(monkeypatch):
    monkeypatch.setenv("HARNESS_MAX_REVISIONS", "two")
    with pytest.raises(ConfigError, match="HARNESS_MAX_REVISIONS"):
        _int_env("HARNESS_MAX_REVISIONS", 2)
