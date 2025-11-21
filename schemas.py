"""
Unified Platform Schemas for Student Activities, Community Services, and Volunteering

Each Pydantic model represents a MongoDB collection. The collection name is the lowercase
of the class name, e.g. Branch -> "branch".

These models validate incoming/outgoing payloads and serve as the single source of truth
for data across the platform.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime

# Core reference data
class Branch(BaseModel):
    code: str = Field(..., description="Unique branch code, e.g., RU-01")
    name: str = Field(..., description="Branch name")
    region: Optional[str] = Field(None, description="Region or city")
    manager_name: Optional[str] = None
    manager_email: Optional[EmailStr] = None

class Role(BaseModel):
    name: Literal[
        "admin",
        "hq_manager",
        "branch_manager",
        "coordinator",
        "reviewer",
        "finance",
        "it",
        "quality",
        "viewer",
    ]
    description: Optional[str] = None

class User(BaseModel):
    full_name: str
    email: EmailStr
    branch_code: Optional[str] = None
    role: str = Field(..., description="Role name")
    is_active: bool = True

# Programs and requests lifecycle
class Program(BaseModel):
    title: str
    type: Literal["student_activity", "community_service", "volunteering"]
    objective: Optional[str] = None
    kpis: List[str] = Field(default_factory=list, description="List of KPI codes or names")

class BudgetItem(BaseModel):
    name: str
    amount: float = Field(ge=0)

class ProgramRequest(BaseModel):
    branch_code: str
    program_title: str
    program_type: Literal["student_activity", "community_service", "volunteering"]
    description: Optional[str] = None
    proposed_date: Optional[datetime] = None
    location: Optional[str] = None
    budget: List[BudgetItem] = Field(default_factory=list)
    requested_by: Optional[str] = None  # user email or id
    status: Literal["submitted", "under_review", "approved", "rejected"] = "submitted"

class Approval(BaseModel):
    request_id: str
    approved_by: str
    decision: Literal["approved", "rejected"]
    notes: Optional[str] = None

class Resource(BaseModel):
    name: str
    type: Literal["venue", "equipment", "it_support", "media", "transport"]
    branch_code: Optional[str] = None
    capacity: Optional[int] = None
    availability_status: Literal["available", "reserved", "maintenance"] = "available"

class Event(BaseModel):
    request_id: Optional[str] = None
    title: str
    branch_code: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    resources: List[str] = Field(default_factory=list)
    status: Literal["scheduled", "in_progress", "completed", "cancelled"] = "scheduled"

# Execution and reporting
class Report(BaseModel):
    request_id: Optional[str] = None
    event_id: Optional[str] = None
    submitted_by: Optional[str] = None
    summary: str
    attendees_count: Optional[int] = Field(default=None, ge=0)
    photos: List[str] = Field(default_factory=list)

class Evaluation(BaseModel):
    request_id: Optional[str] = None
    event_id: Optional[str] = None
    score: float = Field(ge=0, le=100)
    methodology: Optional[str] = None
    comments: Optional[str] = None

class Notification(BaseModel):
    user_email: Optional[EmailStr] = None
    branch_code: Optional[str] = None
    title: str
    message: str
    type: Literal["info", "success", "warning", "error"] = "info"
    is_read: bool = False
