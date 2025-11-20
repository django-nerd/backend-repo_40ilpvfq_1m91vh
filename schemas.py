"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

class Employee(BaseModel):
    """
    Employees collection schema
    Collection name: "employee"
    """
    nik: str = Field(..., description="Employee unique ID (NIK)")
    name: Optional[str] = Field(None, description="Full name")
    division: Optional[str] = Field(None, description="Division/Department")
    password: str = Field(..., description="Plain password for demo (default: 12345)")
    is_active: bool = Field(True, description="Whether employee is active")

class Task(BaseModel):
    """
    Tasks created from the dashboard
    Collection name: "task"
    """
    nik: str = Field(..., description="Employee NIK who requested the task")
    type: Literal[
        "install_packages",
        "activate_windows",
        "activate_office"
    ] = Field(..., description="Type of task")
    status: Literal["pending", "in_progress", "done", "failed"] = Field("pending")
    payload: Optional[Dict[str, Any]] = Field(None, description="Additional data such as division or package list")

class Session(BaseModel):
    """
    Simple session tokens
    Collection name: "session"
    """
    token: str = Field(...)
    nik: str = Field(...)
