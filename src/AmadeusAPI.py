import requests
from fastapi import FastAPI, HTTPException
import os

class AmadeusClient:
    def __init__(self, client_id: str, client_secret: str, access_token: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.base_url = "https://test.api.amadeus.com"

    def get_access_token(self):
        """Get Access token from Amadeus"""

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
            with open(os.path.expanduser("~/.zshrc"), "a") as outfile:
                outfile.write(f"export AMADEUS_ACCESS_TOKEN={self.access_token}")
                outfile.close()
            return self.access_token
        else:
            raise HTTPException(status_code=500, detail="Failed to authenticate with Amadeus API")
        
    def search_flights(self,
                       origin: str,
                       destination: str,
                       departureDate: str,
                       adults: str,
                       maxPrice: str,
                       currencyCode: str = "USD"):
        """Search for flights using the Flight Offers API"""

        if not self.access_token:
            print("no access token yet")
            self.get_access_token()
        
        url = f"{self.base_url}/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departureDate,
            "adults": adults,
            "maxPrice": maxPrice,
            "currencyCode": currencyCode
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=500, detail="Flight search failed")
    
    def get_airport_info(self, airport_code: str):
        """Get Airport Codes"""

        if not self.access_token:
            print("no access token yet")
            self.get_access_token()

        url = f"{self.base_url}/v1/reference-data/locations"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"keyword": airport_code, "subType": "AIRPORT"}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=500, detail="Airport Codes could not be retrieved")

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
client = None

try:
    access_token = os.environ["AMADEUS_ACCESS_TOKEN"]
    client = AmadeusClient(CLIENT_ID, CLIENT_SECRET, access_token)
except Exception as e:
    client = AmadeusClient(CLIENT_ID, CLIENT_SECRET)

# print(client.get_airport_info("LAX"))
print(client.search_flights("JFK", "LAX", "2025-06-04", 1, 200))