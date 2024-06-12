import logging
import azure.functions as func
import pandas as pd
from io import StringIO
import psycopg2
from sshtunnel import SSHTunnelForwarder
# from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

AzureWebJobsStorage = os.environ['AzureWebJobsStorage']
AZURE_VM_SSH_Key = os.environ['AZURE_VM_SSH_Key']
BlobService = BlobServiceClient.from_connection_string(AzureWebJobsStorage)
# QueueService = QueueServiceClient.from_connection_string(AzureWebJobsStorage)

def getCon():
    try:
        tunnel = SSHTunnelForwarder(
            ('40.82.144.200', 22),
            ssh_username='azureuser',
            ssh_pkey="ssh_key.pem",
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
        logging.error(f"Error connecting to database: {e}", exc_info=True)
        return None

def main(myblob: func.InputStream):

    logging.info("!!!!!!PYTHON BLOB TRIGGER FUNCTION STARTED!!!!!!")

    blob_service_client = BlobService.get_blob_client(container=myblob.container, blob=myblob.name)

    try:
        # Blob 메타데이터 확인
        blob_properties = blob_service_client.get_blob_properties()
        metadata = blob_properties.metadata

        if metadata.get('processed') == 'true':
            logging.info(f"Blob {myblob.name} has already been processed. Skipping.")
            return

        blob_content = myblob.read().decode('utf-8')
        blob_data = StringIO(blob_content)
        df = pd.read_csv(blob_data)
        
        insert_data(df)

        # 메타데이터 업데이트
        metadata['processed'] = 'true'
        blob_service_client.set_blob_metadata(metadata)
        logging.info(f"Blob {myblob.name} processed and metadata updated.")

    except Exception as e:
        logging.error(f"Error processing blob: {e}", exc_info=True)
        # try:
        #     queue_client = QueueService.get_queue_client('failed-data')
        #     logging.info(f"Queue client created: {queue_client}")
        #     queue_client.send_message(blob_content)
        #     logging.info("Failed data sent to Queue Storage.")
        # except Exception as e:
        #     logging.error(f"Error sending to Queue Storage: {e}")

def insert_data(df):
    con = None
    cur = None
    try:
        con = getCon()
        if con is None:
            raise Exception("Database connection could not be established.")
        cur = con.cursor()

        for index, row in df.iterrows():
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
        logging.error(f"Error inserting data: {e}", exc_info=True)
        raise e
    finally:
        if cur:
            cur.close()
        if con:
            con.close()
        logging.info("Database connection closed.")
