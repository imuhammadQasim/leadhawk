from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.services.leads.dedupe import normalize_address, normalize_business_name
from app.services.leads.filters import filter_weak_presence
from app.services.leads.google_places import search_places

SOURCE = "google_places"


def _parse_place(place: dict, city: str, category: str) -> dict | None:
    """Turn a raw Places API result into structured Lead fields.

    Returns None if the record is missing the fields needed to identify a
    business at all (broken/partial extraction), rather than writing garbage.
    """
    place_id = place.get("id")
    name = place.get("displayName", {}).get("text")
    if not place_id or not name:
        return None

    address = place.get("formattedAddress")
    return {
        "source": SOURCE,
        "source_place_id": place_id,
        "business_name": name,
        "category": category,
        "city": city,
        "address": address,
        "phone": place.get("internationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "rating": place.get("rating"),
        "review_count": place.get("userRatingCount"),
        "normalized_name": normalize_business_name(name),
        "normalized_address": normalize_address(address),
    }


async def _dedupe(db: AsyncSession, candidates: list[dict]) -> list[dict]:
    """Drop candidates already stored - matched by source place id, or by
    normalized name+address (catches the same business resurfacing under a
    different search query or, once more sources exist, a different site)."""
    if not candidates:
        return []

    place_ids = [c["source_place_id"] for c in candidates]
    names = [c["normalized_name"] for c in candidates]

    existing = await db.execute(
        select(Lead.source_place_id, Lead.normalized_name, Lead.normalized_address).where(
            or_(
                (Lead.source == SOURCE) & Lead.source_place_id.in_(place_ids),
                Lead.normalized_name.in_(names),
            )
        )
    )
    existing_place_ids: set[str] = set()
    existing_name_address: set[tuple[str, str | None]] = set()
    for place_id, norm_name, norm_address in existing:
        existing_place_ids.add(place_id)
        existing_name_address.add((norm_name, norm_address))

    deduped = []
    seen_in_batch: set[tuple[str, str | None]] = set()
    for candidate in candidates:
        key = (candidate["normalized_name"], candidate["normalized_address"])
        if candidate["source_place_id"] in existing_place_ids:
            continue
        if key in existing_name_address or key in seen_in_batch:
            continue
        seen_in_batch.add(key)
        deduped.append(candidate)

    return deduped


async def generate_leads(db: AsyncSession, city: str, category: str) -> list[Lead]:
    """Phase 1+2 pipeline: crawl -> parse -> filter (weak presence) ->
    clean/dedupe -> store. Enrichment (Phase 3) is not implemented yet."""
    places = await search_places(city, category)

    parsed = [_parse_place(place, city, category) for place in places]
    candidates = [p for p in parsed if p is not None]
    if not candidates:
        return []

    weak_presence = await filter_weak_presence(candidates)
    if not weak_presence:
        return []

    to_store = await _dedupe(db, weak_presence)
    if not to_store:
        return []

    now = datetime.now(timezone.utc)
    new_leads = [Lead(**c, created_at=now) for c in to_store]

    db.add_all(new_leads)
    await db.commit()
    for lead in new_leads:
        await db.refresh(lead)

    return new_leads
