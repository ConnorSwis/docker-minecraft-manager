from fastapi.routing import APIRouter
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..controllers import RootController
from ..database import get_db

from pydantic import BaseModel


router = APIRouter()


class ServerResponse(BaseModel):
    unique_id: str
    game_port: int
    rcon_port: int
    rcon_password: str


@router.post("/create-server", response_model=ServerResponse)
def create_server(db: Session = Depends(get_db)):
    return RootController.create_server(db)


@router.get("/server-status/{unique_id}", response_class=HTMLResponse)
def server_status(unique_id: str, request: Request, db: Session = Depends(get_db)):
    return RootController.server_status(unique_id, request, db)


@router.get("/servers-status")
def get_servers_status(db: Session = Depends(get_db)):
    return RootController.get_servers_status(db)


@router.delete("/delete-server/{unique_id}")
def delete_server(unique_id: str, db: Session = Depends(get_db)):
    return RootController.delete_server(unique_id, db)


@router.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request, db: Session = Depends(get_db)):
    return RootController.serve_homepage(request, db)
