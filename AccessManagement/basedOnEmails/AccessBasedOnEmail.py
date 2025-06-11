# from time import sleep
import base64
import requests
from rdsConnect import *
from GetUsersOnNewLabels import *
import argparse
# from toggleUsersPage import data_json


def get_domain_on_env(env):

    if env == "prod":
        domain = "internal.zenarate.com"
    elif env == "beta":
        domain = "beta-internal.zenarate.com"
    elif env == "qa":
        domain = "qa-internal.zenarate.com"
    elif env == "qa2":
        domain = "qa2-internal.zenarate.com"
    else:
        domain = None

    return domain

def btoa_encode(user_id):
    # The string you want to encode (similar to btoa() in JavaScript)
    original_string = str(user_id)

    # Encode the string to bytes using utf-8 encoding, then Base64-encode it
    encoded_bytes = base64.b64encode(original_string.encode('utf-8'))

    # Convert the bytes back to a string
    encoded_string = encoded_bytes.decode('utf-8')

    # print(encoded_string)

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
            # print("Access Token:", access_token)
            return access_token
        else:
            print("Access token not found in the response.")
            return None
    else:
        print("Failed to fetch data. Status code:", response.status_code)
        print("Error message:", response.text)
        return None

def cs_brand_admin_access_all(domain, access_token, account_id, user_id, role, cs_brand_admin_user_id, brand_id_list):

    url = f"https://{domain}/zen-api/idp/v2/users/cs-brand-admin-access"

    request_id = btoa_encode(user_id)

    headers = {
        "Cookie": f'account_id={account_id};_zenarate_id={user_id};_role_id={role};Z-Request-ID={request_id};central_jwt_token={access_token};',
        "Content-Type": "application/json"
    }

    data = {
        "user_id": cs_brand_admin_user_id,
        "brand_ids": brand_id_list,
        "grant": 1
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))
    else:
        print("Failed to fetch data. Status code:", response.status_code)
        print(json.dumps(response.json(), indent=2))

    return response.json()

def cs_brand_admin_access(domain, access_token, account_id, user_id, role, cs_brand_admin_user_id, brand_id):

    url = f"https://{domain}/zen-api/idp/v2/users/cs-brand-admin-access"

    request_id = btoa_encode(user_id)

    headers = {
        "Cookie": f'account_id={account_id};_zenarate_id={user_id};_role_id={role};Z-Request-ID={request_id};central_jwt_token={access_token};',
        "Content-Type": "application/json"
    }

    data = {
        "user_id": cs_brand_admin_user_id,
        "brand_ids": [brand_id],
        "grant": 1
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))
    else:
        print("Failed to fetch data. Status code:", response.status_code)
        print(json.dumps(response.json(), indent=2))

    return response.json()

# cs_brand_admin_access("internal.zenarate.com", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyNzI2NTMsImFjY291bnRfaWQiOjUzNSwiYnJhbmRfaWQiOjI1LCJ1c2VyX3JvbGUiOiJTdXBlckFkbWluIiwiYWNjZXNzX3R5cGUiOiJsb2dpbl9zc28iLCJ0ZWFtIjoiMXwyIiwicm9sZV9pZCI6NCwidmVyc2lvbiI6InYyIiwiY2xhaW1zIjpbeyJyb2xlX2lkIjo0LCJ0ZWFtIjpbXX1dLCJzd2l0Y2hlZCI6e30sImltcGVyc29uYXRlIjp7fSwib3JpZ2luYWxfdXNlciI6eyJ1c2VyX2lkIjoyNzI2NTMsImFjY291bnRfaWQiOjUzNSwiYnJhbmRfaWQiOjI1LCJ1c2VyX3JvbGUiOiJTdXBlckFkbWluIiwiYWNjZXNzX3R5cGUiOiJsb2dpbl9zc28iLCJ0ZWFtIjoiMXwyIiwicm9sZV9pZCI6NCwiY2xhaW1zIjpbeyJyb2xlX2lkIjo0LCJ0ZWFtIjpbXX1dLCJtZXRhX2RhdGEiOnsiZGVjb2RlX21ldGhvZCI6IiJ9fSwiaWF0IjoxNzQ4NTM3OTc4LCJleHAiOjE3NDg1NDUxNzh9.gB3VsPAN9OnEDFRHwRULGTMUQa6Uewd8Gys-oa8TwZg", 535, 272653, "SuperAdmin", 231683, 286)

def main():

    parser = argparse.ArgumentParser(description='Arguments for access')

    parser.add_argument('--brand', required=True, help='Brand Name as per DB')
    parser.add_argument('--env', required=True, help='environment - prod, beta, qa, qa2 etc')
    parser.add_argument('--email', required=True, help='Super Admin email')
    parser.add_argument('--emails', nargs='+', required=True, help='Multiple Emails or single Email')

    args = parser.parse_args()

    # brand = args.brand

    env = args.env
    brand_name = args.brand  # DB strict
    email = args.email
    domain = get_domain_on_env(env)


    access_user_email_list = args.emails
    print(access_user_email_list)

    primary_user_json = connect_to_rds_and_execute_email(env, brand_name, email)
    output_json = {}

    if brand_name.lower() == "all" or brand_name == "*":

        primary_user_json = connect_to_rds_and_execute_email(env, "Zenarate Test", email)

        domain = get_domain_on_env(env)

        brand_id = primary_user_json["brand_id"]
        password = primary_user_json["password"]
        account_id = primary_user_json["account_id"]
        role = primary_user_json["role"]
        user_id = primary_user_json["user_id"]

        brand_ids_list = fetch_all_active_brands(env)

        access_token = fetch_access_token(domain, user_id, password)

        print("User details : ", user_id, role)

        for access_user_email in access_user_email_list:

            access_brand_id, access_user_details = fetch_user_based_on_email(env, access_user_email, "Zenarate Test")

            access_user_name = access_user_details["user_name"]
            access_user_id = access_user_details["user_id"]

            print("Giving Access to: ", access_user_name, "with id: ", access_user_id)
            status = cs_brand_admin_access_all(domain, access_token, account_id, user_id, role, access_user_id, brand_ids_list)
            output_json[access_user_id] = [access_user_id, access_user_name, status["status_code"], status["message"]]

        print(json.dumps(output_json, indent=4))

        with open("output_json.json", "w") as f:
            json.dump(output_json, f, indent=4)

        return 0


    data_json = primary_user_json


    brand_id = data_json["brand_id"]
    password = data_json["password"]
    account_id = data_json["account_id"]
    role = data_json["role"]
    user_id = data_json["user_id"]

    access_token = fetch_access_token(domain, user_id, password)

    print("User details : ", user_id, role)

    for access_user_email in access_user_email_list:

        access_brand_id, access_user_details = fetch_user_based_on_email(env, access_user_email, brand_name)

        access_user_name = access_user_details["user_name"]
        access_user_id = access_user_details["user_id"]

        print("Giving Access to: ", access_user_name, "with id: ", access_user_id)
        status = cs_brand_admin_access(domain, access_token, account_id, user_id, role, access_user_id, access_brand_id)
        output_json[access_user_id] = [access_user_id, access_user_name, status["status_code"], status["message"]]

    print(json.dumps(output_json, indent=4))

    with open("output_json.json", "w") as f:
        json.dump(output_json, f, indent=4)

if __name__ == "__main__":
    main()