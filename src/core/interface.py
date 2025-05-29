from pydantic import BaseModel
from fastapi import FastAPI
from model import IntelTravelModel

response = ""

app = FastAPI()

class TripRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    adults: str
    maxPrice: str
    currencyCode: str

@app.get("/")
def read_root():
    return "Intelligent Travel Agent"

@app.post("/ask")
def trip_request(request: TripRequest):
    global response
    model = IntelTravelModel()
    response = model.trip_planning(request)

@app.get("/results")
def return_answer():
    return response