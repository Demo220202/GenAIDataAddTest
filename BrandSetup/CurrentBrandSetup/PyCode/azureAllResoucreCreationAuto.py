from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.cognitiveservices.models import Deployment, Sku as DeploymentSku
import json
import re
import os


def authenticate():
    client_id = os.getenv("ARM_CLIENT_ID")
    client_secret = os.getenv("ARM_CLIENT_SECRET")
    tenant_id = os.getenv("ARM_TENANT_ID")

    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("Missing one or more Azure credentials. Please check your environment variables.")

    credentials = ClientSecretCredential(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id
    )
    return credentials

def clean_brand_name(brand):
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r'[^A-Za-z0-9]', '', brand)
    return cleaned

SUBSCRIPTION_ID = "de8e65ea-9d88-4eb8-acf1-22c75d8578f0" # as it is not used so hardcoded

credential = authenticate()
subscription_client = SubscriptionClient(credential)
subscription = subscription_client.subscriptions.get(SUBSCRIPTION_ID)
scope_name = subscription.display_name

# Configuration variables
  # Replace with your Azure subscription ID
BRAND = scope_name  # Replace with your brand name
brand_name_scoped = clean_brand_name(BRAND)
brand_name_scoped_l = brand_name_scoped.lower()
STORAGE_ACCOUNT_NAME = f"{brand_name_scoped_l}diagnosestorage"[:24]  # Replace with your storage account name
DIAGNOSTIC_SETTING_NAME = f"{brand_name_scoped_l}_speech_service_request_response_logs"  # Replace with your diagnostic setting name
LOCATION = "West US"  # Resource location

print(BRAND)
print(brand_name_scoped)
print(STORAGE_ACCOUNT_NAME)
print(DIAGNOSTIC_SETTING_NAME)

# Azure clients setup
credential = authenticate()
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
cognitive_client = CognitiveServicesManagementClient(credential, SUBSCRIPTION_ID)
auth_client = AuthorizationManagementClient(credential, SUBSCRIPTION_ID)
storage_client = StorageManagementClient(credential, SUBSCRIPTION_ID)
monitor_client = MonitorManagementClient(credential, SUBSCRIPTION_ID)



# 1. Create a Resource Group
def create_resource_group():
    print(f"Creating resource group '{brand_name_scoped}ResourceGroup' in {LOCATION}...")
    resource_group = resource_client.resource_groups.create_or_update(
        resource_group_name=f"{brand_name_scoped}ResourceGroup",
        parameters={"location": LOCATION}
    )
    print("Resource group created.")
    return resource_group


# 2. Assign roles to the resource group
def assign_roles(resource_group_id):
    roles = [
        {"role": "Contributor", "principal_id": "2b52bc90-a523-45bb-9a14-51c129500139"},
        {"role": "Cognitive Services Language Owner", "principal_id": "4aac6e13-a827-4e73-8b05-527380e5e1b1"}
    ]
    for role in roles:
        print(f"Assigning role '{role['role']}' to principal {role['principal_id']}...")
        auth_client.role_assignments.create(
            scope=resource_group_id,
            role_assignment_name="",
            parameters={
                "role_definition_name": role["role"],
                "principal_id": role["principal_id"]
            }
        )
    print("Roles assigned.")

def create_or_update_deployment(client, resource_group_name, account_name, deployment_name, capacity, model_name, model_version, sku_name):
    try:
        deployment_params = Deployment(
            sku=DeploymentSku(name=sku_name, capacity=capacity),
            properties={
                "model": {
                    "format": "OpenAI",
                    "name": model_name,
                    "version": model_version
                },
                # "dynamicThrottlingEnabled": True,
            }
        )


        deployment = client.deployments.begin_create_or_update(
            resource_group_name,
            account_name,
            deployment_name,
            deployment_params
        ).result()

        print(f"✅ Deployment '{deployment_name}' successfully created/updated.")

        # Fetch and print the JSON details of the deployment
        deployment_details = client.deployments.get(resource_group_name, account_name, deployment_name)
        deployment_json = deployment_details.as_dict()

        print("\n🔹 Deployment JSON after Deployment Resource creation/modification:\n", json.dumps(deployment_json, indent=4))

        return deployment_json  # Return it in case you want to use it elsewhere

    except Exception as e:
        print(f"❌ Failed to create/update deployment '{deployment_name}'. Error: {e}")
        return None

