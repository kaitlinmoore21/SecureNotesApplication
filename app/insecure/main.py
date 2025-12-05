from fastapi import FastAPI, Request, Form, Depends, HTTPException, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from . import models, crud
from .database import SessionLocal, engine


app = FastAPI()

templates = Jinja2Templates(directory="app/insecure/templates")

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/insecure/")
def login_page(request: Request):
    """Serve the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/insecure/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Insecure login (No session/cookie/jwt). If successful, redirects with username in URL."""
    user = crud.insecure_authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    return RedirectResponse(f"/insecure/notes?username={user.username}", status_code=302)

@app.get("/insecure/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/insecure/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Checks if the user exists before attempting to create the record, 
    preventing the 500 IntegrityError.
    """
    if crud.insecure_get_user_by_username(db, username):
  
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already taken."})
    
    crud.insecure_create_user(db, username, password)
    return RedirectResponse("/insecure/", status_code=302)




@app.get("/insecure/notes")
def notes_page(request: Request, username: str, db: Session = Depends(get_db)):

    notes = crud.insecure_get_notes(db, username)
    return templates.TemplateResponse("notes.html", {"request": request, "username": username, "notes": notes})

@app.post("/insecure/notes")
def add_note(request: Request, username: str = Form(...), title: str = Form(None), content: str = Form(...), db: Session = Depends(get_db)):
 
    crud.insecure_add_note(db, username, title=title, content=content)
    return RedirectResponse(f"/insecure/notes?username={username}", status_code=302)

@app.get("/insecure/notes/{note_id}/edit")
def edit_note_page(request: Request, note_id: int = Path(...), db: Session = Depends(get_db)):

    note = crud.insecure_get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return templates.TemplateResponse("edit_note.html", {"request": request, "note": note, "username": request.query_params.get('username')})

@app.post("/insecure/notes/{note_id}/edit")
def edit_note(request: Request, note_id: int = Path(...), username: str = Form(...), title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):

    success = crud.insecure_update_note(db, note_id, title, content)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return RedirectResponse(f"/insecure/notes?username={username}", status_code=302)

@app.get("/insecure/notes/{note_id}/delete")
def delete_note_page(request: Request, note_id: int = Path(...), db: Session = Depends(get_db)):
   
    note = crud.insecure_get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return templates.TemplateResponse("delete_note.html", {"request": request, "note": note, "username": request.query_params.get('username')})

@app.post("/insecure/notes/{note_id}/delete")
@app.post("/insecure/notes/{note_id}/delete/")
def delete_note_confirm(note_id: int = Path(...), username: str = Form(...), db: Session = Depends(get_db)):
    deleted = crud.insecure_delete_note(db, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return RedirectResponse(f"/insecure/notes?username={username}", status_code=302)

@app.get("/insecure/search")
def search(q: str = "", db: Session = Depends(get_db), request: Request = None):
   
    results = crud.insecure_search_notes(db, q)
    return templates.TemplateResponse("search_results.html", {"request": request, "results": results, "query": q})
