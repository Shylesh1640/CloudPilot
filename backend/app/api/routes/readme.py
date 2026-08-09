"""Phase 11 — README Auto-Generation API routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.readme_service import ReadmeGenerationError, ReadmeService

router = APIRouter(prefix="/api/v1", tags=["README Generator"])


class ReadmeResponse(BaseModel):
    analysis_id: uuid.UUID
    content: str  # Raw markdown string


@router.post(
    "/repository-analyses/{analysis_id}/readme",
    response_model=ReadmeResponse,
    summary="Generate a production-quality README.md using AI",
    description=(
        "Uses the completed repository analysis profile and the configured AI provider "
        "(OpenRouter / OpenAI / Gemini) to generate a full, evidence-backed README.md. "
        "Analysis must be in COMPLETED status."
    ),
)
async def generate_readme(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReadmeResponse:
    service = ReadmeService(session)
    try:
        markdown = await service.generate(
            analysis_id=analysis_id,
            user_id=current_user.id,
        )
    except ReadmeGenerationError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    return ReadmeResponse(analysis_id=analysis_id, content=markdown)
