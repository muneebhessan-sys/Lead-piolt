from app.services.messaging.linkedin import LinkedInProvider


def test_linkedin_provider_capabilities():
    provider = LinkedInProvider(access_token="demo")
    assert "linkedin" in provider.capabilities()
    assert provider.name == "LINKEDIN"
