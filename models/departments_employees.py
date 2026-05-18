# departments_employees.py model file, contains table models for departments and employees

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List, Optional
from database import Model
from datetime import datetime, date


# Department model
class DepartmentsModel(Model):
    __tablename__ = "departments"

    id: Mapped[int]  = mapped_column(primary_key = True, init = False)
    name: Mapped[str]
    parent_id: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    employees: Mapped[List["EmployeesModel"]] = relationship(back_populates="department", cascade="all, delete-orphan", init = False, default_factory=list, lazy="selectin")


# Employee model
class EmployeesModel(Model):
    __tablename__= "employees"

    id: Mapped[int] = mapped_column(primary_key = True, init = False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    full_name: Mapped[str]
    position: Mapped[str]
    hired_at: Mapped[Optional[date]] = mapped_column(default = None)
    created_at: Mapped[datetime] = mapped_column(default = datetime.now)

    department: Mapped[DepartmentsModel] = relationship(back_populates="employees", init = False)    
