from app.services.messaging.facebook import FacebookProvider


def test_facebook_provider_capabilities():
    provider = FacebookProvider(page_access_token="demo")
    assert "facebook" in provider.capabilities()
    assert provider.name == "FACEBOOK"
