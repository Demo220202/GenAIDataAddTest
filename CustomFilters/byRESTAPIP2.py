import requests
from azure.identity import DefaultAzureCredential

# === INPUTS ===
subscription_id = "de8e65ea-9d88-4eb8-acf1-22c75d8578f0"
resource_group = "ZenarateOP30GPTAdvancedStories"
account_name = "ZenarateOP30ProdGPTAdvancedStoriesEvaluationWUS3DZ"
rai_policy_name = "CustomFilterTest1"  # Name of the policy you want to create
api_version = "2024-10-01"

# === PAYLOAD ===
payload = {
    "properties": {
        "basePolicyName": "Microsoft.DefaultV2",
        "mode": "Asynchronous_filter",
        "contentFilters": [
            {
                "name": "Hate",
                "blocking": False,
                "enabled": False,
                "severityThreshold": "High",
                "source": "Prompt"
            },
            {
                "name": "Hate",
                "blocking": True,
                "enabled": True,
                "severityThreshold": "Medium",
                "source": "Completion"
            },
            {
                "name": "Sexual",
                "blocking": True,
                "enabled": True,
                "severityThreshold": "High",
                "source": "Prompt"
            },
            {
                "name": "Sexual",
                "blocking": True,
                "enabled": True,
                "severityThreshold": "Medium",
                "source": "Completion"
            },
            {
                "name": "Selfharm",
                "blocking": True,
                "enabled": True,
                "severityThreshold": "High",
                "source": "Prompt"
            },
            {
                "name": "Selfharm",
                "blocking": True,
                "enabled": True,
                "severityThreshold": "Medium",
                "source": "Completion"
            },
            {
                "name": "Violence",
                "blocking": True,
                "enabled": True,
                "severityThreshold": "Medium",
                "source": "Prompt"
            },
            {
                "name": "Violence",
                "blocking": True,
                "enabled": True,
                "severityThreshold": "Medium",
                "source": "Completion"
            },
            {
                "name": "Jailbreak",
                "blocking": True,
                "source": "Prompt",
                "enabled": True
            },
            {
                "name": "Protected Material Text",
                "blocking": True,
                "source": "Completion",
                "enabled": True
            },
            {
                "name": "Protected Material Code",
                "blocking": True,
                "source": "Completion",
                "enabled": True
            },
            {
                "name": "Profanity",
                "blocking": True,
                "source": "Prompt",
                "enabled": True
            }
        ]
    }
}

# === AUTHENTICATION ===
credential = DefaultAzureCredential()
access_token = credential.get_token("https://management.azure.com/.default")

# === REQUEST SETUP ===
url = (
    f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
    f"/providers/Microsoft.CognitiveServices/accounts/{account_name}/raiPolicies/{rai_policy_name}"
    f"?api-version={api_version}"
)

headers = {
    "Authorization": f"Bearer {access_token.token}",
    "Content-Type": "application/json"
}

# === SEND REQUEST ===
response = requests.put(url, headers=headers, json=payload)

# === RESULT ===
if response.status_code in [200, 201]:
    print("✅ RAI policy created/updated successfully.")
    print("Policy ID:", response.json().get("id"))
else:
    print(f"❌ Failed to create/update RAI policy. Status code: {response.status_code}")
    print(response.text)
