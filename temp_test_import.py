from models.departments_employees import DepartmentsModel, EmployeesModel
print("DepartmentsModel ok", DepartmentsModel.__tablename__)
print("EmployeesModel ok", EmployeesModel.__tablename__)
print("Department columns", [c.name for c in DepartmentsModel.__table__.columns])
print("Employee columns", [c.name for c in EmployeesModel.__table__.columns])
print("Department relationships", list(DepartmentsModel.__mapper__.relationships.keys()))
print("Employee relationships", list(EmployeesModel.__mapper__.relationships.keys()))
