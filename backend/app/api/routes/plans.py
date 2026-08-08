"""Infrastructure Planning API routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.infrastructure_plan import PlanRead, PlanResultRead
from app.services.plan_service import PlanService, run_background_planning

router = APIRouter(prefix="/api/v1", tags=["Infrastructure Planning"])


@router.post(
    "/repository-analyses/{analysis_id}/plan",
    response_model=PlanRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate AI Infrastructure Plan",
    description="Trigger AI infrastructure planning based on a completed repository analysis.",
)
async def generate_plan(
    analysis_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PlanRead:
    service = PlanService(session)
    try:
        plan = await service.trigger_plan_generation(
            analysis_id=analysis_id,
            user_id=current_user.id,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    # Schedule background worker
    background_tasks.add_task(run_background_planning, plan.id)

    return PlanRead.model_validate(plan)


@router.get(
    "/infrastructure-plans/{plan_id}",
    response_model=PlanRead,
    summary="Get infrastructure plan status and metadata",
)
async def get_plan_status(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PlanRead:
    service = PlanService(session)
    plan = await service.get_plan(plan_id, current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infrastructure plan record not found or access denied",
        )
    return PlanRead.model_validate(plan)


@router.get(
    "/infrastructure-plans/{plan_id}/result",
    response_model=PlanResultRead,
    summary="Get full validated infrastructure plan result",
)
async def get_plan_result(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PlanResultRead:
    service = PlanService(session)
    plan = await service.get_plan(plan_id, current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infrastructure plan record not found or access denied",
        )
    return PlanResultRead.model_validate(plan)


@router.post(
    "/infrastructure-plans/{plan_id}/regenerate",
    response_model=PlanRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate Infrastructure Plan",
    description="Trigger generation of a new infrastructure plan version.",
)
async def regenerate_plan(
    plan_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PlanRead:
    service = PlanService(session)
    try:
        new_plan = await service.regenerate_plan(
            plan_id=plan_id,
            user_id=current_user.id,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    # Schedule background worker
    background_tasks.add_task(run_background_planning, new_plan.id)

    return PlanRead.model_validate(new_plan)
