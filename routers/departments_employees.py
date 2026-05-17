# departments.py router file. contains router and its endpoints for department

from fastapi import APIRouter, status, HTTPException
from database import SessionDep
from schemas.departments import SDepartmentAdd, SDepartment
from schemas.employees import SEmployee, SEmployeeAdd
from models.departments import DepartmentsModel
from models.employees import EmployeesModel
from sqlalchemy import select, update, delete
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
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
                            detail = f"There is no department with id: {id}.")
    return department


# Router for departments.
departments_employees_router = APIRouter(prefix = "/departments",
                                         tags = ["Departments"])

# DEPARTMENT ENDPOINTS.
# POST department 
# Create new department.
@departments_employees_router.post("/",
                                   status_code = status.HTTP_201_CREATED,
                                   description = 'add new department')
async def department_add(session:SessionDep,
                         department_in:SDepartmentAdd) ->SDepartment:
# Creating dict for a new department to add to db
    department_dict = department_in.model_dump()
    department_dict["name"] = department_dict["name"].strip()
    department_dict["created_at"] = datetime.now()
    department_dict["id"] = None
# Check there is no department with the same name and parent_id:
    query = select(DepartmentsModel).where(DepartmentsModel.name == department_dict["name"], DepartmentsModel.parent_id == department_dict["parent_id"])
    result = await session.execute(query)
    department = result.scalar_one_or_none()
    if department is not None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,
                            detail = f"Department name {department_dict["name"]} with such parent_id already exists.")
    else:
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

# Returning new department
        return new_department

# GET department 
# Get details about department,
# its employees and subdepartments if possible.
# depth: int, [1..5], default = 1, depth of subdepartments search
# include_employees :bool, default=True, show employees or not
@departments_employees_router.get("/{id}",
                                  status_code = status.HTTP_200_OK,
                                  description = "get department data(details, subdepartments, employees)")
async def department_get(session:SessionDep,
                         id:int,
                         include_employees:bool = True,
                         depth:int = 1):
# Lists for endpoint response
    employees = []
    children = []

# Check if there is a department with such id
    department = department_check(id, session)
    if department:
        
# Looking for employees in department
        if include_employees:
            query = select (EmployeesModel).where(EmployeesModel.department_id == id)
            result = await session.execute(query)
            employees_found = result.scalars.all()
            if employees_found:
                for employee in employees_found:
                    employees.append(employee)

# Looking for children
        parent_ids =[department.id]
        for i in range(1, depth+1):
            if parent_ids:
                query = select(DepartmentsModel).where(DepartmentsModel.parent_id.in_(parent_ids))
                result = await session.execute(query)
                children_found = result.scalars.all()
                parent_ids =[]
            if children_found:
                parent_ids =[child.id for child in children_found]
                children[f"depth {i}"] = [child for child in children_found]
                
# Returning result
        return{"department":department,
               "employees":employees,
               "children": children}

# PATCH department 
# Change parent department via its id or name.
# name: str, optional, change mane
# parent_id: int|None, change or remove parent department
@departments_employees_router.patch("/{id}",
                                    status_code = status.HTTP_202_ACCEPTED,
                                    description= 'change department name and/or parent')
async def department_update(session:SessionDep,
                            id:int,
                            name:Optional[str] = None,
                            parent_id: Optional[int|None] = None):

# Check if there is a department with such id
    department_to_update = department_check(id, session)
          
# Check if there is a department with input name and/or id to be parent 
    if department_to_update:
        filters = {}
        if name:
            filters["name"] = name
        if parent_id:
            filters["id"] = parent_id
        if filters:
            query = select(DepartmentsModel).filter_by(**filters)
            result = await session.execute(query)
            new_parent = result.scalar_one_or_none()

# Exception: no input data
        else:        
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,
                                detail = f"No name and parent_id were given")

# Exception: no department with 
        if not new_parent:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
                                detail = f"No department with such name({name}) and/or id{parent_id}")

# Check if probable parent department is also a child or not
        else:
            parents_id =[]
            parents_id.append(new_parent.parent_id)
            while new_parent.parent_id:
                query = select(DepartmentsModel).where(DepartmentsModel.id == new_parent.parent_id)
                result = await session.execute(query)
                new_parent = result.scalar_one_or_none()
                if new_parent.parent_id:
                    parents_id.append(new_parent.parent_id)

            if id in parents_id:
                raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,
                                    detail = f"probable parent deparment, id {parents_id}, is among children of department {id}")

# commit changes
            else:
                update_data = {}
                update_data["parent_id"] = parent_id
                query = update(DepartmentsModel).where(DepartmentsModel.id == id).values(**update_data)
                await session.execute(query)

                await session.commit()
                await session.refresh(department_to_update)
                return department_to_update

# DELETE department
# Delete department, its employees and subdepartments
# or move them to another department
# mode: str, [cascade, reassign], delete employess and subdepartments
# with department or move to another
@departments_employees_router.delete("/{id}",
                                     status_code = status.HTTP_204_NO_CONTENT,
                                     description = "delete department with its employees and subdepartments or move them to another department")
async def department_delete(session:SessionDep,
                            id:int,
                            mode: DeleteMode,
                            reassign_to_department_id: Optional[int|None] = None):
    
# Check if there is a department with such id
    department_to_delete = department_check(id, session)

# Reassign mode
    if department_to_delete:
        if mode == "reassign":

# Exception if reassign_to_department_id wasn`t given
            if reassign_to_department_id ==  None:
                raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,
                                    detail = f"reassign_to_department_id is required in reassign mode")

# Exception if reassign_to_department_id equals id
            elif reassign_to_department_id == id:
                raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,
                                    detail = f"can`t reassign employees to the same department")

# If reassign_to_department_id is OK
            else:
                query = update(EmployeesModel).where(EmployeesModel.department_id == id).values(department_id=reassign_to_department_id)
                await session.execute(query)
                await session.commit()

# Same part of both modes
        if mode == "reassign" or mode == "cascade":
            query = delete(DepartmentsModel).where(DepartmentsModel.id == id)
            await session.execute(query)
            await session.commit()
            query = delete(DepartmentsModel).where(DepartmentsModel.parent_id == id)
            await session.execute(query)
            await session.commit()
            query = delete(EmployeesModel).where(EmployeesModel.department_id== id)
            await session.execute(query)
            await session.commit()

# EMPLOYEES ENDPOINTS:
# POST employee 
# Create new employee.
@departments_employees_router.post("/employees/",
                                   status_code = status.HTTP_201_CREATED,
                                   description = 'add new employee')
async def employee_add(session:SessionDep,
                       id:int,
                       employee_in:SEmployeeAdd)->SEmployee:

# Creating a dict for a new employee
    employee_dict = employee_in.model_dump()
    employee_dict["full_name"] = employee_dict["full_name"].strip()
    employee_dict["created_at"] = datetime.now()
    employee_dict["id"] = None

# Check if there is employee with the same name and department_id
    query = select(EmployeesModel).where(EmployeesModel.department_id ==employee_dict["department_id"], EmployeesModel.full_name == employee_dict['full_name'])
    result = await session.execute(query)
    employee = result.scalar_one_or_none()

# Exception if there is employee
    if employee:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,
                            detail = f"Employee with full name {employee_dict["full_name"]} already exists in department {employee_dict["department_id"]}")

# Creating new employee
    else:
        new_employee = EmployeesModel(**employee_dict)
        session.add(new_employee)
        await session.commit()
        await session.refresh(new_employee)
        return new_employee

                                         
