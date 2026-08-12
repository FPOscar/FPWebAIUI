from open_webui.utils.oauth_registration import (
    overlay_static_oauth_credentials,
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


def test_saved_confidential_credentials_are_preserved_from_encrypted_data():
    resolved = overlay_static_oauth_credentials(
        client_data={
            'client_id': 'provider-client-id',
            'client_secret': 'encrypted-secret',
            'token_endpoint_auth_method': 'client_secret_post',
        },
        oauth_client_id='provider-client-id',
        oauth_client_secret=None,
    )

    assert resolved['client_secret'] == 'encrypted-secret'
    assert resolved['token_endpoint_auth_method'] == 'client_secret_post'


def test_saved_public_credentials_remain_secretless():
    resolved = overlay_static_oauth_credentials(
        client_data={
            'client_id': 'provider-client-id',
            'client_secret': None,
            'token_endpoint_auth_method': 'none',
        },
        oauth_client_id='provider-client-id',
        oauth_client_secret=None,
    )

    assert resolved['client_secret'] is None
    assert resolved['token_endpoint_auth_method'] == 'none'


def test_explicit_static_credentials_override_encrypted_values():
    resolved = overlay_static_oauth_credentials(
        client_data={
            'client_id': 'old-client-id',
            'client_secret': 'old-secret',
            'token_endpoint_auth_method': 'client_secret_post',
        },
        oauth_client_id='new-client-id',
        oauth_client_secret='new-secret',
    )

    assert resolved['client_id'] == 'new-client-id'
    assert resolved['client_secret'] == 'new-secret'


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
