from app.services.messaging.whatsapp import WhatsAppProvider


def test_whatsapp_provider_capabilities():
    provider = WhatsAppProvider(token="demo-token", phone_number_id="123", business_account_id="abc")
    assert "whatsapp" in provider.capabilities()
    assert provider.name == "WHATSAPP"


def test_whatsapp_provider_send_result_shape():
    provider = WhatsAppProvider(token="demo-token", phone_number_id="123", business_account_id="abc")
    result = provider._build_success_result("+15550000000", "hello")
    assert result["status"] == "SENT"
    assert result["channel"] == "WHATSAPP"
