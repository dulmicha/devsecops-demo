from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Status(StrEnum):
    OPEN = "OPEN"
    IN_TRIAGE = "IN_TRIAGE"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class FindingBase(BaseModel):
    """Base schema for security findings."""

    title: str = Field(..., min_length=3, max_length=200, description="Vulnerability title")
    severity: Severity = Field(default=Severity.MEDIUM, description="Finding severity level")
    asset_name: str = Field(..., min_length=2, max_length=100, description="Target asset name")
    cve_id: str | None = Field(
        default=None, max_length=30, description="Associated CVE ID if known"
    )
    status: Status = Field(default=Status.OPEN, description="Current triage status")
    description: str | None = Field(
        default="", max_length=2000, description="Vulnerability context and details"
    )


class FindingCreate(FindingBase):
    """Payload schema for creating a new finding."""

    pass


class FindingUpdate(BaseModel):
    """Payload schema for updating an existing finding."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    severity: Severity | None = None
    asset_name: str | None = Field(default=None, min_length=2, max_length=100)
    cve_id: str | None = Field(default=None, max_length=30)
    status: Status | None = None
    description: str | None = Field(default=None, max_length=2000)


class FindingResponse(FindingBase):
    """Response schema for a security finding."""

    id: str = Field(..., description="Unique UUID identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse[T](BaseModel):
    """Generic envelope for paginated collections."""

    items: list[T]
    total: int = Field(..., ge=0, description="Total matching items")
    limit: int = Field(..., ge=1, description="Page size limit")
    offset: int = Field(..., ge=0, description="Page offset")
    has_more: bool = Field(..., description="Whether subsequent pages exist")
