from typing import Literal, Sequence


TokenEndpointAuthMethod = Literal[
    'none', 'client_secret_basic', 'client_secret_post'
]


def uses_static_oauth_registration(
    *, oauth_client_id: str | None, client_secret: str | None
) -> bool:
    """Return whether supplied credentials describe a pre-registered OAuth client."""
    return bool(oauth_client_id or client_secret)


def resolve_static_oauth_client_id(
    *, connection_id: str, oauth_client_id: str | None
) -> str:
    """Use the provider-issued client ID, retaining compatibility with legacy requests."""
    return oauth_client_id or connection_id


def select_static_token_endpoint_auth_method(
    *, client_secret: str | None, supported_methods: Sequence[str] | None = None
) -> TokenEndpointAuthMethod:
    """Select token authentication for public or confidential static clients."""
    if not client_secret:
        return 'none'

    preferred_method: TokenEndpointAuthMethod = 'client_secret_post'
    if not supported_methods or preferred_method in supported_methods:
        return preferred_method

    for method in ('client_secret_basic', 'client_secret_post'):
        if method in supported_methods:
            return method

    return preferred_method
