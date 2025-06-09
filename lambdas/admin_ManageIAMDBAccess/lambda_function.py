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

    def getDbConnection(dbConfig):
        mydb = mysql.connector.connect(
            host=dbConfig['host'],
            user=dbConfig['user'],
            password=dbConfig['password'],
            database=dbConfig['database'],
            # multi = dbConfig['multipleStatements']
            # client_flags=[ClientFlag.SSL],
            ssl_ca="certs/rds.pem",
        )
        return mydb

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
    def getSecrets(secret):
        try:
            data = secretsmanager.get_secret_value(SecretId=secret)
        except Exception as e:
            data = False
            print("error in getAllSecrets : ", e)
        if (data):
            return json.loads(data['SecretString'])
        else:
            return None

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

        if (data):
            return data
        else:
            return None

    def processAcces():
        SecretName = 'zenarate/users/db/' + event['username']
        secretValue = secretsmanager.get_secret_value(SecretId=SecretName)
        secretsList = getAllSecrets(event['access'])
        ExitstingSecret = secretValue['SecretString']
        NewSecret = event
        print("UserDBAccessUpdated", "from: ", ExitstingSecret, 'to: ', NewSecret)

        if (secretsList):
            print("region2: ", region)
            resourceSet = set()
            resourceArray = []
            dbUser = username.replace('.', '').split('@')[0].lower()
            secret = None
            print("SecretList: ", secretsList)
            try:

                for secret in secretsList:
                    cred = getSecrets(secret["Name"])
                    if (cred):
                        config = {
                            "host": cred['host'],
                            "user": cred['username'],
                            "password": cred['password'],
                            "database": cred['dbname'],
                            # "multipleStatements": True
                        }

                        # print("Cred: ", cred)

                        DBDetails = getDBDetails(cred['dbInstanceIdentifier'])
                        # print("DBDetails: ", DBDetails)

                        if (DBDetails):
                            resource = "arn:aws:rds-db:{region}:186534707636:dbuser:{DBDetails}/{dbUser}".format(
                                region=region, DBDetails=DBDetails, dbUser=dbUser)
                            # To check whether the instance is processed 1st time or not
                            resourceVal = {'resource': resource, 'dbname': cred['dbname']}

                            # newInstance = not(resourceVal in resourceArray)
                            newInstance = not (resource in resourceSet)

                            # print('newInstance :', newInstance, 'role :', secret["Access"], 'dbUser :', dbUser)

                            if ((not ('instanceType' in cred.keys())) or cred['instanceType'] != 'replica'):
                                users = processUser(dbUser, secret["Access"], config, newInstance)
                            else:
                                print('Resource Type : replica')
                            resourceSet.add(resource)
                            resourceArray.append(resourceVal)
                        else:
                            print('no DBDetails')
            except Exception as e:
                print("error in buiding resourceSet/processUser : ", e)
            # print("hhhhh: ", resourceSet)
            if (len(resourceSet) >= 1):
                print("resourceSet : ", resourceSet)
                IAMPolicy = getIAMPolicyTemplate(resourceSet)
                if (IAMPolicy):
                    print("getIAMPolicyTemplate: ", IAMPolicy)
                    putUserPolicy = manageIAMPolicy(IAMPolicy)
                    if (putUserPolicy):
                        updateduserSecret = updateUserSecret()
                        if (updateduserSecret):
                            print("updateduserSecret : ", updateduserSecret)

                            return True
            else:
                print('no resource in set')

    print("event : ", event)
    processAcces()