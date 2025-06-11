import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.resource import ResourceManagementClient
import requests

# Input: List of subscription IDs
subscription_ids = [
    # "ce169ec1-0847-4c2a-8eff-1ab8c0fb07a4",  # Upgrade
    # "ab47af59-59e2-4770-9838-cfef2fc04c91",  # GoDaddy
    # "8e3e497f-f597-4f40-9647-5be32abf3a9b",  # Royal Caribbean
    # "34173732-7fc6-4753-bc14-9f460f3b2547",  # Prudential Pre Hire
    # "883dc4d2-4279-41f9-8c15-44697e51106a",  # customerservice
    # "8425a14f-a905-4b14-9f4b-d5bd483bb2f6",  # First Command
    # "6e51efa7-5734-4819-8c81-4e3a15de9b18",  # Freedom Mortgage
    # "b4086b21-702d-46c2-99ce-1919dd8d9621",  # Michael Wynn
    # "985cd5b4-5257-416e-8b06-1f2222098ef4",  # Nelnet
    # "b2377dda-35ed-4de8-a866-b84cec8ca3ac",  # First Horizon
    # "ffb0386e-7376-438f-b1c6-c46c6fef8351",  # HSBC
    # "955b8f94-e354-46ec-8462-3272bdcea84f",  # PNC Bank
    # "8fff8c3d-7d90-4c96-aa4a-f35da4d3c02f",  # Compare Club
    # "a6b0edf8-b7e1-43cf-b960-4543de90dbc3",  # BOH
    # "f5eb2504-71c9-4d5d-b758-ecfc952962b5",  # Chase
    # "de446dc1-57b9-4a69-bc89-f81d8a83911d",  # FNBO
    # "e7f02a8a-6b01-451b-9485-40002a958c1e",  # Startek
    # "2450acfc-e2f5-441c-b276-9d4aa1f5d1a3",  # United Health Care
    # "bb58c82d-beab-41b5-b643-12aed8f265f0",  # Optum
    # "fee8cb00-2601-4963-a4f9-793ed834e3ab",  # Wolters Kluwer
    # # "3ee4b2f8-a172-414c-881a-c22f47c44ee2",  # Product Enablement
    # "4cbfbd7d-c882-4e04-948b-1bcd351f5a1b",  # Telelink Services
    # "e2114b13-61f2-40e8-987e-b33a9f730060",  # Conduent
    # "ddb8bdaa-c0ee-4dde-a68e-133010343759",  # Sitel
    # "6c9607d5-e5f8-452d-a8d0-497173f28908",  # McKinsey PODS
    # "034e9e07-1e61-456b-87df-26f6a20bcf72",  # Amica
    # "8fd505e4-965a-4299-bd33-3659bf1a618b",  # UMB
    # "302aa751-3cfb-4ea7-8d1b-1e683c19d94e",  # Biogen
    # "ed67f45d-539f-4956-8c6a-fa44feeadc64",  # ICM Credit
    # "52f4a8af-e9f9-492b-bbf7-30691a39f874",  # Comcast
    # "463af01e-2a45-4691-8de0-cb18ab26c778",  # CardWorks
    # "bca07b81-ae78-493e-8642-28159cd67aed",  # Assurant
    # "ce6c1ff9-1df1-463b-a16b-8f87fd11906f",  # Webster Bank
    # "2e3bcbc9-6b83-4e3a-8acf-5d740da7ce30",  # Ibex Global Solutions
    # "0e717037-6c1a-46a8-8728-e34a44793e7d",  # Travelers
    # "aeb00795-1157-4ec0-a15d-ecdfcc65999f",  # SoFi
    # "415b1248-6de7-41b2-8db6-73a6f4b591e9",  # Hyatt
    # "1292eed9-6fea-4bea-9e63-e43bb538a384",  # Tripadvisor
    # "c1a802be-1db4-437c-9d79-1c9e6ce22623",  # T-Mobile
    # "bc813bf2-2182-4f45-9dca-0b5561aea213",  # Coca-Cola
    # "9bff740b-fa8b-45c3-86b9-d248e4ab882b",  # Cherry Technologies
    # "1ec618cf-1bcf-4c70-a126-efccdd3f9c83",  # Wells
    # "5b47237d-34d2-4a98-a0bc-d682523f9108",  # Sun Life
    # "7dd56d72-8a2c-46a5-9354-7b2088341985",  # Visa
    # "d7b44af3-b43a-4313-97d0-7fca36eec114",  # BPO Centers
    # "f420eb36-2789-4c58-87b1-cb8de90b984d",  # ResultsCX
    # "06116825-eb43-4ddb-9ba4-432bae95a273",  # Capgemini
    # "57fa1f0c-831f-444f-a8d0-c5e2cf27ca30",  # Auto & General
    # "28d10935-6dd6-4412-a568-5e820dc327b3",  # Wyndham
    # "e40b7804-e85a-4fa4-8b99-179386006afd",  # Summit
    # "d451bf47-eee4-4572-a9f1-1e3aaafd6a70",  # H&R Block
    # "078b0937-5c7c-4cc6-bb6c-40005166ad34",  # Zopa Bank
    # "99b2e5ca-4611-438f-a55a-e0137eac1c04",  # Verizon
    # "a40ee0de-eae2-4ccc-9fcc-c171d3be6710",  # Northwestern Mutual
    # "8287c444-62f0-4d3c-89a2-de09e0e49f36",  # Prime Marketing
    # "d008090b-7af1-4062-8604-3a7f56207955",  # Zenarate Test
    # "c72eefc8-0ce7-476a-9d23-47902f19b673",  # Migration Test
    "de8e65ea-9d88-4eb8-acf1-22c75d8578f0"
]

# Authenticate using Azure Default Credential
credential = DefaultAzureCredential()

# Helper to find resource group containing 'GPTAdvancedStories'
def get_resource_group(subscription_id):
    resource_client = ResourceManagementClient(credential, subscription_id)
    for rg in resource_client.resource_groups.list():
        print(rg.name)
        if "GPTAdvancedStories" in rg.name:
            return rg.name
    return None

# Helper to get deployment list via REST API
def get_deployments(subscription_id, resource_group, account_name):
    api_url = (
        f"https://management.azure.com/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices"
        f"/accounts/{account_name}/deployments?api-version=2023-05-01"
    )
    token = credential.get_token("https://management.azure.com/.default").token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch deployments for {account_name} in {subscription_id}: {response.status_code}")
        return None

all_subs_dep_json = []

# Main loop
for subscription_id in subscription_ids:

    subscription_based_dep_json = []

    print(f"\n--- Subscription: {subscription_id} ---")
    resource_group = get_resource_group(subscription_id)
    if not resource_group:
        print("No resource group with 'GPTAdvancedStories' found.")
        continue

    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    openai_accounts = [
        acc for acc in cognitive_client.accounts.list_by_resource_group(resource_group)
        if acc.kind == "OpenAI"
    ]

    for account in openai_accounts:
        print(f"\nOpenAI Resource: {account.name}")
        deployments = get_deployments(subscription_id, resource_group, account.name)
        if deployments:
            print(json.dumps(deployments, indent=2))
            deployments_json = deployments
            subscription_based_dep_json.append({account.name: deployments_json})

    all_subs_dep_json.append({subscription_id : subscription_based_dep_json})


# print(json.dumps(all_subs_dep_json, indent=2))

with open("all_subs_dep_read_json.json", "w") as f:
    json.dump(all_subs_dep_json, f, indent=4)