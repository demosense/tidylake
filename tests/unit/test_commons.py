import importlib

from tidylake.core import commons


def reload_commons():
    """
    Reload the commons module so global variables reflect patched state.
    """

    return importlib.reload(commons)


def test_get_use_synthetic_data_true(monkeypatch):
    monkeypatch.setenv("TIDYLAKE_USE_SYNTHETIC_DATA", "true")
    assert commons.get_use_synthetic_data() is True


def test_get_use_synthetic_data_false(monkeypatch):
    monkeypatch.setenv("TIDYLAKE_USE_SYNTHETIC_DATA", "false")
    assert commons.get_use_synthetic_data() is False


def test_get_use_synthetic_data_sample_size_default(monkeypatch):
    monkeypatch.delenv("TIDYLAKE_USE_SYNTHETIC_DATA_SAMPLE_SIZE", raising=False)
    assert (
        commons.get_use_synthetic_data_sample_size()
        == commons.TIDYLAKE_USE_SYNTHETIC_DATA_SAMPLE_SIZE_DEFAULT
    )


def test_get_use_synthetic_data_sample_size(monkeypatch):
    monkeypatch.setenv("TIDYLAKE_USE_SYNTHETIC_DATA_SAMPLE_SIZE", "25")
    assert commons.get_use_synthetic_data_sample_size() == 25


def test_get_execution_mode_interactive(monkeypatch):
    monkeypatch.setitem(commons.__dict__, "get_ipython", lambda: None)
    assert commons.get_execution_mode() == commons.EXECUTION_MODE_INTERACTIVE


def test_get_execution_mode_script(monkeypatch):
    monkeypatch.delenv("TIDYLAKE_USE_SYNTHETIC_DATA", raising=False)
    monkeypatch.delitem(commons.__dict__, "get_ipython", raising=False)
    assert commons.get_execution_mode() == commons.EXECUTION_MODE_SCRIPT


def test_execution_mode_global_updates(monkeypatch):
    monkeypatch.setitem(commons.__dict__, "get_ipython", lambda: None)
    module = reload_commons()
    assert module.execution_mode == module.EXECUTION_MODE_INTERACTIVE
