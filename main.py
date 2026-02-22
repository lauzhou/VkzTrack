import os
import random
from datetime import datetime
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from starlette.middleware.sessions import SessionMiddleware

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


STATUSES = [
    {
        "id": 1,
        "name": "Заказ принят",
        "description": "Мы получили оплату и уже взяли заказ в работу. Выкуп товара будет произведён в течение 1–3 рабочих дней."
    },
    {
        "id": 2,
        "name": "Выкуплено",
        "description": "Товары успешно выкуплены. Сейчас ожидаем доставку посылки на наш склад от продавца."
    },
    {
        "id": 3,
        "name": "Получили на складе в США / Германии",
        "description": "Посылка прибыла на наш зарубежный склад. Рейсы отправляются каждый четверг. Ориентировочное время доставки в Казахстан — 10–15 дней."
    },
    {
        "id": 4,
        "name": "Получили на складе в Казахстане",
        "description": "Посылка прибыла на наш склад в Казахстане и проходит переупаковку для отправки в Россию."
    },
    {
        "id": 5,
        "name": "Посылка передана на отправку СДЭК",
        "description": "Посылка передана в службу доставки СДЭК и скоро начнёт движение к вам."
    },
    {
        "id": 6,
        "name": "На хранении",
        "description": "Посылка находится на складе в Казахстане и ожидает другие позиции для совместной отправки."
    }
]


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True)
    track_number = Column(String, unique=True)
    title = Column(String)
    current_status = Column(Integer, default=1)


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


def get_status_by_id(status_id):
    for s in STATUSES:
        if s["id"] == status_id:
            return s
    return None


# -------- CLIENT --------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/track", response_class=HTMLResponse)
def track(request: Request, track_number: str = Form(...), db: Session = Depends(get_db)):
    package = db.query(Package).filter(Package.track_number == track_number).first()

    status = None
    if package:
        status = get_status_by_id(package.current_status)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "package": package,
        "status": status,
        "statuses": STATUSES
    })


# -------- ADMIN LOGIN --------

@app.get("/admin", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin")
def admin_auth(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/admin", status_code=302)


# -------- DASHBOARD --------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("admin"):
        return RedirectResponse("/admin", status_code=302)

    packages = db.query(Package).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "packages": packages,
        "statuses": STATUSES
    })


@app.post("/dashboard/create")
def create_package(request: Request, title: str = Form(...), db: Session = Depends(get_db)):
    if not request.session.get("admin"):
        return RedirectResponse("/admin", status_code=302)

    track_number = generate_track_number()

    package = Package(
        track_number=track_number,
        title=title,
        current_status=1
    )

    db.add(package)
    db.commit()

    return RedirectResponse("/dashboard", status_code=302)


@app.post("/dashboard/update")
def update_status(request: Request, track_number: str = Form(...), status_id: int = Form(...), db: Session = Depends(get_db)):
    if not request.session.get("admin"):
        return RedirectResponse("/admin", status_code=302)

    package = db.query(Package).filter(Package.track_number == track_number).first()

    if package:
        package.current_status = status_id
        db.commit()

    return RedirectResponse("/dashboard", status_code=302)
