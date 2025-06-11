import requests
from azure.identity import DefaultAzureCredential

# Input parameters
subscription_id = "de8e65ea-9d88-4eb8-acf1-22c75d8578f0"
resource_group = "ZenarateOP30GPTAdvancedStories"
resource_name = "ZenarateOP30ProdGPTAdvancedStoriesEvaluationWUS3DZ"
# location = "eastus"  # or your region

# Example payload for a Guardrails filter
# You should capture this from your browser's developer tools after manually creating the filter once
filter_payload = {
    "filters": [
        {
            "deployment": "gpt-4o-1",
            "enabled": True,
            "categories": {
                "hate": {
                    "severity": "high"
                },
                "self_harm": {
                    "severity": "medium"
                },
                "sexual": {
                    "severity": "high"
                },
                "violence": {
                    "severity": "medium"
                }
            }
        }
    ]
}

# API URL (You must verify the exact endpoint and API version used from dev tools)
api_version = "2024-10-01"
url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{resource_name}/updateFilterConfig?api-version={api_version}"

# Get Azure access token
credential = DefaultAzureCredential()
token = credential.get_token("https://management.azure.com/.default")
headers = {
    "Authorization": f"Bearer {token.token}",
    "Content-Type": "application/json"
}

# Make PATCH or POST request (depending on actual API behavior)
response = requests.post(url, headers=headers, json=filter_payload)

# Output result
if response.status_code in [200, 201, 202]:
    print("✅ Filter configuration updated successfully.")
else:
    print(f"❌ Failed to update filter. Status Code: {response.status_code}")
    print(response.text)
