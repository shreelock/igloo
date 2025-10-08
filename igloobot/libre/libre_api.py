from datetime import datetime
import hashlib

import requests
from typing import Dict

# Constants
BASE_URL = "https://api-us.libreview.io"  # Changed to US-specific endpoint
HEADERS = {
    'accept-encoding': 'gzip',
    'cache-control': 'no-cache',
    'connection': 'Keep-Alive',
    'content-type': 'application/json',
    'product': 'llu.android',
    'version': '4.16.0',
    'account-id': ''
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

    # Check if TOU step is required
    if 'data' in data and 'step' in data['data'] and data['data']['step']['type'] == 'tou':
        # Get the TOU token
        tou_token = data['data']['authTicket']['token']

        # Complete TOU using the correct endpoint from documentation
        tou_headers = {**HEADERS, 'Authorization': f'Bearer {tou_token}'}
        tou_response = requests.post(BASE_URL + "/auth/continue/tou", headers=tou_headers)

        if tou_response.status_code == 200:
            tou_data = tou_response.json()
            auth_ticket = tou_data['data']['authTicket']
            token = auth_ticket['token']
            expires = auth_ticket['expires']
        else:
            auth_ticket = data['data']['authTicket']
            token = auth_ticket['token']
            expires = auth_ticket['expires']
    else:
        # Normal login
        auth_ticket = data['data']['authTicket']
        token = auth_ticket['token']
        expires = auth_ticket['expires']
    
    account_id = data['data']['user']['id']
    return token, expires, account_id


# Function to get connections of patients
def get_patient_connections(token, account_id):
    endpoint = "/llu/connections"  # This is a placeholder, you'll need to replace with the actual endpoint
    headers = {**HEADERS, 'Authorization': f"Bearer {token}", 'account-id': hashlib.sha256(account_id.encode()).hexdigest()}

    response = requests.get(BASE_URL + endpoint, headers=headers)
    response.raise_for_status()
    return response.json()


# Function to retrieve CGM data for a specific patient
def get_cgm_data(token, patient_id, account_id):
    endpoint = f"/llu/connections/{patient_id}/graph"  # This is a placeholder, replace with the actual endpoint
    headers = {**HEADERS, 'Authorization': f"Bearer {token}", 'account-id': hashlib.sha256(account_id.encode()).hexdigest()}

    response = requests.get(BASE_URL + endpoint, headers=headers)
    response.raise_for_status()
    return response.json()


def extract_latest_reading(_response) -> Dict[datetime, int]:
    item = _response['data']['connection']['glucoseItem']
    ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
    val = item['ValueInMgPerDl']
    return {ts: val}


def extract_previous_readings(_response) -> Dict[datetime, int]:
    all_data = _response['data']['graphData']
    _graphdata_map = {}
    for item in all_data:
        ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
        val = item['ValueInMgPerDl']
        _graphdata_map[ts] = val
    return _graphdata_map
