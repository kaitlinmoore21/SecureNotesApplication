import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, Form, Depends, HTTPException, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from . import models, crud
from .database import SessionLocal, engine

SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")
if not SESSION_SECRET:
    raise ValueError("SESSION_SECRET_KEY is not set in .env!")

app = FastAPI()
templates = Jinja2Templates(directory="app/secure/templates")
models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=3600,
    https_only=True,
    same_site="Lax"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request) -> str:
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username

@app.exception_handler(401)
async def unauthenticated_handler(request: Request, exc: HTTPException):
    request.session.clear()
    return RedirectResponse("/secure/", status_code=302)

@app.get("/")
def redirect_to_secure_app():
    return RedirectResponse(url="/secure/", status_code=302)

@app.get("/secure/")
def login_page(request: Request):
    if request.session.get("username"):
        return RedirectResponse("/secure/notes", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "csrf_token": crud.generate_csrf_token()})

@app.post("/secure/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    crud.validate_csrf_token(csrf_token, request)
    user = crud.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials", "csrf_token": crud.generate_csrf_token()})
    request.session["username"] = user.username
    return RedirectResponse("/secure/notes", status_code=302)

@app.get("/secure/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/secure/", status_code=302)

@app.get("/secure/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "csrf_token": crud.generate_csrf_token()})

@app.post("/secure/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    crud.validate_csrf_token(csrf_token, request)
    if crud.get_user_by_username(db, username):
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already taken.", "csrf_token": crud.generate_csrf_token()})
    crud.create_user(db, username, password)
    return RedirectResponse("/secure/", status_code=302)

@app.get("/secure/notes")
def notes_page(request: Request, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    notes = crud.get_notes(db, username)
    return templates.TemplateResponse("notes.html", {"request": request, "username": username, "notes": notes, "csrf_token": crud.generate_csrf_token()})

@app.post("/secure/notes")
def add_note(request: Request, username: str = Depends(get_current_user), title: str = Form(...), content: str = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    crud.validate_csrf_token(csrf_token, request)
    crud.add_note(db, username, title, content)
    return RedirectResponse("/secure/notes", status_code=302)

@app.get("/secure/notes/{note_id}/edit")
def edit_note_page(request: Request, note_id: int = Path(...), username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    note = crud.get_note_by_id(db, note_id)
    if not note or note.username != username:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    return templates.TemplateResponse("edit_note.html", {"request": request, "note": note, "csrf_token": crud.generate_csrf_token()})

@app.post("/secure/notes/{note_id}/edit")
def edit_note(note_id: int = Path(...), username: str = Depends(get_current_user), title: str = Form(...), content: str = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    crud.validate_csrf_token(csrf_token, db)
    success = crud.update_note(db, note_id, username, title, content)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    return RedirectResponse("/secure/notes", status_code=302)

@app.get("/secure/notes/{note_id}/delete")
def delete_note_page(request: Request, note_id: int = Path(...), username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    note = crud.get_note_by_id(db, note_id)
    if not note or note.username != username:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    return templates.TemplateResponse("delete_note.html", {"request": request, "note": note, "csrf_token": crud.generate_csrf_token()})

@app.post("/secure/notes/{note_id}/delete")
def delete_note_confirm(note_id: int = Path(...), username: str = Depends(get_current_user), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    crud.validate_csrf_token(csrf_token, db)
    deleted = crud.delete_note(db, note_id, username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    return RedirectResponse("/secure/notes", status_code=302)

@app.get("/secure/search")
def search_notes(request: Request, q: str = None, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    if not q:
        return RedirectResponse("/secure/notes", status_code=302)
    notes = crud.search_notes(db, username, q)
    return templates.TemplateResponse("search.html", {"request": request, "username": username, "notes": notes, "query": q, "csrf_token": crud.generate_csrf_token()})