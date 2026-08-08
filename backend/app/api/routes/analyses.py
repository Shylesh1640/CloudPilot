"""Repository analysis API routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.repository_analysis import AnalysisRead, AnalysisResultRead, AnalyzeRequest
from app.services.analysis_service import AnalysisService, run_background_analysis
from app.services.repository_analyzer import InvalidGitHubURL

router = APIRouter(prefix="/api/v1", tags=["Repository Analysis"])


@router.post(
    "/projects/{project_id}/repositories/analyze",
    response_model=AnalysisRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze a public GitHub repository",
    description="Inspect a public GitHub repository statically and trigger background analysis.",
)
async def analyze_repository(
    project_id: uuid.UUID,
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalysisRead:
    service = AnalysisService(session)
    try:
        analysis = await service.trigger_analysis(
            project_id=project_id,
            user_id=current_user.id,
            repository_url=payload.repository_url,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except InvalidGitHubURL as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.message)

    # Schedule background analysis execution
    background_tasks.add_task(run_background_analysis, analysis.id)

    return AnalysisRead.model_validate(analysis)


@router.get(
    "/repository-analyses/{analysis_id}",
    response_model=AnalysisRead,
    summary="Get repository analysis status and progress",
)
async def get_analysis_status(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalysisRead:
    service = AnalysisService(session)
    analysis = await service.get_analysis(analysis_id, current_user.id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis record not found or access denied",
        )
    return AnalysisRead.model_validate(analysis)


@router.get(
    "/repository-analyses/{analysis_id}/result",
    response_model=AnalysisResultRead,
    summary="Get detailed repository profile analysis result",
)
async def get_analysis_result(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalysisResultRead:
    service = AnalysisService(session)
    analysis = await service.get_analysis(analysis_id, current_user.id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis record not found or access denied",
        )
    return AnalysisResultRead.model_validate(analysis)
