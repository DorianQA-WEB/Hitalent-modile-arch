import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models import Department as DepartmentModel
from app.models import Employee as EmployeeModel
from app.schemas import Department, DepartmentResponse, EmployeeResponse, Employee, DepartmentOutput, DepartmentUpdate
from app.dependencies import get_async_db


router = APIRouter(
    prefix="/departments",
    tags=["departments"]
)

@router.post('/', response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(department : Department,
                            db : AsyncSession = Depends(get_async_db)):
    """Создать новый отдел."""
    if department.parent_id is not None:
        stmt = select(DepartmentModel).where(DepartmentModel.id == department.parent_id)

        result = await db.scalars(stmt)
        parent = result.first()
        if parent is None:
            raise HTTPException(
                status_code=404,
                detail="Родительский отдел не найден"
            )

    db_department = DepartmentModel(**department.model_dump())
    db.add(db_department)
    await db.commit()
    await db.refresh(db_department)
    return db_department

@router.post('/{id}/employees', status_code=status.HTTP_201_CREATED, response_model=EmployeeResponse)
async def create_employee(employee : Employee,
                          db : AsyncSession = Depends(get_async_db)):
    """Создать нового сотрудника."""
    stmt = select(DepartmentModel).where(DepartmentModel.id == employee.department_id)
    result = await db.scalars(stmt)
    department = result.first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Подразделение не найдено.Нельзя создать сотрудника в несуществующем подразделении.")

    elif employee.department_id is not None:
        stmt = select(DepartmentModel).where(DepartmentModel.id == employee.department_id)

        result = await db.scalars(stmt)
        department = result.first()

        db_employee = EmployeeModel(**employee.model_dump())
        db.add(db_employee)
        await db.commit()
        await db.refresh(db_employee)
        return db_employee


@router.get('/{id}', response_model=DepartmentOutput, status_code=status.HTTP_200_OK)
async def get_department(
    id: int,
    depth: int = Query(default=1, ge=1, le=5),
    include_employees: bool = Query(default=True),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить подразделение с древовидной структурой.
    - department: данные отдела
    - employees: список сотрудников (если include_employees=true), отсортирован по full_name
    - children: вложенные подразделения до указанной глубины (рекурсивно)
    """
    # Загружаем основной отдел с подразделениями и сотрудниками
    stmt = (
        select(DepartmentModel)
        .where(DepartmentModel.id == id)
        .options(selectinload(DepartmentModel.children))
    )
    if include_employees:
        stmt = stmt.options(selectinload(DepartmentModel.employees))

    result = await db.scalars(stmt)
    department = result.first()

    if not department:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    tree = await build_department_tree(
        department=department,
        depth=depth,
        include_employees=include_employees,
        current_depth=0
    )
    return tree


async def build_department_tree(
    department,
    depth: int,
    include_employees: bool,
    current_depth: int
) -> DepartmentOutput:
    """Рекурсивно строит дерево подразделений без доступа к БД."""
    # Обработка сотрудников — безопасная проверка через __dict__
    employees: List[EmployeeResponse] = []
    if include_employees:
        # Используем __dict__ или getattr без вызова ленивой загрузки
        empl_list = department.__dict__.get("employees", [])
        if empl_list is not None and hasattr(empl_list, "__iter__"):
            sorted_employees = sorted(empl_list, key=lambda e: e.full_name)
            employees = [EmployeeResponse.model_validate(emp) for emp in sorted_employees]

    # Обработка подразделений
    children: List[DepartmentOutput] = []
    if current_depth < depth:
        child_list = department.__dict__.get("children", [])
        if child_list is not None and hasattr(child_list, "__iter__"):
            for child_dept in child_list:
                child_tree = await build_department_tree(
                    department=child_dept,
                    depth=depth,
                    include_employees=include_employees,
                    current_depth=current_depth + 1
                )
                children.append(child_tree)

    return DepartmentOutput(
        department=DepartmentResponse.model_validate(department),
        employees=employees,
        children=children
    )


@router.patch('/{id}', response_model=DepartmentResponse, status_code=status.HTTP_200_OK)
async def update_department(
    id: int,
    department: DepartmentUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Обновить подразделение: можно изменить name или parent_id.
    - Оба поля опциональны
    - parent_id может быть null
    - Защита от циклов: нельзя переместить отдел в его потомка
    """
    # Загружаем текущий отдел
    stmt = select(DepartmentModel).where(DepartmentModel.id == id)
    result = await db.scalars(stmt)
    db_department = result.first()

    if not db_department:
        raise HTTPException(status_code=404, detail="Отдел не найден")

    update_data = department.model_dump(exclude_unset=True)

    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]

        # 1. Запрет на self-reference
        if new_parent_id == id:
            raise HTTPException(
                status_code=400,
                detail="Нельзя установить сам себя как родителя"
            )

        # 2. Проверка существования нового родителя
        if new_parent_id is not None:
            parent_stmt = select(DepartmentModel).where(DepartmentModel.id == new_parent_id)
            parent_result = await db.scalars(parent_stmt)
            parent = parent_result.first()
            if not parent:
                raise HTTPException(status_code=404, detail="Родительский отдел не найден")

            # 3. Проверка на цикл: нельзя переместить в потомка
            async def is_ancestor(ancestor_id: int, child_id: int) -> bool:
                """
                Проверяет, является ли ancestor_id предком child_id.
                Проходит вверх по иерархии.
                """
                if ancestor_id == child_id:
                    return True
                stmt_check = select(DepartmentModel.parent_id).where(DepartmentModel.id == child_id)
                parent_id = await db.scalar(stmt_check)
                if parent_id is None:
                    return False
                return await is_ancestor(ancestor_id, parent_id)

            if await is_ancestor(new_parent_id, id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Обнаружен цикл: нельзя переместить отдел в его собственного потомка"
                )

    # Применяем изменения
    for key, value in update_data.items():
        setattr(db_department, key, value)

    await db.commit()
    await db.refresh(db_department)
    return db_department

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    id: int,
    mode: str = Query(..., pattern="^(cascade|reassign)$"),
    reassign_to_department_id: int = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Удалить подразделение с учётом режима:
    - cascade: удалить отдел, всех сотрудников и все дочерние подразделения
    - reassign: удалить отдел, но перевести сотрудников в другой отдел
    """
    # Получаем удаляемый отдел
    stmt = select(DepartmentModel).where(DepartmentModel.id == id)
    result = await db.scalars(stmt)
    department = result.first()

    if not department:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    if mode == "reassign":
        if reassign_to_department_id is None:
            raise HTTPException(
                status_code=400,
                detail="Параметр reassign_to_department_id обязателен при mode=reassign"
            )

        # Проверяем, существует ли целевой отдел
        target_stmt = select(DepartmentModel).where(DepartmentModel.id == reassign_to_department_id)
        target_result = await db.scalars(target_stmt)
        target_department = target_result.first()

        if not target_department:
            raise HTTPException(status_code=404, detail="Целевой отдел для перевода не найден")

        # Переводим сотрудников
        await db.execute(
            update(EmployeeModel)
            .where(EmployeeModel.department_id == id)
            .values(department_id=reassign_to_department_id)
        )

    # Удаляем дочерние подразделения рекурсивно (или они удалятся через cascade)
    # Если используется ORM cascade, достаточно удалить корень
    await db.execute(
        delete(DepartmentModel).where(DepartmentModel.id == id)
    )

    await db.commit()
    await db.refresh(department)
    return HTTPException(status_code=204, detail="Подразделение удалено")

