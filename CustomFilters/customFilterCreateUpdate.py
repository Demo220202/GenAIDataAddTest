# from azure.identity import DefaultAzureCredential
from azure.identity import ClientSecretCredential
import os
from dotenv import load_dotenv
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import RaiPolicy, RaiPolicyProperties, RaiPolicyContentFilter
from azure.mgmt.cognitiveservices.models import Deployment, DeploymentProperties

load_dotenv()

"""

Snippet taken for Azure Doc
Special Thanks to Suhas Sir for initiating this, good for learning!

"""

def authenticate():
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")

    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("Missing one or more Azure credentials. Please check your environment variables.")

    credentials = ClientSecretCredential(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id
    )
    return credentials

def get_resource_group(subs_id, credential):

    subscription_id = subs_id
    resource_group_name = None

    resource_client = ResourceManagementClient(credential, subscription_id)

    for rg in resource_client.resource_groups.list():
        if "GPTAdvancedStories" in rg.name:
            resource_group_name = rg.name
        print(f"Name: {rg.name}, Location: {rg.location}")

    return resource_group_name


def assign_rai_policy_to_model(deployment_name, rai_policy_name, subscription_id, resource_group, resource_name, credential):

    client = CognitiveServicesManagementClient(credential, subscription_id)

    deployments = client.deployments.list(resource_group, resource_name)

    for deployment in deployments:
        name = deployment.name
        if name == deployment_name:  # for gpt-4o-1
            print(f"Updating deployment: {name}")
            new_props = DeploymentProperties(
                model=deployment.properties.model,
                rai_policy_name=rai_policy_name,
                scale_settings=deployment.properties.scale_settings
            )

            updated_deployment = Deployment(
                sku=deployment.sku,
                properties=new_props
            )

            result = client.deployments.begin_create_or_update(
                resource_group_name=resource_group,
                account_name=resource_name,
                deployment_name=name,
                deployment=updated_deployment
            ).result()

            print(f"✔️ RAI Policy assigned to deployment '{name}': {result.properties.rai_policy_name}")
        else:
            print(f"Skipping deployment: {name}")


def create_or_update_custom_policy(resource_name, resource_group_name, rai_policy_name, client):

    rai_policy = RaiPolicy(
        properties=RaiPolicyProperties(
            base_policy_name="Microsoft.DefaultV2",
            mode="Default",
            content_filters=[
                RaiPolicyContentFilter(name="Violence", severity_threshold="High", blocking=True, enabled=True,
                                       source="Prompt"),
                RaiPolicyContentFilter(name="Hate", severity_threshold="High", blocking=True, enabled=True,
                                       source="Prompt"),
                RaiPolicyContentFilter(name="Sexual", severity_threshold="High", blocking=True, enabled=True,
                                       source="Prompt"),
                RaiPolicyContentFilter(name="Selfharm", severity_threshold="High", blocking=True, enabled=True,
                                       source="Prompt"),
                RaiPolicyContentFilter(name="Jailbreak", blocking=False, enabled=True, source="Prompt"),
                RaiPolicyContentFilter(name="Indirect Attack", blocking=False, enabled=False, source="Prompt"),
                RaiPolicyContentFilter(name="Violence", severity_threshold="Medium", blocking=True, enabled=True,
                                       source="Completion"),
                RaiPolicyContentFilter(name="Hate", severity_threshold="Medium", blocking=True, enabled=True,
                                       source="Completion"),
                RaiPolicyContentFilter(name="Sexual", severity_threshold="Medium", blocking=True, enabled=True,
                                       source="Completion"),
                RaiPolicyContentFilter(name="Selfharm", severity_threshold="Medium", blocking=True, enabled=True,
                                       source="Completion"),
                RaiPolicyContentFilter(name="Protected Material Text", blocking=True, enabled=True,
                                       source="Completion"),
                RaiPolicyContentFilter(name="Protected Material Code", blocking=False, enabled=True,
                                       source="Completion"),
            ]
        )
    )

    response = client.rai_policies.create_or_update(
        resource_group_name=resource_group_name,
        account_name=resource_name,
        rai_policy_name=rai_policy_name,
        rai_policy=rai_policy
    )

    print(response)


def main():

    credential = authenticate()

    subscription_id_list = [
        "de8e65ea-9d88-4eb8-acf1-22c75d8578f0"
    ]
    rai_policy_name = "CustomFilterTest1"
    deployment_name = "gpt-4o-1"

    for subscription_id in subscription_id_list:

    # subscription_id = "de8e65ea-9d88-4eb8-acf1-22c75d8578f0" # Zenarate-OP-30
        resource_group_name = get_resource_group(subscription_id, credential)
        # rai_policy_name = "CustomFilterTest1"
        # deployment_name = "gpt-4o-1"

        client = CognitiveServicesManagementClient(credential, subscription_id)

        openai_accounts = [
            res for res in client.accounts.list_by_resource_group(resource_group_name)
            if res.kind == 'OpenAI'
        ]


        for account in openai_accounts:

            resource_name = account.name

            print(f"\nProcessing OpenAI resource: {resource_name}")

            create_or_update_custom_policy(resource_name, resource_group_name, rai_policy_name, client)

            assign_rai_policy_to_model(deployment_name, rai_policy_name, subscription_id, resource_group_name, resource_name, credential)


if __name__ == "__main__":
    main()