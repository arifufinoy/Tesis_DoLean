from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Project, User
from app.schemas.projects import ProjectCreateRequest, ProjectListResponse, ProjectResponse, ProjectUpdateRequest

router = APIRouter(prefix="/projects", tags=["projects"])


def project_or_404(project_id: UUID, owner_id: UUID, db: Session) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == owner_id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Crear proyecto")
def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = Project(owner_id=current_user.id, name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=ProjectListResponse, summary="Listar proyectos propios")
def list_projects(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    base_query = select(Project).where(Project.owner_id == current_user.id)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    projects = list(db.scalars(base_query.order_by(Project.created_at.desc()).offset(offset).limit(limit)))
    return ProjectListResponse(items=projects, total=total, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectResponse, summary="Consultar proyecto propio")
def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    return project_or_404(project_id, current_user.id, db)


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Actualizar proyecto propio")
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    if not payload.model_fields_set:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Debe enviar al menos un campo")
    project = project_or_404(project_id, current_user.id, db)
    if "name" in payload.model_fields_set:
        project.name = payload.name
    if "description" in payload.model_fields_set:
        project.description = payload.description
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar proyecto propio")
def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    project = project_or_404(project_id, current_user.id, db)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
