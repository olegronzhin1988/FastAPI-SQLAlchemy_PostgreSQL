# departments.py router file. contains router and its endpoints for department

from fastapi import APIRouter, status, HTTPException
from database import SessionDep
from schemas.departments import SDepartmentAdd, SDepartment
from schemas.employees import SEmployee
from models.departments import DepartmentsModel
from models.employees import EmployeesModel
from sqlalchemy import select
from datetime import datetime

# Router for departments.
departments_router = APIRouter(prefix = "/departments",
                               tags = ["Departments"])

# ENDPOINTS:

# POST department 
# Create new department.
@departments_router.post("/",
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
@departments_router.get("/{id}",
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
    query = select(DepartmentsModel).where(DepartmentsModel.id == id)
    result = await session.execute(query)
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
                            detail = f"There is no department with id: {id}.")
    else:
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
# Change its name and/or parent department.
# name: str, optional, change mane
# parent_id: int|None, change or remove parent department
@departments_router.patch("/{id}",
                          status_code = status.HTTP_202_ACCEPTED,
                          description= 'change department name and/or parent')
async def department_update(session:SessionDep,
                            id:int,
                            name:str,
                            parent_id:int|None):
    pass

# DELETE department
# Delete department, its employees and subdepartments
# or move them to another department
# mode: str, [cascade, reassign], delete employess and subdepartments
# with department or move to another
@departments_router.delete("/{id}",
                           status_code = status.HTTP_204_NO_CONTENT,
                           description = "delete department with its employees and subdepartments or move them to another department")
async def department_delete(session:SessionDep,
                            mode):
    pass