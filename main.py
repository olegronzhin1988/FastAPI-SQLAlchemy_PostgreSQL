# main.py file contains app instance and main function to run app.

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine, Model
from routers.departments import departments_router
from routers.employees import employees_router

# Decorated lifespan function, activates database connection
# on app/server launch.
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    print("PostgreSQL DB connected")
    yield
    print("Database desconected")

# Creating app
app = FastAPI(lifespan = lifespan,
              title = "Employee-Department API",
              description = "Organizational structure API, used to create dependances between dfferent departments and employees",
              version = "1.0.0")

# Connecting routers
app.include_router(departments_router, employees_router)

# Default wellcome root GET endpoint
@app.get("/")
async def root():
    return {"message":"API app is on, wellcome"}

# App autostart with uvicorn server.
# Localhost and port are set for local PC work only.
# Reload is turned on for adaptive change/reload.

if __name__ == "__main__":
    uvicorn.run("main:app",
                host = "127.0.0.1",
                port = 8000,
                reload = True)