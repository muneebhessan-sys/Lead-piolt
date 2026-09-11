import ipaddress, socket
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

def validate_public_url(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"https://{value}")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public HTTP(S) URLs are allowed")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None)
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if not ip.is_global:
                raise ValueError("Internal or non-public network address blocked")
    except socket.gaierror as exc:
        raise ValueError("Host could not be resolved") from exc
    return parsed.geturl()

async def audit_website(value: str) -> dict:
    url = validate_public_url(value)
    redirect_count = 0
    async with httpx.AsyncClient(timeout=15, follow_redirects=False, headers={"User-Agent":"LeadPilotAudit/1.0"}) as client:
        while True:
            request = client.build_request("GET", url)
            response = await client.send(request, stream=True)
            if response.is_redirect:
                location = response.headers.get("location")
                await response.aclose()
                if not location or redirect_count >= 5:
                    raise ValueError("Unsafe or excessive redirect")
                url = validate_public_url(str(httpx.URL(url).join(location)))
                redirect_count += 1
                continue
            content = bytearray()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > 1_000_000:
                    await response.aclose()
                    raise ValueError("Response exceeds 1 MB audit limit")
            break
    soup = BeautifulSoup(bytes(content), "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    meta = soup.find("meta", attrs={"name":"description"})
    h1 = soup.find("h1")
    viewport = soup.find("meta", attrs={"name":"viewport"})
    reasons = []
    if not title: reasons.append("Missing page title")
    if not meta: reasons.append("Missing meta description")
    if not h1: reasons.append("Missing H1")
    status = "GOOD" if not reasons and response.status_code < 400 else "NEEDS_IMPROVEMENT"
    return {"url":str(response.url),"http_status":response.status_code,"https":response.url.scheme=="https","redirect_count":redirect_count,"title":title,"meta_description":meta.get("content") if meta else None,"h1":h1.get_text(" ", strip=True) if h1 else None,"viewport":bool(viewport),"classification":status,"reasons":reasons}
