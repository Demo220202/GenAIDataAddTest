import mysql.connector
from mysql.connector import Error

from secretKeyFetch import *

def connect_to_rds_and_execute(env, brand_name):

    """
    To establish connection to RDS database and get the data of particular user for package creation

    :param env:
    :param brand_name:
    :return: The data in JSON format that has the variables - user_id, brand_id, account_id, role, url
    """

    global data, cursor, connection

    try:
        data = None
        connection = None

        secret_value = get_secret(env)

        # RDS connection details
        rds_endpoint = secret_value["host"]
        rds_user = secret_value["username"]
        rds_password = secret_value["password"]
        database_name = secret_value["dbname"]

        # Establishing the connection
        connection = mysql.connector.connect(
            host=rds_endpoint,
            user=rds_user,
            password=rds_password,
            database=database_name
        )

        if connection.is_connected():
            print("Successfully connected to AWS RDS MySQL instance.")

            # Create a cursor object
            cursor = connection.cursor()

            # First Query: Set the variable
            first_query = f"""
                        set @brandUrl = (
                            select url 
                            from brand 
                            where name = "{brand_name}" 
                            limit 1
                        )
                        """
            cursor.execute(first_query)
            print("First query executed successfully: Brand URL set.")

            # Second Query: Use the variable
            second_query = """
                        select u.id "user_id", u.password "password", a.id "account_id", a.brandName "brand_id", aa.itemname "role", @brandUrl "url"
                        from user u
                        left join account a on u.account_id = a.id
                        left join AuthAssignment aa on u.id = aa.userid
                        where u.email = concat("brand.admin@", @brandUrl)
                        """
            cursor.execute(second_query)

            # Display the results
            results = cursor.fetchall()
            print("Second query results:")
            data = results
            for row in results:
                print(row)

    except Error as e:
        print(f"Error: {e}")

    finally:
        # Close the connection if it was successfully created
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

            # Conversion of data to json data for ease in other module
            data_json = {
                "user_id": data[0][0],
                "password": data[0][1],
                "account_id": data[0][2],
                "brand_id": data[0][3],
                "role": data[0][4],
                "url": f"{env}-{data[0][5]}" if env != "prod" else data[0][5]
            }

            return data_json


def connect_to_rds_and_execute_email(env, brand_name, email):

    """
    To establish connection to RDS database and get the data of particular user for package creation

    :param env:
    :param brand_name:
    :return: The data in JSON format that has the variables - user_id, brand_id, account_id, role, url
    """

    global data, cursor, connection

    try:
        data = None
        connection = None

        secret_value = get_secret(env)

        # RDS connection details
        rds_endpoint = secret_value["host"]
        rds_user = secret_value["username"]
        rds_password = secret_value["password"]
        database_name = secret_value["dbname"]

        # Establishing the connection
        connection = mysql.connector.connect(
            host=rds_endpoint,
            user=rds_user,
            password=rds_password,
            database=database_name
        )

        if connection.is_connected():
            print("Successfully connected to AWS RDS MySQL instance.")

            # Create a cursor object
            cursor = connection.cursor()

            # First Query: Set the variable
            first_query = f"""
                        set @brandUrl = (
                            select url 
                            from brand 
                            where name = "{brand_name}" 
                            limit 1
                        )
                        """
            cursor.execute(first_query)
            print("First query executed successfully: Brand URL set.")

            # Second Query: Use the variable
            second_query = """
                                    select u.id "user_id", u.password "password", a.id "account_id", a.brandName "brand_id", aa.itemname "role", @brandUrl "url"
                                    from user u
                                    left join account a on u.account_id = a.id
                                    left join AuthAssignment aa on u.id = aa.userid
                                    where u.email = %s
                                    """
            cursor.execute(second_query, (email,))

            # Display the results
            results = cursor.fetchall()
            print("Second query executed successfully.")
            data = results

    except Error as e:
        print(f"Error: {e}")

    finally:
        # Close the connection if it was successfully created
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

            # Conversion of data to json data for ease in other module
            data_json = {
                "user_id": data[0][0],
                "password": data[0][1],
                "account_id": data[0][2],
                "brand_id": data[0][3],
                "role": data[0][4],
                "url": f"{data[0][5]}" if env != "prod" else data[0][5]
            }

            return data_json

def fetch_all_active_brands(env):

    global data, cursor, connection, brand_ids, brand_ids_list

    try:
        data = None
        connection = None

        secret_value = get_secret(env)

        # RDS connection details
        rds_endpoint = secret_value["host"]
        rds_user = secret_value["username"]
        rds_password = secret_value["password"]
        database_name = secret_value["dbname"]

        # Establishing the connection
        connection = mysql.connector.connect(
            host=rds_endpoint,
            user=rds_user,
            password=rds_password,
            database=database_name
        )

        if connection.is_connected():
            print("Successfully connected to AWS RDS MySQL instance.")

            # Create a cursor object
            cursor = connection.cursor()

            cursor.execute("SELECT id FROM brand WHERE inactive = 0")
            brand_ids = cursor.fetchall()

            if not brand_ids:
                raise Exception(f"Brands not found in main_db.")

            brand_ids_list = []

            for brand_id in brand_ids:
                brand_ids_list.append(brand_id[0])

            print(f"✅ Brand ID List : {brand_ids_list}")
            print("Total number of active brands : ", len(brand_ids_list))

    except Error as e:
        print(f"Error: {e}")

    finally:
        # Close the connection if it was successfully created
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

            # Conversion of data to json data for ease in other module

            return brand_ids_list