from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.storage import StorageManagementClient
import subprocess

SUBSCRIPTION_ID = "de8e65ea-9d88-4eb8-acf1-22c75d8578f0"
credential = DefaultAzureCredential()

subscription_client = SubscriptionClient(credential)
subscription = subscription_client.subscriptions.get(SUBSCRIPTION_ID)
scope_name = subscription.display_name

BRAND = scope_name
brand_name_scoped_l = BRAND.lower().replace(" ", "").replace("-", "").replace("PayAsYouGo", "")
brand_name_scoped = BRAND.replace(" ", "").replace("-", "").replace("PayAsYouGo", "")
STORAGE_ACCOUNT_NAME = f"{brand_name_scoped_l}diagnosestorage"[:24]
DIAGNOSTIC_SETTING_NAME = f"{brand_name_scoped_l}_speech_service_request_response_logs"
RESOURCE_GROUP_NAME = f"{brand_name_scoped}ResourceGroup"

# Azure clients
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
cognitive_client = CognitiveServicesManagementClient(credential, SUBSCRIPTION_ID)
monitor_client = MonitorManagementClient(credential, SUBSCRIPTION_ID)
storage_client = StorageManagementClient(credential, SUBSCRIPTION_ID)

# List of resource names created earlier
cognitive_accounts = [
    f"{brand_name_scoped}-Authoring",
    f"{brand_name_scoped}App",
    f"{brand_name_scoped}ReportingApp",
    f"{brand_name_scoped}SpeechServices",
    f"z-{brand_name_scoped}",
    f"tts-{brand_name_scoped}"
]

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

# Purge diagnostic settings
def delete_diagnostic_setting(target_resource_id):
    try:
        print(f"Deleting diagnostic setting '{DIAGNOSTIC_SETTING_NAME}' from {target_resource_id}...")
        monitor_client.diagnostic_settings.delete(resource_uri=target_resource_id, name=DIAGNOSTIC_SETTING_NAME)
        print("Diagnostic setting deleted.")
    except Exception as e:
        print(f"Diagnostic setting deletion failed or not found: {e}")

# Purge Cognitive Services Accounts
def delete_cognitive_accounts():
    for account_name in cognitive_accounts:
        try:
            print(f"Deleting Cognitive Services account: {account_name}")
            cognitive_client.accounts.begin_delete(RESOURCE_GROUP_NAME, account_name).wait()
            print(f"Deleted: {account_name}")
        except Exception as e:
            print(f"Failed to delete {account_name}: {e}")

# Delete storage account
def delete_storage_account():
    print(f"Deleting storage account '{STORAGE_ACCOUNT_NAME}'...")
    try:
        storage_client.storage_accounts.delete(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
        print("Storage account deleted.")
    except Exception as e:
        print(f"Failed to delete storage account: {e}")


# Delete resource group
def delete_resource_group():
    try:
        print(f"Deleting resource group: {RESOURCE_GROUP_NAME}")
        resource_client.resource_groups.begin_delete(RESOURCE_GROUP_NAME).wait()
        print("Resource group deleted.")
    except Exception as e:
        print(f"Failed to delete resource group: {e}")

def purge_cognitive_account(resource_group):
    """
    Purges a soft-deleted Cognitive Services account.
    """
    for account_name in cognitive_accounts:
        try:
            print(f"Purging Cognitive Services account: {account_name}")
            location = "eastus" if "z-" in account_name or "tts-" in account_name else "westus"

            result = subprocess.run(
                [
                    "az", "cognitiveservices", "account", "purge",
                    "--name", account_name,
                    "--resource-group", resource_group,
                    "--location", location
                ],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            # return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to purge cognitive account {account_name}: {e.stderr}")
            return False


if __name__ == "__main__":
    print("Starting cleanup process...")
    set_subscription(SUBSCRIPTION_ID)
    # Try to get the ID of the SpeechServices account (for diagnostic setting deletion)
    try:
        speech_service = cognitive_client.accounts.get(RESOURCE_GROUP_NAME, f"{brand_name_scoped}SpeechServices")
        delete_diagnostic_setting(speech_service.id)
    except Exception as e:
        print(f"Speech service not found or could not get ID: {e}")

    delete_cognitive_accounts()
    purge_cognitive_account(RESOURCE_GROUP_NAME)
    delete_storage_account()
    delete_resource_group()

    print("Cleanup complete.")
