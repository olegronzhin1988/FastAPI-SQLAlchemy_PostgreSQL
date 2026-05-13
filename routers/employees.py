# employees.py router filem contains router and its endpoints

from fastapi import APIRouter, status, HTTPException
from datetime import datetime, date
from database import SessionDep

# Router for employees.
employees_router = APIRouter(prefix = 'departments/{id:int}/employees',
                             tags = ["Employees"]) 

# ENDPOINTS:

# POST employee 
# Create new employee.
@employees_router.post("/",
                       status_code = status.HTTP_201_CREATED,
                       description = 'add new department')
async def employee_add():
    pass
