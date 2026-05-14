# employees.py schemas file, contains employee schemas

from pydantic import BaseModel, ConfigDict
from datetime import date

# Employee schema, as it is added BY user,
# data sent by user.