# employees.py schemas file, contains employee schemas

from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime

# Employee schema, as it is added BY user,
# data sent by user.
class SEmployeeAdd(BaseModel):
    full_name: str = Field(default =...,
                           title = "Full name",
                           description = "Surname, first name and patronymic of employee",
                           min_length = 1,
                           max_length = 200)
    
    position: str = Field(default =...,
                          title = "Position",
                          description = "Position employee occupies in department",
                          min_length = 1,
                          max_length = 200)
    
    hired_at: date|None = Field(default = None,
                                title = "Date of hire",
                                description = "Date employee was hired to department")

    department_id: int = Field(default = ...,
                               title = "Department ID",
                               description = "ID of department where employee works")
    
# Setting for Pydantic Model, to work with ORM Model
    model_config = ConfigDict(from_attributes = True)

# Employee schema, as it is in database, and as given TO user
class SEmployee(SEmployeeAdd):
    id: int = Field(default = ...,
                    title = "Employee ID",
                    description = "Employee ID, as its given by database",
                    ge = 1)
    
    created_at: datetime = Field(default = ...,
                                 title = "Employee creation date and time",
                                 description = "Date and time when employee was added to database")