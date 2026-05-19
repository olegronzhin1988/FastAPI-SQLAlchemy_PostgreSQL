# departments_employees.py router file. contains router and its endpoints for department and employee

from fastapi import APIRouter, status, HTTPException
from database import SessionDep
from schemas.departments import SDepartmentAdd, SDepartment
from schemas.employees import SEmployee, SEmployeeAdd
from models.departments_employees import DepartmentsModel, EmployeesModel
from sqlalchemy import select, update
from datetime import datetime
from enum import Enum
from typing import Optional

# Class for department delete mode
class DeleteMode(str, Enum):
    CASCADE = "cascade"
    REASSIGN = "reassign"

# Function to check if there is a department with such id
async def department_check(id:int, session:SessionDep):
    query = select(DepartmentsModel).where(DepartmentsModel.id == id)
    result = await session.execute(query)
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no department with id: {id}.")
    return department


# Router for departments.
departments_employees_router = APIRouter(prefix="/departments",
                                         tags=["Departments"])

# DEPARTMENT ENDPOINTS.
# POST department 
# Create new department.
@departments_employees_router.post("/",
                                   status_code=status.HTTP_201_CREATED,
                                   description='add new department')
async def department_add(session:SessionDep,
                         department_in:SDepartmentAdd) -> SDepartment:
# Creating dict for a new department to add to db
    department_dict = department_in.model_dump()
    department_dict["name"] = department_dict["name"].strip()
    department_dict["created_at"] = datetime.now()

    if department_dict["parent_id"] is not None:
        await department_check(department_dict["parent_id"], session)

# Check there is no department with the same name and parent_id:
    query = select(DepartmentsModel).where(
        DepartmentsModel.name == department_dict["name"],
        DepartmentsModel.parent_id == department_dict["parent_id"]
    )
    result = await session.execute(query)
    department = result.scalar_one_or_none()
    if department is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Department name {department_dict['name']} with such parent_id already exists.")

# Creating DepartmentsModel object to add to db:
    new_department = DepartmentsModel(**department_dict)
    session.add(new_department)
    await session.commit()
    await session.refresh(new_department)

# Check if new department id and parent_id are the same, if yes - correcting parent_id 
    if new_department.id == new_department.parent_id:
        new_department.parent_id = None
        session.add(new_department)
        await session.commit()
        await session.refresh(new_department)

    return new_department

# GET department 
# Get details about department,
# its employees and subdepartments if possible.
# depth: int, [1..5], default = 1, depth of subdepartments search
# include_employees :bool, default=True, show employees or not
@departments_employees_router.get("/{id}",
                                  status_code=status.HTTP_200_OK,
                                  description="get department data(details, subdepartments, employees)")
async def department_get(session:SessionDep,
                         id:int,
                         include_employees:bool=True,
                         depth:int=1):
    employees = []
    children = []

    department = await department_check(id, session)
    if department:
        if include_employees:  
            employees = department.employees
            if employees:
                employees = [SEmployee.model_validate(employee) for employee in employees]
                employees = sorted(employees, key=lambda x: x.full_name)
            else:
                employees = []
        query = department.children
        children = await session.execute(query)
        children = children.scalars().all()
        children = [SDepartment.model_validate(child) for child in children]
    return {
        "department": SDepartment.model_validate(department),
        "employees": employees,
        "children": children
    }

# PATCH department 
# Change parent department via its id or name.
# name: str, optional, change name
# parent_id: int|None, change or remove parent department
@departments_employees_router.patch("/{id}",
                                    status_code=status.HTTP_202_ACCEPTED,
                                    description='change department name and/or parent')
async def department_update(session:SessionDep,
                            id:int,
                            name:Optional[str] = None,
                            parent_id:Optional[int|None] = None):
    department_to_update = await department_check(id, session)

    if name is None and parent_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No name or parent_id were given")

    if name is not None:
        department_to_update.name = name.strip()

    if parent_id is not None:
        if parent_id == id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="A department cannot be its own parent")

        new_parent = await department_check(parent_id, session)

        parents_id = []
        current_parent = new_parent
        while current_parent is not None:
            if current_parent.id == id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Department {id} cannot be moved under its own descendant")
            parents_id.append(current_parent.id)
            current_parent = current_parent.parent

        department_to_update.parent_id = parent_id

    session.add(department_to_update)
    await session.commit()
    await session.refresh(department_to_update)
    return department_to_update

# DELETE department
# Delete department, its employees and subdepartments
# or move them to another department
# mode: str, [cascade, reassign], delete employees and subdepartments
# with department or move to another
@departments_employees_router.delete("/{id}",
                                     status_code=status.HTTP_204_NO_CONTENT,
                                     description="delete department with its employees and subdepartments or move them to another department")
async def department_delete(session:SessionDep,
                            id:int,
                            mode:DeleteMode,
                            reassign_to_department_id:Optional[int|None] = None):
    department_to_delete = await department_check(id, session)

    if mode == DeleteMode.REASSIGN:
        if reassign_to_department_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="reassign_to_department_id is required in reassign mode")
        if reassign_to_department_id == id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="cannot reassign employees to the same department")
        await department_check(reassign_to_department_id, session)

        query = update(EmployeesModel).where(EmployeesModel.department_id == id).values(department_id=reassign_to_department_id)
        await session.execute(query)
        await session.commit()

    await session.delete(department_to_delete)
    await session.commit()

# EMPLOYEES ENDPOINTS:
# POST employee 
# Create new employee.
@departments_employees_router.post("/employees/",
                                   status_code=status.HTTP_201_CREATED,
                                   description='add new employee')
async def employee_add(session:SessionDep,
                       employee_in:SEmployeeAdd) -> SEmployee:
    employee_dict = employee_in.model_dump()
    employee_dict["full_name"] = employee_dict["full_name"].strip()
    employee_dict["created_at"] = datetime.now()

    await department_check(employee_dict["department_id"], session)

    query = select(EmployeesModel).where(
        EmployeesModel.department_id == employee_dict["department_id"],
        EmployeesModel.full_name == employee_dict["full_name"]
    )
    result = await session.execute(query)
    employee = result.scalar_one_or_none()

    if employee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Employee with full name {employee_dict['full_name']} already exists in department {employee_dict['department_id']}")

    new_employee = EmployeesModel(**employee_dict)
    session.add(new_employee)
    await session.commit()
    await session.refresh(new_employee)
    return new_employee

                                         
