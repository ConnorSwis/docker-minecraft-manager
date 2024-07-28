from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import docker
from docker.models.containers import Container
import random
import string
import socket

from .database import SessionLocal, init_db, Server

init_db()

app = FastAPI()
client = docker.from_env()

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/create-server", response_model=ServerResponse)
def create_server(db: Session = Depends(get_db)):
    game_port = get_random_port(25000, 25999)
    rcon_port = game_port + 1000
    rcon_password = ''.join(random.choices(string.ascii_letters + string.digits, k=36))
    unique_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    container: Container = client.containers.run(
        "itzg/minecraft-server",
        detach=True,
        ports={
            '25565/tcp': game_port,
            '25575/tcp': rcon_port
        },
        environment={
            "EULA": "TRUE",
            "RCON_PASSWORD": rcon_password,
            "ENABLE_RCON": "true"
        },
        remove=True
    )

    server_entry = Server(unique_id=unique_id, container_id=container.id, game_port=str(game_port), rcon_port=str(rcon_port), rcon_password=rcon_password)
    db.add(server_entry)
    db.commit()

    return {
        "unique_id": unique_id,
        "game_port": game_port,
        "rcon_port": rcon_port,
        "rcon_password": rcon_password
    }

@app.get("/server-status/{unique_id}")
def server_status(unique_id: str, db: Session = Depends(get_db)):
    server_entry = db.query(Server).filter(Server.unique_id == unique_id).first()
    if not server_entry:
        return {"status": "DELETED"}

    container_id = server_entry.container_id
    try:
        container = client.containers.get(container_id)
        if container.status == "running":
            # Check if the RCON port is open
            for port_mapping in container.attrs['NetworkSettings']['Ports']['25575/tcp']:
                if is_port_open("localhost", int(port_mapping['HostPort'])):
                    return {"status": "RUNNING"}
        elif container.status == "paused":
            return {"status": "PAUSED"}
        else:
            return {"status": "DELETED"}
    except docker.errors.NotFound:
        db.delete(server_entry)
        db.commit()
        return {"status": "DELETED"}

@app.get("/servers")
def get_servers(db: Session = Depends(get_db)):
    servers = db.query(Server).all()
    return [{"unique_id": server.unique_id} for server in servers]

@app.delete("/delete-server/{unique_id}")
def delete_server(unique_id: str, db: Session = Depends(get_db)):
    server_entry = db.query(Server).filter(Server.unique_id == unique_id).first()
    if not server_entry:
        raise HTTPException(status_code=404, detail="Server not found")

    container_id = server_entry.container_id
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
    except docker.errors.NotFound:
        pass

    db.delete(server_entry)
    db.commit()
    return {"status": "DELETED"}

@app.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
