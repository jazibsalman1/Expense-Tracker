from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import hashlib  # for password hashing
import uvicorn

app = FastAPI()

# Static (CSS/JS/Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates (HTML files)
templates = Jinja2Templates(directory="templates")

# ✅ Database connection
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# ✅ Create table (if not exists)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password TEXT NOT NULL,
    date_of_birth TEXT NOT NULL
)
""")
conn.commit()

# ✅ Signup page (form)
@app.get("/", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# ✅ Login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
# ✅ Home page
@app.get("/index", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ✅ Handle signup form submission
@app.post("/signup")
async def signup(
    request: Request,
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    dateOfBirth: str = Form(...)
):
    # Checking password match
    if password != confirmPassword:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match!"
        })

    # Hash password before saving
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("""
            INSERT INTO users (first_name, last_name, email, phone, password, date_of_birth)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (firstName, lastName, email, phone, hashed_password, dateOfBirth))
        conn.commit()
    except sqlite3.IntegrityError:
        # Email already exists
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Email already exists!"
        })

    # Redirect to login page after success
    return RedirectResponse(url="/login", status_code=303)
