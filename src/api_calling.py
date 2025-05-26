import requests

# Step 1: Auth
auth_resp = requests.post(
    'https://test.api.amadeus.com/v1/security/oauth2/token',
    data={
        'grant_type': 'client_credentials',
        'client_id': 'oejdFFuyHrUNG2JghIAUBtaUphuLicZi',
        'client_secret': 'w2L5zvfXJeZ3fabV',
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

def return_results(params):
    resp = requests.get(
        'https://test.api.amadeus.com/v2/shopping/flight-offers',
        headers=headers,
        params=params
    )
    valid_offers = []
    desired_destination = "LAX"
    
    for offer in resp.json()['data']:
        segments = offer['itineraries'][0]['segments']
        final_arrival = segments[-1]['arrival']['iataCode']
        if final_arrival == desired_destination:
            valid_offers.append(offer)
    return valid_offers
