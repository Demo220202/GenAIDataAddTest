import mysql.connector
from mysql.connector.constants import ClientFlag
import json
from botocore.exceptions import ClientError
from botocore.client import Config
from functools import reduce
import boto3


def lambda_handler(event, context):
    region = event["region"] if ("region" in event) else "us-east-1"
    username = event["username"] if ("username" in event) else "root"
    policyName = username + '_DB_Access_Policy_' + region
    secretsmanager = boto3.client('secretsmanager', region_name=region)
    rds = boto3.client('rds', region_name=region)
    iam = boto3.client('iam')



    def store_or_update_secret(email, region, secret_value):
        """
        Create or update a secret in AWS Secrets Manager.

        :param email: User's email address to include in the secret name and description.
        :param region: AWS region where the secret is associated.
        :param secret_value: The plain text value to store in the secret.
        """
        secret_name = f"zenarate/users/db/{email}"
        description = f"Giving DB Access of region : {region} to the user - {email}"

        # Initialize the Secrets Manager client
        session = boto3.Session(region_name=region)
        client = session.client("secretsmanager")

        try:
            # Try to describe the secret to check if it exists
            client.describe_secret(SecretId=secret_name)

            # If no exception, the secret exists — just update it :)
            response = client.update_secret(
                SecretId=secret_name,
                Description=description,
                SecretString=secret_value,
            )

            print(f"Secret '{secret_name}' updated successfully.")
            print(json.dumps(response, indent=4))
            return response

        except client.exceptions.ResourceNotFoundException:
            # Secret does not exist — just create it :)
            try:
                response = client.create_secret(
                    Name=secret_name,
                    Description=description,
                    SecretString=secret_value,
                    Tags=[
                        {"Key": "org", "Value": "zenarate"},
                        {"Key": "env", "Value": "users"},
                    ],
                )
                print(f"Secret '{secret_name}' created successfully.")
                print(json.dumps(response, indent=4))
                return response
            except Exception as e:
                print(f"Error creating secret '{secret_name}': {e}")
                return None
        except Exception as e:
            print(f"Error updating or checking secret '{secret_name}': {e}")
            return None

    # Get the list of all the secrets
    def getAllSecrets(accessList):
        print("accessList: ", accessList)
        rootList = []
        try:
            for access in accessList:
                # print('access1: ', access)
                secrets = getSecretsList(access['env'], access['role'])
                # print("Secret1: ", secrets)
                rootList = rootList + list(secrets)
                # print("rootList1: ",rootList)
        except Exception as e:
            print("error in getAllSecrets : ", e)

        print("RootList: ", rootList);
        return None if (len(rootList) < 1) else rootList

    # Fetch all the secrets with the root users
    def getSecretsList(secret, access):
        # print("getSecretsList:", secret, access)
        data = secretsmanager.list_secrets(MaxResults=100, Filters=[{'Key': 'name', 'Values': [secret]}])
        print("getSecretsList:", data)
        if (len(data["SecretList"]) > 0):
            print("datafromSecret:", data)
            rootSecrets = map(lambda s: {"Name": s["Name"], "Access": access},
                              list(filter(lambda x: ("/root" in x["Name"]), data["SecretList"])))
            return rootSecrets
        else:
            print("no secret list found")

    # Fetch the secret value from the Secrets Manager
    def getDbConnection(dbConfig):
        try:
            mydb = mysql.connector.connect(
                host=dbConfig['host'],
                user=dbConfig['user'],
                password=dbConfig['password'],
                database=dbConfig['database'],
                ssl_ca="certs/rds.pem",
            )
            cursor = mydb.cursor()
            cursor.execute("SELECT 1;")  # Validate DB access
            cursor.fetchone()
            cursor.close()
            return mydb
        except mysql.connector.Error as err:
            print(f"Database connection failed for {dbConfig['host']} - {dbConfig['database']}: {err}")
            return None  # Handling invalid credentials or unreachable DB

    # Fetch the secret value from the Secrets Manager
    def getSecrets(secret):
        try:
            data = secretsmanager.get_secret_value(SecretId=secret)
            return json.loads(data['SecretString'])
        except Exception as e:
            print(f"Failed to retrieve secret: {secret} -> {e}")
            return None  # if secret doesn't exist

    # Fetch the RDS details for the IAM policy (not the DB credentials)
    def getDBDetails(identifier):
        try:
            data = rds.describe_db_instances(DBInstanceIdentifier=identifier)
        except Exception as e:
            data = False
            print("error in getDBDetails : ", e)
        if (data):
            return data['DBInstances'][0]['DbiResourceId']
        else:
            return None

    # Create User and add the required access to the user based on the roles
    def processUser(userName, role, config, newInstance):
        db = config["database"]
        sql = []
        if (newInstance):
            sql.append("DROP USER IF EXISTS {userName};".format(userName=userName))
            sql.append(
                "CREATE USER {userName} IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';".format(userName=userName))
        if (role == 'ADMIN'):
            sql.append(
                "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, CREATE VIEW, SHOW VIEW, CREATE TEMPORARY TABLES, LOCK TABLES, INDEX, ALTER, EVENT, TRIGGER, CREATE ROUTINE, ALTER ROUTINE, EXECUTE, REFERENCES ON {db}.* TO '{userName}'@'%' WITH GRANT OPTION; ".format(
                    db=db, userName=userName))
        elif (role == 'DEV'):
            sql.append(
                "GRANT SELECT, INSERT, UPDATE, CREATE, CREATE VIEW, SHOW VIEW, CREATE TEMPORARY TABLES, LOCK TABLES, INDEX, EVENT, TRIGGER, CREATE ROUTINE, ALTER ROUTINE, EXECUTE, REFERENCES ON {db}.* TO '{userName}'@'%' WITH GRANT OPTION; ".format(
                    db=db, userName=userName))
        elif (role == 'VIEW_ONLY'):
            sql.append("GRANT SELECT ON {db}.* TO '{userName}'@'%' WITH GRANT OPTION;".format(db=db, userName=userName))

        sql.append("FLUSH PRIVILEGES;")

        conn = getDbConnection(config)
        cursor = conn.cursor()
        statements = ''
        if (len(sql) > 1):
            for query in sql:
                result = cursor.execute(query)
                statements = statements + cursor.statement

        # print("config: ", config)
        # print("statements : ", statements)

        cursor.close()
        conn.commit()
        conn.close()

        if (result):
            return result

    # Generate the IAM policy template
    def getIAMPolicyTemplate(resources):
        resourcesArray = []
        for resource in (resources):
            resourcesArray.append(resource)

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "rds-db:connect"
                    ],
                    "Resource": resourcesArray
                }
            ]
        }
        # return JSON.stringify(policy);
        return json.dumps(policy, separators=(',', ':'))  # to be verified at consumption

    # Attach the IAM policy to the respective IAM user
    def manageIAMPolicy(IAMPolicy):
        try:
            data = iam.put_user_policy(
                PolicyDocument=IAMPolicy,
                PolicyName=policyName,
                UserName=username
            )
        except Exception as e:
            data = False
            print("error in manage iam policy : ", e)
        if (data):
            return data
        else:
            return None

    def updateUserSecret():
        params = {
            "SecretId": 'zenarate/users/db/' + username,
            "SecretString": json.dumps(event, separators=(',', ':'))  # JSON.stringify(event)
        }
        try:
            data = secretsmanager.put_secret_value(**(params))
        except Exception as e:
            data = False
            print("error in update secret : ", e)
            print("Creating Secret now!")
            secret_content = json.dumps(event, separators=(',', ':'))
            data = store_or_update_secret(event['username'], event['region'], secret_content)

        if (data):
            return data
        else:
            return None

    def processAcces():
        SecretName = 'zenarate/users/db/' + event['username']
        try:
            secretValue = secretsmanager.get_secret_value(SecretId=SecretName)
            ExitstingSecret = secretValue['SecretString']
        except:
            ExitstingSecret = "{}"
        NewSecret = event
        print("UserDBAccessUpdated", "from: ", ExitstingSecret, 'to: ', NewSecret)

        secretsList = getAllSecrets(event['access'])
        if not secretsList:
            print("No secrets found.")
            return

        resourceSet = set()
        resourceArray = []
        dbUser = username.replace('.', '').split('@')[0].lower()

        for secret in secretsList:
            cred = getSecrets(secret["Name"])
            if not cred:
                print(f"Skipping secret {secret['Name']} due to missing or invalid credentials.")  # if required secret doesn't exist
                continue

            # Else use the values
            config = {
                "host": cred['host'],
                "user": cred['username'],
                "password": cred['password'],
                "database": cred['dbname'],
            }

            dbConn = getDbConnection(config)
            if not dbConn:
                print(f"Skipping secret {secret['Name']} due to DB connection failure.")  # if unable to connect DB, 2 reasons -> db doesn't exist, wrong db name
                continue

            DBDetails = getDBDetails(cred['dbInstanceIdentifier'])
            if not DBDetails:
                print(f"Skipping secret {secret['Name']} due to missing DB instance details.")  # fetching DB resource ID, if not then continue
                dbConn.close()
                continue

            resource = f"arn:aws:rds-db:{region}:186534707636:dbuser:{DBDetails}/{dbUser}" # db resource id used here
            resourceVal = {'resource': resource, 'dbname': cred['dbname']}
            newInstance = resource not in resourceSet

            if 'instanceType' not in cred or cred['instanceType'] != 'replica':
                processUser(dbUser, secret["Access"], config, newInstance)
            else:
                print('Resource Type : replica - skipping user creation.')

            resourceSet.add(resource)
            resourceArray.append(resourceVal)
            dbConn.close()

        if resourceSet:
            IAMPolicy = getIAMPolicyTemplate(resourceSet)
            if IAMPolicy:
                if manageIAMPolicy(IAMPolicy):
                    updateUserSecret()

    print("event : ", event)
    processAcces()