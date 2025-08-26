from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
import hashlib
import uvicorn

app = FastAPI()

# ✅ Add session middleware (secret key is important!)
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

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

# ✅ Signup page
@app.get("/", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# ✅ Login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ✅ Home page (protected)
@app.get("/index", response_class=HTMLResponse)
async def home_page(request: Request):
    # Check if user is logged in
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("index.html", {"request": request})

# ✅ Signup form
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
    if password != confirmPassword:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match!"
        })

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("""
            INSERT INTO users (first_name, last_name, email, phone, password, date_of_birth)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (firstName, lastName, email, phone, hashed_password, dateOfBirth))
        conn.commit()
    except sqlite3.IntegrityError:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Email already exists!"
        })

    return RedirectResponse(url="/login", status_code=303)

# ✅ Login form
@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("""
        SELECT * FROM users WHERE email = ? AND password = ?
    """, (email, hashed_password))
    user = cursor.fetchone()

    if user:
        # Save user session
        request.session["user"] = {"id": user[0], "email": user[3]}
        return RedirectResponse(url="/index", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid email or password!"
    })

# ✅ Logout
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  # remove session
    return RedirectResponse(url="/login", status_code=303)

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
