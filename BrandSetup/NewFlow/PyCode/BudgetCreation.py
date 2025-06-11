# from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.resource import SubscriptionClient
from datetime import datetime
import re
import argparse
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

def is_leap_year(year):

    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True

    return False

def set_last_day(month, year):
    if month == 2:
        return 29 if is_leap_year(year) == True else 28

    last_day = 31 if month in (1, 3, 5, 7, 8, 10, 12) else 30
    return last_day

def clean_brand_name(brand):
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r'[^A-Za-z0-9]', '', brand)
    return cleaned

def create_budget(subscription_ids, alert_emails):

    # Initialize credentials
    credential = authenticate()
    subscription_client = SubscriptionClient(credential)

    curr_year, curr_month = datetime.now().year, datetime.now().month
    exp_year, exp_month = curr_year + 10, 12 if curr_month == 1 else curr_month - 1
    exp_day = set_last_day(exp_month, exp_year)

    print("Current Year and Month: ", curr_year, curr_month)
    print("Expiration Year, Month and Day: ", exp_year, exp_month, exp_day)

    for subscription_id in subscription_ids:

        # Initialize the client
        subscription = subscription_client.subscriptions.get(subscription_id)

        # Use the subscription display name as the scope name
        scope_name = subscription.display_name
        # Cleaning the scope_name by removing both '-' and ' ' and 'PayAsYouGo' if exists
        scope_name_cleaned = clean_brand_name(scope_name)

        # Initialize the Consumption Management Client
        consumption_client = ConsumptionManagementClient(credential, subscription_id)

        # Budget details
        budget_name = f"{scope_name_cleaned}-Alert-Cost-Reached100"
        budget_parameters = {
            "category": "Cost",
            "amount": 100.0,
            "time_grain": "Monthly",
            "time_period": {
                "start_date": datetime(curr_year, curr_month, 1, 0, 0, 0).isoformat() + "Z",
                # ISO format with UTC timezone
                "end_date": datetime(exp_year, exp_month, exp_day, 23, 59, 59).isoformat() + "Z",
                # ISO format with UTC timezone
            },
            "notifications": {
                "Actual_GreaterThan_100Percent": {
                    "enabled": True,
                    "operator": "GreaterThan",
                    "threshold": 100.0,
                    "contact_emails": alert_emails,
                }
            }
        }

        print("Creating budget: ", budget_name)
        # Create the budget
        try:
            response = consumption_client.budgets.create_or_update(
                scope=f"/subscriptions/{subscription_id}",
                budget_name=budget_name,
                parameters=budget_parameters
            )
            print(f"Budget created: {response.name}")
        except Exception as e:
            print(f"An error occurred for subscription {subscription_id}: {e}")


def main():
    # Replace with your subscription IDs

    parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
    # Constants
    # parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
    parser.add_argument('--subscription_id', required=True, help='Azure Subscription ID')

    args = parser.parse_args()

    subscription_id = args.subscription_id

    subscription_ids = [
        subscription_id  #
    ]

    # Alert recipients
    alert_emails = [
        "monika.samant@zenarate.com",
        "akash@zenarate.com",
        "raghavt@zenarate.com",
        "robertj@zenarate.com",
        "vinod.singh@zenarate.com",
    ]

    create_budget(subscription_ids, alert_emails)

if __name__ == "__main__":
    main()