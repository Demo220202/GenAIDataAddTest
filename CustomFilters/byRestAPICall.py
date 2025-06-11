from azure.identity import DefaultAzureCredential
import requests

credential = DefaultAzureCredential()
token = credential.get_token("https://management.azure.com/.default").token

subscription_id = "de8e65ea-9d88-4eb8-acf1-22c75d8578f0"
resource_group = "ZenarateOP30GPTAdvancedStories"
account_name = "ZenarateOP30ProdGPTAdvancedStoriesEvaluationWUS3DZ"
rai_policy_name = "CustomFilterTest1"

url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{account_name}/raiPolicies/{rai_policy_name}?api-version=2024-10-01"

payload = {
    "properties": {
        "basePolicyName": "Microsoft.DefaultV2",
        "contentFilters": [
            {
                "blocking": False,
                "enabled": False,
                "name": "Hate",
                "severityThreshold": "High",
                "source": "Prompt",
            },
            {
                "blocking": True,
                "enabled": True,
                "name": "Hate",
                "severityThreshold": "Medium",
                "source": "Completion",
            },
            {
                "blocking": True,
                "enabled": True,
                "name": "Sexual",
                "severityThreshold": "High",
                "source": "Prompt",
            },
            {
                "blocking": True,
                "enabled": True,
                "name": "Sexual",
                "severityThreshold": "Medium",
                "source": "Completion",
            },
            {
                "blocking": True,
                "enabled": True,
                "name": "Selfharm",
                "severityThreshold": "High",
                "source": "Prompt",
            },
            {
                "blocking": True,
                "enabled": True,
                "name": "Selfharm",
                "severityThreshold": "Medium",
                "source": "Completion",
            },
            {
                "blocking": True,
                "enabled": True,
                "name": "Violence",
                "severityThreshold": "Medium",
                "source": "Prompt",
            },
            {
                "blocking": True,
                "enabled": True,
                "name": "Violence",
                "severityThreshold": "Medium",
                "source": "Completion",
            },
            {"blocking": True, "enabled": True, "name": "Jailbreak", "source": "Prompt"},
            {"blocking": True, "enabled": True, "name": "Protected Material Text", "source": "Completion"},
            {"blocking": True, "enabled": True, "name": "Protected Material Code", "source": "Completion"},
            {"blocking": True, "enabled": True, "name": "Profanity", "source": "Prompt"},
        ],
        "mode": "Default"
    }
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.put(url, json=payload, headers=headers)
print(response.status_code)
print(response.json())
