from gateway.config import GatewayConfig, Platform, PlatformConfig


def test_enterprise_connected_platforms_only_return_internal_platforms():
    config = GatewayConfig(
        platforms={
            Platform.TELEGRAM: PlatformConfig(enabled=True, token="telegram-token"),
            Platform.API_SERVER: PlatformConfig(enabled=True),
            Platform.WEBHOOK: PlatformConfig(enabled=True),
        },
    )

    connected = config.get_connected_platforms()

    assert Platform.API_SERVER in connected
    assert Platform.WEBHOOK in connected
    assert Platform.TELEGRAM not in connected
