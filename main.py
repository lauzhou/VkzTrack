from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import random

# --- Database setup ---
DATABASE_URL = "postgresql://user:password@host:port/dbname"  # твой Postgres URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()
Base = declarative_base()

# --- Models ---
class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    track_number = Column(String, unique=True, index=True)
    deep_link = Column(String)
    current_status = Column(Integer, default=1)

Base.metadata.create_all(bind=engine)

# --- App setup ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- Generate 6-digit track ---
def generate_track():
    today = datetime.now()
    date_part = today.strftime("%m%d")  # MMDD
    rand_part = f"{random.randint(0,99):02d}"  # 2 случайные цифры
    return date_part + rand_part

# --- Routes ---

# Admin login page
@app.get("/admin")
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

# Dashboard
@app.post("/dashboard/create")
async def create_package(request: Request, title: str = Form(...)):
    track_number = generate_track()
    deep_link = f"https://t.me/vezemizkzbot?start={track_number}"

    new_package = Package(
        title=title,
        track_number=track_number,
        deep_link=deep_link,
        current_status=1
    )
    db.add(new_package)
    db.commit()
    db.refresh(new_package)

    return RedirectResponse("/dashboard", status_code=303)

@app.get("/dashboard")
async def dashboard(request: Request):
    packages = db.query(Package).all()
    # статусы для админки
    statuses = [
        {"id":1,"name":"Заказ принят","icon":"✅"},
        {"id":2,"name":"Выкуплено","icon":"🛒"},
        {"id":3,"name":"Получили на складе США/Германия","icon":"✈️"},
        {"id":4,"name":"Получили на складе Казахстан","icon":"📦"},
        {"id":5,"name":"Передано на отправку СДЭК","icon":"🚚"},
        {"id":6,"name":"На хранении","icon":"⏳"}
    ]
    return templates.TemplateResponse("dashboard.html", {"request": request, "packages": packages, "statuses": statuses})

@app.post("/dashboard/update")
async def update_status(track_number: str = Form(...), status_id: int = Form(...)):
    package = db.query(Package).filter(Package.track_number == track_number).first()
    if package:
        package.current_status = status_id
        db.commit()
    return RedirectResponse("/dashboard", status_code=303)
