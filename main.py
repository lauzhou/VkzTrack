from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Package  # твоя модель

DATABASE_URL = "postgres://user:password@host:port/dbname"  # твой URL

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# ---------- HOME ----------
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------- ADMIN LOGIN PAGE ----------
@app.get("/admin")
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

# ---------- ADMIN AUTH ----------
@app.post("/admin")
async def admin_auth(request: Request, password: str = Form(...)):
    if password == "1234":  # твой пароль
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/admin", status_code=303)

# ---------- DASHBOARD ----------
@app.get("/dashboard")
async def dashboard(request: Request):
    packages = db.query(Package).all()

    statuses = [
        {"id": 1, "name": "Заказ принят", "icon": "✅", "description": "Мы получили оплату и уже взяли заказ в работу. Товар будет выкуплен в течение 1-3 дней."},
        {"id": 2, "name": "Выкуплено", "icon": "🛒", "description": "Товары выкуплены, ожидаем посылку на нашем складе от продавца."},
        {"id": 3, "name": "Склад США/Германия", "icon": "✈️", "description": "Посылка прибыла на склад. Рейс в Казахстан вылетает каждый четверг."},
        {"id": 4, "name": "Склад Казахстан", "icon": "📦", "description": "Посылка прибыла на наш склад в Казахстане и готовится к переупаковке."},
        {"id": 5, "name": "Передано СДЭК", "icon": "🚚", "description": "Посылка передана на отправку СДЭК."},
        {"id": 6, "name": "На хранении", "icon": "⏳", "description": "Посылка на складе в Казахстане и ожидает другие позиции для отправки."},
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "packages": packages, "statuses": statuses},
    )
