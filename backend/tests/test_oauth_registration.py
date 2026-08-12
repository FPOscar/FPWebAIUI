from open_webui.utils.oauth_registration import (
    resolve_static_oauth_client_id,
    select_static_token_endpoint_auth_method,
    uses_static_oauth_registration,
)


def test_public_client_uses_static_registration_without_secret():
    assert uses_static_oauth_registration(
        oauth_client_id='provider-client-id', client_secret=None
    )


def test_legacy_confidential_client_uses_static_registration_from_secret():
    assert uses_static_oauth_registration(
        oauth_client_id=None, client_secret='client-secret'
    )


def test_dynamic_registration_is_used_when_no_static_credentials_are_supplied():
    assert not uses_static_oauth_registration(
        oauth_client_id=None, client_secret=None
    )
    assert not uses_static_oauth_registration(oauth_client_id='', client_secret='')


def test_provider_client_id_wins_with_legacy_connection_id_fallback():
    assert (
        resolve_static_oauth_client_id(
            connection_id='bloomberg', oauth_client_id='provider-client-id'
        )
        == 'provider-client-id'
    )
    assert (
        resolve_static_oauth_client_id(
            connection_id='legacy-connection', oauth_client_id=None
        )
        == 'legacy-connection'
    )


def test_public_client_uses_none_even_when_server_metadata_omits_it():
    assert (
        select_static_token_endpoint_auth_method(
            client_secret=None,
            supported_methods=['client_secret_basic', 'client_secret_post'],
        )
        == 'none'
    )


def test_confidential_client_prefers_post_and_can_fall_back_to_basic():
    assert (
        select_static_token_endpoint_auth_method(
            client_secret='client-secret',
            supported_methods=['client_secret_post', 'client_secret_basic'],
        )
        == 'client_secret_post'
    )
    assert (
        select_static_token_endpoint_auth_method(
            client_secret='client-secret',
            supported_methods=['client_secret_basic'],
        )
        == 'client_secret_basic'
    )
