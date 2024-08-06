from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from .routes import routers

app = FastAPI()
# client = docker.from_env()

app.mount("/static", StaticFiles(directory="src/static"), name="static")

for router in routers:
    app.include_router(router)
