"""
Схемы Pydantic для валидации и сериализации данных API.

Определяет модели входных, выходных и вложенных данных для отделов и сотрудников.
Используется в FastAPI для:
- Валидации входящих запросов.
- Сериализации ответов из ORM (SQLAlchemy) моделей.
- Поддержки вложенных структур (например, дерево отделов с сотрудниками).

Включает:
- Базовые схемы создания/обновления.
- Схемы ответов с ID и метаданными.
- Иерархическую схему DepartmentOutput для отображения древовидной структуры.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List


class Department(BaseModel):
    """
    Схема для создания нового отдела.

    Поля:
        name: Название отдела (обязательное, 1–200 символов).
        parent_id: ID родительского отдела или None (для корневых отделов).
    """
    name : str = Field(..., min_length=1, max_length=200, description="название отдела (1-200 символов)")
    parent_id : int | None = Field(None, description="id родительского отдела или None")

    @field_validator('name')
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

class DepartmentResponse(Department):
    """
    Схема ответа с данными отдела.

    Используется при возврате существующего отдела.
    Добавляет:
        id: Уникальный идентификатор отдела.
        created_at: Дата и время создания записи.
    """
    id : int = Field(..., description="id отдела")
    created_at : datetime = Field(..., description="дата создания отдела")

    model_config = ConfigDict(from_attributes=True)


class Employee(BaseModel):
    """
    Схема для создания нового сотрудника.

    Поля:
        department_id: Привязка к отделу.
        full_name: Полное имя (ФИО), 1–200 символов.
        position: Должность, 1–200 символов.
        hired_at: Дата приёма на работу (может быть None).
        created_at: Дата создания записи.
    """
    department_id : int = Field(..., description="id отдела")
    full_name : str = Field(..., min_length=1, max_length=200, description="ФИО сотрудника от 1 до 200 символов")
    position : str = Field(..., min_length=1, max_length=200, description="должность сотрудника от 1 до 200 символов")
    hired_at : datetime | None = Field(None, description="дата приема на работу")
    created_at : datetime = Field(..., description="дата создания сотрудника")


class EmployeeResponse(Employee):
    """
    Схема ответа с данными сотрудника.

    Добавляет поле `id` к базовой схеме.
    """
    id : int = Field(..., description="id сотрудника")

    model_config = ConfigDict(from_attributes=True)


class DepartmentOutput(BaseModel):
    """
    Иерархическая схема для вывода дерева отделов.

    Представляет один узел дерева:
        - Информация об отделе.
        - Список сотрудников этого отдела.
        - Список вложенных подотделов (рекурсивно).

    Используется в эндпоинтах, возвращающих структуру компании.
    """
    department : DepartmentResponse
    employees : List[EmployeeResponse] = []
    children : List["DepartmentOutput"] = []

    model_config = ConfigDict(from_attributes=True)

DepartmentOutput.model_rebuild()


class DepartmentUpdate(BaseModel):
    """
    Схема для частичного обновления отдела.

    Все поля необязательные — можно обновить только одно.
    Поля:
        name: Новое название (если передано).
        parent_id: Новый родительский ID (или None).
    """
    name: str | None = Field(None, min_length=1, max_length=200, description="название отдела (1-200 символов)")
    parent_id: int | None = Field(None, description="id родительского отдела или None")

    model_config = ConfigDict(from_attributes=True)