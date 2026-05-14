# departments.py schemas file, contains department schemas

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Department schema, as it is added BY user,
# data sent by user.
class SDepartmentAdd(BaseModel):
    name: str = Field(default=...,
                      title = "Department name",
                      description = "Department name, given by user",
                      min_length = 1,
                      max_length = 200)

    parent_id: int|None = Field(default = None,
                                title = "Parent department ID",
                                description = "ID of parent department, if there is any")
# Setting for Pydantic Model, to work with ORM Model
    model_config = ConfigDict(from_attributes = True)

# Department schema, as it is in database, and as given TO user
class SDepartment(SDepartmentAdd):
    id: int = Field(default = ...,
                    title = "Department ID",
                    description = "Department ID, as its given by database",
                    ge = 1)
    created_at: datetime = Field(default = ...,
                                 title = "Department creation date and time",
                                 description = "Date and time when department was added to database")