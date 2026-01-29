from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.core.deps import get_current_user, get_db
from app.models.service_history import ServiceDocument, ServiceHistory
from app.models.user import User
from app.models.watch import Watch
from app.schemas.service_history import (
    ServiceDocumentResponse,
    ServiceHistoryCreate,
    ServiceHistoryResponse,
    ServiceHistoryUpdate,
)
from app.utils.file_upload import (
    delete_file,
    save_service_document,
    validate_document_file,
)

router = APIRouter()


def verify_watch_ownership(watch_id: UUID, current_user: User, db: Session) -> Watch:
    """
    Verify that the current user owns the specified watch.

    Args:
        watch_id: UUID of the watch
        current_user: Currently authenticated user
        db: Database session

    Returns:
        The watch object if found and owned by user

    Raises:
        HTTPException: 404 if watch not found or not owned by user
    """
    watch = (
        db.query(Watch)
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    return watch


def verify_service_ownership(
    watch_id: UUID, service_id: UUID, current_user: User, db: Session
) -> tuple[Watch, ServiceHistory]:
    """
    Verify that the current user owns the watch and the service record belongs to that watch.

    Args:
        watch_id: UUID of the watch
        service_id: UUID of the service history record
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Tuple of (watch, service_history)

    Raises:
        HTTPException: 404 if watch or service not found
    """
    # First verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Then verify service belongs to this watch
    service = (
        db.query(ServiceHistory)
        .options(joinedload(ServiceHistory.documents))
        .filter(ServiceHistory.id == service_id, ServiceHistory.watch_id == watch_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service record not found"
        )

    return watch, service


@router.post("/{watch_id}/service-history", response_model=ServiceHistoryResponse)
def create_service_history(
    watch_id: UUID,
    service_data: ServiceHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new service history record for a watch.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Create service history record
    service = ServiceHistory(
        watch_id=watch.id,
        service_date=service_data.service_date,
        provider=service_data.provider,
        service_type=service_data.service_type,
        description=service_data.description,
        cost=service_data.cost,
        cost_currency=service_data.cost_currency,
        next_service_due=service_data.next_service_due,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@router.get("/{watch_id}/service-history", response_model=List[ServiceHistoryResponse])
def list_service_history(
    watch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all service history records for a watch, ordered by date (most recent first).
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Query service history with eager loading of documents
    services = (
        db.query(ServiceHistory)
        .options(joinedload(ServiceHistory.documents))
        .filter(ServiceHistory.watch_id == watch.id)
        .order_by(ServiceHistory.service_date.desc())
        .all()
    )

    return services


@router.get(
    "/{watch_id}/service-history/{service_id}", response_model=ServiceHistoryResponse
)
def get_service_history(
    watch_id: UUID,
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific service history record.
    """
    _, service = verify_service_ownership(watch_id, service_id, current_user, db)
    return service


@router.put(
    "/{watch_id}/service-history/{service_id}", response_model=ServiceHistoryResponse
)
def update_service_history(
    watch_id: UUID,
    service_id: UUID,
    service_data: ServiceHistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a service history record.
    """
    _, service = verify_service_ownership(watch_id, service_id, current_user, db)

    # Update fields if provided
    update_data = service_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)

    return service


@router.delete(
    "/{watch_id}/service-history/{service_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_service_history(
    watch_id: UUID,
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a service history record and all associated documents.
    """
    _, service = verify_service_ownership(watch_id, service_id, current_user, db)

    # Delete all associated document files from storage
    for document in service.documents:
        # Build path for service documents: service-docs/{file_path}
        full_path = f"service-docs/{document.file_path}"
        delete_file(full_path, settings.UPLOAD_DIR)

    # Delete service record (cascade will remove documents from DB)
    db.delete(service)
    db.commit()

    return None


# Document management endpoints


@router.post(
    "/{watch_id}/service-history/{service_id}/documents",
    response_model=ServiceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_service_document(
    watch_id: UUID,
    service_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a document (receipt, certificate, etc.) for a service record.
    Allowed formats: PDF, JPG, PNG
    Max size: 10MB
    """
    # Verify ownership
    _, service = verify_service_ownership(watch_id, service_id, current_user, db)

    # Validate file
    is_valid, error_message = validate_document_file(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_message
        )

    # Check file size (10MB limit)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit",
        )

    # Save file to storage
    file_metadata = save_service_document(
        file=file,
        watch_id=watch_id,
        service_id=service_id,
        upload_dir=settings.UPLOAD_DIR,
    )

    # Create database record
    document = ServiceDocument(
        service_history_id=service.id,
        file_path=file_metadata["file_path"],
        file_name=file_metadata["file_name"],
        file_size=file_metadata["file_size"],
        mime_type=file_metadata["mime_type"],
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get(
    "/{watch_id}/service-history/{service_id}/documents",
    response_model=List[ServiceDocumentResponse],
)
def list_service_documents(
    watch_id: UUID,
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all documents for a service record.
    """
    _, service = verify_service_ownership(watch_id, service_id, current_user, db)
    return service.documents


@router.delete(
    "/{watch_id}/service-history/{service_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_service_document(
    watch_id: UUID,
    service_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a service document.
    """
    _, service = verify_service_ownership(watch_id, service_id, current_user, db)

    # Find the document
    document = (
        db.query(ServiceDocument)
        .filter(
            ServiceDocument.id == document_id,
            ServiceDocument.service_history_id == service.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Delete file from storage
    full_path = f"service-docs/{document.file_path}"
    delete_file(full_path, settings.UPLOAD_DIR)

    # Delete database record
    db.delete(document)
    db.commit()

    return None
