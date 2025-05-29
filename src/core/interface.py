from pydantic import BaseModel
from fastapi import FastAPI
from model import IntelTravelModel
import model
import os

response = ""

app = FastAPI()

class TripRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    adults: str
    maxPrice: str
    currencyCode: str

class APIKey(BaseModel):
    client_id: str
    client_secret: str
    groq_api_key: str
    

@app.get("/")
def read_root():
    return "Intelligent Travel Agent"

@app.post("/set")
def set_api_keys(api_keys: APIKey):
    model.CLIENT_ID = api_keys.client_id
    model.CLIENT_SECRET = api_keys.client_secret
    os.environ["GROQ_API_KEY"] = api_keys.groq_api_key
    model.set_access_token(model.CLIENT_ID, model.CLIENT_SECRET)

@app.post("/ask")
def trip_request(request: TripRequest):
    global response
    model = IntelTravelModel()
    response = model.trip_planning(request)

@app.get("/results")
def return_answer():
    return response