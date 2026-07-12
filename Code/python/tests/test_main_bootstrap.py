from unittest.mock import Mock

from Code.python import main as main_module


def test_main_boots_ui_before_running_server(monkeypatch):
    calls = []

    def fake_build_ui():
        calls.append("build_ui")

    def fake_run(*args, **kwargs):
        calls.append("run")

    monkeypatch.setattr(main_module, "build_ui", fake_build_ui)
    monkeypatch.setattr(main_module.ui, "run", fake_run)

    main_module.main()

    assert calls == ["build_ui", "run"]
