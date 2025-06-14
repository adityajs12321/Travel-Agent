from pydantic import BaseModel
from fastapi import FastAPI
from model_v2 import IntelTravelModel
import model_v2
import os
import uuid

response = ""

app = FastAPI()

id = None
default_val = 10

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
    model_v2.CLIENT_ID = api_keys.client_id
    model_v2.CLIENT_SECRET = api_keys.client_secret
    os.environ["GROQ_API_KEY"] = api_keys.groq_api_key
    model_v2.set_access_token(model_v2.CLIENT_ID, model_v2.CLIENT_SECRET)

@app.post("/ask")
def trip_request(request: str, conversation_id: str = id):
    """
    Handles trip planning requests.
    
    Args:
        request (str): Trip planning query string
        
    Returns:
        str: Trip planning response
    """

    global id
    id = uuid.uuid1() if conversation_id is None else conversation_id
    _conversation_id = conversation_id if conversation_id is not None else id
    global response
    model = IntelTravelModel()
    response = model.trip_planning(_conversation_id, request)
    return {
        "Response": response,
        "Conversation ID": _conversation_id
    }