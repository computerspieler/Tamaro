from openai import OpenAI
import os
from datetime import datetime
import json
import logging

from fastapi import FastAPI, Request, Response, Body, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlalchemy
from sqlalchemy import Column, String, create_engine, Integer
from sqlalchemy.orm import sessionmaker, Session

from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
class Settings(BaseModel):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    KEY_LENGTH: int = 5
    KEY_CHARACTERS: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

settings = Settings()
client = OpenAI(
  api_key = settings.OPENAI_API_KEY,
)
templates = Jinja2Templates(directory="templates")

questions = json.loads(open("./questions.json", "r").read())
questions_grouped_by_type = {
    "employe": [],
    "manager": []
}
for question in questions:
    questions_grouped_by_type["employe"].append(question["employe"])
    questions_grouped_by_type["manager"].append(question["manager"])

# === DB related stuff ===
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = sqlalchemy.orm.declarative_base()

class ID(Base):
    __tablename__ = "ids"
    id = Column(String(length=5), primary_key=True, index=True)
    role = Column(String)

class Pair(Base):
    __tablename__ = "pairs"
    id1 = Column(String(length=5), primary_key=True)
    id2 = Column(String(length=5), primary_key=True)

class Answers(Base):
    __tablename__ = "answers"
    user_id = Column(String(length=5), primary_key=True, index=True)
    question_id = Column(Integer, primary_key=True, index=True)
    response = Column(Integer)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === The app ===
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/get-id", response_class=JSONResponse)
async def get_id(role: str, db: Session = Depends(get_db)):
    now = datetime.now()
    init_val = int(now.microsecond + (now.second + (now.minute + 60 * now.hour) * 60)*1e6)
    is_in_db = True
    l = len(settings.KEY_CHARACTERS)
    while is_in_db:
        id = ""
        val = init_val
        for _ in range(settings.KEY_LENGTH):
            id += settings.KEY_CHARACTERS[val % l]
            val //= l
        is_in_db = db.query(ID).filter(ID.id == id).count() > 0
        print(is_in_db)
        init_val += 1
    db_elt = ID(id = id, role = role)
    db.add(db_elt)
    db.commit()
    db.refresh(db_elt)
    return db_elt

@app.get("/get-questions", response_class=JSONResponse)
async def get_questions(role: str):
    return questions_grouped_by_type[role]

class AssociationModel(BaseModel):
    me: str
    them: str

@app.post("/associate")
async def question_html(response: Response,
    me: str = Body(..., embed=True),
    them: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    response.status_code = status.HTTP_404_NOT_FOUND
    if len(me) != settings.KEY_LENGTH:
        return None
    if len(them) != settings.KEY_LENGTH:
        return None
    if db.query(ID).filter(ID.id == me).count() == 0:
        return None
    if db.query(ID).filter(ID.id == them).count() == 0:
        return None
    id1 = min(me, them)
    id2 = max(me, them)
    response.status_code = status.HTTP_409_CONFLICT
    if db.query(Pair).filter(Pair.id1 == id1).count() > 0:
        return None
    if db.query(Pair).filter(Pair.id2 == id2).count() > 0:
        return None
    
    db.add(Pair(id1 = id1, id2 = id2))
    db.commit()
    response.status_code = status.HTTP_200_OK
    return None

@app.post("/has-associated")
async def has_associated(response: Response,
    id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    response.status_code = status.HTTP_200_OK
    return db.query(Pair).filter((Pair.id1 == id) | (Pair.id2 == id)).count() > 0

@app.post("/answers")
async def question_html(response: Response,
    answers: list[int] = Body(..., embed=True),
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    try:
        response.status_code = status.HTTP_200_OK
        for i, answer in enumerate(answers):
            db_elt = Answers(user_id=user_id, question_id=i, response=answer)
            db.add(db_elt)
        db.commit()
    except Exception as e:
        logging.error(e)
        response.status_code = status.HTTP_400_BAD_REQUEST
        db.rollback()
    finally:
        return None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("roles.html", {"request": request})

@app.get("/question", response_class=HTMLResponse)
async def question_html(request: Request, id: str, role: str):
    return templates.TemplateResponse("questions.html", {"request": request})

@app.get("/response", response_class=HTMLResponse)
async def index(request: Request, id: str):
    return templates.TemplateResponse("responses.html", {"request": request})