import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.resource import SubscriptionClient, ResourceManagementClient
import re
import subprocess

def set_subscription(subscription_id):
    """
    Sets the active Azure subscription programmatically using subprocess.
    """
    try:
        print(f"Setting subscription to: {subscription_id}")
        result = subprocess.run(
            ["az", "account", "set", "--subscription", subscription_id],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Subscription set successfully: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error setting subscription: {e.stderr}")
        raise

def getDeploymentResource(credential, subscription_id):
    resource_group = None

    # credential = DefaultAzureCredential()
    client = CognitiveServicesManagementClient(credential, subscription_id)

    resource_client = ResourceManagementClient(credential, subscription_id)

    for rg in resource_client.resource_groups.list():
        if "ResourceGroup" in rg.name:
            resource_group = rg.name
        print(f"Name: {rg.name}, Location: {rg.location}")

    accounts = client.accounts.list_by_resource_group(resource_group)

    deployment_name = None

    for account in accounts:
        if account.kind.lower() == "openai":
            print(f"\n[OpenAI Resource] {account.name}")
            deployments = client.deployments.list(resource_group, account.name)

            for deployment in deployments:
                print(f"   - Deployment Name: {deployment.name}")
                deployment_name = deployment.name
                deployment_details = client.deployments.get(resource_group, account.name,
                                                            deployment.name)
                deployment_json = deployment.as_dict()
                print("   - Deployment Type:", deployment_json["sku"]["name"])
                print("   - Capacity:", deployment_json["sku"]["capacity"])
                print("   - Version Upgrade Policy:", deployment_json["properties"]["version_upgrade_option"])

                # print("\n🔹 Deployment JSON after toggling:\n", json.dumps(deployment_json, indent=4))

    return deployment_name

def clean_brand_name(brand):
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r'[^A-Za-z0-9]', '', brand)
    return cleaned

def getResourceJSON(subscription_id):
    # brand_name = "Genpact-Bluestone"
    # subscription_id = "d7b44af3-b43a-4313-97d0-7fca36eec114"


    # Authenticate with DefaultAzureCredential
    set_subscription(subscription_id)
    credential = DefaultAzureCredential()
    subscription_client = SubscriptionClient(credential)
    subscription = subscription_client.subscriptions.get(subscription_id)
    scope_name = subscription.display_name

    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)

    brand_name = clean_brand_name(scope_name)
    resource_group_name = f"{brand_name}ResourceGroup"

    # List of resource names to fetch keys and endpoints for
    resources = {
        "openai": f"z-{brand_name}",  # Azure OpenAI
        "speech": f"tts-{brand_name}",  # Azure Speech Service
        "luis_authoring": f"{brand_name}-Authoring",  # Language Understanding (LUIS) Authoring
        "luis_app": f"{brand_name}App",  # Another LUIS instance
        "reporting_app": f"{brand_name}ReportingApp",  # Additional LUIS service
        "speech_services": f"{brand_name}SpeechServices",  # Another Speech service
    }

    returnJson = {}

    # List to store each resource's dictionary with the desired format
    resource_data_list = []
    print("Resource Group :", resource_group_name)
    # Fetch keys and endpoints for each resource
    for service, resource_name in resources.items():
        try:
            keys = cognitive_client.accounts.list_keys(resource_group_name, resource_name)
            resource = cognitive_client.accounts.get(resource_group_name, resource_name)
            endpoint = resource.properties.endpoint

            print(resource.name ,keys.key1, endpoint)
            # Store the formatted data in the resource_data_list

            if ("Authoring" in resource.name or "App" in resource.name or "ReportingApp" in resource.name):
                returnJson[resource.name] = [keys.key1, endpoint]

            if service == "openai":
                model_name = getDeploymentResource(credential, subscription_id)
                resource_data_list.append({
                    keys.key1: {
                        "service": "Azure",
                        "resource_type": "Open AI",
                        "capacity": "0",
                        "inactive": "0",
                        "region": "eastus",
                        "endpoint": endpoint,
                        "resource_name": resource_name,
                        "model_type": "Deployment",
                        "model_name": model_name,
                        "key": keys.key1,
                        "resource_action": None
                    }
                })

            elif service == "speech":
                resource_data_list.append({
                    keys.key1: {
                        "service": "Azure",
                        "resource_type": "Speech",
                        "capacity": "0",
                        "inactive": "0",
                        "region": "eastus",
                        "endpoint": endpoint,
                        "resource_name": "Azure-Text To Speech",
                        "key": keys.key1,
                        "resource_action": None
                    }
                })

            elif service == "luis_authoring":
                resource_data_list.append({
                    keys.key1: {
                        "service": "Azure",
                        "resource_type": "LUIS Authoring",
                        "capacity": "414",
                        "inactive": "0",
                        "region": "westus",
                        "endpoint": endpoint,
                        "resource_name": resource_name,
                        "key": keys.key1,
                        "resource_action": "0"
                    }
                })

        except Exception as e:
            print(f"Error retrieving keys for {service}: {e}")

    # Now resource_data_list contains the formatted data for each resource
    # print(resource_data_list)
    print(json.dumps(resource_data_list, indent=2))
    for resource_json in resource_data_list:
        print(resource_json)

    returnJson["brand_name"] = brand_name
    returnJson["resource_group"] = resource_group_name

    return returnJson

def main():

    subscription_id = "f2f15065-2e82-4202-a2cc-af51e16f8772"
    # credential = DefaultAzureCredential()
    datajson = getResourceJSON(subscription_id)
    print(json.dumps(datajson, indent=2))

if __name__ == "__main__":
    main()