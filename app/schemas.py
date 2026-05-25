from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List


class Department(BaseModel):
    name : str = Field(..., min_length=1, max_length=200, description="название отдела (1-200 символов)")
    parent_id : int | None = Field(None, description="id родительского отдела или None")

    @field_validator('name')
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

class DepartmentResponse(Department):
    id : int = Field(..., description="id отдела")
    created_at : datetime = Field(..., description="дата создания отдела")

    model_config = ConfigDict(from_attributes=True)


class Employee(BaseModel):
    department_id : int = Field(..., description="id отдела")
    full_name : str = Field(..., min_length=1, max_length=200, description="ФИО сотрудника от 1 до 200 символов")
    position : str = Field(..., min_length=1, max_length=200, description="должность сотрудника от 1 до 200 символов")
    hired_at : datetime | None = Field(None, description="дата приема на работу")
    created_at : datetime = Field(..., description="дата создания сотрудника")


class EmployeeResponse(Employee):
    id : int = Field(..., description="id сотрудника")

    model_config = ConfigDict(from_attributes=True)


class DepartmentOutput(BaseModel):
    department : DepartmentResponse
    employees : List[EmployeeResponse] = []
    children : List["DepartmentOutput"] = []

    model_config = ConfigDict(from_attributes=True)

DepartmentOutput.model_rebuild()


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200, description="название отдела (1-200 символов)")
    parent_id: int | None = Field(None, description="id родительского отдела или None")

    model_config = ConfigDict(from_attributes=True)