# 3. Create Cognitive Services Accounts (LUIS, SpeechServices, OpenAI)
def create_cognitive_account(account_name, kind, sku="S0", custom_subdomain_name=None):
    print(f"Creating Cognitive Services account '{account_name}' of kind '{kind}'...")
    location = "eastus" if "z-" in account_name or "tts-" in account_name else LOCATION
    account_params = {
        "location": location,
        "kind": kind,
        "sku": {"name": sku},
    }
    if custom_subdomain_name:
        account_params["properties"] = {"custom_sub_domain_name": custom_subdomain_name}
        print(account_params)

    cognitive_account = cognitive_client.accounts.begin_create(
        f"{brand_name_scoped}ResourceGroup",
        account_name,
        account_params,
    ).result()

    print(f"Cognitive Services account '{account_name}' created.")
    return cognitive_account


# Function to create a storage account
def create_storage_account():
    print(f"Creating storage account '{STORAGE_ACCOUNT_NAME}'...")
    storage_account = storage_client.storage_accounts.begin_create(  # Use storage_client
        f"{brand_name_scoped}ResourceGroup",
        STORAGE_ACCOUNT_NAME,
        {
            "sku": {"name": "Standard_GRS"},
            "kind": "StorageV2",
            "location": LOCATION
        }
    ).result()
    print(f"Storage account '{STORAGE_ACCOUNT_NAME}' created.")
    return storage_account


# 5. Create Diagnostic Settings
# Function to create a diagnostic setting for the resource
def create_diagnostic_setting(target_resource_id, storage_account_id, diagnostic_setting_name):
    print(f"Creating diagnostic setting '{diagnostic_setting_name}'...")
    diagnostic_setting = monitor_client.diagnostic_settings.create_or_update(
        name=diagnostic_setting_name,
        resource_uri=target_resource_id,
        parameters={
            "storage_account_id": storage_account_id,
            "logs": [
                {
                    "category": "Audit",
                    "enabled": True,
                    "retention_policy": {"enabled": True, "days": 0}
                },
                {
                    "category": "Trace",
                    "enabled": True,
                    "retention_policy": {"enabled": True, "days": 0}
                }
            ],
            "metrics": [
                {
                    "category": "AllMetrics",
                    "enabled": True,
                    "retention_policy": {"enabled": True, "days": 0}
                }
            ]
        }
    )
    print(f"Diagnostic setting '{diagnostic_setting_name}' created.")
    return diagnostic_setting



# Main program execution
if __name__ == "__main__":
    # Step 1: Create resource group
    resource_group = create_resource_group()

    # Step 2: Assign roles
    # assign_roles(resource_group.id)

    # Step 3: Create Cognitive Services accounts (LUIS, SpeechServices, OpenAI)
    create_cognitive_account(account_name=f"{brand_name_scoped}-Authoring", kind="LUIS.Authoring", sku='F0')
    create_cognitive_account(account_name=f"{brand_name_scoped}App", kind="LUIS")
    create_cognitive_account(account_name=f"{brand_name_scoped}ReportingApp", kind="LUIS")
    speech_services = create_cognitive_account(account_name=f"{brand_name_scoped}SpeechServices", kind="SpeechServices")

    # Create the OpenAI resource
    openai_account_name = f"z-{brand_name_scoped}"
    openai_account = create_cognitive_account(
        account_name=openai_account_name,
        kind="OpenAI",
        custom_subdomain_name=openai_account_name,
        sku="S0"
    )

    create_or_update_deployment(cognitive_client, f"{brand_name_scoped}ResourceGroup", openai_account_name, f"{brand_name_scoped}_v1", 120, "gpt-35-turbo",
                                "0125", "Standard")

    # CognitiveService
    tts_account_name = f"tts-{brand_name_scoped}"
    tts_account = create_cognitive_account(
        account_name=tts_account_name,
        kind="CognitiveServices",
        sku="S0",
        custom_subdomain_name=tts_account_name.lower()
    )

    # Step 4: Create storage account
    storage_account = create_storage_account()

    # Step 5: Create diagnostic settings for Speech Services (and OpenAI if needed)
    diagnostic_setting = create_diagnostic_setting(
        target_resource_id=speech_services.id,  # ID of the Speech Services resource
        storage_account_id=storage_account.id,  # ID of the storage account
        diagnostic_setting_name=DIAGNOSTIC_SETTING_NAME  # Name of the diagnostic setting
    )

    # Optionally, you could add diagnostic settings for the OpenAI account too
    # create_diagnostic_setting(
    #     target_resource_id=openai_account.id,
    #     storage_account_id=storage_account.id
    # )

    print("All resources created successfully!")


# Optimization -
# For beta, checking for the length of storage account(not exceeding 24) and inputs(as minimum as possible)