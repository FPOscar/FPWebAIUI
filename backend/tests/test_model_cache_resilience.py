import asyncio
from types import SimpleNamespace

from open_webui.utils import model_cache


class FakeModelCache:
    def __init__(self, *, values=None, error=None):
        self.values = values or {}
        self.error = error

    def _raise_if_unavailable(self):
        if self.error:
            raise self.error

    def __getitem__(self, key):
        self._raise_if_unavailable()
        if key not in self.values:
            raise KeyError(key)
        return self.values[key]

    def __len__(self):
        self._raise_if_unavailable()
        return len(self.values)

    def items(self):
        self._raise_if_unavailable()
        return self.values.items()

    def set(self, mapping):
        self._raise_if_unavailable()
        self.values = mapping


def make_request(cache, local_models=None):
    state = SimpleNamespace(
        MODELS=cache,
        LOCAL_MODELS=local_models or {},
    )
    return SimpleNamespace(app=SimpleNamespace(state=state))


def test_redis_read_failure_uses_last_in_process_model_cache():
    expected = {'id': 'gpt-test'}
    cache = FakeModelCache(error=ConnectionError('redis unavailable'))
    request = make_request(cache, {'gpt-test': expected})

    assert model_cache.has_model_cache(request)
    assert model_cache.get_models_from_cache(request) == {'gpt-test': expected}
    assert model_cache.get_model_from_cache(request, 'gpt-test') is expected


def test_healthy_redis_miss_does_not_resurrect_stale_local_model():
    cache = FakeModelCache()
    request = make_request(cache, {'removed-model': {'id': 'removed-model'}})

    assert model_cache.get_model_from_cache(request, 'removed-model') is None


def test_failed_redis_write_retains_shared_cache_object_and_updates_fallback():
    cache = FakeModelCache(error=ConnectionError('redis unavailable'))
    request = make_request(cache)
    expected = {'gpt-test': {'id': 'gpt-test'}}

    model_cache.update_model_cache(request, expected)

    assert request.app.state.MODELS is cache
    assert request.app.state.LOCAL_MODELS is expected


def test_model_cache_miss_refreshes_and_returns_request_local_mapping():
    cache = FakeModelCache()
    request = make_request(cache)
    expected = {'id': 'gpt-test', 'name': 'Test model'}
    calls = []

    async def refresh_models():
        calls.append('refresh')
        return [expected]

    model, refreshed_models = asyncio.run(
        model_cache.get_model_from_cache_or_refresh(
            request,
            'gpt-test',
            {},
            refresh_models,
        )
    )

    assert model is expected
    assert refreshed_models == {'gpt-test': expected}
    assert calls == ['refresh']


def test_unknown_model_in_populated_cache_does_not_refresh_providers():
    request = make_request(FakeModelCache(values={'known-model': {'id': 'known-model'}}))
    calls = []

    async def refresh_models():
        calls.append('refresh')
        return []

    model, refreshed_models = asyncio.run(
        model_cache.get_model_from_cache_or_refresh(
            request,
            'unknown-model',
            model_cache.get_models_from_cache(request),
            refresh_models,
        )
    )

    assert model is None
    assert refreshed_models is None
    assert calls == []
