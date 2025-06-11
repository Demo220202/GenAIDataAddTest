import requests
from azure.identity import DefaultAzureCredential

# Input your Azure resource details
subscription_id = "e40b7804-e85a-4fa4-8b99-179386006afd"
resource_group = "SummitGPTAdvancedStories"
account_name = "SummitProdGPTAdvancedStoriesEvaluationWestUS3"
api_version = "2024-10-01"

# Construct the URL for the API request
url = (
    f"https://management.azure.com/subscriptions/{subscription_id}/"
    f"resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/"
    f"accounts/{account_name}/raiPolicies?api-version={api_version}"
)

# Use Azure Identity to get an access token
credential = DefaultAzureCredential()
access_token = credential.get_token("https://management.azure.com/.default")

# Set headers
headers = {
    "Authorization": f"Bearer {access_token.token}",
    "Content-Type": "application/json"
}

# Make the GET request
response = requests.get(url, headers=headers)

# Handle the response
if response.status_code == 200:
    policies = response.json()
    print("✅ RAI Policies retrieved successfully:")
    for policy in policies.get("value", []):
        print(f"- Policy Name: {policy.get('name')}")
        print(f"  ID: {policy.get('id')}")
        print(f"  Type: {policy.get('type')}")
        print(f"  Properties: {policy.get('properties')}")
        print()
else:
    print(f"❌ Failed to retrieve RAI policies. Status code: {response.status_code}")
    print(response.text)
