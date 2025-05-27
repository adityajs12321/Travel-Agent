from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import requests
import json
import asyncio
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent Travel Planning Agent", version="1.0.0")

# Pydantic Models
class TripPreferences(BaseModel):
    budget_range: Optional[str] = Field(None, description="Budget range: low, medium, high")
    travel_class: Optional[str] = Field("ECONOMY", description="Flight class preference")
    cuisine_preference: Optional[List[str]] = Field(None, description="Preferred cuisines")
    activities: Optional[List[str]] = Field(None, description="Preferred activities")
    accommodation_type: Optional[str] = Field(None, description="Hotel, Airbnb, etc.")

class TripRequest(BaseModel):
    origin: str = Field(..., description="Departure city/airport code")
    destination: str = Field(..., description="Destination city/airport code")
    departure_date: date = Field(..., description="Departure date")
    return_date: Optional[date] = Field(None, description="Return date for round trip")
    passengers: int = Field(1, description="Number of passengers")
    preferences: Optional[TripPreferences] = None

class AgentThought(BaseModel):
    step: int
    thought: str
    action: str
    observation: str
    reflection: str

class TravelPlan(BaseModel):
    flights: List[Dict[str, Any]]
    restaurants: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]
    agent_reasoning: List[AgentThought]
    confidence_score: float
    total_estimated_cost: Optional[float] = None

# Amadeus API Client
class AmadeusClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://test.api.amadeus.com"
        
    async def get_access_token(self):
        """Get OAuth2 access token from Amadeus"""
        url = f"{self.base_url}/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            return self.access_token
        else:
            raise HTTPException(status_code=500, detail="Failed to authenticate with Amadeus API")
    
    async def search_flights(self, origin: str, destination: str, departure_date: str, 
                           return_date: str = None, adults: int = 1, travel_class: str = "ECONOMY"):
        """Search for flights using Amadeus Flight Offers API"""
        if not self.access_token:
            await self.get_access_token()
            
        url = f"{self.base_url}/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "travelClass": travel_class,
            "max": 10
        }
        
        if return_date:
            params["returnDate"] = return_date
            
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Flight search failed: {response.text}")
            return {"data": []}
    
    async def get_airport_info(self, airport_code: str):
        """Get airport information"""
        if not self.access_token:
            await self.get_access_token()
            
        url = f"{self.base_url}/v1/reference-data/locations"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"keyword": airport_code, "subType": "AIRPORT"}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return {"data": []}

