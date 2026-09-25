from app.services.messaging.instagram import InstagramProvider


def test_instagram_provider_capabilities():
    provider = InstagramProvider(access_token="demo")
    capabilities = provider.capabilities()
    assert "instagram" in capabilities
    assert provider.name == "INSTAGRAM"
