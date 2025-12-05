from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models

def insecure_search_notes(db: Session, query: str):
    if not query:
        return []
    return db.query(models.Note).filter(
        or_(
            models.Note.title.ilike(f"%{query}%"),
            models.Note.content.ilike(f"%{query}%")
        )
    ).all()


def insecure_get_user_by_username(db: Session, username: str):
   
    return db.query(models.User).filter(models.User.username == username).first()

def insecure_create_user(db: Session, username: str, password: str):

    user = models.User(username=username, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def insecure_authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(
        models.User.username == username, models.User.password == password
    ).first()
    return user

def insecure_get_notes(db: Session, username: str):

    return db.query(models.Note).filter(models.Note.username == username).all()

def insecure_add_note(db: Session, username: str, content: str, title: str = None):

    note = models.Note(username=username, content=content, title=title)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

def insecure_get_note_by_id(db: Session, note_id: int):
   
    return db.query(models.Note).filter(models.Note.id == note_id).first()

def insecure_update_note(db: Session, note_id: int, title: str, content: str) -> bool:

    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        return False
    note.title = title
    note.content = content
    db.commit()
    return True

def insecure_delete_note(db: Session, note_id: int) -> bool:

    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if note:
        db.delete(note)
        db.commit()
        return True
    return False