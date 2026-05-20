# departments_employees.py model file, contains table models for departments and employees

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List, Optional
from database import Model
from datetime import datetime, date


# Department model
class DepartmentsModel(Model):
    __tablename__ = "departments"
# parameters
    id: Mapped[int]  = mapped_column(primary_key = True, init = False)
    name: Mapped[str]
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

# relationships
#  departmnet->employees, one to many
    employees: Mapped[List["EmployeesModel"]] = relationship(
        back_populates="department", 
        cascade="all, delete-orphan",
        uselist = True, 
        init = False,
        default_factory=list, 
        lazy="selectin")
    
# parent -> children, one to many, self-referential
    children: Mapped[List["DepartmentsModel"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        init = False,
        uselist = True,
        default_factory=list,
        collection_class = list,
        lazy = "selectin",
        join_depth=7)  #if there is no join_depth, there will be error, and only "dynamic" will work 

# children ->parent, many to one, self-referential    
    parent: Mapped[Optional["DepartmentsModel"]] = relationship(
        back_populates="children",
        remote_side=[id],
        init = False,
        lazy = "noload")

# Employee model
class EmployeesModel(Model):
    __tablename__= "employees"

# parameters
    id: Mapped[int] = mapped_column(primary_key = True, init = False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    full_name: Mapped[str]
    position: Mapped[str]
    hired_at: Mapped[Optional[date]] = mapped_column(default = None)
    created_at: Mapped[datetime] = mapped_column(default = datetime.now)

# relationships
# employee->department, many to one
    department: Mapped[DepartmentsModel] = relationship(back_populates="employees", init = False)    
