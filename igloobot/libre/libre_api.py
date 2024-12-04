from datetime import datetime

import requests
from typing import Dict

# Constants
BASE_URL = "https://api.libreview.io"  # or "https://api-eu.libreview.io" for Europe
HEADERS = {
    'accept-encoding': 'gzip',
    'cache-control': 'no-cache',
    'connection': 'Keep-Alive',
    'content-type': 'application/json',
    'product': 'llu.android',
    'version': '4.7'
}


# Function to log in and retrieve JWT token
def login(email, password):
    endpoint = "/llu/auth/login"
    payload = {
        "email": email,
        "password": password
    }

    response = requests.post(BASE_URL + endpoint, headers=HEADERS, json=payload)
    response.raise_for_status()
    data = response.json()
    # print(data)
    token = data.get('data', []).get("authTicket", []).get("token", [])  # Access the "token" key from the response JSON
    # print(token)
    return token


# Function to get connections of patients
def get_patient_connections(token):
    endpoint = "/llu/connections"  # This is a placeholder, you'll need to replace with the actual endpoint
    headers = {**HEADERS, 'Authorization': f"Bearer {token}"}

    response = requests.get(BASE_URL + endpoint, headers=headers)
    response.raise_for_status()
    return response.json()


# Function to retrieve CGM data for a specific patient
def get_cgm_data(token, patient_id):
    endpoint = f"/llu/connections/{patient_id}/graph"  # This is a placeholder, replace with the actual endpoint
    headers = {**HEADERS, 'Authorization': f"Bearer {token}"}

    response = requests.get(BASE_URL + endpoint, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_latest_reading(_response) -> Dict[datetime, int]:
    item = _response['data']['connection']['glucoseItem']
    ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
    val = item['ValueInMgPerDl']
    return {ts: val}

def extract_graph_data(_response) -> Dict[datetime, int]:
    all_data = _response['data']['graphData']
    _graphdata_map = {}
    for item in all_data:
        ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
        val = item['ValueInMgPerDl']
        _graphdata_map[ts] = val
    return _graphdata_map
