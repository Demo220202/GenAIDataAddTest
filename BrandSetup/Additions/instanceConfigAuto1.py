import os
import time
import boto3

session = boto3.Session(profile_name="default", region_name="us-west-1")

sts_client = session.client('sts') # sts client
identity = sts_client.get_caller_identity()
print(f"Authenticated as: {identity['Arn']}")

# Initialize AWS clients
ec2_client = session.client('ec2')  # ec2 client
ssm_client = session.client('ssm')  # ssm client

def get_template_site_name(env, site_name):

    if env == "BuildServer":
        return "app.zenarate.com", site_name
    elif env == "Aditya":
        return "app.zenarate.com", site_name
    elif env == "zenarate/beta":
        return "beta.zenarate.com", f"beta-{site_name}"
    elif env == "zenarate/uat":
        return "uat-app.zenarate.com", f"uat-{site_name}"
    elif env == "dev":
        return "dev.zenarate.com", f"dev-{site_name}"
    elif env == "zenarate/qa":
        return "qa.zenarate.com", f"qa-{site_name}"
    elif env == "qa2":
        return "qa2.zenarate.com", f"qa2-{site_name}"
    else:
        raise Exception(f"Unknown environment: {env}")


def specific_names_to_be_excluded(excluded_name_list, name_tag_value):

    flag = False
    for excluded_name in excluded_name_list:
        if excluded_name.lower() in name_tag_value.lower():
            flag = True
            break

    return flag

def get_instances_by_tag(tag_key, tag_value, excluded_name_list):
    """
    Fetch all running EC2 instances with a specific tag.
    :param tag_key: The key of the tag (e.g., 'env').
    :param tag_value: The value of the tag (e.g., 'qa, beta etcetra').
    :return: List of instance IDs.
    """
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},  # only for running instances
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]}        # Filter based on tags --> can be changed by the programmer as per requirement
        ]
    )

    instances = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            # Fetch 'Name' tag value if present
            name_tag_value = next(
                (tag['Value'] for tag in instance.get('Tags', []) if tag['Key'].lower() == 'name'),
                None
            )

            # Check if 'Name' tag contains excluded_names (case-insensitive)
            if name_tag_value and (specific_names_to_be_excluded(excluded_name_list, name_tag_value)):
                continue

            instances.append([instance['InstanceId'], name_tag_value])  # Add to the list if not excluded


    return instances

def execute_commands(instance_ids, commands):
    """
    Execute commands on EC2 instances via SSM.
    :param instance_ids: List of EC2 instance IDs.
    :param commands: List of shell commands to execute.
    :return: Command ID.
    """
    if not instance_ids:
        print("No running instances found with the specified tag.")
        return

    response = ssm_client.send_command(
        InstanceIds=instance_ids,
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': commands},
    )
    command_id = response['Command']['CommandId']
    print(f"Command sent. Command ID: {command_id}")
    return command_id


def get_command_output(instance_id, command_id):
    while True:
        time.sleep(2)  # Wait for a couple of seconds before fetching the result

        response = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id,
        )

        status = response['Status']

        if status in ['Success', 'Failed', 'TimedOut', 'Cancelled']:
            print(f"\nCommand Status for {instance_id}: {status}")

            if 'StandardOutputContent' in response and response['StandardOutputContent']:
                print(f"Standard Output for {instance_id}:\n{response['StandardOutputContent']}")

            if 'StandardErrorContent' in response and response['StandardErrorContent']:
                print(f"Standard Error for {instance_id}:\n{response['StandardErrorContent']}")

            break
        else:
            print(f"Status for {instance_id}: {status}. Waiting for the command to finish...")


def main():
    # Specify the tag to filter instances
    tag_key = "env" # Checked/Changed by the programmer
    tag_value = "zenarate/beta" # Checked/Changed by the programmer

    site_name = "costco.zenarate.com"  # Changed by the programmer
    template_site_name, site_name = get_template_site_name(tag_value, site_name)
    # site_name = "setf.zenarate.com" # Changed by the programmer
    print(site_name)

    excluded_name_list = ["scim", "guide", "verizon", "uatzenarate", "lrs", "adsf"] # Can be inserted by the programmer

    # Fetch the running instance(s) based on tags
    instances = get_instances_by_tag(tag_key, tag_value, excluded_name_list)
    print(f"Found running instances with tag {tag_key}={tag_value}: ")

    instances_ids = []
    for instance in instances:
        print(f"\t{instance[0]}: {instance[1]}")
        instances_ids.append(instance[0])


    # Commands definition on Ubuntu
    commands = [
        f"x1=\"{site_name}.conf\"",
        f"x2=\"{site_name}\"",
        f"s_name=\"{template_site_name}.conf\"",
        f"s_url=\"{template_site_name}\"",
        "file_path=\"/etc/nginx/sites-enabled/\"",
        "cd $file_path",
        "sudo cp $s_name $x1",
        "sudo sed -i \"s/$s_url/$x2/g\" \"$x1\"",
        f"cat $x1 | grep {site_name}",
        "sudo nginx -t",
        "sudo systemctl restart nginx",
        "sudo systemctl status nginx",
        "echo 'Changes applied successfully.'"
    ]

    commands_read = [
        f"x1=\"{site_name}.conf\"",
        f"x2=\"{site_name}\"",
        # f"s_name=\"{template_site_name}.conf\"",
        # f"s_url=\"{template_site_name}\"",
        "file_path=\"/etc/nginx/sites-enabled/\"",
        "cd $file_path",
        # "sudo cp $s_name $x1",
        # "sudo sed -i \"s/$s_url/$x2/g\" \"$x1\"",
        f"cat $x1 | grep {site_name}",
        # "sudo nginx -t",
        # "sudo systemctl restart nginx",
        # "sudo systemctl status nginx",
        "echo 'Read successfully.'"
    ]

    # Commands execute karo
    # if instances:
    #     command_id = execute_commands(instances_ids, commands)
    #     print(f"Commands executed successfully. Command ID: {command_id}")
    # else:
    #     print("No running instances with the specified tag to execute commands on.")

    if instances:
        command_id = execute_commands(instances_ids, commands_read)

        if command_id:
            for instance_id in instances_ids:
                get_command_output(instance_id, command_id)
    else:
        print("No running instances with the specified tag to execute commands on.")


if __name__ == "__main__":
    main()
