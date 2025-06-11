import subprocess
import sys
import argparse
from azure.identity import ClientSecretCredential
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

def run_command(command):
    """Run a shell command and print its output or error."""
    try:
        print(f"\nExecuting: {command}")
        result = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {e.cmd}")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
    # Constants
    # parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
    parser.add_argument('--subscription_id', required=True, help='Azure Subscription ID')

    args = parser.parse_args()

    subscription_id = args.subscription_id

    credentials = authenticate()

    if len(sys.argv) < 2:
        print("Usage: python resourceRegistration.py")
        sys.exit(1)

    # Set the subscription
    run_command(f"az account set --subscription {subscription_id}")

    # Create resource group 'test' in East US
    run_command("az group create --name test --location eastus")

    # Create LUIS Authoring resource
    run_command("az cognitiveservices account create -n test001 -g test --kind LUIS.Authoring --sku F0 -l WestUS")

    # Create LUIS Prediction resource
    run_command("az cognitiveservices account create -n prediction-resource002 -g test --kind LUIS --sku S0 -l westus --yes")
