import logging
import azure.functions as func
import pandas as pd
from io import StringIO
import psycopg2
from sshtunnel import SSHTunnelForwarder
from azure.storage.queue import QueueServiceClient
import os

AzureWebJobsStorage = os.environ['AzureWebJobsStorage']

def getCon():
    try:
        tunnel = SSHTunnelForwarder(
            ('40.82.144.200', 22),
            ssh_username='azureuser',
            ssh_pkey='~/.ssh/sua-vm_key.pem',
            remote_bind_address=('sua-db.postgres.database.azure.com', 5432)
        )

        tunnel.start()

        con = psycopg2.connect(
            host='localhost',
            port=tunnel.local_bind_port,
            user='postgres',
            password='p@ssw0rd',
            dbname='sua_db'
        )

        return con
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")

def main(myblob: func.InputStream):

    try:
        blob_content = myblob.read().decode('utf-8')
        blob_data = StringIO(blob_content)
        df = pd.read_csv(blob_data)
        insert_data(df)
    except Exception as e:
        logging.error(f"Error processing blob: {e}")
        try:
            queue_client = QueueServiceClient.from_connection_string(AzureWebJobsStorage).get_queue_client('failed-data')
            logging.info(f"Queue client created: {queue_client}")
            queue_client.send_message(blob_content)
            logging.info("Failed data sent to Queue Storage.")
        except Exception as e:
            logging.error(f"Error sending to Queue Storage: {e}")

def insert_data(df):
    try:
        con = getCon()
        cur = con.cursor()
        
        for index, row in df.iterrows():
            # logging.info(f"event_time")
            cur.execute("SELECT name FROM devices WHERE device_id = %s;", (row['device_id'],))
            device_name = cur.fetchone()[0]
            cur.execute("SELECT kr_name FROM data_types WHERE id = %s;", (row['data_type'],))
            data_type_name = cur.fetchone()[0]
            logging.info(f"Device name: {device_name} - Data type name: {data_type_name}")
            cur.execute("INSERT INTO gh_data_item (device_id, device_name, value, data_type_id, data_type_name) VALUES (%s, %s, %s, %s, %s);",
                        (row['device_id'], device_name, row['value'], row['data_type'], data_type_name))
        
        con.commit()
        logging.info("Data inserted successfully.")
    except Exception as e:
        logging.error(f"Error inserting data: {e}")
        raise e
    finally:
        if cur:
            cur.close()
        if con:
            con.close()
        logging.info("Database connection closed.")
