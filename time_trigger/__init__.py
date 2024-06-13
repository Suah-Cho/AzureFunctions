import azure.functions as func
from azure.storage.blob import BlobServiceClient

import logging
import os
import psycopg2
import pandas as pd
from io import StringIO
import sshtunnel

# Environment variables
storage_connection_string = os.environ["AzureWebJobsStorage"]

ssh_host = os.environ["SSH_HOST"]
ssh_username = os.environ["SSH_USERNAME"]
ssh_key = os.environ["SSH_KEY"]
db_host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]

app = func.FunctionApp()

def insert_blob_to_db(df, con, blob_service_client, container_client, blob):
    try:
        cur = con.cursor()
        for index, row in df.iterrows():
            # logging.info(f"event_time")
            cur.execute("SELECT name FROM devices WHERE device_id = %s;", (row['device_id'],))
            device_name = cur.fetchone()[0]
            cur.execute("SELECT kr_name FROM data_types WHERE id = %s;", (row['data_type'],))
            data_type_name = cur.fetchone()[0]
            # logging.info(f"Device name: {device_name} - Data type name: {data_type_name}")
            cur.execute("INSERT INTO gh_data_item (device_id, device_name, value, data_type_id, data_type_name) VALUES (%s, %s, %s, %s, %s);",
                        (row['device_id'], device_name, row['value'], row['data_type'], data_type_name))
        cur.execute("COMMIT;")

        logging.info("Data inserted successfully")

        cur.close()

        # blob move to done
        try:
            blob_client = container_client.get_blob_client(blob.name)
            new_blob_name = "done/" + blob.name[len("todo-"):]
            new_blob_client = blob_service_client.get_blob_client('data', new_blob_name)
            new_blob_client.start_copy_from_url(blob_client.url)
            blob_client.delete_blob()

            logging.info(f"{blob.name} - Blob moved to done")
        except Exception as e:
            logging.error(f"Failed to move blob: {e}")
    except Exception as e:
        logging.error(f"Failed to insert data: {e}")
        

def process_blob(blob, blob_service_client, container_client, con):

    blob_client = container_client.get_blob_client(blob.name)
    blob_content = StringIO(blob_client.download_blob().readall().decode("utf-8"))
    df = pd.read_csv(blob_content)
    insert_blob_to_db(df, con, blob_service_client, container_client, blob)


def main(mytimer: func.TimerRequest) -> None:
    logging.info("Python Blob trigger function processed.")
    try:
        # Connect to the database
        tunnel = sshtunnel.SSHTunnelForwarder(
                (ssh_host, 22),
                ssh_username=ssh_username,
                ssh_pkey=ssh_key,
                remote_bind_address=(db_host, 5432)
            )

        tunnel.start()

        con = psycopg2.connect(
            host='localhost',
            port=tunnel.local_bind_port,
            database=db_name,
            user=db_user,
            password=db_password
        )

        logging.info("Connection established")

        try:
            # Create BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

            # Get the container client
            container_client = blob_service_client.get_container_client("data")

            # List the blobs in the container
            blob_list = container_client.list_blobs(name_starts_with="todo-")

            # Read the blob content
            for blob in blob_list:
                process_blob(blob, blob_service_client, container_client, con)

        except Exception as e:
            # Failed to read the blob content
            logging.error(f"Failed to read the blob content: {e}")
    except Exception as e:
        # Failed to connect to the database
        logging.error(f"Database Connections Failed!!!: {e}")
    
    logging.info("Python Blob trigger function executed.")


# @app.blob_trigger(arg_name="myblob", path="data/{name}", connection="AzureWebJobsStorage")
# def blob_trigger_func(myblob: func.InputStream):
    

# '''
# 14:00 ~ 15:00 - pair programming
# 디프 알고리즘(?)
# '''