# Tools for the Agent
class TravelTools:
    def __init__(self, amadeus_client: AmadeusClient):
        self.amadeus = amadeus_client
        
    async def flight_search_tool(self, origin: str, destination: str, departure_date: str,
                                return_date: str = None, passengers: int = 1, travel_class: str = "ECONOMY"):
        """Tool 1: Flight Search"""
        try:
            result = await self.amadeus.search_flights(
                origin, destination, departure_date, return_date, passengers, travel_class
            )
            
            flights = []
            for offer in result.get("data", [])[:5]:  # Limit to top 5 offers
                flight_info = {
                    "id": offer.get("id"),
                    "price": offer.get("price", {}).get("total"),
                    "currency": offer.get("price", {}).get("currency"),
                    "itineraries": []
                }
                
                for itinerary in offer.get("itineraries", []):
                    itinerary_info = {
                        "duration": itinerary.get("duration"),
                        "segments": []
                    }
                    
                    for segment in itinerary.get("segments", []):
                        segment_info = {
                            "departure": {
                                "airport": segment.get("departure", {}).get("iataCode"),
                                "time": segment.get("departure", {}).get("at")
                            },
                            "arrival": {
                                "airport": segment.get("arrival", {}).get("iataCode"),
                                "time": segment.get("arrival", {}).get("at")
                            },
                            "airline": segment.get("carrierCode"),
                            "flight_number": segment.get("number")
                        }
                        itinerary_info["segments"].append(segment_info)
                    
                    flight_info["itineraries"].append(itinerary_info)
                flights.append(flight_info)
                
            return flights
        except Exception as e:
            logger.error(f"Flight search error: {e}")
            return []
    
    async def restaurant_search_tool(self, destination: str, cuisine_preferences: List[str] = None):
        """Tool 2: Restaurant/Food Recommendations (Mock implementation)"""
        # In a real implementation, you'd use Yelp API, Google Places API, or similar
        mock_restaurants = [
            {
                "name": f"Local Cuisine Restaurant in {destination}",
                "cuisine": cuisine_preferences[0] if cuisine_preferences else "Local",
                "rating": 4.5,
                "price_range": "$$",
                "address": f"123 Main St, {destination}",
                "description": "Authentic local dining experience"
            },
            {
                "name": f"International Bistro - {destination}",
                "cuisine": "International",
                "rating": 4.2,
                "price_range": "$$$",
                "address": f"456 Central Ave, {destination}",
                "description": "Fine dining with international flavors"
            },
            {
                "name": f"Street Food Market - {destination}",
                "cuisine": "Street Food",
                "rating": 4.0,
                "price_range": "$",
                "address": f"789 Market Square, {destination}",
                "description": "Local street food and quick bites"
            }
        ]
        return mock_restaurants
    
    async def activity_search_tool(self, destination: str, activity_preferences: List[str] = None):
        """Tool 3: Activity/Attraction Recommendations (Mock implementation)"""
        # In real implementation, use TripAdvisor API, GetYourGuide API, or similar
        mock_activities = [
            {
                "name": f"City Tour of {destination}",
                "type": "Sightseeing",
                "duration": "3 hours",
                "price": 25.0,
                "rating": 4.6,
                "description": f"Comprehensive guided tour of {destination}'s main attractions"
            },
            {
                "name": f"Local Museum - {destination}",
                "type": "Cultural",
                "duration": "2 hours",
                "price": 15.0,
                "rating": 4.3,
                "description": f"Learn about the history and culture of {destination}"
            },
            {
                "name": f"Adventure Activity in {destination}",
                "type": "Adventure" if activity_preferences and "adventure" in [p.lower() for p in activity_preferences] else "Recreation",
                "duration": "4 hours",
                "price": 50.0,
                "rating": 4.4,
                "description": f"Exciting outdoor activity in {destination}"
            }
        ]
        return mock_activities

# ReAct Agent Implementation
class ReActTravelAgent:
    def __init__(self, tools: TravelTools):
        self.tools = tools
        self.thoughts: List[AgentThought] = []
        self.step_count = 0
        
    def think(self, context: str) -> str:
        """Reasoning step of ReAct pattern"""
        thoughts = [
            f"I need to plan a trip based on: {context}",
            "First, I should search for flights to get the basic transportation sorted",
            "Then I'll look for restaurant recommendations based on user preferences",
            "Finally, I'll suggest activities that match the user's interests",
            "I should reflect on each step to ensure quality recommendations"
        ]
        return thoughts[min(self.step_count, len(thoughts) - 1)]
    
    def act(self, action_plan: str) -> str:
        """Action step of ReAct pattern"""
        actions = [
            "search_flights",
            "search_restaurants", 
            "search_activities",
            "compile_results"
        ]
        return actions[min(self.step_count, len(actions) - 1)]
    
    def reflect(self, observation: str) -> tuple[str, float]:
        """Reflection step to evaluate the quality of results"""
        if "flights" in observation.lower() and "price" in observation.lower():
            confidence = 0.8 if len(observation) > 100 else 0.6
            reflection = "Flight search completed successfully with pricing information"
        elif "restaurant" in observation.lower():
            confidence = 0.7
            reflection = "Restaurant recommendations provided with variety"
        elif "activity" in observation.lower():
            confidence = 0.7
            reflection = "Activity suggestions match user preferences"
        else:
            confidence = 0.5
            reflection = "Basic information provided, could be enhanced"
            
        return reflection, confidence
    
    async def plan_trip(self, request: TripRequest) -> TravelPlan:
        """Main trip planning method using ReAct pattern"""
        self.thoughts = []
        self.step_count = 0
        
        # Step 1: Search Flights
        thought = self.think(f"Trip from {request.origin} to {request.destination}")
        action = self.act("Planning flight search")
        
        flights = await self.tools.flight_search_tool(
            request.origin,
            request.destination,
            request.departure_date.isoformat(),
            request.return_date.isoformat() if request.return_date else None,
            request.passengers,
            request.preferences.travel_class if request.preferences else "ECONOMY"
        )
        
        observation = f"Found {len(flights)} flight options with prices ranging from various airlines"
        reflection, confidence1 = self.reflect(str(flights))
        
        self.thoughts.append(AgentThought(
            step=1,
            thought=thought,
            action=action,
            observation=observation,
            reflection=reflection
        ))
        self.step_count += 1
        
        # Step 2: Search Restaurants
        thought = self.think("Now searching for dining options")
        action = self.act("Planning restaurant search")
        
        cuisine_prefs = request.preferences.cuisine_preference if request.preferences else None
        restaurants = await self.tools.restaurant_search_tool(request.destination, cuisine_prefs)
        
        observation = f"Found {len(restaurants)} restaurant recommendations"
        reflection, confidence2 = self.reflect(str(restaurants))
        
        self.thoughts.append(AgentThought(
            step=2,
            thought=thought,
            action=action,
            observation=observation,
            reflection=reflection
        ))
        self.step_count += 1
        
        # Step 3: Search Activities
        thought = self.think("Searching for activities and attractions")
        action = self.act("Planning activity search")
        
        activity_prefs = request.preferences.activities if request.preferences else None
        activities = await self.tools.activity_search_tool(request.destination, activity_prefs)
        
        observation = f"Found {len(activities)} activity suggestions"
        reflection, confidence3 = self.reflect(str(activities))
        
        self.thoughts.append(AgentThought(
            step=3,
            thought=thought,
            action=action,
            observation=observation,
            reflection=reflection
        ))
        
        # Calculate overall confidence
        overall_confidence = (confidence1 + confidence2 + confidence3) / 3
        
        # Estimate total cost (basic calculation)
        total_cost = None
        if flights:
            flight_cost = sum([float(f.get("price", 0)) for f in flights[:1]])  # First flight
            restaurant_cost = len(restaurants) * 30  # Rough estimate
            activity_cost = sum([a.get("price", 0) for a in activities])
            total_cost = flight_cost + restaurant_cost + activity_cost
        
        return TravelPlan(
            flights=flights,
            restaurants=restaurants,
            activities=activities,
            agent_reasoning=self.thoughts,
            confidence_score=overall_confidence,
            total_estimated_cost=total_cost
        )

