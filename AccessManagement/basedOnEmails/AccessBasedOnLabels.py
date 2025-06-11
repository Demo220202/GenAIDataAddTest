# from time import sleep
import base64
import requests
from rdsConnect import *
from GetUsersOnNewLabels import *
# from toggleUsersPage import data_json
import argparse

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


def main():

    parser = argparse.ArgumentParser(description='Arguments for access')

    parser.add_argument('--brand', required=True, help='Brand Name as per DB')
    parser.add_argument('--env', required=True, help='environment - prod, beta, qa, qa2 etc')
    parser.add_argument('--email', required=True, help='Super Admin email')
    parser.add_argument('--label', required=True, help='Label tier 1')
    parser.add_argument('--label_value', required=True, help='Label tier 2')

    args = parser.parse_args()

    brand = args.brand

    env = args.env
    brand_name = args.brand # DB strict
    email = args.email
    domain = get_domain_on_env(env)

    label = args.label
    label_value = args.label_value

    labels_list = [[label, label_value]]

    data_json = {}

    output_json = {}

    if len(labels_list) > 0:
        data_json = connect_to_rds_and_execute_email(env, brand_name, email)

    if brand_name == "all" or brand_name == "*":

        brand_id = data_json["brand_id"]
        password = data_json["password"]
        account_id = data_json["account_id"]
        role = data_json["role"]
        user_id = data_json["user_id"]

        access_token = fetch_access_token(domain, user_id, password)

        brand_ids_list = fetch_all_active_brands(env)

        print("User details : ", user_id, role)

        brand_id, cs_brand_admin_user_ids = fetchUserIds(env, "Zenarate Test", email, labels_list)

        for cs_brand_admin_user_id in cs_brand_admin_user_ids:
            print("Giving Access to: ", cs_brand_admin_user_id[1], "with id: ", cs_brand_admin_user_id[0], "under", cs_brand_admin_user_id[3], "associated with the team", cs_brand_admin_user_id[2])
            status = cs_brand_admin_access_all(domain, access_token, account_id, user_id, role, cs_brand_admin_user_id[0], brand_ids_list)
            output_json[cs_brand_admin_user_id[0]] = [cs_brand_admin_user_id[0], cs_brand_admin_user_id[1], status["status_code"], status["message"]]

        print(json.dumps(output_json, indent=4))

        with open("output_json.json", "w") as f:
            json.dump(output_json, f, indent=4)

        return 0

    if data_json:

        brand_id = data_json["brand_id"]
        password = data_json["password"]
        account_id = data_json["account_id"]
        role = data_json["role"]
        user_id = data_json["user_id"]

        access_token = fetch_access_token(domain, user_id, password)

        print("User detials : ", user_id, role)

        brand_id, cs_brand_admin_user_ids = fetchUserIds(env, brand_name, email, labels_list)


        for cs_brand_admin_user_id in cs_brand_admin_user_ids:
            print("Giving Access to: ", cs_brand_admin_user_id[1], "with id: ", cs_brand_admin_user_id[0], "under", cs_brand_admin_user_id[3], "associated with the team", cs_brand_admin_user_id[2])
            status = cs_brand_admin_access(domain, access_token, account_id, user_id, role, cs_brand_admin_user_id[0], brand_id)
            output_json[cs_brand_admin_user_id[0]] = [cs_brand_admin_user_id[0], cs_brand_admin_user_id[1], status["status_code"], status["message"]]

            print("Access Status: ", cs_brand_admin_user_id[0], cs_brand_admin_user_id[1], status["status_code"], status["message"])

        with open("output_json.json", "w") as f:
            json.dump(output_json, f, indent=4)

if __name__ == "__main__":
    main()