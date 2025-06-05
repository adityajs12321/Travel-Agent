from pydantic import BaseModel
from fastapi import FastAPI
from model import IntelTravelModel
import model
import os

response = ""

app = FastAPI()

class TripPreferences(BaseModel):
    """Hotel preferences model containing distance from airport and ratings criteria."""
    distance_from_airport: str
    ratings: str

class TripRequest(BaseModel):
    """Trip request parameters including origin, destination and travel details."""
    origin: str
    destination: str
    departure_date: str
    adults: str
    maxPrice: str
    currencyCode: str
    hotelPrefs: TripPreferences

class APIKey(BaseModel):
    """API key configuration model."""
    client_id: str
    client_secret: str
    groq_api_key: str
    

@app.get("/")
def read_root():
    return "Intelligent Travel Agent"

@app.post("/set")
def set_api_keys(api_keys: APIKey):
    """
    Sets required API keys for the application.
    
    Args:
        api_keys (APIKey): Object containing client ID, client secret and Groq API key
    """
    model.CLIENT_ID = api_keys.client_id
    model.CLIENT_SECRET = api_keys.client_secret
    os.environ["GROQ_API_KEY"] = api_keys.groq_api_key
    model.set_access_token(model.CLIENT_ID, model.CLIENT_SECRET)

@app.post("/ask")
def trip_request(request: str):
    """
    Handles trip planning requests.
    
    Args:
        request (str): Trip planning query string
        
    Returns:
        str: Trip planning response
    """
    global response
    model = IntelTravelModel()
    response = model.trip_planning(request)
    return response