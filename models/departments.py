# departments.py model file, contains table models for departments

from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import datetime

# Department model
class DepartmentsModel(Model):
    __tablename__ = "departments"

    id: Mapped[int]  = mapped_column(primary_key = True,
                                     autoincrement=True)
    name: Mapped[str]
    parent_id: Mapped[int|None] = mapped_column(default=None)
    created_at: Mapped[datetime]
