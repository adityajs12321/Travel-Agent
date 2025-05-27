import requests
import os

# Step 1: Auth
auth_resp = requests.post(
    'https://test.api.amadeus.com/v1/security/oauth2/token',
    data={
        'grant_type': 'client_credentials',
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
    }
)
access_token = auth_resp.json()['access_token']

# Step 2: Call Flight Destinations API
headers = {'Authorization': f'Bearer {access_token}'}

params = {
    'originLocationCode': 'JFK',
    'destinationLocationCode': 'LAX',
    'departureDate': '2025-06-15',
    'adults': '1',
    'maxPrice': '200',
    'currencyCode': 'USD'
}

def return_results(originLocationCode, destinationLocationCode, departureDate, adults, maxPrice, currencyCode):
    params = {
        'originLocationCode': originLocationCode,
        'destinationLocationCode': destinationLocationCode,
        'departureDate': departureDate,
        'adults': adults,
        'maxPrice': maxPrice,
        'currencyCode': currencyCode
    }
    resp = requests.get(
        'https://test.api.amadeus.com/v2/shopping/flight-offers',
        headers=headers,
        params=params
    )
    valid_offers = []
    desired_destination = destinationLocationCode
    print(resp.json())
    
    for offer in resp.json()['data']:
        segments = offer['itineraries'][0]['segments']
        final_arrival = segments[-1]['arrival']['iataCode']
        if final_arrival == desired_destination:
            valid_offers.append(offer)
    return valid_offers

# print(return_results(params['originLocationCode'], params['destinationLocationCode'], params['departureDate'], params['adults'], params['maxPrice'], params['currencyCode']))