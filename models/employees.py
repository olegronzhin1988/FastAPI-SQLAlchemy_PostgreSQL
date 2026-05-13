# employees.py model file, contains table models for employees

from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import datetime, date

# Employee model
class EmployeesModel(Model):
    __tablename= "employees"

    id: Mapped[int] = mapped_column(primary_key=True, 
                                    autoincrement=True)
    department_id: Mapped[int] = mapped_column()
    full_name: Mapped[str]
    position: Mapped[str]
    hired_at: Mapped[date|None] = mapped_column(default = None)
    created_at: Mapped[datetime]
