"""
API endpoints для управления workflow
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.tables import workflows, workflow_runs
from app.schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowStep,
)

router = APIRouter()


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    trigger_event: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка workflow"""
    query = select(workflows)
    
    if is_active is not None:
        query = query.where(workflows.c.is_active == is_active)
    
    if trigger_event:
        query = query.where(workflows.c.trigger_event == trigger_event)
    
    query = query.offset(skip).limit(limit).order_by(workflows.c.created_at.desc())
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    """Получение workflow по ID"""
    query = select(workflows).where(workflows.c.id == workflow_id)
    result = await db.execute(query)
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return dict(row)


@router.post("/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание нового workflow"""
    query = workflows.insert().values(
        name=workflow.name,
        trigger_event=workflow.trigger_event,
        steps=[step.model_dump() for step in workflow.steps],
        tenant_id=workflow.tenant_id,
        is_active=True
    )
    result = await db.execute(query)
    await db.flush()
    
    workflow_id = result.inserted_primary_key[0]
    
    get_query = select(workflows).where(workflows.c.id == workflow_id)
    get_result = await db.execute(get_query)
    row = get_result.fetchone()
    
    return dict(row)


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow: WorkflowUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление workflow"""
    # Проверка существования
    check_query = select(workflows).where(workflows.c.id == workflow_id)
    check_result = await db.execute(check_query)
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Формируем данные для обновления
    update_data = {k: v for k, v in workflow.model_dump().items() if v is not None}
    
    # Конвертируем шаги в dict
    if "steps" in update_data:
        update_data["steps"] = [step.model_dump() if isinstance(step, WorkflowStep) else step for step in update_data["steps"]]
    
    query = workflows.update().where(
        workflows.c.id == workflow_id
    ).values(**update_data)
    await db.execute(query)
    await db.flush()
    
    get_query = select(workflows).where(workflows.c.id == workflow_id)
    get_result = await db.execute(get_query)
    row = get_result.fetchone()
    
    return dict(row)


@router.delete("/workflows/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление workflow"""
    # Проверка существования
    check_query = select(workflows).where(workflows.c.id == workflow_id)
    check_result = await db.execute(check_query)
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    query = workflows.delete().where(workflows.c.id == workflow_id)
    await db.execute(query)
    await db.flush()
    
    return None


@router.post("/workflows/{workflow_id}/toggle", response_model=WorkflowResponse)
async def toggle_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    """Включить/выключить workflow"""
    check_query = select(workflows).where(workflows.c.id == workflow_id)
    check_result = await db.execute(check_query)
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Переключаем is_active
    query = workflows.update().where(
        workflows.c.id == workflow_id
    ).values(
        is_active=~workflows.c.is_active
    )
    await db.execute(query)
    await db.flush()
    
    get_query = select(workflows).where(workflows.c.id == workflow_id)
    get_result = await db.execute(get_query)
    row = get_result.fetchone()
    
    return dict(row)


# === Workflow Runs ===

@router.get("/workflows/{workflow_id}/runs")
async def list_workflow_runs(
    workflow_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение истории выполнений workflow"""
    query = select(workflow_runs).where(
        workflow_runs.c.workflow_id == workflow_id
    )
    
    if status:
        query = query.where(workflow_runs.c.status == status)
    
    query = query.offset(skip).limit(limit).order_by(workflow_runs.c.started_at.desc())
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/workflow-runs/{run_id}")
async def get_workflow_run(run_id: int, db: AsyncSession = Depends(get_db)):
    """Получение информации о выполнении workflow"""
    query = select(workflow_runs).where(workflow_runs.c.id == run_id)
    result = await db.execute(query)
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    
    return dict(row)


@router.post("/workflows/{workflow_id}/trigger")
async def trigger_workflow_manual(
    workflow_id: int,
    context: dict = {},
    db: AsyncSession = Depends(get_db)
):
    """
    Ручной запуск workflow
    
    Полезно для тестирования workflow
    """
    from app.services.workflow_engine import WorkflowEngine
    
    # Проверка существования
    check_query = select(workflows).where(workflows.c.id == workflow_id)
    check_result = await db.execute(check_query)
    workflow = check_result.fetchone()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow_dict = dict(workflow)
    
    if not workflow_dict["is_active"]:
        raise HTTPException(status_code=400, detail="Workflow is disabled")
    
    # Запуск workflow
    engine = WorkflowEngine(db)
    run_id = await engine.start_workflow(workflow_id, context)
    
    return {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "status": "running"
    }
