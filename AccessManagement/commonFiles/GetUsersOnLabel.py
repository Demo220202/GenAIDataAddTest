import mysql.connector
# from AzureGenAIResourceRead import *
from rdsConnectAzure import *
import json


def db_execution(brand_name, user_email, MAIN_DB_CONFIG, BOT_DB_CONFIG, labels_list):

    # Connect to databases
    user_id_list = []

    try:

        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        bot_db_conn = mysql.connector.connect(**BOT_DB_CONFIG)

        main_cursor = main_db_conn.cursor(dictionary=True)
        bot_cursor = bot_db_conn.cursor(dictionary=True)

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

            main_cursor.execute(
            """
                select u.id as 'user_id', u.username as 'user_name'
                from user u 
                left join user_tag_mappings utm on u.id = utm.user_id 
                left join tags t on utm.tag_id = t.id
                where (t.name = %s) AND (u.inactive = 0 and t.inactive = 0 and utm.inactive = 0)
                order by user_id
            """
            ,(label,))

            user_Ids = main_cursor.fetchall()
            print(user_Ids)

            for user_Id in user_Ids:
                user_id_list.append([user_Id["user_id"], user_Id["user_name"], label])

        print(user_id_list)

        if not user_Ids:
            raise Exception(f"Account '{user_Ids}' not found in main_db.")


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

        return brand_id, user_id_list


def fetchUserIds(env, brand_name, user_email, labels_list):

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

    user_ids = db_execution(brand_name, user_email, MAIN_DB_CONFIG,
                                       BOT_DB_CONFIG, labels_list)

    print(user_ids)

    return user_ids

# fetchUserIds("", "", "")

