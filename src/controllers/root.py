import random
import string
import socket
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from ..database import Server

templates = Jinja2Templates(directory="src/templates")


class ServerResponse(BaseModel):
    unique_id: str
    game_port: int
    rcon_port: int
    rcon_password: str


def get_random_port(start, end):
    return random.randint(start, end)


def is_port_open(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def get_server_status(server):
    # Simulate Docker logic with dummy code
    # try:
    #     container = client.containers.get(server.container_id)
    #     return container.status == "running"
    # except docker.errors.NotFound:
    #     return False

    # Dummy status logic
    return True if server.unique_id.startswith('a') else False


class RootController:
    @staticmethod
    def create_server(db: Session):
        game_port = get_random_port(25000, 25999)
        rcon_port = game_port + 1000
        rcon_password = ''.join(random.choices(
            string.ascii_letters + string.digits, k=36))
        unique_id = ''.join(random.choices(
            string.ascii_letters + string.digits, k=6))

        server_entry = Server(unique_id=unique_id, container_id=unique_id, game_port=str(
            game_port), rcon_port=str(rcon_port), rcon_password=rcon_password)
        db.add(server_entry)
        db.commit()

        return ServerResponse(
            unique_id=unique_id,
            game_port=game_port,
            rcon_port=rcon_port,
            rcon_password=rcon_password
        )

    @staticmethod
    def server_status(unique_id: str, request: Request, db: Session):
        server_entry = db.query(Server).filter(
            Server.unique_id == unique_id).first()

        if not server_entry:
            return templates.TemplateResponse("status.jinja", {
                "request": request,
                "server": None,
                "status": "DELETED"
            })

        status = "RUNNING"  # Placeholder for actual status logic

        return templates.TemplateResponse("status.jinja", {
            "request": request,
            "server": server_entry,
            "status": status
        })

    @staticmethod
    def get_servers_status(db: Session):
        servers = db.query(Server).all()
        server_statuses = []

        for server in servers:
            status = "Running" if get_server_status(server) else "Stopped"
            server_statuses.append({
                "unique_id": server.unique_id,
                "status": status
            })

        return {"servers": server_statuses}

    @staticmethod
    def delete_server(unique_id: str, db: Session):
        server_entry = db.query(Server).filter(
            Server.unique_id == unique_id).first()
        if not server_entry:
            raise HTTPException(status_code=404, detail="Server not found")

        # Dummy Docker code (commented out for simulation)
        # container_id = server_entry.container_id
        # try:
        #     container = client.containers.get(container_id)
        #     container.remove(force=True)
        # except docker.errors.NotFound:
        #     pass

        db.delete(server_entry)
        db.commit()
        return {"status": "DELETED"}

    @staticmethod
    def serve_homepage(request: Request, db: Session):
        servers = db.query(Server).all()
        server_statuses = []

        for server in servers:
            status = "Running" if get_server_status(server) else "Stopped"
            server_statuses.append({
                "unique_id": server.unique_id,
                "status": status
            })

        return templates.TemplateResponse("index.jinja", {
            "request": request,
            "servers": server_statuses
        })
