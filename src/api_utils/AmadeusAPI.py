import requests
from fastapi import HTTPException
import os

class AmadeusClient:
    """Client for Amadeus Self Service API"""
    def __init__(self, client_id: str, client_secret: str, access_token: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.base_url = "https://test.api.amadeus.com"

    def get_access_token(self):
        """Get Access token from Amadeus"""

        print("getting access token...")

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
            os.environ['AMADEUS_ACCESS_TOKEN'] = self.access_token
        else:
            print(response)
            print("Failed to authenticate")
            raise HTTPException(status_code=500, detail="Failed to authenticate with Amadeus API")
        
    def search_flights(self,
                       origin: str,
                       destination: str,
                       departureDate: str,
                       adults: str,
                       maxPrice: str,
                       currencyCode: str = "USD"):
        """Search for flights using the Flight Offers API"""

        print("searching for flights...")

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
        elif response.status_code == 401:
            print("access token expired")
            self.get_access_token()
            new_response = self.search_flights(
                origin,
                destination,
                departureDate,
                adults,
                maxPrice,
                currencyCode
            )
            return new_response
        else:
            print(response)
            raise HTTPException(status_code=500, detail="Flight search failed")
    
    def search_hotels(self,
                      cityCode: str,
                      radius: str,
                      ratings: str):
        """Search for hotels using the Hotel Search API"""

        print("searching for hotels")

        url = f"{self.base_url}/v1/reference-data/locations/hotels/by-city"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        params = {
            'cityCode': cityCode,
            'radius': radius,
            'ratings': ratings,
        }

        response = requests.get(url, headers=headers, params=params)
        if (response.status_code == 200):
            return response.json()
        else:
            print(response)
            raise HTTPException(status_code=500, detail="Hotel search failed")

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