# Initialize components (You need to set your Amadeus API credentials)
AMADEUS_CLIENT_ID = "your_amadeus_client_id"  # Replace with your actual credentials
AMADEUS_CLIENT_SECRET = "your_amadeus_client_secret"  # Replace with your actual credentials

amadeus_client = AmadeusClient(AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET)
travel_tools = TravelTools(amadeus_client)
agent = ReActTravelAgent(travel_tools)

# FastAPI Endpoints
@app.get("/")
async def root():
    return {"message": "Intelligent Travel Planning Agent", "version": "1.0.0"}

@app.post("/plan-trip", response_model=TravelPlan)
async def plan_trip(request: TripRequest):
    """
    Main endpoint to plan a trip using the ReAct agent pattern
    """
    try:
        travel_plan = await agent.plan_trip(request)
        return travel_plan
    except Exception as e:
        logger.error(f"Trip planning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search-flights")
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
    travel_class: str = "ECONOMY"
):
    """
    Direct flight search endpoint
    """
    try:
        flights = await travel_tools.flight_search_tool(
            origin, destination, departure_date, return_date, passengers, travel_class
        )
        return {"flights": flights}
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search-restaurants")
async def search_restaurants(destination: str, cuisine: Optional[str] = None):
    """
    Restaurant search endpoint
    """
    try:
        cuisine_list = [cuisine] if cuisine else None
        restaurants = await travel_tools.restaurant_search_tool(destination, cuisine_list)
        return {"restaurants": restaurants}
    except Exception as e:
        logger.error(f"Restaurant search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search-activities")
async def search_activities(destination: str, activity_type: Optional[str] = None):
    """
    Activity search endpoint
    """
    try:
        activity_list = [activity_type] if activity_type else None
        activities = await travel_tools.activity_search_tool(destination, activity_list)
        return {"activities": activities}
    except Exception as e:
        logger.error(f"Activity search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent-status")
async def get_agent_status():
    """
    Get current agent status and reasoning history
    """
    return {
        "agent_type": "ReAct (Reasoning + Acting)",
        "tools_available": ["flight_search", "restaurant_search", "activity_search"],
        "patterns_implemented": ["ReAct", "Reflection"],
        "last_reasoning_steps": len(agent.thoughts),
        "amadeus_api_connected": amadeus_client.access_token is not None
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)