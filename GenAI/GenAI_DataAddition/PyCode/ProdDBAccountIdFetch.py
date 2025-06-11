import mysql.connector
from AzureGenAIResourceRead import *
from rdsConnectAzure import *
import json

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def db_execution(brand_name, user_email, MAIN_DB_CONFIG, BOT_DB_CONFIG, account_list):
    # Connect to databases
    account_access_ids = {}

    try:

        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        bot_db_conn = mysql.connector.connect(**BOT_DB_CONFIG)

        main_cursor = main_db_conn.cursor(dictionary=True)
        bot_cursor = bot_db_conn.cursor(dictionary=True)

        ### Step 1: Fetch brand_id from main_db
        # brand_name = "Chase"
        main_cursor.execute("SELECT id FROM brand WHERE name = %s", (brand_name,))
        brand = main_cursor.fetchone()
        main_db_conn.commit()

        if not brand:
            raise Exception(f"Brand '{brand_name}' not found in main_db.")

        brand_id = brand["id"]
        print(f"✅ Brand ID for '{brand_name}': {brand_id}")

        # Fetch the user_id
        # user_email = "adityap@zenarate.com"
        main_cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        user = main_cursor.fetchone()

        user_id = user["id"]
        print(f"User ID for '{user_email}': {user_id}")
        if not user:
            raise Exception(f"Email '{user_email}' not found in main_db.")

        main_cursor.execute("SELECT a.id, a.name FROM account a WHERE brandName = %s and inactive = 0", (brand_id,))
        account_ids_details = main_cursor.fetchall()

        print(json.dumps(account_ids_details, indent=4))
        if not account_ids_details:
            raise Exception(f"Account '{account_ids_details}' not found in main_db.")

        account_access_ids = {}

        if len(account_list) == 1 and account_list[0].lower() == "all":
            for account_details in account_ids_details:

                main_cursor.execute(
                    "SELECT usr.id FROM user_switch_role usr LEFT JOIN user u ON usr.user_id = u.id WHERE usr.account_id = %s AND u.email = %s",(account_details["id"], user_email))
                access_id_ls = main_cursor.fetchone()

                print(access_id_ls)

                access_id = access_id_ls["id"]

                account_access_ids[account_details["id"]] = {
                    "access_id": access_id,
                    "name": account_details["name"]
                }
        else:
            for account_details in account_ids_details:
                if account_details["name"] in account_list:

                    main_cursor.execute("SELECT usr.id FROM user_switch_role usr LEFT JOIN user u ON usr.user_id = u.id WHERE usr.account_id = %s AND u.email = %s", (account_details["id"], user_email))
                    access_id_ls = main_cursor.fetchone()

                    print(access_id_ls)

                    access_id = access_id_ls["id"]

                    account_access_ids[account_details["id"]] = {
                        "access_id": access_id,
                        "name": account_details["name"]
                    }

        print(json.dumps(account_access_ids, indent=4))

        ### Step 2: Insert into bot_db service_resources

        # query_variables = getQueryVariables(subscription_id, resource_group_name)

        # for key, value in query_variables.items():
        #
        #     resource_name = key
        #     endpoint = value["endpoint"]
        #     key = value["keys"]
        #     region = value["region"].lower()
        #     type = value["type"]
        #
        #     insert_service_resource = """
        #     INSERT INTO service_resources (brand_id, service, resource_type, resource, resource_id, region, endpoint, `key`)
        #     VALUES (%s, 'Azure', %s, %s, %s, %s, %s, %s)
        #     """
        #
        #     bot_cursor.execute(insert_service_resource, (brand_id, type, resource_name, resource_name, region, endpoint, key))
        #     bot_db_conn.commit()
        #     print("✅ Inserted into service_resources.")
        #
        #     ### Step 3: Fetch newly inserted resource ID
        #     bot_cursor.execute(
        #         "SELECT id FROM service_resources WHERE brand_id = %s AND resource = %s",
        #         (brand_id, resource_name)
        #     )
        #     resource = bot_cursor.fetchone()
        #
        #     if not resource:
        #         raise Exception("❌ Error: Resource ID not found after insert.")
        #
        #     resource_id = resource["id"]
        #     print(f"✅ Fetched Resource ID: {resource_id}")
        #
        #     ### Step 4: Insert into resource_model
        #     insert_resource_model = """
        #     INSERT INTO resource_model (model_type, model_name, resource_id, inactive, created_by, updated_by)
        #     VALUES ('Deployment', 'gpt-4o', %s, 0, %s, %s)
        #     """
        #
        #     bot_cursor.execute(insert_resource_model, (resource_id, user_id, user_id))
        #     bot_db_conn.commit()
        #     print("✅ Inserted into resource_model.")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Close connections
        if main_cursor:
            main_cursor.close()
        if bot_cursor:
            bot_cursor.close()
        if main_db_conn:
            main_db_conn.close()
        if bot_db_conn:
            bot_db_conn.close()
        print("🔄 Database connections closed.")

        return account_access_ids


def fetchAccountAccessIds(env, brand_name, user_email, account_list):

    # env = "prod"
    main_secret, bot_secret = get_secret(env)

    MAIN_DB_CONFIG = {
        "host": main_secret["host"],
        "user": main_secret["username"],
        "password": main_secret["password"],
        "database": main_secret["dbname"]
    }

    BOT_DB_CONFIG = {
        "host": bot_secret["host"],
        "user": bot_secret["username"],
        "password": bot_secret["password"],
        "database": bot_secret["dbname"]
    }

    print(MAIN_DB_CONFIG)
    print(BOT_DB_CONFIG)

    account_ids_details = db_execution(brand_name, user_email, MAIN_DB_CONFIG,
                                       BOT_DB_CONFIG, account_list)

    print(account_ids_details)

    return account_ids_details


# def main():
#
#     env = "prod"
#     main_secret, bot_secret = get_secret(env)
#
#     config = load_config('openai_resources.json')
#
#
#     # Database connection details
#
#     brand_name = "Chase"
#         # "Wolters Kluwer" # as per brand table
#     subscription_id = ""
#         # "fee8cb00-2601-4963-a4f9-793ed834e3ab"
#     resource_group_name = config["resources"][0]["resource_group"]
#     user_email = "adityap@zenarate.com"
#
#     # MAIN_DB_CONFIG = {
#     #     "host": "localhost",
#     #     "user": "root",
#     #     "password": "password",
#     #     "database": "PoC"
#     # }
#     #
#     # BOT_DB_CONFIG = {
#     #     "host": "localhost",
#     #     "user": "root",
#     #     "password": "password",
#     #     "database": "PoC_bot"
#     # }
#
#     MAIN_DB_CONFIG = {
#         "host": main_secret["host"],
#         "user": main_secret["username"],
#         "password": main_secret["password"],
#         "database": main_secret["dbname"]
#     }
#
#     BOT_DB_CONFIG = {
#         "host": bot_secret["host"],
#         "user": bot_secret["username"],
#         "password": bot_secret["password"],
#         "database": bot_secret["dbname"]
#     }
#
#     print(MAIN_DB_CONFIG)
#     print(BOT_DB_CONFIG)
#
#     # Function to execute queries and return results
#     # def execute_query(cursor, query, params=None):
#     #     cursor.execute(query, params or ())
#     #     return cursor.fetchall()
#
#     account_list = ["Branch - Banker", "Branch - Manager"]
#     account_ids_details = db_execution(brand_name, user_email, MAIN_DB_CONFIG, BOT_DB_CONFIG, account_list)
#
#     print(account_ids_details)
#
# if __name__ == "__main__":
#     main()