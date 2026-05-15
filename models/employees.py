# employees.py model file, contains table models for employees

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Foreignkey
from database import Model
from datetime import datetime, date
from departments import DepartmentsModel

# Employee model
class EmployeesModel(Model):
    __tablename= "employees"

    id: Mapped[int] = mapped_column(primary_key = True,
                                    index = True, 
                                    autoincrement = True)
    department_id: Mapped[int] = mapped_column(Foreignkey("departments.id"))
    full_name: Mapped[str]
    position: Mapped[str]
    hired_at: Mapped[date|None] = mapped_column(default = None)
    created_at: Mapped[datetime] = mapped_column(default = datetime.now())

# Connection employees.department_id --> departments.id
    owner: Mapped["DepartmentsModel"] = relationship(back_populates="employees")
    