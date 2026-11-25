import pytest


@pytest.fixture(autouse=True)
def _isolate_shared_engine(tmp_path_factory, monkeypatch):
    """Never let the test suite read or write the developer's real ~/.aim/engine (Issue #141)."""
    engine_root = tmp_path_factory.mktemp("shared-engine")
    monkeypatch.setenv("AIM_ENGINE_ROOT", str(engine_root))
    yield str(engine_root)
