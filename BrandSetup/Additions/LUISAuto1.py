import requests
import time
import os
import subprocess
import json

from AzureTestingJSON import getResourceJSON

subscription_id = "f2f15065-2e82-4202-a2cc-af51e16f8772"

dataJson = getResourceJSON(subscription_id)

authoringResource = ""
AppResource = ""
ReportingAppResource = ""

for key, value in dataJson.items():
    if "Authoring" in key:
        authoringResource = key
    elif f"{dataJson["brand_name"]}App" in key:
        AppResource = key
    elif f"{dataJson["brand_name"]}ReportingApp" in key:
        ReportingAppResource = key

print(authoringResource)
print(AppResource)
print(ReportingAppResource)

# Environment setup
AUTHORING_KEY = dataJson[authoringResource][0]
ENDPOINT = dataJson[authoringResource][1]  # e.g. https://westus.api.cognitive.microsoft.com
HEADERS = {
    'Ocp-Apim-Subscription-Key': AUTHORING_KEY,
    'Content-Type': 'application/json'
}


def get_prediction_resource_arm_id(resource_group, resource_name):
    """Fetch the ARM ID of the prediction resource from Azure CLI."""
    cmd = [
        "az", "cognitiveservices", "account", "show",
        "--name", resource_name,
        "--resource-group", resource_group,
        "--query", "id",
        "--output", "tsv"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"❌ Failed to get ARM ID for prediction resource '{resource_name}':\n{result.stderr}")

    return result.stdout.strip()

def checkKey(region, app_id):
    url = f"https://{region}.api.cognitive.microsoft.com/luis/authoring/v3.0-preview/apps/{app_id}"
    headers = {
        "Ocp-Apim-Subscription-Key": AUTHORING_KEY
    }

    resp = requests.get(url, headers=headers)
    print(resp.status_code, resp.text)

def get_azure_rm_token():
    """Get Azure Resource Manager token for LUIS ARM operations."""
    result = subprocess.run(
        ['az', 'account', 'get-access-token', '--resource', 'https://management.core.windows.net/', '--query', 'accessToken', '--output', 'tsv'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Failed to get token: {result.stderr}")
    return result.stdout.strip()


def assign_prediction_resource_to_luis_app(app_id, region, resource_name, resource_group, subscription_id):
    token = get_azure_rm_token()

    # Build the full Azure resource ID
    prediction_resource_arm_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{resource_name}"

    # Use regional LUIS endpoint (not the authoring one)
    endpoint = f"https://{region}.api.cognitive.microsoft.com"

    url = f"{endpoint}/luis/api/v2.0/apps/{app_id}/azureaccounts"

    headers = {
        "Authorization": f"Bearer {token}",
        "Ocp-Apim-Subscription-Key": AUTHORING_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "azureSubscriptionId": subscription_id,
        "resourceGroup": resource_group,
        "accountName": resource_name
    }

    print("Request URL:", url)
    print("Request Body:", body)

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 201:
        print("[✅] Prediction resource assigned successfully.")
    else:
        print(f"[❌] Failed: {response.status_code} - {response.text}")




def import_app(json_file_path):
    url = f"{ENDPOINT}/luis/authoring/v3.0-preview/apps/import?appName=tempApp"
    with open(json_file_path, 'r') as f:
        body = f.read()
    response = requests.post(url, headers=HEADERS, data=body)
    response.raise_for_status()
    app_id = response.json()
    print(f"[✔] Imported app with ID: {app_id}")
    return app_id

def rename_app(app_id, new_name):
    url = f"{ENDPOINT}/luis/authoring/v3.0-preview/apps/{app_id}"
    body = {
        "name": new_name,
        "description": f"Renamed to {new_name}"
    }
    response = requests.put(url, headers=HEADERS, json=body)
    response.raise_for_status()
    print(f"[✔] Renamed app to: {new_name}")

def train_app(app_id, version_id='0.1'):
    url = f"{ENDPOINT}/luis/authoring/v3.0-preview/apps/{app_id}/versions/{version_id}/train"
    response = requests.post(url, headers=HEADERS)
    response.raise_for_status()
    print("[✔] Training started...")

    # Polling for training completion
    status_url = f"{ENDPOINT}/luis/authoring/v3.0-preview/apps/{app_id}/versions/{version_id}/train"
    while True:
        r = requests.get(status_url, headers=HEADERS)
        r.raise_for_status()
        statuses = r.json()
        if all(s['details']['status'] == 'Success' for s in statuses):
            print("[✔] Training completed")
            break
        print("⏳ Training in progress...")
        time.sleep(2)

def publish_app(app_id, version_id='0.1'):
    url = f"{ENDPOINT}/luis/authoring/v3.0-preview/apps/{app_id}/publish"
    body = {
        "versionId": version_id,
        "isStaging": False,  # False = production slot
        "region": "westus"  # Replace with your app's region
    }
    response = requests.post(url, headers=HEADERS, json=body)
    response.raise_for_status()
    endpoint_url = response.json().get('endpointUrl')
    print(f"[✔] App published to production at: {endpoint_url}")

# === Run the workflow ===

def add_train_n_publish(JSON_PATH, NEW_APP_NAME, REGION):

    json_path = JSON_PATH
    new_app_name = NEW_APP_NAME
    region = REGION

    print(new_app_name)

    app_id = import_app(json_path)

    checkKey(region, app_id)

    rename_app(app_id, new_app_name)

    for key, value in dataJson.items():

        print("Key: ", key)

        if AppResource in key:
            resource_name = AppResource
            resource_group = dataJson["resource_group"]

            assign_prediction_resource_to_luis_app(app_id, region, resource_name, resource_group, subscription_id)

        if ReportingAppResource in key:
            resource_name = ReportingAppResource
            resource_group = dataJson["resource_group"]

            assign_prediction_resource_to_luis_app(app_id, region, resource_name, resource_group, subscription_id)

    train_app(app_id)
    publish_app(app_id)

if __name__ == "__main__":

    print(dataJson)

    # Sample JSON

    json_path = "/Users/mac/Downloads/Sample template.json"
    new_app_name = f"{dataJson["brand_name"]} - Prod"
    region = "westus"

    add_train_n_publish(json_path, new_app_name, region)

    # COPY ME FOR BLANKS

    json_path = "/Users/mac/Downloads/Copy Me for Blanks.json"
    new_app_name = f"Copy Me for Blanks"
    region = "westus"

    add_train_n_publish(json_path, new_app_name, region)

