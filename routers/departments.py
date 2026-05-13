# departments.py router file. contains router and its endpoints for department

from fastapi import APIRouter, status, HTTPException
from database import SessionDep

# Router for departments.
departments_router = APIRouter(prefix = "/departments",
                               tags = ["Departments"])

# ENDPOINTS:

# POST department 
# Create new department.
@departments_router.post("/",
                         status_code = status.HTTP_201_CREATED,
                         description = 'add new department')
async def department_add():
    pass
    
# GET department 
# Get details about department,
# its employees and subdepartments if possible.
# depth: int, [1..5], depth of subdepartments
# include_employees :bool, default=True, show employees or not
@departments_router.get("/{id:imt}",
                        status_code = status.HTTP_200_OK,
                        description = "get department data(details, subdepartments, employees)")
async def department_get():
    pass

# PATCH department 
# Change its name and/or parent department.
# name: str, optional, change mane
# parent_id: int|None, change or remove parent department
@departments_router.patch("/{id:int}",
                          status_code = status.HTTP_202_ACCEPTED,
                          description= 'change department name and/or parent')
async def department_update():
    pass

# DELETE department
# Delete department, its employees and subdepartments
# or move them to another department
# mode: str, [cascade, reassign], delete employess and subdepartments
# with department or move to another
@departments_router.delete("/{id:int}",
                           status_code = status.HTTP_204_NO_CONTENT,
                           description = "delete department with its employees and subdepartments or move them to another department")
async def department_delete():
    pass