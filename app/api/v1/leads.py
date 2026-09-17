import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadGenerateRequest, LeadGenerateResponse, LeadResponse
from app.services.leads.pipeline import generate_leads

router = APIRouter(prefix="/leads", tags=["leads"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=LeadGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_leads_endpoint(
    request: LeadGenerateRequest, db: AsyncSession = Depends(get_db)
) -> LeadGenerateResponse:
    try:
        leads = await generate_leads(db, request.city, request.category)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        logger.exception("Google Places request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch listings from source."
        ) from exc

    return LeadGenerateResponse(
        code=201,
        success=True,
        message=f"Stored {len(leads)} new lead(s).",
        count=len(leads),
        leads=leads,
    )


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    city: str | None = None,
    category: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[Lead]:
    query = select(Lead).order_by(Lead.created_at.desc()).limit(limit)
    if city:
        query = query.where(Lead.city == city)
    if category:
        query = query.where(Lead.category == category)

    return list(await db.scalars(query))
