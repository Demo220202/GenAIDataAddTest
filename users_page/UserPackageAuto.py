# import json
from time import sleep

import requests
from rdsConnect import *

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


def fetch_access_token_team_specific():

    return None


def check_job_running(domain, access_token, account_id, user_id, role):

    url = f"https://{domain}/platform/auth/backtrack_batch_validation"

    headers = {
        # 'Authorization': f'Bearer {access_token}',
        'Cookie': f'account_id={account_id};_loggedIn_id={user_id};_zenarate_id={user_id};_role_id={role};central_jwt_token={access_token}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))

        if data.get("message") == "No Job in progress" and data.get("data").get("job_status") == "NO_JOB_IN_PROGRESS":
            return False
        return True

    else:
        print("Failed to fetch data. Status code:", response.status_code)
        print("Error message:", response.text)


def create_or_modify_userpackage(domain, access_token, brand_id, account_id, user_id, role):

    url = f"https://{domain}/platform/auth/user_package_update_all_brands?brand_id={brand_id}"

    headers = {
        # 'Authorization': f'Bearer {access_token}',
        'Cookie': f'account_id={account_id};_loggedIn_id={user_id};_zenarate_id={user_id};_role_id={role};central_jwt_token={access_token}'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print("Failed to fetch data. Status code:", response.status_code)
        print("Error message:", response.text)




def main():

    variables = {}

    env = "prod"
    brand_name = "T-Mobile" # As per DB Table

    data_json = connect_to_rds_and_execute(env, brand_name)

    print(json.dumps(data_json, indent=2))

    user_id = data_json["user_id"]
    password = data_json["password"]
    brand_id = data_json["brand_id"]
    account_id = data_json["account_id"]
    role = data_json["role"]
    domain = data_json["url"]

    print("Genarating Access Token...")
    access_token = fetch_access_token(domain, user_id, password)


    job_is_running = True

    if access_token is not None:
        job_is_running = check_job_running(domain, access_token, account_id, user_id, role)
        print(job_is_running)


    if not job_is_running:
        create_or_modify_userpackage(domain, access_token, brand_id, account_id, user_id, role)

    job_is_running = check_job_running(domain, access_token, account_id, user_id, role)

    while job_is_running:
        job_is_running = check_job_running(domain, access_token, account_id, user_id, role)
        sleep(10)

    variables["access_token"] = access_token
    variables["brand_id"] = brand_id
    variables["account_id"] = account_id
    variables["user_id"] = user_id
    variables["role"] = role
    variables["domain"] = domain

    print("Done.")

    return variables

if __name__ == "__main__":
    main()
