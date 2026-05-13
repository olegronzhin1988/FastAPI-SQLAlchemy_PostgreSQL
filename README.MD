# Transaction Manager 

Simple project with FastAPI, SQLAlchemy 2 and PostgreSQL database.
Allows different users to create transactions and categories for them to manage spendings.

## Features
- CRUD: Create, Read, Update and Delete(soft & hard) tasks.
- PostgreSQL database
- Swagger UI
- Uvicorn and database autostart from main.py file

## Tech
- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL 
- Pydantic
- datetime

## install and start
- Clone repository
- Create virtual environment(venv) in project folder(python -m venv venv) and activate it(venv\Scripts\activate)
- Install all from requirements.txt (pip install -r requirements.txt)
- start main.py from terminal (python main.py)
- Open Swagger UI to test ( ttp://127.0.0.1:8000/docs)
- To quit uvicorn server, press Ctrl+C