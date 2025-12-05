import secrets
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_csrf_tokens = {}

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_user(db: Session, username: str, password: str):
    hashed = hash_password(password)
    user = models.User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def get_notes(db: Session, username: str):
    return db.query(models.Note).filter(models.Note.username == username).all()

def add_note(db: Session, username: str, title: str, content: str):
    note = models.Note(username=username, title=title, content=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

def get_note_by_id(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()

def update_note(db: Session, note_id: int, username: str, title: str, content: str):
    note = get_note_by_id(db, note_id)
    if note and note.username == username:
        note.title = title
        note.content = content
        db.commit()
        return True
    return False

def delete_note(db: Session, note_id: int, username: str):
    note = get_note_by_id(db, note_id)
    if note and note.username == username:
        db.delete(note)
        db.commit()
        return True
    return False

def search_notes(db: Session, username: str, q: str):
    return db.query(models.Note).filter(models.Note.username == username, models.Note.title.ilike(f"%{q}%")).all()


def generate_csrf_token():
    token = secrets.token_hex(16)
    _csrf_tokens[token] = True
    return token

def validate_csrf_token(token: str, request_or_db):
    if not token or token not in _csrf_tokens:
        raise ValueError("CSRF token missing or invalid")
    _csrf_tokens.pop(token, None)