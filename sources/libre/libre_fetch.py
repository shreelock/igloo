import json
import requests

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


# Main Function
def fetch_cgm_data():
    email = ""  # Replace with your actual email
    password = ""  # Replace with your actual password

    token = login(email, password)
    patient_data = get_patient_connections(token)

    patient_id = patient_data['data'][0]["patientId"]
    cgm_data = get_cgm_data(token, patient_id)

    return cgm_data


if __name__ == "__main__":
    fetch_cgm_data()
