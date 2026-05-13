# main.py file contains app instance and main function to run app.

import uvicorn
from fastapi import FastAPI

app = FastAPI(title = "Employee-Department API",
              description = "Organizational structure API, used to create dependances between dfferent departments and employees",
              version = "1.0.0")



# App autostart with uvicorn server.
# Localhost and port are set for local PC work only.
# Reload is turned on for adaptive change/reload.

if __name__ == "__main__":
    uvicorn.run("main:app",
                host = "127.0.0.1",
                port = 8000,
                reload = True)