import logging

from fastapi import Request

log = logging.getLogger(__name__)


def has_model_cache(request: Request) -> bool:
    """Return whether a shared model cache is available, with a local outage fallback."""
    try:
        return bool(request.app.state.MODELS)
    except Exception as e:
        fallback = getattr(request.app.state, 'LOCAL_MODELS', {})
        log.warning(f'Failed to read Redis model cache, using in-process cache: {e}')
        return bool(fallback)


def get_model_from_cache(request: Request, model_id: str):
    """Read one model without letting a transient Redis failure break chat routing."""
    try:
        return request.app.state.MODELS[model_id]
    except KeyError:
        # A healthy shared cache is authoritative. Do not resurrect a model that
        # was deliberately removed but still exists in this process's fallback.
        return None
    except Exception as e:
        log.warning(f'Failed to read model {model_id!r} from Redis, using in-process cache: {e}')
        return getattr(request.app.state, 'LOCAL_MODELS', {}).get(model_id)


async def get_model_from_cache_or_refresh(
    request: Request,
    model_id: str,
    refresh_models,
):
    """Resolve a model, refreshing once when the shared cache misses it.

    The refreshed mapping is returned with the selected model so the caller can
    continue using the request-local result even if the Redis write failed.
    """
    model = get_model_from_cache(request, model_id)
    if model is not None:
        return model, None

    models = await refresh_models()
    models_dict = {item['id']: item for item in models}
    return models_dict.get(model_id), models_dict


def update_model_cache(request: Request, models_dict: dict) -> None:
    # Keep a per-process copy so requests can continue during a Redis outage.
    # Crucially, retain the RedisDict itself so the process reconnects to shared
    # state once Redis recovers instead of diverging permanently.
    request.app.state.LOCAL_MODELS = models_dict

    if hasattr(request.app.state.MODELS, 'set'):
        try:
            request.app.state.MODELS.set(models_dict)
        except Exception as e:
            log.warning(f'Failed to update Redis model cache, using in-process cache: {e}')
    else:
        request.app.state.MODELS = models_dict
