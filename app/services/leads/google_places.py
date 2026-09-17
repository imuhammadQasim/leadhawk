import httpx

from app.config.settings import get_settings

settings = get_settings()

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.id,places.displayName,places.rating,places.userRatingCount,"
    "places.formattedAddress,places.internationalPhoneNumber,places.websiteUri"
)
MAX_RESULTS = 20


# TEMPORARY mock — replace with real search_places() once you have an API key
async def search_places(city: str, category: str) -> list[dict]:
    return [
        {"id": "mock1", "displayName": {"text": "Joe's Auto Repair"}, "rating": 2.8,
         "userRatingCount": 6, "formattedAddress": f"12 Main St, {city}",
         "internationalPhoneNumber": "+92 300 1234567", "websiteUri": None},
        {"id": "mock2", "displayName": {"text": "Prime Cuts Barbershop"}, "rating": 4.7,
         "userRatingCount": 210, "formattedAddress": f"45 Market Rd, {city}",
         "internationalPhoneNumber": "+92 300 7654321", "websiteUri": "https://primecuts.com"},
        {"id": "mock3", "displayName": {"text": "Sunny Cafe"}, "rating": 3.2,
         "userRatingCount": 15, "formattedAddress": f"9 Park Ave, {city}",
         "internationalPhoneNumber": None, "websiteUri": "https://sunnycafe-broken-link.test"},
    ]
