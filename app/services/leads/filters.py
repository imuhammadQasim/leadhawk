#Google Places se businesses milne ke baad ye filter karta hai ke kaunse businesses "weak online presence" wale hain aur actual leads banne chahiye.
import asyncio

import httpx

from app.config.settings import get_settings

settings = get_settings()


async def _website_is_broken(url: str | None) -> bool:
    """A missing website counts as broken; an unreachable/erroring one does too."""
    if not url:
        return True

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            response = await client.head(url)
            if response.status_code >= 400:
                # Some sites reject HEAD; retry with GET before giving up.
                response = await client.get(url)
            return response.status_code >= 400
    except httpx.HTTPError:
        return True


async def filter_weak_presence(candidates: list[dict]) -> list[dict]:
    """Keep only listings showing a weak online presence: missing/broken
    website, low rating, or few reviews - the businesses worth pitching."""
    if not candidates:
        return []

    website_broken = await asyncio.gather(
        *(_website_is_broken(c["website"]) for c in candidates)
    )

    weak = []
    for candidate, broken in zip(candidates, website_broken):
        review_count = candidate["review_count"] or 0
        rating = candidate["rating"]
        low_rating = rating is not None and rating < settings.LEAD_MIN_RATING
        few_reviews = review_count < settings.LEAD_MIN_REVIEWS

        if broken or low_rating or few_reviews:
            weak.append(candidate)

    return weak
