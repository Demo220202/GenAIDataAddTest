from time import sleep
import base64
import requests
from ProdDBAccountIdFetch import *
from rdsConnect import *

def btoa_encode(user_id):
    # The string you want to encode (similar to btoa() in JavaScript)
    original_string = str(user_id)

    # Encode the string to bytes using utf-8 encoding, then Base64-encode it
    encoded_bytes = base64.b64encode(original_string.encode('utf-8'))

    # Convert the bytes back to a string
    encoded_string = encoded_bytes.decode('utf-8')

    print(encoded_string)

    return encoded_string

def fetch_access_token(domain, user_id, password):

    url = f"https://{domain}/platform/auth/login"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "user_id": f"{user_id}",
        "session_id": "<string>",
        "user_switch_role_id": "0",
        "password": f"{password}",
        "host_name": "<string>"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:

        data = response.json()

        # Fetch the access_token
        datum = data.get("data")
        access_token = datum.get("access_token")

        if access_token:
            print("Access Token:", access_token)
            return access_token
        else:
            print("Access token not found in the response.")
            return None
    else:
        print("Failed to fetch data. Status code:", response.status_code)
        print("Error message:", response.text)
        return None


def fetch_access_token_team_specific(domain, original_token, access_id):

    url = f"https://{domain}/platform/auth/switched"

    # request_id = btoa_encode(user_id)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        # 'Cookie': f'_loggedIn_id={user_id};_zenarate_id={user_id};_role_id={role};Z-Request-ID={request_id};central_jwt_token={original_token};'
    }

    payload = {
        "access_id": access_id,
        "original_token": f"{original_token}"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:

        data = response.json()

        # Fetch the access_token
        datum = data.get("data")
        access_token = datum.get("access_token")

        if access_token:
            print("Access Token:", access_token)
            return access_token
        else:
            print("Access token not found in the response.")
            return None

    else:
        print("Failed to fetch data. Status code:", response.status_code)
        print("Error message:", response.text)
        return None


def fetch_teams_access_token(env, brand_name, user_email, account_list, data_json):

    # env = "prod"
    # brand_name = "Chase"
    # user_email = "amitj@zenarate.com"
    # account_list = ["Branch - Banker", "Branch - Manager"]

    account_ids_details = fetchAccountAccessIds(env, brand_name, user_email, account_list)

    print(account_ids_details)

    # data_json = connect_to_rds_and_execute_email(env, brand_name, user_email)

    domain = data_json["url"]
    brand_id = data_json["brand_id"]
    password = data_json["password"]
    account_id = data_json["account_id"]
    role = data_json["role"]
    user_id = data_json["user_id"]
    password = data_json["password"]

    original_token = fetch_access_token(domain, user_id, password)

    teams_token = []

    for key, val in account_ids_details.items():
        print(f"For team: {val}: ")
        team_token = fetch_access_token_team_specific(domain, original_token, val["access_id"])
        teams_token.append([val["name"], team_token])

    return teams_token

# def main():
#
#     env = "prod"
#     brand_name = "Chase"
#     user_email = "amitj@zenarate.com"
#     account_list = ["Branch - Banker", "Branch - Manager"]
#
#     account_ids_details = fetchAccountAccessIds(brand_name, user_email, account_list)
#
#     print(account_ids_details)
#
#     data_json = connect_to_rds_and_execute_email(env, brand_name, user_email)
#
#     domain = data_json["url"]
#     brand_id = data_json["brand_id"]
#     password = data_json["password"]
#     account_id = data_json["account_id"]
#     role = data_json["role"]
#     user_id = data_json["user_id"]
#     password = data_json["password"]
#
#     original_token = fetch_access_token(domain, user_id, password)
#
#     teams_token = []
#
#     for key, val in account_ids_details.items():
#         print(f"For team: {val}: ")
#         team_token = fetch_access_token_team_specific(domain, original_token, val["access_id"], user_id, role)
#         teams_token.append([val["name"], team_token])
#
#     print(teams_token)
#
#
# if __name__ == "__main__":
#     main()