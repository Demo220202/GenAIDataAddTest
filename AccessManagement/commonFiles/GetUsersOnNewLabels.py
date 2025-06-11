import mysql.connector
# from AzureGenAIResourceRead import *
from rdsConnectNewDBs import *
import json


def db_execution(brand_name, user_email, MAIN_DB_CONFIG, LABEL_DB_CONFIG, labels_list, label_value=None):

    # Connect to databases
    user_id_list = []

    try:

        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        label_db_conn = mysql.connector.connect(**LABEL_DB_CONFIG)

        main_cursor = main_db_conn.cursor(dictionary=True)
        label_cursor = label_db_conn.cursor(dictionary=True)

        # Step 1: Fetch brand_id from main_db
        main_cursor.execute("SELECT id FROM brand WHERE name = %s", (brand_name,))
        brand = main_cursor.fetchone()
        main_db_conn.commit()

        if not brand:
            raise Exception(f"Brand '{brand_name}' not found in main_db.")

        brand_id = brand["id"]
        print(f"✅ Brand ID for '{brand_name}': {brand_id}")

        # Fetch the user_id
        main_cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        user = main_cursor.fetchone()

        user_id = user["id"]
        print(f"User ID for '{user_email}': {user_id}")
        if not user:
            raise Exception(f"Email '{user_email}' not found in main_db.")

        for label in labels_list:

            label_value = label[1]
            print("Label Name : ", label_value)

            label_cursor.execute(
                """
                    select id, config
                    from label_config
                    where name = %s
                """
                , (label[0],))

            label_details = label_cursor.fetchall()

            label_id = label_details[0]["id"]
            label_config = label_details[0]["config"]

            print("Label id : ", label_id)
            print("Label config : ",label_config)
            label_config = json.loads(label_config)

            if label_value.lower() == "all" or label_value == "*":

                main_cursor.execute(
                            """
                                select lva.entity_id as 'user_id', u.username as 'user_name'
                                from label_value_association lva
                                left join user u on lva.entity_id = u.id
                                where lva.label_id = %s and lva.entity_type = 'user' and lva.status = 'ACTIVE';
                            """
                , (label_id,))

                user_ids = main_cursor.fetchall()
                print(user_ids)

                for user_detail in user_ids:
                    user_id_list.append(
                        [user_detail["user_id"], user_detail["user_name"], label[0], label_value])

            else:
                for data_json in label_config["label_values"]:

                    if data_json["inactive"] is False and data_json["label_value"] == label_value:
                        print(data_json)
                        print(data_json["label_value"], "does exist!")

                        main_cursor.execute(
                            """
                                select lva.entity_id as 'user_id', u.username as 'user_name'
                                from label_value_association lva
                                left join user u on lva.entity_id = u.id
                                where lva.label_id = %s and lva.entity_type = 'user' and lva.picklist_value = %s and lva.status = 'ACTIVE';
                            """
                        , (label_id, data_json["label_id"],))

                        user_ids = main_cursor.fetchall()
                        print(user_ids)

                        for user_detail in user_ids:
                            user_id_list.append([user_detail["user_id"], user_detail["user_name"], label[0], label_value])


        print(user_id_list)


    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Close connections
        if main_cursor:
            main_cursor.close()
        if label_cursor:
            label_cursor.close()
        if main_db_conn:
            main_db_conn.close()
        if label_db_conn:
            label_db_conn.close()
        print("🔄 Database connections closed.")

        return brand_id, user_id_list


def fetchUserIds(env, brand_name, user_email, labels_list):

    main_secret, label_secret = get_secret(env)

    MAIN_DB_CONFIG = {
        "host": main_secret["host"],
        "user": main_secret["username"],
        "password": main_secret["password"],
        "database": main_secret["dbname"]
    }

    LABEL_DB_CONFIG = {
        "host": label_secret["host"],
        "user": label_secret["username"],
        "password": label_secret["password"],
        "database": label_secret["dbname"]
    }

    print("Main DB: ", MAIN_DB_CONFIG["database"])
    print("Labels DB: ", LABEL_DB_CONFIG["database"])

    user_ids = db_execution(brand_name, user_email, MAIN_DB_CONFIG,
                            LABEL_DB_CONFIG, labels_list)

    print(user_ids)

    return user_ids

