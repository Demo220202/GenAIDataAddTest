import json
# from textwrap import indent
import base64
from UserPackageAuto import *
from rdsConnect import *
import requests

def btoa_encode(user_id):
    # The string you want to encode (similar to btoa() in JavaScript)
    original_string = str(user_id)

    # Encode the string to bytes using utf-8 encoding, then Base64-encode it
    encoded_bytes = base64.b64encode(original_string.encode('utf-8'))

    # Convert the bytes back to a string
    encoded_string = encoded_bytes.decode('utf-8')

    print(encoded_string)

    return encoded_string


def toggleUsersPage(data):

    data["brand_settings_data"]["migration_settings"]["enable_manage_users"] = False if data["brand_settings_data"]["migration_settings"]["enable_manage_users"] == True else True
    data["brand_settings_data"]["migration_settings"]["enable_manage_users_url"] = "/platform-app/#/dashboard/manage/users" if data["brand_settings_data"]["migration_settings"]["enable_manage_users_url"] == "" else data["brand_settings_data"]["migration_settings"]["enable_manage_users_url"]
    # if data["brand_settings_data"]["migration_settings"]["enable_manage_users_url"] == "" else ""
    # data["brand_settings_data"]["brand_scoring_methodology"] = "stars"

    return data

def get_brand_settings(access_token, domain, brand_id, account_id, user_id, role):

    url = f"https://{domain}/platform/auth/brand_settings_id/{brand_id}"
    request_id = btoa_encode(user_id)
    headers = {
        # 'Authorization': f'Bearer {access_token}',
        'Cookie': f'account_id={account_id};_loggedIn_id={user_id};_zenarate_id={user_id};_role_id={role};Z-Request-ID={request_id};central_jwt_token={access_token};'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        data = response_json.get('data')
        return data

    return None


def change_brand_settings(access_token, domain, brand_id, account_id, user_id, role, updated_data):

    url = f"https://{domain}/platform/auth/update_brand_settings"

    request_id = btoa_encode(user_id)

    payload = json.dumps(updated_data)
    headers = {
        # 'Authorization': f'Bearer {access_token}',
        'Cookie': f'account_id={account_id};_loggedIn_id={user_id};_zenarate_id={user_id};_role_id={role};Z-Request-ID={request_id};central_jwt_token={access_token};',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)
    print(json.dumps(response.json(), indent=2))
    if response.status_code == 200:
        return True
    return False



# All these variables will be set by calling other modules

env = "prod"
brand_name = "T-Mobile" # As per table

data_json = connect_to_rds_and_execute(env, brand_name)
domain = data_json["url"]
brand_id = data_json["brand_id"]
password = data_json["password"]
account_id = data_json["account_id"]
role = data_json["role"]
user_id = data_json["user_id"]
access_token = fetch_access_token(domain, user_id, password)

# End of variables

print("Getting brand settings...")
data = get_brand_settings(access_token, domain, brand_id, account_id, user_id, role)
print(json.dumps(data, indent=4))

print("Toggled Data: ")
data = toggleUsersPage(data)
print(json.dumps(data, indent=4))

flag = input("Press 'yes' to proceed or any other key to exit: ")

if flag == "yes":
    print("Brand Settings Change Status: ")
    print(change_brand_settings(access_token, domain, brand_id, account_id, user_id, role, data))