# departments.py model file, contains table models for departments

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List
from database import Model
from datetime import datetime
from employees import EmployeesModel

# Department model
class DepartmentsModel(Model):
    __tablename__ = "departments"

    id: Mapped[int]  = mapped_column(primary_key = True,
                                     index = True,
                                     autoincrement = True)
    name: Mapped[str]
    parent_id: Mapped[int|None] = mapped_column(ForeignKey("departments.id"), 
                                                default = None)
    created_at: Mapped[datetime] = mapped_column(default = datetime.now())

# Connection departments.id --> employees.department_id
    categories: Mapped[List["EmployeesModel"]] = relationship(
        back_populates="department_id",
        cascade = "all, delete-orphan")

# Connection departments.id --> departments.parent_id
    categories: Mapped[List["DepartmentsModel"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan")

# Connection departments.parent_id -->departments.id
    owner: Mapped["DepartmentsModel"] = relationship(back_populates="departments")