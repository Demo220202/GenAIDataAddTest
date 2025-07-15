from time import sleep
from multipleTeamGenAccessToken import *
import requests
from rdsConnect import *
import argparse

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
        "host_name": "<string>",
        "account_id":[]
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



def add_scenario_category(name, access_token, url):
    url = f"https://{url}/apis/api/v1/advance-authoring/add-scenario-category/"
    headers = {
        # "Authorization": f"Bearer {auth_token}",
        # 'Content-Type': 'application/json',
        'Cookie': f'central_jwt_token={access_token}'
    }
    data = {"name": f"{name}"}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))
        datum = data.get("data")
        category_id = datum.get("id")
        return category_id

    return None


def add_scenario_template(category_id, access_token, url):
    url = f"https://{url}/apis/api/v1/advance-authoring/add-scenario-template/"
    headers = {
        # "Authorization": f"Bearer {access_token}"
        'Cookie': f'central_jwt_token={access_token}'
    }
    data = {
        "name": "Custom", # Can be replaced if provided
        "category_id": category_id,
        "text": "REPLACE ME" # Can be replaced if provided
    }

    response = requests.post(url, data=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))

    return response.json()


def add_scenario_template_p2(access_token, url):
    url = f"https://{url}/apis/api/v1/advance-authoring/add-persona-template/"
    headers = {
        # "Authorization": f"Bearer {access_token}"
        'Cookie': f'central_jwt_token={access_token}'
    }
    data = {
        "name": "Custom", # Can be replaced if provided
        "text": "REPLACE ME" # Can be replaced if provided
    }

    response = requests.post(url, data=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))

    return response.json()


def add_scoring_template(access_token, url):
    url = f"https://{url}/apis/api/v1/advance-authoring/add-scoring-template/"
    headers = {
        # "Authorization": f"Bearer {auth_token}",
        'Cookie': f'central_jwt_token={access_token}'
    }

    meta_json = {
        "tips": [
            "Tip Number 1",
            "Tip Number 2"
        ],
        "summary": "The summary in 400 words"
    }

    data = {
        "meta_json": meta_json,
        "inactive": 0,
        "type": "summary"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))

    return response.json()


def add_scoring_template_with_categories(access_token, url):
    url = f"https://{url}/apis/api/v1/advance-authoring/add-scoring-template/"
    headers = {
        # "Authorization": f"Bearer {auth_token}",
        'Cookie': f'central_jwt_token={access_token}'
    }

    meta_json = {
        "evaluation_categories": [
            {
                "children": [
                    {
                        "skill_id": "",
                        "skill_output": {},
                        "skill_output_type": "TEXT|NUMBER|BULLET_POINT|JSON|CATEGORICAL",
                        "explanation_reason": {
                            "explanation_phrases": [
                                {
                                    "phrase_reason": ""
                                }
                            ]
                        }
                    }
                ],
                "category_id": "",
                "category_output": {},
                "explanation_reason": {
                    "explanation_phrases": [
                        {
                            "phrase_reason": ""
                        }
                    ]
                },
                "category_output_type": "NUMBER|BULLET_POINT|JSON|CATEGORICAL"
            }
        ]
    }

    data = {
        "meta_json": meta_json,
        "inactive": 0,
        "type": "category"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))

    return response.json()


def main():

    parser = argparse.ArgumentParser(description='Arguments for access')

    parser.add_argument('--brand_name', required=True, help='Brand Name as per DB')
    parser.add_argument('--env', required=True, help='environment - prod, beta, qa, qa2 etc')
    parser.add_argument('--csbaemail', required=True, help='CS Brand Admin email')
    parser.add_argument('--account_list', nargs='+', required=True, help='Multiple Account/Teams or single Account/Team')
    parser.add_argument('--scenario', nargs='+', required=True, help='Scenario Category given by CS')

    args = parser.parse_args()

    env = args.env
    brand_name = args.brand_name # Based on DB Name
    email = args.csbaemail # This user must have access of the brand that we are using right now(team - mandatory)
    account_list = args.account_list # Team
    scenario_category = args.scenario # Sales, Marketing

    data_json = connect_to_rds_and_execute_email(env, brand_name, email)
    #
    # print(json.dumps(data_json, indent=2))
    #
    # user_id = data_json["user_id"]
    # password = data_json["password"]
    # brand_id = data_json["brand_id"]
    # account_id = data_json["account_id"]
    # role = data_json["role"]
    domain = data_json["url"]

    print("Domain: ", domain)

    teams_token = fetch_teams_access_token(env, brand_name, email, account_list, data_json)

    for data in teams_token:

        token = data[1]

        access_token = token

        print(f"{data[0]} : {token}")

        # print("Adding Scenario Categories...")
        # category_id = add_scenario_category(scenario_category, access_token, domain)
        #
        # print("Adding Scenario Templates...")
        # add_scenario_template(category_id, access_token, domain)
        #
        # print("Adding Persona Templates...")
        # add_scenario_template_p2(access_token, domain)
        #
        # print("Adding Scoring Templates...")
        # add_scoring_template(access_token, domain)
        #
        # print("Adding Scoring Templates P2...")
        # add_scoring_template_with_categories(access_token, domain)


    print("Done. Ab Ghar jaao!")

if __name__ == "__main__":
    main()
