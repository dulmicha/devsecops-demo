from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.config import settings
from app.database import db
from app.models import (
    FindingCreate,
    FindingResponse,
    FindingUpdate,
    PaginatedResponse,
    Severity,
    Status,
)

router = APIRouter(prefix="/api/v1/findings", tags=["Security Findings"])


@router.get(
    "",
    response_model=PaginatedResponse[FindingResponse],
    summary="List security findings with pagination and filtering",
)
def list_findings(
    response: Response,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=settings.max_page_limit,
            description="Maximum items to return",
        ),
    ] = settings.default_page_limit,
    severity: Annotated[Severity | None, Query(description="Filter by severity")] = None,
    status_filter: Annotated[
        Status | None, Query(alias="status", description="Filter by status")
    ] = None,
    search: Annotated[str | None, Query(description="Search across title, asset, or CVE")] = None,
) -> PaginatedResponse[FindingResponse]:
    """Retrieve a paginated collection of security findings."""
    items, total = db.get_all(
        offset=offset,
        limit=limit,
        severity=severity,
        status=status_filter,
        search=search,
    )

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page-Size"] = str(len(items))
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@router.get(
    "/{finding_id}",
    response_model=FindingResponse,
    summary="Get a security finding by ID",
)
def get_finding(finding_id: str) -> FindingResponse:
    """Retrieve a single security finding by its unique ID."""
    finding = db.get_by_id(finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security finding with ID '{finding_id}' not found",
        )
    return finding


@router.post(
    "",
    response_model=FindingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new security finding",
)
def create_finding(payload: FindingCreate) -> FindingResponse:
    """Create and store a new security finding."""
    return db.create(payload)


@router.put(
    "/{finding_id}",
    response_model=FindingResponse,
    summary="Update an existing security finding",
)
def update_finding(finding_id: str, payload: FindingUpdate) -> FindingResponse:
    """Update fields of an existing security finding."""
    updated = db.update(finding_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security finding with ID '{finding_id}' not found",
        )
    return updated


@router.delete(
    "/{finding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a security finding",
)
def delete_finding(finding_id: str) -> None:
    """Remove a security finding from the store."""
    deleted = db.delete(finding_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security finding with ID '{finding_id}' not found",
        )
