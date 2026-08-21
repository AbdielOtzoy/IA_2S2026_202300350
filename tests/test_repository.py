import pytest

from backend.knowledge import KnowledgeReloadError


def test_reload_failure_restores_json_and_prolog(repository):
    old_json = repository.data_file.read_bytes()
    old_prolog = repository.prolog_file.read_bytes()
    original_reload = repository.engine.reload
    calls = {"count": 0}

    def fail_on_mutation():
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("motor simulado caído")
        return original_reload()

    repository.engine.reload = fail_on_mutation
    with pytest.raises(KnowledgeReloadError):
        repository.mutate("prueba rollback", lambda kb: kb)
    assert repository.data_file.read_bytes() == old_json
    assert repository.prolog_file.read_bytes() == old_prolog
