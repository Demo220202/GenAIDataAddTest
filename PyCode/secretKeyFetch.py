import boto3
import json
from botocore.exceptions import ClientError

def fetch_secret(secret_name, region_name):
    """
    Fetch a secret from AWS Secrets Manager
    :param secret_name
    :param region_name
    :return: The secret value as a dictionary.
    """

    session = boto3.Session(region_name=region_name)
    client = session.client('secretsmanager')

    try:

        response = client.get_secret_value(SecretId=secret_name)

        # Check if the secret is stored as plain text or JSON
        if "SecretString" in response:
            secret = response["SecretString"]
        else:
            # Decode binary secrets
            secret = response["SecretBinary"].decode("utf-8")

        # Convert to a dictionary if the secret is JSON
        try:
            return json.loads(secret)
        except json.JSONDecodeError:
            return secret

    except ClientError as e:
        print(f"Error fetching secret: {e}")
        return None

def get_secret(env):

    if env == "prod":
        secret_name = "zenarate/prod/db-report-replica/main/root"
        region_name = "us-west-2"
        return fetch_secret(secret_name, region_name)
    elif env == "beta":
        secret_name = "zenarate/beta/db/main/root"
        region_name = "us-west-1"
        return fetch_secret(secret_name, region_name)
    elif env == "qa":
        secret_name = "zenarate/qa/db/main/root"
        region_name = "us-west-1"
        return fetch_secret(secret_name, region_name)

# secret_name = "zenarate/prod/db-report-replica/main/root"
# region_name = "us-west-2"
#
# secret_value = fetch_secret(secret_name, region_name)
# Usage
# if __name__ == "__main__":
#
#     secret_name = "zenarate/prod/db-report-replica/main/root"
#     region_name = "us-west-2"
#
#     secret_value = fetch_secret(secret_name, region_name)
#     if secret_value:
#         print("Fetched secret:")
#         print(secret_value)

# print(secret_value)
