import argparse
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.resource import ResourceManagementClient
# from azure.mgmt.cognitiveservices.models import CognitiveServicesAccountCreateParameters, Sku, CognitiveServicesAccountProperties
import os
import re

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

def get_rg(credential, subscription_id):

    resource_client = ResourceManagementClient(credential, subscription_id)
    resource_group_name = None

    for rg in resource_client.resource_groups.list():
        if "ResourceGroup" in rg.name:
            resource_group_name = rg.name
        print(f"Name: {rg.name}, Location: {rg.location}")

    return resource_group_name

def clean_brand_name(brand):
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r'[^A-Za-z0-9]', '', brand)
    return cleaned

def create_resource(client, resource_group, resource_name, region, subscription_id, custom_domain):
    params = {
        "location": region,
        "kind": "TextAnalytics",  # Specify the resource kind (e.g., TextAnalytics for CLU)
        "sku": {"name": "S"},  # Define SKU name (e.g., "S" for standard tier)
        "properties": {"customSubDomainName": custom_domain}  # Additional properties
    }
    poller = client.accounts.begin_create(
        resource_group_name=resource_group,
        account_name=resource_name,
        account=params
    )
    result = poller.result()
    print(f"Created resource: {result.name} in region: {result.location} with custom domain: {custom_domain}")

def main():
    # parser = argparse.ArgumentParser(description="Create Azure Cognitive Services resources.")
    # parser.add_argument("brand", help="Brand name")
    # parser.add_argument("subscription_id", help="Azure subscription ID")
    # parser.add_argument("resource_group", help="Azure resource group name")
    # args = parser.parse_args()

    parser = argparse.ArgumentParser(description='Create CLU Resources')
    # Constants
    # parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
    parser.add_argument('--subscription_id', required=True, help='Azure Subscription ID')
    parser.add_argument('--brand', required=True, help='Azure Brand Name')

    args = parser.parse_args()

    subscription_id = args.subscription_id
    brand = args.brand
    brand = clean_brand_name(brand)
    # subscription_id = "0ad3d206-436b-43e9-8dbd-3c0e7c3df34c"
    # resource_group = f"{brand}ResourceGroup"

    credential = authenticate()
    resource_group = get_rg(credential, subscription_id)
    client = CognitiveServicesManagementClient(credential, subscription_id)

    # Define region lists
    region_map = {
        "Authoring": ["EastUS", "EastUS2", "WestUS2", "WestUS3", "SouthCentralUS"],
        "Reporting": ["CentralUS", "NorthCentralUS", "WestCentralUS", "WestUS"],
        "Prediction": ["CentralUS", "NorthCentralUS", "WestCentralUS", "WestUS"],
    }

    for resource_type, regions in region_map.items():
        for region in regions:
            resource_name = f"{brand}CLU{resource_type}{region}"
            custom_domain = resource_name.lower()

            try:
                create_resource(client, resource_group, resource_name, region, subscription_id, custom_domain)
            except Exception as e:
                print(f"Failed to create {resource_name} in {region}: {e}")

if __name__ == "__main__":
    main()
