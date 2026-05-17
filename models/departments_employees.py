# departments_employees.py model file, contains table models for departments and employees

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List, Optional
from database import Model
from datetime import datetime, date


# Department model
class DepartmentsModel(Model):
    __tablename__ = "departments"

    id: Mapped[int]  = mapped_column(primary_key = True,
                                     index = True,
                                     autoincrement = True)
    name: Mapped[str]

    employees: Mapped[List["EmployeesModel"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
        init = False
    )

    children: Mapped[List["DepartmentsModel"]] = relationship(
        back_populates="parent",
        foreign_keys="DepartmentsModel.parent_id",
        cascade="all, delete-orphan",
        init = False
    )

    parent: Mapped[Optional["DepartmentsModel"]] = relationship(
        back_populates="children",
        remote_side=[id],
        foreign_keys="DepartmentsModel.parent_id",
        init = False
    )

    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"),
                                                     nullable=True,
                                                     default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

# Employee model
class EmployeesModel(Model):
    __tablename__= "employees"

    id: Mapped[int] = mapped_column(primary_key = True,
                                    index = True, 
                                    autoincrement = True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    full_name: Mapped[str]
    position: Mapped[str]

# Connection employees.department_id --> departments.id
    department: Mapped["DepartmentsModel"] = relationship(back_populates="employees")

    hired_at: Mapped[Optional[date]] = mapped_column(default = None)
    created_at: Mapped[datetime] = mapped_column(default = datetime.now)