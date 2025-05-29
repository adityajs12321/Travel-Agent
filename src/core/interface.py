from pydantic import BaseModel
from fastapi import FastAPI
from model import IntelTravelModel

response = ""

app = FastAPI()

class TripRequest(BaseModel):
    origin: str = None
    destination: str = None
    departure_date: str = None
    adults: str = None
    maxPrice: str = None
    currencyCode: str = None

@app.get("/")
def read_root():
    return "LLM Backend"

@app.post("/set")
def set_access_token(client_id: str, client_secret:str, groq_api_key: str):
    return

@app.post("/ask")
def answer_question(question: TripRequest):
    global response
    model = IntelTravelModel()
    response = model.trip_planning(request=question)

@app.get("/results")
def return_answer():
    return response