from pydantic import BaseModel
from fastapi import FastAPI
from model_v2 import IntelTravelModel
import model_v2
import os
import uuid
from Models.model_config import ModelAdapter
from model_v3 import set_router_agent, trip_planning

response = ""

app = FastAPI()

prev_id, id = None, None

_client_name = ""
_model = ""
_api_key = ""
client: ModelAdapter

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

@app.post("/model")
def model_type(client_name: str, model: str, api_key: str = ""):
    global _client_name
    global _model
    global _api_key
    global client
    _client_name = client_name
    _model = model
    _api_key = api_key
    client = ModelAdapter(client_name=client_name, model=model, api_key=api_key)


# model_v2
# @app.post("/ask")
# def trip_request(request: str, conversation_id: str = id):
#     """
#     Handles trip planning requests.
    
#     Args:
#         request (str): Trip planning query string
        
#     Returns:
#         str: Trip planning response
#     """

#     global id
#     id = uuid.uuid1() if conversation_id is None else conversation_id
#     _conversation_id = conversation_id if conversation_id is not None else id
#     global _client_name, _model, _api_key
#     client = ModelAdapter(client_name=_client_name, model=_model, api_key=_api_key)
#     global response
#     model = IntelTravelModel()
#     response = model.trip_planning(_conversation_id, request, client)
#     return {
#         "Response": response,
#         "Conversation ID": _conversation_id
#     }

@app.post("/ask")
def trip_request(request: str, conversation_id: str = id):
    """
    Handles trip planning requests.
    
    Args:
        request (str): Trip planning query string
        
    Returns:
        str: Trip planning response
    """

    global client, id, prev_id

    id = str(uuid.uuid4()) if conversation_id is None else conversation_id
    _conversation_id = conversation_id if conversation_id is not None else id

    print(prev_id, ", ", id)
    if (prev_id != _conversation_id): 
        set_router_agent(_conversation_id, client)
        print("\n\nInitialised router agent\n\n")
        prev_id = _conversation_id

    response = trip_planning(request, client)
    return {
        "Response": response,
        "Conversation ID": _conversation_id
    }