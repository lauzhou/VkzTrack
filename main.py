import os
import random
from datetime import datetime
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import requests

DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    track_number = Column(String, unique=True, index=True)
    status = Column(String, default="Создана")


Base.metadata.create_all(bind=engine)


def generate_track_number():
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = str(random.randint(100, 999))
    return f"{timestamp}{random_part}"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/track", response_class=HTMLResponse)
def track(request: Request, track_number: str = Form(...), db: Session = Depends(get_db)):
    package = db.query(Package).filter(Package.track_number == track_number).first()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "package": package
    })


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.post("/admin/create")
def create_package(password: str = Form(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        return RedirectResponse("/admin", status_code=302)

    track_number = generate_track_number()
    package = Package(track_number=track_number)
    db.add(package)
    db.commit()

    return RedirectResponse("/admin", status_code=302)


@app.post("/admin/update")
def update_status(password: str = Form(...), track_number: str = Form(...), status: str = Form(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        return RedirectResponse("/admin", status_code=302)

    package = db.query(Package).filter(Package.track_number == track_number).first()
    if package:
        package.status = status
        db.commit()

    return RedirectResponse("/admin", status_code=302)
