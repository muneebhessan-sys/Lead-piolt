from dataclasses import dataclass
import httpx
from app.config import settings

FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.addressComponents,places.location,places.types,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.businessStatus,places.googleMapsUri,nextPageToken"
class GooglePlacesError(RuntimeError): pass

@dataclass(frozen=True)
class NormalizedPlace:
    place_id: str
    name: str
    category: str | None
    categories: list[str]
    address: str | None
    locality: str | None
    city: str | None
    region: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    phone: str | None
    website: str | None
    rating: float | None
    review_count: int | None
    business_status: str | None
    maps_url: str | None

def normalize_place(place: dict) -> NormalizedPlace:
    components = {item.get("types", [None])[0]: item for item in place.get("addressComponents", []) if item.get("types")}
    locality = (components.get("locality") or components.get("postal_town") or {}).get("longText")
    city = locality or (components.get("administrative_area_level_2") or {}).get("longText")
    region = (components.get("administrative_area_level_1") or {}).get("shortText") or (components.get("administrative_area_level_1") or {}).get("longText")
    country = (components.get("country") or {}).get("longText")
    location = place.get("location") or {}
    types = [value for value in place.get("types", []) if isinstance(value, str)]
    display_name = place.get("displayName") or {}
    return NormalizedPlace(
        place_id=str(place.get("id") or ""), name=str(display_name.get("text") or ""),
        category=types[0] if types else None, categories=types,
        address=place.get("formattedAddress"), locality=locality, city=city, region=region, country=country,
        latitude=float(location["latitude"]) if location.get("latitude") is not None else None,
        longitude=float(location["longitude"]) if location.get("longitude") is not None else None,
        phone=place.get("nationalPhoneNumber"), website=place.get("websiteUri"),
        rating=float(place["rating"]) if place.get("rating") is not None else None,
        review_count=int(place["userRatingCount"]) if place.get("userRatingCount") is not None else None,
        business_status=place.get("businessStatus"), maps_url=place.get("googleMapsUri"),
    )
class GooglePlacesProvider:
    endpoint = "https://places.googleapis.com/v1/places:searchText"
    def __init__(self, api_key: str | None = None): self.api_key = api_key if api_key is not None else settings.google_places_api_key
    def configured(self) -> bool: return bool(self.api_key)
    async def search(self, text_query: str, limit: int) -> list[dict]:
        if not self.configured(): raise GooglePlacesError("GOOGLE_PLACES_NOT_CONFIGURED")
        results=[]; token=None
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            while len(results)<limit:
                data={"textQuery":text_query,"pageSize":min(20,limit-len(results))}
                if token:data["pageToken"]=token
                response=await client.post(self.endpoint,json=data,headers={"X-Goog-Api-Key":self.api_key,"X-Goog-FieldMask":FIELD_MASK,"Content-Type":"application/json"})
                if response.status_code in {401,403}: raise GooglePlacesError("GOOGLE_AUTH_FAILED")
                if response.status_code==429: raise GooglePlacesError("GOOGLE_RATE_LIMITED")
                response.raise_for_status(); body=response.json(); results.extend(body.get("places",[])); token=body.get("nextPageToken")
                if not token: break
        return results[:limit]
