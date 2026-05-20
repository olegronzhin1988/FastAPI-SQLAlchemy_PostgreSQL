# departments_employees.py router file. contains router and its endpoints for department and employee

from fastapi import APIRouter, status, HTTPException
from database import SessionDep
from schemas.departments import SDepartmentAdd, SDepartment
from schemas.employees import SEmployee, SEmployeeAdd
from models.departments_employees import DepartmentsModel, EmployeesModel
from sqlalchemy import select, update, null
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

# Function for bad request HTTPException
def bad_request_exception(detail):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail= detail)

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
        bad_request_exception(detail=f"Department name {department_dict['name']} with such parent_id already exists.")

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

# Function for children if depth > 1
    def children_tree(department:DepartmentsModel, end_depth:int = 1, current_depth:int = 0) -> dict:

        data = {
            "id": department.id,
            "name": department.name,
            "parent_id":department.parent_id,
            "created_at":department.created_at,
            "children":[]
        }
        if current_depth < end_depth:
            data["children"] = [children_tree(child, end_depth, current_depth+1) for child in department.children if child]
            if current_depth == end_depth-1 or not data["children"]:
                del data["children"]
            return data
        
# Creating lists
    employees = []
    children = []

# Check if there is department with such id
    department = await department_check(id, session)

    if department:

# Looking for employees if necessary
        if include_employees:  
            employees = department.employees
            employees = [SEmployee.model_validate(employee) for employee in employees]
            employees = sorted(employees, key=lambda x: x.full_name)

# Looking for children
        if depth == 1:
            children = [SDepartment.model_validate(child) for child in department.children]
        if 1< depth <=5 :
            children = [children_tree(child, end_depth=depth) for child in department.children]

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
                                    description='change department parent by name or id')
async def department_update(session:SessionDep,
                            id:int,
                            name:Optional[str] = None,
                            parent_id:Optional[int|None] = None):

# Check if there is department with such id    
    # Check if there is department with such id
    department_to_update = await department_check(id, session)

    # Variable to store the new parent ID
    new_parent_id = None

    # Looking for new parent department if name and/or id were given:
    if name or parent_id:
        conditions = []
        details = "No department with "
        if name:
            conditions.append(DepartmentsModel.name == name.strip())
            details += f"name {name.strip()} "
            if parent_id:
                details += "and "
        if parent_id:
            conditions.append(DepartmentsModel.id == parent_id)
            details += f"id {parent_id}"

        query = select(DepartmentsModel).where(*conditions)
        result = await session.execute(query)
        new_parent = result.scalar_one_or_none()

        # New parent department wasn't found
        if not new_parent:
            bad_request_exception(detail=details)

        # New parent department exists
        else:
            # Exception: id and new parent id are the same
            if new_parent.id == id:
                bad_request_exception(detail="A department cannot be its own parent")

            # Check if department to update is a parent of its new parent or not
            visited = set()
            current_parent = new_parent
            while current_parent:
                if current_parent.id in visited:
                    bad_request_exception(detail="Circular reference detected")
                visited.add(current_parent.id)
                
                if id == current_parent.id:
                    bad_request_exception(detail=f"Department {id} cannot be moved under its own descendant")
                
                if current_parent.parent_id:
                    # Используем запрос для загрузки родителя
                    parent_query = select(DepartmentsModel).where(DepartmentsModel.id == current_parent.parent_id)
                    parent_result = await session.execute(parent_query)
                    current_parent = parent_result.scalar_one_or_none()
                else:
                    break

            # Store the found parent's ID for the update
            new_parent_id = new_parent.id

    # Determine the final parent_id for the update
    final_parent_id = new_parent_id if new_parent_id is not None else parent_id

    # Updating department
    query = update(DepartmentsModel).where(DepartmentsModel.id == id).values(parent_id=final_parent_id)
    await session.execute(query)
    await session.commit()

    # Refresh and return updated department
    query = select(DepartmentsModel).where(DepartmentsModel.id == id)
    result = await session.execute(query)
    updated_department = result.scalar_one_or_none()
    
    if updated_department:
        # ✅ IMPORTANT FIX: Return Pydantic schema, NOT ORM object
        return SDepartment.model_validate(updated_department)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Department with id {id} wasn't found. Something wrong")  

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
    
# Check if there is department with such id   
    department_to_delete = await department_check(id, session)

# Reassign employees if necessary
    if mode == DeleteMode.REASSIGN:
        if reassign_to_department_id is None:
            bad_request_exception(detail="reassign_to_department_id is required in reassign mode")

        if reassign_to_department_id == id:
            bad_request_exception(detail="cannot reassign employees to the same department")

# Check if there is department to reassign employees
        await department_check(reassign_to_department_id, session)
        query = update(EmployeesModel).where(EmployeesModel.department_id == id).values(department_id=reassign_to_department_id)
        await session.execute(query)
        await session.commit()

# Updating department to delete
        await session.refresh(department_to_delete)

# delete department
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

# Creating employee dict from import data    
    employee_dict = employee_in.model_dump()
    employee_dict["full_name"] = employee_dict["full_name"].strip()
    employee_dict["created_at"] = datetime.now()

# Check if there is department with such id   
    await department_check(employee_dict["department_id"], session)

# Check if there is employee with the same name in this department
    query = select(EmployeesModel).where(
        EmployeesModel.department_id == employee_dict["department_id"],
        EmployeesModel.full_name == employee_dict["full_name"])
    result = await session.execute(query)
    employee = result.scalar_one_or_none()

# Exception - employee with this name already exists in this department
    if employee:
        bad_request_exception(detail=f"Employee with full name {employee_dict['full_name']} already exists in department {employee_dict['department_id']}")

# Assigning employee to department
    new_employee = EmployeesModel(**employee_dict)
    session.add(new_employee)
    await session.commit()
    await session.refresh(new_employee)
    return new_employee

                                         
